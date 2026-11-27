# -*- coding: utf-8 -*-
"""gdc13aeb3 (очередь): консультанты возможной покупки Imperial Brands.

Список консультантов не ложится в таблицу FIXES (docs/card_editing_scripts.md). Источники —
заявления Altria и Imperial Brands от 26 ноября 2026 года (RNS, полные тексты на 6ix.com):
«Deutsche Bank and Perella Weinberg are acting as financial advisers to Altria.»;
«Goldman Sachs (Financial Adviser to Imperial Brands) … Morgan Stanley (Financial Adviser and
Corporate Broker to Imperial Brands)». Оба адреса уже стоят в src карточки.

    python3 pipeline/fix_gdc13aeb3_advisers_2026_11_27.py            # сухой прогон
    python3 pipeline/fix_gdc13aeb3_advisers_2026_11_27.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
ID = 'gdc13aeb3'
U_ALTRIA = 'https://6ix.com/news/statement-re-possible-offer-94'
U_IMB = 'https://6ix.com/news/statement-re-possible-offer-95'
ROWS = [
    ['Финансовый консультант покупателя', 'Deutsche Bank', 'Консультирует Altria. Источник: ' + U_ALTRIA],
    ['Финансовый консультант покупателя', 'Perella Weinberg', 'Консультирует Altria. Источник: ' + U_ALTRIA],
    ['Финансовый консультант покупаемой компании', 'Goldman Sachs',
     'Консультирует Imperial Brands. Источник: ' + U_IMB],
    ['Финансовый консультант покупаемой компании', 'Morgan Stanley',
     'Консультирует Imperial Brands, также ее корпоративный брокер. Источник: ' + U_IMB],
]


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))      # читаем прямо перед записью
    card = next(c for c in data['cards'] if c.get('id') == ID)
    urls = {s[1] for s in card.get('src') or []}
    assert U_ALTRIA in urls and U_IMB in urls, 'сначала источники заявлений — review.py --write'
    law = card.setdefault('law', {})
    adv = law.get('adv') or []
    assert all(isinstance(r, list) for r in adv), adv
    added = [r for r in ROWS if not any(x[:2] == r[:2] for x in adv)]
    print('добавить строк: %d' % len(added))
    for r in added:
        print('  ', r[0], '—', r[1])
    if write and added:
        law['adv'] = adv + added
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
