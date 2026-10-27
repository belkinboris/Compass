# -*- coding: utf-8 -*-
"""Профиль g6921da17 («Фонд развития территорий», продавец в gba764f10)
ловится check_post.py как родовое описание вместо имени: ORG_ROLE матчит
слово «Фонд» в начале, а дальше идет обычное (не в кавычках) продолжение
названия — ровно так пишутся официальные госфонды по-русски («Фонд
социального страхования», «Фонд капитального ремонта»), но регэксп
рассчитан на случаи вида «Фонд под управлением …» и не отличает одно от
другого. Чинится не регэкспом (риск для всей базы), а точным именем:
полное официальное имя — ППК «Фонд развития территорий» (так оно и
значится в прессе и у самой организации) — начинается с «ППК», не «Фонд»,
и несет собственное название в кавычках, как положено.

Запуск:
    python3 pipeline/fix_frt_profile_name_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_frt_profile_name_2026_10_16.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
COMPANY_ID = 'g6921da17'
OLD_NAME = 'Фонд развития территорий'
NEW_NAME = 'ППК «Фонд развития территорий»'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][COMPANY_ID]
    assert comp['name'] == OLD_NAME, 'name уже не %r: %r' % (OLD_NAME, comp['name'])
    print('%s: name %r -> %r' % (COMPANY_ID, OLD_NAME, NEW_NAME))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fc = fresh['companies'][COMPANY_ID]
    assert fc['name'] == OLD_NAME, 'name поменяли параллельно — перечитайте'
    fc['name'] = NEW_NAME
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
