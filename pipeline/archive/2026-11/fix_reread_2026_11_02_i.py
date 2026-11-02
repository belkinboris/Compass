# -*- coding: utf-8 -*-
"""Вычитка базы, партия «i» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_i.py.

- g8f548826 (ВТБ/«Росгосстрах Жизнь»): приемка держит отметку
  `party_legal_form:target` — у профиля «Росгосстрах Жизни» (g385a04a0) нет
  `legal_short`. `party_legal_names.py` его не предлагает: реестровое краткое
  имя `ООО СК "РОСГОССТРАХ ЖИЗНЬ"` — между правовой формой и кавычкой стоит
  «СК», и регэксп `legal_short()` его не разбирает. Ставим по реестру
  (сайт /api/companies/g385a04a0/fns: ООО СК "РОСГОССТРАХ ЖИЗНЬ",
  ИНН 7743504307): «ООО СК «Росгосстрах Жизнь»».

Остальным сторонам партии legal_short ставит сам `party_legal_names.py
--write` (g835eac98 — «Русал», g831d0fc8 — «Резотстрой» и «Стрела»).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_i.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CHANGES = [
    # (профиль, ожидаемое имя, поле, старое значение, новое значение)
    ('g385a04a0', '«Росгосстрах Жизнь»', 'legal_short', None, 'ООО СК «Росгосстрах Жизнь»'),
]


def apply(data):
    for cid, name, field, old, new in CHANGES:
        c = data['companies'][cid]
        assert c.get('name') == name, (cid, c.get('name'))
        assert c.get(field) == old, (cid, field, c.get(field), old)
        c[field] = new
        print('  %s %s: %r -> %r' % (cid, field, old, new))


def main(argv):
    write = '--write' in argv
    # перечитать прямо перед записью: параллельные прогоны пишут ту же базу
    data = json.load(open(BASE, encoding='utf-8'))
    apply(data)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
