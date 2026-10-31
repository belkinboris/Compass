# -*- coding: utf-8 -*-
"""Аудит, раунд 2 (6 сентября 2026): предметом сделки записан ПРОДАВЕЦ.

`g3e3f233c` «Структура «Ростелекома» и «Сбербанка» продала бизнес-центр на
Арбате»: в `target` стоял профиль «Ростелеком», и мультипликатор делил цену
здания (1,55 млрд ₽) на операционную прибыль ПАО «Ростелеком» — «EV/операц.
прибыль ≈ ×0,15» на карточке и в рыночных медианах. Предмет сделки — здание,
профиля у него нет: `target` снимается, предмет — текстом в `asset`.

`g21ef1542` «Ingka Centres продала штаб-квартиру в Химках компании
КЛС-Химки»: в `target` стоял профиль Ingka Centres (продавец), предмет —
здание. Профиль переносится в `seller_id`, предмет — текстом.

Найдено замером по всей базе: имя профиля из `target` стоит в заголовке
ПЕРЕД глаголом продажи и не встречается после него — 17 кандидатов, из них
15 верные («SoftwareONE продала российский бизнес» с предметом «SoftwareONE
(российский бизнес)» — это и есть проданный актив), неверных два, оба здесь.

Запуск: python3 pipeline/fix_audit_round2_wrong_targets.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = {
    'g3e3f233c': {'assert': {'target': 'g00f14033', 'asset': None, 'seller_id': None},
                  'set': {'target': None, 'asset': 'бизнес-центр на Арбате в Москве (6,3 тыс. м²)'}},
    'g21ef1542': {'assert': {'target': 'g088c1281', 'asset': None, 'seller_id': None, 'seller': 'Ingka Centres'},
                  'set': {'target': None, 'seller_id': 'g088c1281', 'seller': None,
                          'asset': 'штаб-квартира Ingka Centres в Химках'}},
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    assert data['companies']['g00f14033']['name'] == 'Ростелеком'
    assert data['companies']['g088c1281']['name'].startswith('Ingka Centres')
    for did, fx in FIXES.items():
        deal = by_id[did]
        for k, v in fx['assert'].items():
            assert deal.get(k) == v, (did, k, deal.get(k))
        print(did, deal['title'][:70])
        for k, v in fx['set'].items():
            print('  %s: %r -> %r' % (k, deal.get(k), v))
            if write:
                if v is None:
                    deal.pop(k, None)
                else:
                    deal[k] = v
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
