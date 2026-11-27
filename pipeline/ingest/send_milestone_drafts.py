# -*- coding: utf-8 -*-
"""Приток: черновик поста-вехи в консоль (раздел A MILESTONES_BRIEF.md, 22 августа).

ЗАЧЕМ ОТДЕЛЬНЫЙ ШАГ ОТ `send_drafts.py`. Три существующих типа консольных
сообщений (📣 пост, 🗂 карточка, ⚠️ сырье) устроены вокруг ОДНОЙ сделки; веха
устроена вокруг ОДНОГО СОБЫТИЯ этой сделки (`review.py --milestone <id>
<kind> "<заголовок>" --write` уже поставил `newsworthy`/`headline`/`snapshot`
— см. review.py и REVISION_BRIEF.md). Ввинчивать четвертый тип в и без того
плотный `build_plan()` `send_drafts.py` рискованнее, чем завести маленький
отдельный скрипт: очередь та же консоль (Telegram-группа), но дедуп, кнопки
и решение — вокруг `event['id']`, а не `deal['id']`.

ЧТО ДЕЛАЕТ ЭТОТ ШАГ. Находит вехи (`newsworthy` + `headline` + вид из
закрытого списка `review.POSTWORTHY_MILESTONE_KINDS`), которым еще не
отправлен пост (та же проверка, что и на стороне отправки —
`send_telegram.milestone_candidates`, единая функция, не дублируется) И
которым еще не отправлен ЧЕРНОВИК (`event['milestone_drafted_at']` не
стоит). Отправляет «📌 [веха <id сделки>~<вид>]» с текстом
(`format_post.render_milestone`) и кнопками «пост в канал» / «без поста» —
теми же вердиктами (`post_ok`/`post_no`), что у обычного поста, просто
`deal_id` в `callback_data` несет вид этапа через `~` (не `:` — тот уже
занят разбором `mod:<id>:<вердикт>`; не `-` — id сделок сами бывают с
дефисами). Веха выходит только по кнопке или ответу (молчание не публикует
с 12 ноября 2026); `milestone_drafted_at`, который здесь проставляется, —
отсчет для напоминания в личку через сутки (remind_undecided.py).

ГОТОВЫЙ ПОСТ — СРАЗУ НА САЙТ (5 октября 2026). Перед черновиком в консоль
тот же текст поста и его кнопки уходят на сайт (`store_on_site`,
`POST /api/ops/milestone-draft`): по кнопке «пост в канал» сайт публикует
этап в основной канал сразу, а не ждет рутину публикации (UniCredit:
конкурент — 19:30, мы — 20:07). Пост с текстом, который не прошел
`check_post.check`, и пост в канал недвижимости на сайт не кладутся — их,
как раньше, выпускает рутина публикации. Сайт недоступен — черновик все
равно уходит в консоль: потерять скорость лучше, чем потерять этап.

ПОВТОРНЫЙ ПОКАЗ ГАСИТ КНОПКИ ПРЕЖНЕГО (27 ноября 2026, бэклог D9). «Арнест»,
12 ноября: заголовок этапа поправили, отметку показа сняли руками — и в консоли
оказалось два живых сообщения с кнопками, 19:32 со старым заголовком и 19:55 с
новым. Теперь при отправке запоминаются номера сообщений
(`event['milestone_draft_msgs']`), а новый показ того же этапа сначала снимает
кнопки с прежнего сообщения (`retire_shown`). Показать заново после правки —
`--resend <id сделки>~<вид>`, отметки руками не снимать.

Запуск:
    python3 pipeline/ingest/send_milestone_drafts.py            # план без отправки
    python3 pipeline/ingest/send_milestone_drafts.py --write    # отправить
    python3 pipeline/ingest/send_milestone_drafts.py --resend <id сделки>~<вид> --write
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
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))        # console_topics

import channels                                           # noqa: E402
import check_post                                         # noqa: E402
import console_topics                                      # noqa: E402
import format_post                                        # noqa: E402
import send_drafts                                       # noqa: E402  (send_targets/send_one/PAUSE)
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
    """Черновик вехи в консоль — с разметкой, как пост в канале
    (`send_one(..., html=True)`): шапку и строку кнопок экранируем, текст
    вехи уже HTML. До 25 сентября 2026 владелец видел в консоли сырые теги."""
    header = ('📌 [веха %s~%s] — %s, на проверку\n'
              'Ниже — пост о новом этапе сделки, как он уйдет подписчикам.\n'
              '━━━━━━━━━━━━\n' % (format_post.esc(deal['id']), format_post.esc(event['kind']),
                                  channels.destination(deal)))
    buttons = format_post.buttons_preview(deal)
    return (header + format_post.render_milestone(deal, event)
            + ('\n\n' + format_post.esc(buttons) if buttons else ''))


def site_draft(deal, event, reply_to=None):
    """Что сайт опубликует по кнопке: текст поста, кнопки и маршрут.
    None — пост сайту не доверяем (не прошел механическую вычитку)."""
    text = format_post.render_milestone(deal, event)
    if check_post.check(text):
        return None
    draft = {'combo': '%s~%s' % (deal['id'], event['kind']), 'event_id': event['id'],
             'text': text, 'buttons': format_post.render_buttons(deal),
             'route': list(channels.channels_for(deal))}
    # номер первого поста о сделке в основном канале: этап выходит ответом на него
    if isinstance(reply_to, int):
        draft['reply_to'] = reply_to
    return draft


def store_on_site(deal, event, client=None, reply_to=None):
    """Положить готовый пост этапа на сайт. True — положили."""
    draft = site_draft(deal, event, reply_to)
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if draft is None or not token:
        return False
    import httpx
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        r = client.post('%s/api/ops/milestone-draft' % site, json={'token': token, **draft})
        return r.status_code == 200
    except Exception as e:                                    # noqa: BLE001
        print('Сайт не принял пост этапа %s (%s) — его выпустит рутина публикации.'
              % (draft['combo'], e))
        return False
    finally:
        if own:
            client.close()


def build_plan(resend=None):
    """`resend` — «<id сделки>~<вид>»: показать этот этап заново, хотя он уже
    показан (правили заголовок или снимок). Вышедший этап заново не показывается:
    `milestone_candidates` его не отдает."""
    data = json.load(open(DATA, encoding='utf-8'))
    milestones = data.get('telegram_milestones') or {}
    undrafted = [(deal, event) for deal, event in send_telegram.milestone_candidates(
                    data['deals'], milestones, data.get('telegram_post_state') or {})
                if (('%s~%s' % (deal['id'], event['kind'])) == resend if resend
                    else not event.get('milestone_drafted_at'))]
    plan = [(milestone_message(deal, event), milestone_keyboard(deal['id'], event['kind']), deal, event)
           for deal, event in undrafted]
    return plan, data


def retire_shown(client, token, event):
    """Снять кнопки с прежнего показа этого этапа: сообщение остается в ленте,
    нажать на нем больше нечего. Сбой (сообщение удалено, старше 48 часов для
    бота без прав) показу не мешает — новый проект поста важнее."""
    for chat, mid in event.get('milestone_draft_msgs') or []:
        try:
            r = client.post(telegram_endpoint.method_url(token, 'editMessageReplyMarkup'),
                            json={'chat_id': chat, 'message_id': mid,
                                  'reply_markup': {'inline_keyboard': []}})
            if r.status_code != 200:
                print('  кнопки прежнего показа не сняты (%s, сообщение %s): %s' % (chat, mid, r.text[:120]))
        except Exception as e:                                # noqa: BLE001
            print('  кнопки прежнего показа не сняты (%s, сообщение %s): %s' % (chat, mid, e))


def stamp(sent_events):
    """Записать отметки показа в СВЕЖЕПРОЧИТАННУЮ базу: отправка идет минуты, и
    `json.dump` снимка, прочитанного до нее, стер бы чужую запись (CLAUDE.md)."""
    data = json.load(open(DATA, encoding='utf-8'))
    by = {(deal['id'], event.get('id')): event for deal in data['deals'] for event in deal.get('events') or []}
    for (deal_id, event_id), (at, msgs) in sent_events.items():
        event = by.get((deal_id, event_id))
        if event is None:
            print('Этап %s сделки %s пропал из базы, пока шла отправка, — отметка показа не записана.'
                  % (event_id, deal_id))
            continue
        event['milestone_drafted_at'] = at
        if msgs:
            event['milestone_draft_msgs'] = msgs
        else:
            event.pop('milestone_draft_msgs', None)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def main(write=False, resend=None, client=None):
    plan, data = build_plan(resend)
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

    sent_events = {}
    thread = console_topics.thread_id('decision')
    own = client is None
    if own:
        import httpx
        client = httpx.Client(timeout=20)
    try:
        for i, (text, keyboard, deal, event) in enumerate(plan):
            if i:
                time.sleep(send_drafts.PAUSE)
            if not store_on_site(deal, event, client,
                                 reply_to=(data.get('telegram_posts') or {}).get(deal['id'])):
                print('Этап %s: сайт сам не опубликует — выпустит рутина публикации.' % event['id'])
            ok_all, msgs = True, []
            for chat in chats:
                if not send_drafts.send_one(client, token, chat, text, keyboard, thread, html=True, sent=msgs):
                    ok_all = False
            if ok_all:
                # Кнопки прежнего показа снимаем ПОСЛЕ того, как новый дошел:
                # иначе при сбое отправки нажать было бы не на что.
                retire_shown(client, token, event)
                sent_events[(deal['id'], event.get('id'))] = (
                    datetime.now(timezone.utc).isoformat(timespec='seconds'), msgs)
    finally:
        if own:
            client.close()
    if sent_events:
        stamp(sent_events)
    print('Отправлено черновиков вех: %d' % len(sent_events))
    return 0


if __name__ == '__main__':
    _resend = None
    if '--resend' in sys.argv:
        _resend = sys.argv[sys.argv.index('--resend') + 1]
    sys.exit(main('--write' in sys.argv, resend=_resend))
