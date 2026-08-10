# -*- coding: utf-8 -*-
"""Карточка gd378fb8e («ГК «Лакра Синтез» приобрела сеть магазинов «Краски.
Дом маляра»») и профиль предмета (gbae7f513, ООО «Склад красок») несли
отрасль «Пищепром и напитки» — сеть продаёт краски и стройматериалы для
ремонта, а не еду и не напитки. Покупатель (ГК «Лакра Синтез») в базе уже
верно стоит «Химия и удобрения» — производитель лакокрасочных материалов;
сеть его же розницы логично относится к той же отрасли.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. Как и с ProstoKap/«Полипап» — профиль предмета
сам несёт неверную отрасль, менять оба места приходится одной правкой с
`assert` на оба исходных значения, а не таблицей `FIXES`.

Запуск:
    python3 pipeline/fix_kraski_domalyara_industry.py            # сухой прогон
    python3 pipeline/fix_kraski_domalyara_industry.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'gd378fb8e'
COMPANY_ID = 'gbae7f513'
OLD_IND = 'Пищепром и напитки'
NEW_IND = 'Химия и удобрения'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('ind') == OLD_IND, \
        'отрасль сделки уже другая: %r' % deal.get('ind')
    company = data['companies'].get(COMPANY_ID)
    assert company is not None, 'нет профиля %s' % COMPANY_ID
    assert company.get('ind') == OLD_IND, \
        'отрасль профиля уже другая: %r' % company.get('ind')

    print('%s: ind %r -> %r' % (DEAL_ID, OLD_IND, NEW_IND))
    print('%s: ind %r -> %r' % (COMPANY_ID, OLD_IND, NEW_IND))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['ind'] = NEW_IND
    company['ind'] = NEW_IND
    assert deal['ind'] == NEW_IND and company['ind'] == NEW_IND, \
        'отрасль не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
