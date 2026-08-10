# -*- coding: utf-8 -*-
"""Отрасли профилей компаний вне справочника INDUSTRIES.

ЧТО СЛОМАНО. `test_industries_are_from_the_known_list` проверяет отрасль
только у СДЕЛОК, не у компаний — тот же справочник `INDUSTRIES` в фильтре
каталога компаний (`<select id="coind">`) собран из канонического списка, а
`companyRows()` фильтрует строго `c.ind===coInd`. У четырёх профилей `ind`
не входит в список вовсе: «Металлургия» (Evraz, Челябинский завод
металлоконструкций), «Нефтесервис» (Baker Hughes), «Промышленность»
(Роскосмос). Эти четыре профиля НИКОГДА не найдутся ни по одному пункту
фильтра отрасли на «Компаниях» — только через поиск по имени или прямую
ссылку со страницы сделки. Дефект не ловится ни одним существующим
тестом, потому что тот единственный, что мог бы, смотрит не туда.

ЧТО ДЕЛАЕТ. Переводит все четыре профиля на ближайшую отрасль из
канонического списка: «Металлургия» → «ГМК и добыча» (metals/mining —
прямое соответствие для металлургии и переработки металла), «Нефтесервис»
→ «Нефть и газ» (нефтесервисные компании обслуживают эту отрасль, отдельной
категории для них в справочнике нет), «Промышленность» → «Машиностроение»
(Роскосмос — ракетно-космическое машиностроение, ближайший из имеющихся
пунктов; отдельной категории для космической отрасли в справочнике нет).

Запуск:
    python3 pipeline/fix_company_industries_off_list.py            # сухой прогон
    python3 pipeline/fix_company_industries_off_list.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
INDEX = 'static/index.html'

FIXES = {
    'g1986021e': ('Металлургия', 'ГМК и добыча'),       # Evraz
    'g8cff91963': ('Металлургия', 'ГМК и добыча'),      # ЧЗМК
    'g631ec584': ('Нефтесервис', 'Нефть и газ'),        # Baker Hughes
    'g6fa918a3': ('Промышленность', 'Машиностроение'),  # Роскосмос
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    html = open(INDEX, encoding='utf-8').read()
    listed = {x.strip().strip('"') for x in
              re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1).split(',')}

    fixed = 0
    for cid, (old_ind, new_ind) in FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert new_ind in listed, 'новая отрасль %r сама не входит в INDUSTRIES' % new_ind
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  %-12s %-34s %s -> %s' % (cid, str(c.get('name'))[:34], old_ind, new_ind))
        c['ind'] = new_ind
        fixed += 1

    off_list = sorted({c.get('ind') for c in comps.values()} - listed - {None, ''})
    print('\nОтраслей исправлено: %d' % fixed)
    print('Осталось вне справочника после правки: %s' % (off_list or 'ни одной'))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
