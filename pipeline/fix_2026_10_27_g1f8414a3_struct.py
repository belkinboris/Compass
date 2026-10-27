"""«Агропромкредит» (g1f8414a3): «Как устроена сделка» объясняет статус, а не спорит с ним (27 октября 2026).

Статус «Закрыта» у выигранных повторных торгов — правило владельца
(docs/card_status_dates.md), а текст начинался с «это пока победа на торгах,
а не закрытая сделка». Читатель видел спор двух строк одной карточки.

    python3 pipeline/fix_2026_10_27_g1f8414a3_struct.py --write    # затем facts_derive.py --write
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'deals_promoted.json')
NEW = ('Статус «Закрыта» — по итогам торгов: конкурс окончен, победитель назван, цена зафиксирована. Право на 100% долей '
       'банка перейдет к «ЭсЭфАй» после корпоративных и регуляторных одобрений, которых на день объявления победы еще не '
       'было, — об этом сама «ЭсЭфАй» пишет в своем сообщении. Первые торги со стартовой ценой 2,854 млрд ₽ не состоялись: '
       'желающих не нашлось; на повторных цену снизили вдвое.')


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in base['deals'] if x['id'] == 'g1f8414a3')
    assert d['law']['struct'].startswith('Сама «ЭсЭфАй» в своем сообщении подчеркивает'), d['law']['struct'][:60]
    print('law.struct →', NEW)
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    d['law']['struct'] = NEW
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
