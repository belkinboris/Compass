# -*- coding: utf-8 -*-
"""Заявки на доступ, оставленные на сайте, — в консоль основателей.

ЗАЧЕМ. Сайт шлёт заявку в Telegram сам, в момент регистрации
(`_notify_access_request` в main.py). Но отправка — сетевой вызов, и её сбой
регистрацию НЕ роняет (так и задумано: заявка важнее уведомления). Значит,
заявка может лежать на сайте, а в консоли о ней никто не узнает — и человек
будет ждать доступа, пока кто-нибудь не заглянет в базу.

Этот скрипт закрывает дыру: берёт ожидающих через тот же
`/api/access/requests?token=…`, что и владелец из сессии, и шлёт по каждому
сообщение с кнопками «Одобрить»/«Отклонить». Кнопки несут `acc:<id>:ok|no` —
те же, что у автоматического уведомления, и id берётся ИЗ ОТВЕТА БОЕВОГО
САЙТА, а не откуда-то ещё: 4 сентября 2026 нажатие по кнопке с чужим (взятым
из локальной базы) id одобрило на проде совсем других людей.

Запуск:
    python3 pipeline/send_access_requests.py            # показать, что уйдёт
    python3 pipeline/send_access_requests.py --write    # отправить
    python3 pipeline/send_access_requests.py --write --again   # показать ещё раз
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import telegram_endpoint                                  # noqa: E402
from send_drafts import send_one, PAUSE                   # noqa: E402

SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
# Кого уже показывали. Без этой памяти шаг в почасовой рутине слал бы одну и ту
# же заявку каждый час, пока по ней не нажмут кнопку, — и консоль перестали бы
# читать. В git: контейнер рутины одноразовый.
STATE = os.path.join(HERE, 'access_requests_sent.json')


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding='utf-8'))
    return {"sent": []}


def save_state(state):
    json.dump(state, open(STATE, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, sort_keys=True)


def fetch_pending(token):
    import httpx
    r = httpx.get(SITE + '/api/access/requests', params={'token': token}, timeout=20)
    r.raise_for_status()
    return r.json()


def render(req):
    when = str(req.get('created_at') or '')[:16].replace('T', ' ')
    return "\n".join([
        "🔑 Заявка на доступ к сайту — ждёт решения",
        "%s, %s, %s" % (req.get('full_name') or '—',
                        req.get('company') or 'компания не указана',
                        req.get('position') or 'должность не указана'),
        "Почта: %s" % req.get('email'),
        "Оставлена: %s" % when,
    ])


def main():
    write = '--write' in sys.argv
    token = (os.environ.get('MODERATION_TOKEN') or
             os.environ.get('TELEGRAM_WEBHOOK_SECRET') or '').strip()
    if not token:
        print('Нет токена (MODERATION_TOKEN / TELEGRAM_WEBHOOK_SECRET) — сайт не ответит.')
        return 1

    data = fetch_pending(token)
    pending = data.get('pending') or []
    state = load_state()
    again = '--again' in sys.argv
    fresh = [r for r in pending if again or r['id'] not in state['sent']]
    print('Ждут решения: %d (из них не показывали: %d) | уже с доступом: %s | дверь закрыта: %s'
          % (len(pending), len(fresh), data.get('approved_count'), data.get('gate')))
    if not fresh:
        print('Отправлять нечего.')
        return 0
    pending = fresh

    bot = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = [x.strip() for x in
             (os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '') or
              os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '')).split(',') if x.strip()]
    for req in pending:
        print('\n' + render(req))
        print('   кнопки: acc:%d:ok / acc:%d:no' % (req['id'], req['id']))
    if not write:
        print('\nСухой прогон. Отправить: --write')
        return 0
    if not bot or not chats:
        print('\nОтправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.')
        return 1

    import httpx
    import time
    sent = 0
    with httpx.Client(timeout=20) as client:
        for i, req in enumerate(pending):
            keys = {'inline_keyboard': [[
                {'text': '✅ Одобрить', 'callback_data': 'acc:%d:ok' % req['id']},
                {'text': '🗑 Отклонить', 'callback_data': 'acc:%d:no' % req['id']}]]}
            ok = all(send_one(client, bot, chat, render(req), keys) for chat in chats)
            if ok and req['id'] not in state['sent']:
                state['sent'].append(req['id'])
                save_state(state)
            sent += 1 if ok else 0
            print('  %s заявка #%d' % ('отправлено' if ok else 'НЕ ДОШЛО', req['id']))
            if i < len(pending) - 1:
                time.sleep(PAUSE)
    print('Отправлено: %d из %d' % (sent, len(pending)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
