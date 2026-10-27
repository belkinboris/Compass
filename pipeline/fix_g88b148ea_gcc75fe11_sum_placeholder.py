# -*- coding: utf-8 -*-
"""g88b148ea и gcc75fe11: поле `sum` («Обзор») записано прочерком «—», а
`eco.sum` («Экономист») — тем же прочерком; test_the_sum_on_the_overview_...
считает «—» в `sum` ЗАПОЛНЕННЫМ значением (канонический пустой маркер этого
поля — строка «Не раскрыта», см. аналогичный случай gd0139978/g6c2af36f,
2026-10-27), из-за чего молчание «Экономиста» читается как расхождение.
Сумма не названа ни в одном источнике ни у одной из двух карточек —
«Не раскрыта» верно отражает источник. `review.py`'s `sum_is_supported`
не разбирает плейсхолдеры (только млн/млрд), поэтому запись — этим
одноразовым скриптом, а не таблицей FIXES.

Без --write — сухой прогон.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
IDS = ('g88b148ea', 'gcc75fe11')


def main(write):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for i in IDS:
        card = by_id[i]
        assert card['sum'] == '—', (i, card['sum'])
        print('%s: sum %r -> %r' % (i, card['sum'], 'Не раскрыта'))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.loads(DATA.read_text(encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for i in IDS:
        card = by_id[i]
        assert card['sum'] == '—', (i, card['sum'])
        card['sum'] = 'Не раскрыта'
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Сделано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
