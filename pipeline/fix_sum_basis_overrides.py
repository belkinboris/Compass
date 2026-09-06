# -*- coding: utf-8 -*-
"""Явное поле `sum_basis` там, где по тексту суммы не видно, что число — не цена.

С 6 сентября 2026 смысл суммы («цена, названная сторонами» / оценка / диапазон /
нижняя граница / стартовая цена торгов / объём привлечения / не цена вовсе)
выводится из текста `sum` функцией `deal_multiples.sum_basis()`, и только
'disclosed' идёт в мультипликаторы и в «Только покупки». Но текст суммы не
всегда говорит, что это за число: «71 млрд ₽» у карточки «Carlsberg требует у
России компенсацию за срыв продажи «Балтики»» — сумма ИСКА, а не цена сделки.
Такие случаи помечаются явным полем карточки, которое сильнее разбора текста;
значение — только из закрытого списка `SUM_BASES`.

Запуск:
    python3 pipeline/fix_sum_basis_overrides.py           # сухой прогон
    python3 pipeline/fix_sum_basis_overrides.py --write
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deal_multiples import SUM_BASES  # noqa: E402

DATA = 'static/data/deals_promoted.json'

OVERRIDES = {
    # id: (ожидаемый текст суммы, смысл)
    'ce6b8c447': ('71 млрд ₽', 'not_a_price'),  # иск Carlsberg о компенсации, сделка не состоялась
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    for did, (sum_text, basis) in OVERRIDES.items():
        assert basis in SUM_BASES, basis
        d = deals[did]
        assert d.get('sum') == sum_text, (did, d.get('sum'))
        if d.get('sum_basis') == basis:
            print(f'{did}: sum_basis уже {basis}')
            continue
        assert not d.get('sum_basis'), (did, d.get('sum_basis'))
        print(f'{did}: sum_basis -> {basis} ({d["title"][:60]})')
        if write:
            d['sum_basis'] = basis
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
