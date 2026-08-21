# -*- coding: utf-8 -*-
"""X5 Group/«Форвард-Маркет» (`g99780470`): месячный дообыск нашёл имена
бенефициаров АО «Форвард» (продавца) и судьбу сети «Полушка» после
сделки — временное закрытие в сентябре 2024 и перезапуск под брендом
«Полушка Около» 8 октября 2024 — из источника, отличного от уже
занятого поля `eco.context`. Слияние разовым скриптом.

Запуск: python3 pipeline/fix_x5_forward_market_followup.py           # проверка
        python3 pipeline/fix_x5_forward_market_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g99780470'

OLD_CONTEXT = (
    'ООО «Форвард-Маркет» зарегистрировано в Уфе в мае 2009 года. '
    'Учредителем выступает АО «Форвард», группа управляет сетью '
    'универсамов «Полушка», является крупным дистрибьютором в области '
    'FMCG (товары повседневного спроса).')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Нынешние владельцы «Форварда» не раскрываются — по данным '
    '«Контур.Фокуса», цепочка собственников упирается в нескольких '
    'основных акционеров: Виктора, Галину и Алексея Дроновых, Геннадия '
    'Полякова — и ряд миноритариев. В сентябре 2024 года магазины '
    '«Полушка» временно закрылись для ребрендинга, а 8 октября '
    'обновлённые супермаркеты открылись под новым названием «Полушка '
    'Около».')

NEW_SRCS = [
    ['UFA1.RU', 'https://ufa1.ru/text/business/2024/02/20/73249328/'],
    ['UFA1.RU', 'https://ufa1.ru/text/business/2024/11/22/74357561/'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — бенефициары продавца и судьба «Полушки»' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
