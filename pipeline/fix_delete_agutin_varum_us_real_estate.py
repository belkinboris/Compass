# -*- coding: utf-8 -*-
"""Удаляет карточку `gb57df995` («Агутин и Варум вложили миллионы
долларов в недвижимость в США») — просьба партнёра владельца (чат
«M&A Faces», 27 августа: «Попроси это удалить плиз»), переданная
владельцем. Класс ровно тот, что CLAUDE.md называет «почти всегда мимо»:
жилая недвижимость физлиц («если какой-то физик просто купил, всё
равно») плюс нероссийский контур (США) без значимой российской стороны —
`buyer_name` держит текстом «Агутин и Варум», профиля компании нет,
`target`/`seller_id` пусты, сирот в COMPANIES не остаётся.

Правки review.py к этой карточке (шесть записей одного файла,
`pipeline/ingest/fixes/batch_daily_2026_08_23.py`) сняты ДО этого скрипта
вместе — обязательный порядок (см. CLAUDE.md, «Слияние дублей обязано
снять правки к удалённой карточке вместе с ней» — тот же урок применим и
к прямому удалению).

Пост в канале (telegram_posts: 58) удаляется ОТДЕЛЬНО, до этого скрипта,
через Bot API `deleteMessage` (бот — админ канала) — если вызов не
пройдёт (например, истёк срок или пост уже удалён вручную), скрипт всё
равно снимает карточку и запись `telegram_posts`: застрявший пост в
канале хуже, чем расхождение на один message_id.

Запуск: python3 pipeline/fix_delete_agutin_varum_us_real_estate.py                 # проверка
        python3 pipeline/fix_delete_agutin_varum_us_real_estate.py --delete-post   # удалить пост в канале
        python3 pipeline/fix_delete_agutin_varum_us_real_estate.py --write         # снять карточку из базы
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'gb57df995'


def delete_channel_post():
    import telegram_endpoint
    import send_telegram
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not token:
        print('TELEGRAM_BOT_TOKEN не задан — пост в канале не тронут.')
        return
    data = json.load(open(DATA, encoding='utf-8'))
    mid = data.get('telegram_posts', {}).get(CARD_ID)
    if not mid:
        print('В telegram_posts нет message_id для %s — удалять нечего.' % CARD_ID)
        return
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID', '') or send_telegram.DEFAULT_CHANNEL
    with send_telegram._client() as client:
        r = client.post(telegram_endpoint.method_url(token, 'deleteMessage'),
                         json={'chat_id': chat_id, 'message_id': mid})
        body = r.json()
    if body.get('ok'):
        print('Пост message_id=%s удалён из канала.' % mid)
    else:
        print('deleteMessage не удался (message_id=%s): %s' % (mid, body.get('description')))
        print('Карточка из базы всё равно будет снята — если пост остался в канале, '
              'message_id=%s нужно удалить вручную.' % mid)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    before = len(data['deals'])
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена — уже удалена?' % CARD_ID
    assert card.get('buyer') is None and card.get('target') is None and card.get('seller_id') is None, (
        'у карточки есть связанные профили компаний — удаление может осиротить их, проверьте вручную')

    print('УДАЛЯЕМ %s: %s' % (CARD_ID, card['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    data['deals'] = [c for c in data['deals'] if c['id'] != CARD_ID]
    assert len(data['deals']) == before - 1
    data.get('telegram_posts', {}).pop(CARD_ID, None)
    data.get('telegram_milestones', {}).pop(CARD_ID, None)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: карточка и запись telegram_posts удалены.')


if __name__ == '__main__':
    if '--delete-post' in sys.argv:
        delete_channel_post()
    else:
        main(write='--write' in sys.argv)
