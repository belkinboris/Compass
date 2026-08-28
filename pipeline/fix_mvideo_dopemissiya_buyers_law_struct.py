# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF), карточка gb5d8a18a (ЦБ зарегистрировал
допэмиссию акций «М.видео» по закрытой подписке, 13 августа 2026): дельта-поиск
дочитал ту же статью «Ведомостей», что уже стоит первым источником карточки, и
нашёл неизвлечённую деталь — конкретные названия четырёх юрлиц-приобретателей.
Карточка уже честно писала «покупатели — не новые инвесторы с открытого рынка,
а сама компания и структуры, связанные с её текущими собственниками», но не
называла их поимённо. Не через review.py: расширение поля, а не новая правка
по отдельной таблице — тот же приём, что уже применялся для похожих находок.

Запуск: python3 pipeline/fix_mvideo_dopemissiya_buyers_law_struct.py
        python3 pipeline/fix_mvideo_dopemissiya_buyers_law_struct.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb5d8a18a'

OLD_STRUCT = (
    'Покупатели размещения - не новые инвесторы с открытого рынка, а сама '
    'компания и структуры, связанные с ее текущими собственниками. В компании '
    'отметили, что решение не связано с изменениями структуры контроля или '
    'какими-либо корпоративными изменениями подобного рода.'
)
STRUCT_ADDITION = (
    ' В круг потенциальных приобретателей ценных бумаг вошли ООО «Кэпиталгард», '
    'ПАО «Эсэфай», ООО «Эсэфай кэпитал», ООО «Лэнбури».'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
