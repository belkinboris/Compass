# -*- coding: utf-8 -*-
"""Карточка g0924279f («Дмитрий Хотимский инвестировал в ProstoKap») и профиль
предмета (gb316113e, ООО «Полипап») несли отрасль «Пищепром и напитки» —
а ProstoKap производит бумажные стаканы и крышки для них, то есть саму
упаковку, а не еду и не напитки.

ПОЧЕМУ «ПРОИЗВОДСТВО ТАРЫ», А НЕ «ПИЩЕПРОМ». Граница уже проведена в
CLAUDE.md по ПРОДУКТУ: «производит саму упаковку — в тару». Источник
(kommersant.ru/doc/8516012) прямо называет предмет «производством бумажных
стаканов и крышек для них» — ровно тот случай, а не сырьё/краски ДЛЯ
упаковки (которые остаются химией) и не готовая еда/напиток в этой таре.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `industry_is_supported()` для `ind` либо ищет
слово словаря `industry_by_words` в цитате (в словаре для «Производство
тары» нет стема на «стакан»/«полипап», расширять ради одной карточки не
нужно), либо профиль компании с ТЕМ ЖЕ `ind`, что и предлагаемое значение —
а профиль предмета сейчас сам несёт неверную отрасль, править который надо
той же правкой. Меняются оба места разом, с `assert` на оба исходных
значения.

Запуск:
    python3 pipeline/fix_prostokap_industry.py            # сухой прогон
    python3 pipeline/fix_prostokap_industry.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'g0924279f'
COMPANY_ID = 'gb316113e'
OLD_IND = 'Пищепром и напитки'
NEW_IND = 'Производство тары'


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
