"""«Сити Капитал» / Desport (g4a53d81b): eco.sum снова «458 млн рублей» (27 октября 2026).

`pipeline/fix_2026_10_27_sum_in_both_lenses.py` переписал eco.sum в «458 млн ₽»,
а таблица правок (pipeline/ingest/fixes/written_g4a53d81b_2026_10_26.py) держит
«458 млн рублей» — `test_review_table_is_applied_and_not_pending` требует, чтобы
база совпадала с таблицей. Нормализация «рублей → ₽» нужна только полю sum
(`test_cover_sum_uses_currency_symbol`), eco.sum — проза «Экономиста».

    python3 pipeline/fix_2026_10_27_g4a53d81b_eco_sum.py --write
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'deals_promoted.json')


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in base['deals'] if x['id'] == 'g4a53d81b')
    assert d['eco'].get('sum') == '458 млн ₽' and d.get('sum') == '458 млн ₽', (d['eco'].get('sum'), d.get('sum'))
    print('g4a53d81b: eco.sum «458 млн ₽» → «458 млн рублей» (sum остается «458 млн ₽»)')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    d['eco']['sum'] = '458 млн рублей'
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
