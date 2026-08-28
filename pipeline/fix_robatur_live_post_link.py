# -*- coding: utf-8 -*-
"""Правит УЖЕ ОТПРАВЛЕННЫЙ пост канала о «Робатуре» (`gc7e35605`,
telegram_posts message_id 65) — тот же дефект, что и в данных карточки
(см. fix_robatur_wrong_tg_link.py): строка «Источник» в посте вела на
t.me/rusven/7684 (чужая новость), а не на t.me/rusven/7686 (про «Робатур»).

Стандартный механизм «⟳ Обновлено» (send_telegram.py, load_today_updates)
правит пост только когда факт СДЕЛКИ дописал enrich.py в data/inbox/updates/
за текущий день — это подходит для новых фактов, а не для правки уже
неверной ссылки, внесённой одноразовым скриптом в static/data напрямую.
Поэтому правка live-поста — тоже одноразовая, тем же путём, что и
`send_telegram.py` (editMessageText, тот же импорт), но без строки
«⟳ Обновлено» — это не новый факт о сделке, а исправление цитаты, и молчаливая
правка честнее наигранной «новости» (родня «финстрока из ФНС... молчаливая
дорисовка», П7-9).

Запуск: python3 pipeline/fix_robatur_live_post_link.py           # покажет текст
        python3 pipeline/fix_robatur_live_post_link.py --write   # применит правку в канале
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, ROOT)

import format_post          # noqa: E402
import send_telegram        # noqa: E402

CARD_ID = 'gc7e35605'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == CARD_ID), None)
    assert deal is not None, '%r не найдена' % CARD_ID
    mid = data.get('telegram_posts', {}).get(CARD_ID)
    assert mid, 'у %r нет message_id в telegram_posts — нечего править' % CARD_ID
    assert deal.get('src', [None])[0][1] == 'https://t.me/rusven/7686', (
        'ожидали уже исправленный src в данных (fix_robatur_wrong_tg_link.py --write) — '
        'сейчас %r' % (deal.get('src'),))

    text = format_post.render(deal, data['companies'])
    print('message_id=%s\n---\n%s\n---' % (mid, text))
    if not write:
        print('Сухой прогон. Отправка правки в канал — с ключом --write.')
        return

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID', '') or send_telegram.DEFAULT_CHANNEL
    if not token:
        print('TELEGRAM_BOT_TOKEN не задан — правка не отправлена.')
        return
    with send_telegram._client() as client:
        send_telegram.edit_message(client, token, chat_id, mid, text)
    print('Правка отправлена в канал (editMessageText, message_id=%s).' % mid)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
