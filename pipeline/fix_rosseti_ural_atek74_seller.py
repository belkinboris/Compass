# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g66c6db22 («Россети Урал»
приобрело 100% доли в «АТЭК74»): дельта-поиск нашёл прежнего владельца
(100% принадлежало «Группе Голос» — материнской структуре застройщика
«Голос.Девелопмент») и подтвердил, что сделка была возмездной, а не
безвозмездной передачей бесхозных сетей: совет директоров «Россети
Урал» отдельно рассматривал именно цену приобретаемого имущества,
финансирование — за счёт нетарифных источников, а не заёмных средств.
Точная сумма нигде не названа. Не через review.py: seller — структурное
поле, не проверяется дословной цитатой одного источника.

Запуск: python3 pipeline/fix_rosseti_ural_atek74_seller.py
        python3 pipeline/fix_rosseti_ural_atek74_seller.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g66c6db22'

OLD_SELLER = None
NEW_SELLER = 'Группа Голос'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'До сделки 100% «АТЭК74» принадлежало «Группе Голос» — материнской '
    'структуре застройщика «Голос.Девелопмент» (бывшая СК «Легион»). '
    'Сделка была возмездной: совет директоров «Россети Урал» отдельно '
    'рассматривал цену приобретаемого имущества, а финансирование таких '
    'приобретений компания ведёт за счёт нетарифных источников, не '
    'заёмных средств. Точная сумма сделки не раскрывалась.'
)

NEW_SRC = ['boomin.ru', 'https://boomin.ru/kompanii/birzhevyye-kompanii/gruppa-golos/tab/companies']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') == OLD_SELLER
    assert deal['eco']['context'] == OLD_CONTEXT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src'])

    print('=== seller ===', NEW_SELLER)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===', NEW_SRC)

    if write:
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = 'text'
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
