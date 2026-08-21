# -*- coding: utf-8 -*-
"""Mayr-Melnhof/MM Packaging/Granelle (`g57b3b93c`): «Шаг 0» дочитывания
(вычитка карточки КАК ЕСТЬ до нового поиска) нашёл `law.struct` на
НЕМЕЦКОМ языке — предложение перенесено из пресс-релиза австрийского
офиса CMS дословно, без перевода: «CMS hat MM Packaging in der gesamten
Transaktion in allen rechtlichen Belangen beraten.» На русскоязычном
сайте это не мелочь, а нарушение самого продукта («Язык — русский:
интерфейс», CLAUDE.md). `review.py` дословную проверку перевода
провести не может (перевод по определению не литеральная подстрока
исходника), поэтому правка — разовым скриптом с явным переводом и
assert на исходный немецкий текст, а не через таблицу FIXES.

Запуск: python3 pipeline/fix_mm_packaging_german_text.py           # проверка
        python3 pipeline/fix_mm_packaging_german_text.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g57b3b93c'
OLD_STRUCT = ('CMS hat MM Packaging in der gesamten Transaktion in '
              'allen rechtlichen Belangen beraten.')
NEW_STRUCT = ('CMS консультировала MM Packaging по всем юридическим '
              'вопросам на протяжении всей сделки.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law'].get('struct') == OLD_STRUCT, (
        'law.struct изменился с ожидаемого: %r' % card['law'].get('struct'))
    print('ПРАВИМ  %s: law.struct — перевод с немецкого на русский' % CARD_ID)
    if write:
        card['law']['struct'] = NEW_STRUCT
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
