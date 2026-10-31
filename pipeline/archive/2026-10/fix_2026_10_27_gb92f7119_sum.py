"""CarPrice → Ростех (gb92f7119): сумма снята снова (27 октября 2026).

`pipeline/fix_2026_10_27_sum_in_both_lenses.py` скопировал eco.sum «8 млрд ₽»
в sum — а аудит ROLE_WRONG/CONTRADICTION ранее снял эту сумму с карточки
(pipeline/ingest/fixes/fix_role_wrong_contradiction_audit_batch1.py): 8 млрд ₽ —
стоимость имущества Галицкого, обращенного в доход государства, а CarPrice и
доли в компаниях переданы СВЕРХ этой суммы, их отдельная оценка не называлась.
Поэтому sum снова пуст, а eco.sum больше не выглядит как цена: он объясняет,
почему цены нет (иначе инвариант «сумма в обоих экранах» снова потребует ее
скопировать).

    python3 pipeline/fix_2026_10_27_gb92f7119_sum.py --write    # затем facts_derive.py --write
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'deals_promoted.json')
NEW_ECO = ('Не раскрыта: CarPrice и доли в десяти компаниях переданы Ростеху сверх имущества Александра Галицкого '
           'на 8 млрд ₽, обращенного в доход государства; отдельно эти активы не оценивались.')


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in base['deals'] if x['id'] == 'gb92f7119')
    assert d.get('sum') == '8 млрд ₽' and d['eco'].get('sum') == '8 млрд ₽', (d.get('sum'), d['eco'].get('sum'))
    print('gb92f7119: sum «8 млрд ₽» → пусто; eco.sum → «%s»' % NEW_ECO)
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    d['sum'] = None
    d['eco']['sum'] = NEW_ECO
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
