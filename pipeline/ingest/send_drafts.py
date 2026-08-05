# -*- coding: utf-8 -*-
"""Приток, шаг 6: отправить владельцу и партнёру черновики новых карточек.

ЗАЧЕМ. Владелец попросил видеть проект телеграм-поста ДО публикации и проект
карточки ДО появления на сайте — чтобы успеть поправить. Поэтому карточки из
ворот попадают в `static/data/pending.json` (сайт показывает их только по
прямой ссылке #/preview/<id> с плашкой «черновик»), а этот шаг шлёт каждому
проверяющему сообщение: маркер «[черновик <id>]», текст будущего поста, ссылку
на предпросмотр и две кнопки — «Опубликовать» и «Придержать».

КАК ВОЗВРАЩАЕТСЯ РЕШЕНИЕ. Кнопка или ответ на сообщение с исправленным текстом
приходят вебхуком НА САЙТ (он уже принимает /start привязки), сайт пишет их в
таблицу moderation_decisions, а рутина публикации забирает их по
/api/moderation/decisions и применяет approve.py. Напрямую из этого контейнера
решения не прочитать: база сайта в приватной сети хостинга.

ГРУППА ИЛИ ЛИЧНЫЕ СООБЩЕНИЯ — ДВЕ РАЗНЫЕ ВЕЩИ. `TELEGRAM_REVIEW_CHAT_IDS`
(личные id владельца и партнёра) — это ПРАВО решать: вебхук проверяет по нему
того, кто нажал кнопку или ответил, и только его решение засчитывается.
`TELEGRAM_REVIEW_GROUP_ID` (один id общего чата, необязательный) — это АДРЕС
отправки: если задан, черновик уходит туда одной копией, оба видят один и тот
же пост и решение друг друга. Не задан — черновик уходит личным сообщением
каждому из TELEGRAM_REVIEW_CHAT_IDS отдельно, у каждого своя копия кнопок.
Право решать всегда проверяется по личному id (`from.id` в апдейте), а не по
чату, куда упало сообщение, — иначе в группе, где `chat.id` один на всех,
проверка либо пускала бы кого угодно, либо не пускала бы никого.

МОЛЧАНИЕ — СОГЛАСИЕ. Если за сутки никто не ответил, approve.py публикует
карточку как есть: платформа только что починила приток, и снова остановить
его немым шагом было бы повторением тормоза E9. Это написано в самом сообщении.

Запуск:
    python3 pipeline/ingest/send_drafts.py            # план без отправки
    python3 pipeline/ingest/send_drafts.py --write    # отправить
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import format_post                                       # noqa: E402
import telegram_endpoint                                 # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')


def reviewers():
    """Личные id владельца и партнёра — ПРАВО решать, а не адрес отправки.

    Проверяется на стороне вебхука (main.py: `_is_reviewer`) по отправителю
    сообщения или кнопки (`from.id`), а не по чату, в который упало сообщение
    (`chat.id`). Это важно для группы: у всех участников общий `chat.id`, а
    `from.id` у каждого свой.
    """
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',') if x.strip()]


def send_targets():
    """Куда СЛАТЬ черновик — не то же самое, что «кто вправе решать».

    Если задана общая группа (`TELEGRAM_REVIEW_GROUP_ID` — один id, у групп
    Telegram он отрицательный), пост уходит туда ОДИН раз: владелец и партнёр
    видят один и тот же черновик, видят решение друг друга и могут ответить в
    одной ветке. Без группы — прежнее поведение: личное сообщение КАЖДОМУ из
    `TELEGRAM_REVIEW_CHAT_IDS» отдельно; тогда у каждого своя копия кнопок, и
    если один нажмёт «Опубликовать», у другого кнопки останутся нетронутыми
    (актуальное решение всё равно применится — `approve.py` берёт последнее по
    времени, — но со стороны это выглядит нескоординированно).
    """
    group = os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip()
    return [group] if group else reviewers()


def draft_message(card, companies):
    """Первая строка — маркер: по нему вебхук привязывает ответ к карточке."""
    post = format_post.render(card, companies)
    preview = '%s/#/preview/%s' % (SITE, card['id'])
    return ('[черновик %s]\n'
            'Проект поста для канала — ниже. Карточка: %s\n'
            'Кнопки: опубликовать или придержать. Ответ на ЭТО сообщение с '
            'вашим текстом заменит текст поста. Молчание сутки = публикуем как есть.\n'
            '\n%s' % (card['id'], preview, post))


def keyboard(card):
    return {'inline_keyboard': [[
        {'text': '✅ Опубликовать', 'callback_data': 'mod:%s:ok' % card['id']},
        {'text': '✋ Придержать', 'callback_data': 'mod:%s:hold' % card['id']},
    ]]}


def main(write=False):
    if not os.path.exists(PENDING):
        print('Черновиков нет (%s отсутствует).' % os.path.relpath(PENDING, ROOT))
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))
    comps = json.load(open(DATA, encoding='utf-8'))['companies']
    todo = [c for c in pending['cards'] if not c.get('draft_sent')]
    chats = send_targets()
    print('Черновиков без рассылки: %d | адресов отправки: %d%s'
          % (len(todo), len(chats),
             ' (общая группа)' if os.environ.get('TELEGRAM_REVIEW_GROUP_ID') else ''))
    if not todo:
        return 0
    for card in todo[:3]:
        print('\n--- %s ---\n%s' % (card['id'], draft_message(card, comps)[:500]))
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
        for card in todo:
            ok_all = True
            for chat in chats:
                r = client.post(telegram_endpoint.method_url(token, 'sendMessage'), json={
                    'chat_id': chat, 'text': draft_message(card, comps),
                    'reply_markup': keyboard(card), 'disable_web_page_preview': True,
                })
                if not (r.status_code == 200 and r.json().get('ok')):
                    ok_all = False
                    print('  не дошло до %s: %s' % (chat, r.text[:120]))
            if ok_all:
                card['draft_sent'] = True
                sent += 1
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Разослано черновиков: %d' % sent)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
