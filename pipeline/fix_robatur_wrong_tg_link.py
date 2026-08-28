# -*- coding: utf-8 -*-
"""«Южная фабрика стартапов» инвестировала в «Робатур» (`gc7e35605`) —
партнёр владельца заметил (чат «M&A Faces», 27 августа): первая ссылка
карточки (t.me/rusven/7684) ведёт на СОВСЕМ ДРУГУЮ новость канала
«Русский Венчур» (про The Games Fund/Spektra Games), а не на пост про
«Робатур».

КОРЕНЬ (проверено живым забором той же страницы, t.me/s/rusven, 28 августа):
`parse_telegram()` в `pipeline/ingest/fetch.py` до этой сессии собирал даты/
ссылки и тексты постов ДВУМЯ независимыми регэксп-проходами и склеивал их по
ПОЗИЦИИ в списке — а в этой самой ленте пост №7681 не имеет текста (только
фото/форвард), из-за чего список текстов отстал от списка ссылок на 1, и
дальше на 2 (второй пост без текста, 7682) — так текст поста 7686
(«Робатур... привлек инвестиции») попал в паре с url поста 7684. Починено в
`fetch.py` (парсинг блоками сообщений, а не двумя параллельными списками),
это отдельный коммит; здесь — только правка уже осевшей в базе карточки.

Верный адрес (7686) подтверждён живым чтением той же страницы: пост с
текстом «Российский проект "Робатур" привлек инвестиции от университетской
стартап-студии "Южная фабрика стартапов"...» стоит по адресу
t.me/rusven/7686, соседний с ошибочно взятым 7684.

Второй источник карточки (`t.me/s/southernstartupstudio`) — голая ссылка на
канал без номера поста, тот же класс дефекта, что «домен без пути»: заменена
на конкретный пост №24 («Наш стартап ООО «Робатур» на ИННОПРОМ-2026»),
найденный живым забором того же канала — это тот самый пост, из которого
`batch_2026_08_25_ingest_robatur.py` брал цитаты про Александра Абатурова и
ИННОПРОМ-2026 (совпадает дословно с `eco.context` карточки).

Запуск: python3 pipeline/fix_robatur_wrong_tg_link.py           # проверка
        python3 pipeline/fix_robatur_wrong_tg_link.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gc7e35605'
OLD_SRC = [
    ['Телеграм-канал: Русский Венчур', 'https://t.me/rusven/7684'],
    ['Телеграм-канал: Южная фабрика стартапов', 'https://t.me/s/southernstartupstudio'],
]
NEW_SRC = [
    ['Телеграм-канал: Русский Венчур', 'https://t.me/rusven/7686'],
    ['Телеграм-канал: Южная фабрика стартапов', 'https://t.me/southernstartupstudio/24'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card.get('src') == OLD_SRC, (
        'ожидали src=%r, сейчас %r — состояние изменилось' % (OLD_SRC, card.get('src')))

    print('ПРАВИМ %s: src -> rusven/7686 (верный пост) + southernstartupstudio/24 '
          '(конкретный пост вместо голой ссылки на канал)' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['src'] = NEW_SRC
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
