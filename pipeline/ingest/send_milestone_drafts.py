# -*- coding: utf-8 -*-
"""Приток: черновик поста-вехи в консоль (раздел A MILESTONES_BRIEF.md, 22 августа).

ЗАЧЕМ ОТДЕЛЬНЫЙ ШАГ ОТ `send_drafts.py`. Три существующих типа консольных
сообщений (📣 пост, 🗂 карточка, ⚠️ сырьё) устроены вокруг ОДНОЙ сделки; веха
устроена вокруг ОДНОГО СОБЫТИЯ этой сделки (`review.py --milestone <id>
<kind> "<заголовок>" --write` уже поставил `newsworthy`/`headline`/`snapshot`
— см. review.py и REVISION_BRIEF.md). Ввинчивать четвёртый тип в и без того
плотный `build_plan()` `send_drafts.py` рискованнее, чем завести маленький
отдельный скрипт: очередь та же консоль (Telegram-группа), но дедуп, кнопки
и решение — вокруг `event['id']`, а не `deal['id']`.

ЧТО ДЕЛАЕТ ЭТОТ ШАГ. Находит вехи (`newsworthy` + `headline` + вид из
закрытого списка `review.POSTWORTHY_MILESTONE_KINDS`), которым ещё не
отправлен пост (та же проверка, что и на стороне отправки —
`send_telegram.milestone_candidates`, единая функция, не дублируется) И
которым ещё не отправлен ЧЕРНОВИК (`event['milestone_drafted_at']` не
стоит). Отправляет «📌 [веха <id сделки>~<вид>]» с текстом
(`format_post.render_milestone`) и кнопками «пост в канал» / «без поста» —
теми же вердиктами (`post_ok`/`post_no`), что у обычного поста, просто
`deal_id` в `callback_data` несёт вид этапа через `~` (не `:` — тот уже
занят разбором `mod:<id>:<вердикт>`; не `-` — id сделок сами бывают с
дефисами). Молчание сутки после этого черновика = веха выходит — тот же
принцип, что у карточек предпросмотра, отсчёт ведёт `send_telegram.py`'s
`plan_milestones()` от `milestone_drafted_at`, который здесь и проставляется.

Запуск:
    python3 pipeline/ingest/send_milestone_drafts.py            # план без отправки
    python3 pipeline/ingest/send_milestone_drafts.py --write    # отправить
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)                                  # telegram_endpoint в корне
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import format_post                                        # noqa: E402
import send_drafts                                        # noqa: E402  (send_targets/send_one/PAUSE)
import send_telegram                                       # noqa: E402  (milestone_candidates)
import telegram_endpoint                                   # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def milestone_keyboard(deal_id, kind):
    combo = '%s~%s' % (deal_id, kind)
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:%s:post_ok' % combo},
        {'text': '🔕 Без поста', 'callback_data': 'mod:%s:post_no' % combo},
    ]]}


def milestone_message(deal, event):
    header = '📌 [веха %s~%s] — НА КАНАЛ, на проверку\n\n' % (deal['id'], event['kind'])
    return header + format_post.render_milestone(deal, event)


def build_plan():
    data = json.load(open(DATA, encoding='utf-8'))
    milestones = data.get('telegram_milestones') or {}
    undrafted = [(deal, event) for deal, event in send_telegram.milestone_candidates(data['deals'], milestones)
                if not event.get('milestone_drafted_at')]
    plan = [(milestone_message(deal, event), milestone_keyboard(deal['id'], event['kind']), deal, event)
           for deal, event in undrafted]
    return plan, data


def main(write=False):
    plan, data = build_plan()
    chats = send_drafts.send_targets()
    print('Черновиков вех к отправке: %d | адресов: %d' % (len(plan), len(chats)))
    for text, _kb, _deal, _event in plan[:3]:
        print('\n%s\n%s' % ('-' * 40, text[:400]))
    if not plan:
        return 0
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not (write and token and chats):
        if not chats:
            print('\nНи TELEGRAM_REVIEW_GROUP_ID, ни TELEGRAM_REVIEW_CHAT_IDS не заданы — отправлять некому.')
        if not token:
            print('TELEGRAM_BOT_TOKEN не задан — показываю план, не отправляю.')
        if not write:
            print('Сухой прогон. Отправка — с ключом --write.')
        return 0

    import httpx
    sent = 0
    with httpx.Client(timeout=20) as client:
        for i, (text, keyboard, deal, event) in enumerate(plan):
            if i:
                time.sleep(send_drafts.PAUSE)
            ok_all = True
            for chat in chats:
                if not send_drafts.send_one(client, token, chat, text, keyboard):
                    ok_all = False
            if ok_all:
                sent += 1
                event['milestone_drafted_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Отправлено черновиков вех: %d' % sent)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
