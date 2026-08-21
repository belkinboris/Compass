# -*- coding: utf-8 -*-
"""Совкомбанк/«Группа Астра» (`g072d8c14`): месячный дообыск нашёл судьбу
аналогичной РЕПО-схемы у того же мажоритария — «Сбербанк КИБ» вёл
параллельную сделку репо с Денисом Фроловым и полностью закрыл свою
позицию 6 июля 2026 года (доля сократилась с 5,3% до 3,4%). Доля
Совкомбанка (5,68%) на актуальном снимке TAdviser не изменилась —
ре-консолидации пакета, о возможности которой писал источник карточки,
пока не произошло. `eco.context` уже занято другим предложением —
дословно объединить с этой цитатой `review.py` не может, правка разовым
скриптом.

ВНИМАНИЕ, не исправлено намеренно: TAdviser называет ДРУГУЮ стартовую
цифру доли Фролова (64,9% на 31.12.2024, а не 62,2%, как в карточке) —
расхождение источников по историческому проценту, не в рамках этой
правки; сама актуальная цифра (52,1%) совпадает и не меняется.

Запуск: python3 pipeline/fix_sovcombank_astra_followup.py           # проверка
        python3 pipeline/fix_sovcombank_astra_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g072d8c14'
OLD_CONTEXT = (
    '«Группа Астра», один из крупнейших в России разработчиков '
    'инфраструктурного программного обеспечения, провела IPO в '
    'октябре 2023 года, с ценой размещения 333 руб. за акцию, однако '
    'на момент сделки цена упала до 291 руб.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Параллельную сделку репо с тем же мажоритарием, Денисом '
    'Фроловым, вёл «Сбербанк КИБ» — 6 июля 2026 года он сообщил о '
    'сокращении своей доли в «Группе Астра» с 5,3% до 3,4%, что '
    'связано с полным закрытием обязательств Фролова перед банком по '
    'сделкам репо. Доля самого Совкомбанка (5,68%) с момента сделки не '
    'изменилась — реконсолидации пакета пока не произошло.')
NEW_SRC = ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:'
           'Группа_Астра_(ранее_ГК_Астра)']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — судьба параллельной РЕПО-схемы Сбербанка' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        if NEW_SRC not in src:
            src.append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
