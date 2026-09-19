# -*- coding: utf-8 -*-
"""Заявки «уточнить/дополнить», оставленные посетителями сайта, — в консоль.

ЗАЧЕМ. `POST /api/deals/{id}/corrections` и `POST /api/corrections` пишут
только в таблицу `correction_requests` — до 19 сентября 2026 это был
чисто write-only канал: ни экрана, ни скрипта, который бы его читал, не
было вовсе (см. KNOWN_ISSUES.md). Заявка могла годами лежать в базе, и
единственный способ её увидеть — прямой SQL-запрос к боевой базе. Этот
скрипт закрывает дыру тем же приёмом, что и `send_access_requests.py`:
берёт ожидающих через мост `/api/corrections/pending?token=…`, шлёт каждую
в тему консоли «Заметки от пользователей» и, в отличие от заявок на доступ
(те остаются в базе как аккаунты), УДАЛЯЕТ показанные через
`/api/corrections/consume` — постоянное место текста теперь Telegram, а не
эта таблица (владелец 19 сентября 2026: «если они засоряют базу данных, то
нужно их оттуда убирать»).

Заголовок сообщения называет сделку по имени, а не по голому id: для этого
скрипт читает `static/data/deals_promoted.json` из локального чекаута (то
же самое имя даже проще, чем ходить за ним на сайт) и учитывает `merged` —
карточка могла с тех пор слиться с другой.

Запуск:
    python3 pipeline/send_corrections_to_console.py            # показать, что уйдёт
    python3 pipeline/send_corrections_to_console.py --write    # отправить и удалить показанное
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import console_topics                                      # noqa: E402
import site_bridge                                         # noqa: E402
from send_drafts import send_one, PAUSE                   # noqa: E402

SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def _token():
    return (os.environ.get('MODERATION_TOKEN') or
            os.environ.get('TELEGRAM_WEBHOOK_SECRET') or '').strip()


def fetch_pending(token):
    return site_bridge.get_json('/api/corrections/pending',
                                {'token': token}).get('corrections') or []


def consume(token, ids):
    return site_bridge.post_json('/api/corrections/consume',
                                 {'token': token, 'ids': ids}).get('deleted', 0)


def _deal_label(deal_id, deals_by_id, merged):
    """Название сделки для заголовка сообщения — или честная причина, если
    карточки больше нет (удалена без редиректа) или она никогда не была
    привязана (сообщение из футера)."""
    if not deal_id:
        return None, None
    real_id = merged.get(deal_id, deal_id)
    deal = deals_by_id.get(real_id)
    if not deal:
        return None, deal_id
    return deal.get('title') or real_id, real_id


def render(row, deals_by_id, merged):
    when = str(row.get('created_at') or '')[:16].replace('T', ' ')
    lines = ["📝 Уточнение с сайта"]
    label, real_id = _deal_label(row.get('deal_id'), deals_by_id, merged)
    if label:
        lines.append("По сделке: %s" % label)
        lines.append("%s/#/deal/%s" % (SITE, real_id))
    elif real_id:
        lines.append("По сделке %s — карточка не найдена (удалена или объединена с другой)" % real_id)
    else:
        lines.append("Общее сообщение (не привязано к карточке)")
    lines.append("")
    lines.append(row.get('body') or '')
    if row.get('contact'):
        lines.append("")
        lines.append("Контакт: %s" % row['contact'])
    lines.append("")
    lines.append("Оставлено: %s" % (when or '?'))
    return "\n".join(lines)


def main():
    write = '--write' in sys.argv
    token = _token()
    if not token:
        print('Нет токена (MODERATION_TOKEN / TELEGRAM_WEBHOOK_SECRET) — сайт не ответит.')
        return 1

    # Отказ сайта — не повод падать трассировкой: рутина обязана сказать
    # человеку, ЧТО именно не так. 19 сентября 2026 первый реальный прогон
    # получил от сайта страницу приложения (эндпоинт ещё не выложен) и
    # сообщил об этом JSONDecodeError'ом — диагноз пришлось искать руками.
    try:
        pending = fetch_pending(token)
    except site_bridge.BridgeUnavailable as e:
        print('Заявки забрать не удалось: %s' % e.reason)
        print('ИТОГ ПРОГОНА: сайт не отдал заявки (отправлено=0, удалено=0).')
        return 1
    print('Ждут отправки в консоль: %d' % len(pending))
    if not pending:
        print('ИТОГ ПРОГОНА: отправлять нечего (отправлено=0, удалено=0).')
        return 0

    base = json.load(open(DATA, encoding='utf-8'))
    deals_by_id = {d['id']: d for d in base['deals']}
    merged = base.get('merged', {})

    for row in pending:
        print('\n' + render(row, deals_by_id, merged))

    if not write:
        print('\nСухой прогон. Отправить: --write')
        print('ИТОГ ПРОГОНА: сухой прогон, ничего не отправлено (отправлено=0, удалено=0).')
        return 0

    bot = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = console_topics.console_chats()
    if not bot or not chats:
        print('\nОтправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.')
        print('ИТОГ ПРОГОНА: консоли нет, ничего не отправлено (отправлено=0, удалено=0).')
        return 1

    import httpx
    import time
    thread = console_topics.thread_id('user_notes')
    sent_ids = []
    with httpx.Client(timeout=20) as client:
        for i, row in enumerate(pending):
            text = render(row, deals_by_id, merged)
            ok = all(send_one(client, bot, chat, text, None, thread) for chat in chats)
            print('  %s заявка #%d' % ('отправлено' if ok else 'НЕ ДОШЛО', row['id']))
            if ok:
                sent_ids.append(row['id'])
            if i < len(pending) - 1:
                time.sleep(PAUSE)

    try:
        deleted = consume(token, sent_ids) if sent_ids else 0
    except site_bridge.BridgeUnavailable as e:
        # Сообщения уже ушли в консоль — это главное; не удалённые из базы
        # заявки придут повторно следующим прогоном, и об этом надо сказать.
        print('Отправлено в консоль, но из базы не удалено: %s' % e.reason)
        print('ИТОГ ПРОГОНА: отправлено %d, удалено 0 — эти же заявки придут ещё раз.'
              % len(sent_ids))
        return 1
    print('\nОтправлено: %d из %d, удалено из базы: %d' % (len(sent_ids), len(pending), deleted))
    print('ИТОГ ПРОГОНА: отправлено %d, удалено %d.' % (len(sent_ids), deleted))
    return 0


if __name__ == '__main__':
    sys.exit(main())
