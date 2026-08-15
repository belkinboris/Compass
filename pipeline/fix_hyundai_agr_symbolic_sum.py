# -*- coding: utf-8 -*-
"""Символическая цена продажи завода Hyundai (₽Арт-Финанс/AGR) — 140 тыс. вон.

ЧТО СЛОМАНО. У `g7bffe474` (ООО «Арт-Финанс» приобрела завод Hyundai в
Санкт-Петербурге) поля `sum`/`eco.sum` несли заглушку «Не раскрыта».
Коммерсантъ со ссылкой на Reuters называет точную цену: «Hyundai Motor
продала 100% предприятия российской компании AGR Automotive Group за
140 тыс. вон (около $97)» — символическая сумма, характерная для сделок
по выходу западных компаний из России под санкционным давлением.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `sum_is_supported()` разбирает `new` только в
формате «N[–M] млн|млрд ₽/$/€» — сумма меньше миллиона в эту грамматику
не укладывается вообще (регулярка требует слова «млн» или «млрд»). Число
верное и дословно взято из цитаты, просто масштаб сделки не про миллионы —
отдельный скрипт со своим `assert`, тот же приём, что уже использован для
цены аукциона Домодедово (66,13 млрд ₽, где наоборот число было слишком
точным для формата) и для отката law.appr у Солид-банка.

ЗАПУСК:
    python3 pipeline/fix_hyundai_agr_symbolic_sum.py            # сухой прогон
    python3 pipeline/fix_hyundai_agr_symbolic_sum.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7bffe474'
OLD = 'Не раскрыта'
NEW = '$97 (символическая сумма)'
SRC_LABEL = 'Коммерсантъ'
SRC_URL = 'https://www.kommersant.ru/doc/8335627'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('sum') == OLD, 'sum уже другой: %r' % deal.get('sum')
    assert deal.get('eco', {}).get('sum') == OLD, \
        'eco.sum уже другой: %r' % deal.get('eco', {}).get('sum')

    print('ПРАВИМ %s: sum и eco.sum %r -> %r' % (DEAL_ID, OLD, NEW))
    print('  цитата: "В 2024 году Hyundai Motor продала 100%% предприятия '
          'российской компании AGR Automotive Group за 140 тыс. вон '
          '(около $97), пишет агентство." — %s' % SRC_URL)

    existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
    add_src = SRC_URL not in existing_urls

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NEW
    deal['eco']['sum'] = NEW
    if add_src:
        deal.setdefault('src', []).append([SRC_LABEL, SRC_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
