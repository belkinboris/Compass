# -*- coding: utf-8 -*-
"""Каталог вычитки, класс E3: голый id профиля в текстовом поле стороны.

Продавец/покупатель хранится ДВУМЯ способами: ссылкой на профиль
(`seller_id`/`buyer`) или именем текстом (`seller`/`buyer_name`). У трёх
карточек в текстовом поле лежал не текст, а служебный id профиля («g...»,
«c...») — на экране показывался бы этот id вместо имени компании. Найдено
чтением у cc16fce80 (починена в круге 4), сплошной прогон нашёл ещё две.

Во всех трёх id ссылается на РЕАЛЬНЫЙ существующий профиль с настоящим
именем — правка безопасна: id просто переносится в правильное поле
(`seller_id`), а не придумывается заново.

Запуск:
    python3 pipeline/fix_bare_profile_id_in_party_field.py            # сухой прогон
    python3 pipeline/fix_bare_profile_id_in_party_field.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PAT = re.compile(r'^[gc][0-9a-f]{8}$')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    plan = []
    for d in data['deals']:
        for text_field, ref_field in (('seller', 'seller_id'), ('buyer_name', 'buyer')):
            v = d.get(text_field)
            if isinstance(v, str) and PAT.match(v.strip()) and v.strip() in comps:
                plan.append((d, text_field, ref_field, v.strip()))

    print('Карточек с голым id профиля: %d' % len(plan))
    for d, text_field, ref_field, pid in plan:
        print('  %s %s=%r -> %s=%r (%s)' % (
            d['id'], text_field, pid, ref_field, pid, comps[pid]['name']))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for d, text_field, ref_field, pid in plan:
        d[text_field] = None
        d[ref_field] = pid

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
