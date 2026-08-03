# -*- coding: utf-8 -*-
"""Ссылка на издание внутри суммы — убрать, число оставить.

ЗАЧЕМ. Перенос «Дополнительной информации» по полям взял сумму из пометки
компактного импорта «Сумма: 17,7 млрд руб. (191,5 млн долл. по данным
Financial Times)». Скобка здесь — не уточнение числа, а ссылка на издание, и
после нормализации валюты значок склеился со словом: «191,5 млн $по данным
Financial Times». Это поймал `test_currency_symbol_not_glued_to_next_word`.

ПОЧЕМУ НЕ ПРАВИТЬ ОБЩИМ ПРАВИЛОМ. `normalize_sum.py` намеренно не выбрасывает
скобки с цифрами: «$2 млрд (по $59 за акцию)» — это объяснение числа, и его
надо сохранить. Здесь цифры в скобке тоже есть, но они лишь пересчёт той же
суммы в другой валюте плюс имя издания — а имя издания на обложке не нужно:
оно видно по ссылке на источник (то же соображение, что «пометка
недостоверности — только «(по оценке)», без имени оценщика»).

Скобка не выбрасывается насовсем: полное предложение с пересчётом и ссылкой
на Financial Times остаётся в «Дополнительной информации» той же карточки.

Запуск:
    python3 pipeline/fix_source_note_inside_sum.py            # сухой прогон
    python3 pipeline/fix_source_note_inside_sum.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g96da922c'
WAS = '17,7 млрд ₽ (191,5 млн $по данным Financial Times)'
NOW = '17,7 млрд ₽'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal is not None, 'карточки %s нет в базе' % DEAL_ID
    assert deal.get('sum') == WAS, 'обложка сейчас %r, а не %r' % (deal.get('sum'), WAS)
    # Пересчёт и ссылка на издание обязаны остаться в тексте карточки: мы
    # убираем их с обложки, а не из базы.
    assert 'Financial Times' in str(deal.get('extra') or ''), \
        'пересказ с ссылкой на издание пропал из «Дополнительной информации»'

    print('%s  %s' % (DEAL_ID, str(deal.get('title'))[:62]))
    print('   обложка: %r -> %r' % (deal.get('sum'), NOW))
    print('   линза:   %r -> %r' % ((deal.get('eco') or {}).get('sum'), NOW))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NOW
    deal.setdefault('eco', {})['sum'] = NOW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
