# -*- coding: utf-8 -*-
"""Каталог вычитки, класс E5: «, - » после закрывающей цитаты — 30 полей.

Подкласс класса C1 (« - » как тире), который регулярка C1 не покрывала:
там дефис требовал перед собой букву/цифру/скобку/кавычку, а здесь перед
дефисом стоит ЗАПЯТАЯ — типовая атрибуция прямой речи: «...", - сказал X»
вместо «..., — сказал X». Диапазона после запятой не бывает никогда, так
что замена всегда на длинное тире, без разбора на два случая, как в C1.

Запуск:
    python3 pipeline/fix_comma_hyphen_attribution.py            # сухой прогон
    python3 pipeline/fix_comma_hyphen_attribution.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ECO_FIELDS = ('rationale', 'context', 'share', 'val', 'target_fin', 'fin', 'sum', 'finadv')
LAW_FIELDS = ('struct', 'appr', 'terms')

PAT = re.compile(r',\s*-\s*(?=[а-яёА-ЯЁ])')


def fix_field(text):
    return PAT.sub(', — ', text)


def _self_check():
    assert fix_field('«Avito», - сказал представитель') == \
        '«Avito», — сказал представитель'
    assert fix_field('оформление сделки", - добавил Войцеховский.') == \
        'оформление сделки", — добавил Войцеховский.'
    assert fix_field('регуляторов, - рассказал CNews Гуральник') == \
        'регуляторов, — рассказал CNews Гуральник'
    # запятая без атрибуции цитаты — не трогать (нет буквы сразу после дефиса)
    unchanged = 'значение 5, -3 и 7'
    assert fix_field(unchanged) == unchanged


def get_field(card, path):
    obj = card
    for part in path.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def set_field(card, path, value):
    parts = path.split('.')
    obj = card
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))

    plan = []
    for deal in data['deals']:
        pairs = [('extra', deal.get('extra'))]
        pairs += [('eco.' + k, (deal.get('eco') or {}).get(k)) for k in ECO_FIELDS]
        pairs += [('law.' + k, (deal.get('law') or {}).get(k)) for k in LAW_FIELDS]
        for field, value in pairs:
            if not isinstance(value, str) or not value:
                continue
            new = fix_field(value)
            if new != value:
                plan.append((deal, field, value, new))

    print('Правок «, - » -> «, — »: %d' % len(plan))
    for deal, field, old, new in plan[:8]:
        print('  %s %-13s %r -> %r' % (deal['id'], field, old[-40:], new[-40:]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, field, _old, new in plan:
        set_field(deal, field, new)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
