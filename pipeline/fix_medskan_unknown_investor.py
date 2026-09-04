# -*- coding: utf-8 -*-
"""Заметка 515 (консоль, 4 сентября 2026): «Пишем, что неизвестный
инвестор и в комментариях можно добавить, что есть новости, что это
ГПБ, но ссылку надо не забыть», отвечая на карточку `g2197ed53»
(«Газпромбанк может стать акционером сети медицинских центров
«Медскан»»).

Ни сама компания, ни Газпромбанк сделку публично не подтвердили (уже
записано в eco.context); Туголуков на прямой вопрос ответил «Нет, не
про это». Владелец решил: раз имя конкретного инвестора не подтверждено
ни одной стороной, заголовок и `buyer` должны называть его честно
неизвестным, а версия про ГПБ остаётся в тексте как неофициальная, со
ссылкой на источник.

Запуск: python3 pipeline/fix_medskan_unknown_investor.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g2197ed53'
OLD_TITLE = 'Газпромбанк может стать акционером сети медицинских центров «Медскан»'
NEW_TITLE = 'Неизвестный инвестор может стать акционером сети медицинских центров «Медскан»'
OLD_BUYER = 'gf1f56e08'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {c['id']: c for c in data['deals']}
    card = by_id[CARD_ID]
    assert card['title'] == OLD_TITLE, card['title']
    assert card['buyer'] == OLD_BUYER, card['buyer']
    assert card.get('buyer_name') is None

    card['title'] = NEW_TITLE
    card['buyer'] = None
    card['buyer_name'] = 'неизвестный инвестор'

    print(f'{CARD_ID}: заголовок и покупатель переписаны — «неизвестный инвестор», версия про ГПБ осталась в тексте')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
