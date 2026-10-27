# -*- coding: utf-8 -*-
"""Показать владельцу в консоли общий пост указа № 738 — обычным сообщением
«📣 [пост g8a599c40]» с кнопками «Пост в канал» / «Без поста» / ✏️.

ЗАЧЕМ ОТДЕЛЬНЫЙ ЗАПУСК. Решение владельца 16 октября 2026: пять карточек
указа (Tarkett, «Каппа Рус», «Менсен Пакаджинг СНГ», «Онтэкс РУ», «Эвиосис
Пэкэджинг Кубань») — на сайт по отдельности, в канал — один общий пост. Пост
записан у Tarkett (`post_override` + `post_covers`,
`pipeline/fix_temporary_management_type_2026_10_16.py`). `send_drafts.py`
второй раз проект поста этой карточки не покажет: под прежним одиночным
проектом уже есть нажатие («Пост в канал», 07:10 UTC), и
`send_drafts.answered_cards()` правильно не шлет новую версию поверх
непримененного ответа. Здесь ответ относится к старому тексту, а новый текст
— новое решение владельца, поэтому сообщение уходит этим скриптом, теми же
функциями (`post_message_text`, `post_keyboard`, `send_one`, тема
«Подтверждение постов»).

Порядок: pending.json с общим постом закоммичен и доехал до сайта — скрипт
сам сверяет это с сайтом и без этого ничего не шлет.

Запуск:
    python3 pipeline/send_joint_post_2026_10_16.py            # показать, что уйдет
    python3 pipeline/send_joint_post_2026_10_16.py --write    # отправить в консоль
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import send_drafts  # noqa: E402
import console_topics  # noqa: E402

LEAD = 'g8a599c40'
PENDING = send_drafts.PENDING


def site_has_joint_post(card):
    """Сайт отдает pending.json, где у карточки тот же общий пост."""
    try:
        import httpx
        r = httpx.get('%s/static/data/pending.json' % send_drafts.SITE,
                      params={'nocache': os.getpid()}, timeout=20)
        site = {c.get('id'): c for c in r.json().get('cards', [])}
    except Exception as e:                                   # noqa: BLE001
        print('Сайт не ответил (%s) — не отправляю.' % e)
        return False
    live = site.get(card['id']) or {}
    return live.get('post_override') == card['post_override'] \
        and live.get('post_covers') == card['post_covers']


def main(write):
    raw = open(PENDING, encoding='utf-8').read()
    pending = json.loads(raw)
    card = next(c for c in pending['cards'] if c['id'] == LEAD)
    assert card.get('post_override') and card.get('post_covers'), 'у карточки нет общего поста'
    comps = json.load(open(send_drafts.DATA, encoding='utf-8'))['companies']
    rendered = send_drafts.draft_post_text(card, comps)
    text = send_drafts.post_message_text(card, comps, rendered=rendered)
    print(text)
    if card.get('post_draft_sent') and card.get('post_preview') == rendered:
        print('\nЭтот текст уже показан в консоли — повторно не шлю.')
        return 0
    if not site_has_joint_post(card):
        print('\nСайт еще не отдает pending.json с общим постом — сначала push и деплой данных.')
        return 1
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chats = send_drafts.send_targets()
    if not write or not token or not chats:
        print('\nСухой прогон (или нет токена/адреса консоли). Отправка — с ключом --write.')
        return 0
    import httpx
    thread = console_topics.thread_id('decision')
    ok = True
    with httpx.Client(timeout=20) as client:
        for chat in chats:
            ok = send_drafts.send_one(client, token, chat, text, send_drafts.post_keyboard(card),
                                      thread, html=True) and ok
    if not ok:
        print('Не дошло — отметку не ставлю.')
        return 1
    if open(PENDING, encoding='utf-8').read() != raw:
        pending = json.load(open(PENDING, encoding='utf-8'))
        card = next(c for c in pending['cards'] if c['id'] == LEAD)
    card['post_draft_sent'] = True
    card['post_preview'] = rendered
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nОтправлено в консоль (адресов: %d).' % len(chats))
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
