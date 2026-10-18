# -*- coding: utf-8 -*-
"""Привязка покупателя в карточке gcd8fe39c («Aspace хочет купить сеть
коворкингов Multispace в Москве») к профилю Aspace.

ПОЧЕМУ. 12 октября профиля Aspace в базе не было, и приёмка оставила
покупателя текстом (`buyer_name: "Aspace"`). 18 октября профиль заведён
приёмкой карточки ga5a7f3c1 («Атолл Капитал» получил до 25% Aspace,
АО «А Спэйс», ИНН 9702082272) — теперь обе сделки о сети Aspace видны на
одной странице компании. Сторона пишется один раз: ссылка `buyer` ставится,
текст `buyer_name` снимается (docs/card_parties.md, «Сторона записана один
раз»).

Запуск:
    python3 pipeline/link_aspace_multispace_buyer_2026_10_18.py          # сухой прогон
    python3 pipeline/link_aspace_multispace_buyer_2026_10_18.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcd8fe39c'
ASPACE_ID = 'g6f14b502'


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
    assert base['companies'][ASPACE_ID]['name'] == 'Aspace', base['companies'].get(ASPACE_ID)
    deal = next(d for d in base['deals'] if d['id'] == DEAL_ID)
    if deal.get('buyer') == ASPACE_ID and 'buyer_name' not in deal:
        print('уже привязано')
        return 0
    assert deal.get('buyer_name') == 'Aspace' and not deal.get('buyer'), (deal.get('buyer_name'), deal.get('buyer'))
    assert ASPACE_ID not in (deal.get('target'), deal.get('seller_id'), deal.get('asset_id'))
    deal['buyer'] = ASPACE_ID
    del deal['buyer_name']
    print('%s: buyer_name «Aspace» -> buyer %s' % (DEAL_ID, ASPACE_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
