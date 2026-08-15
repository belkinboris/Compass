# -*- coding: utf-8 -*-
"""Символическая цена продажи российского бизнеса OBI — 1 евро (партия 5
агентов, раунд 6, 15 августа 2026).

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `sum_is_supported()` разбирает `new` только в
формате «N[–M] млн|млрд ₽/$/€» — сумма меньше миллиона (тем более «1 евро»)
в эту грамматику не укладывается вообще. Тот же приём, что уже применён к
символической цене завода Hyundai (140 тыс. вон/$97,
pipeline/fix_hyundai_agr_symbolic_sum.py).

ЗАПУСК:
    python3 pipeline/fix_r6_obi_symbolic_sum.py            # сухой прогон
    python3 pipeline/fix_r6_obi_symbolic_sum.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'c21076c79'
NEW_SUM = '€1 (символическая сумма)'
SRC_LABEL = 'Ведомости'
SRC_URL = 'https://www.vedomosti.ru/business/articles/2022/07/30/933793-obi-zakrila-sdelku-prodazhe'
QUOTE = ('Сумма сделки символическая, говорит один из собеседников '
         '«Ведомостей». Второй добавляет, что она составила 1 евро.')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('sum') is None, 'sum уже другой: %r' % deal.get('sum')
    assert (deal.get('eco') or {}).get('sum') == '—', \
        'eco.sum уже другой: %r' % (deal.get('eco') or {}).get('sum')

    print('ПРАВИМ %s: sum и eco.sum None/«—» -> %r' % (DEAL_ID, NEW_SUM))
    print('  цитата: "%s" — %s' % (QUOTE, SRC_URL))

    existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
    add_src = SRC_URL not in existing_urls

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NEW_SUM
    deal.setdefault('eco', {})['sum'] = NEW_SUM
    if add_src:
        deal.setdefault('src', []).append([SRC_LABEL, SRC_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
