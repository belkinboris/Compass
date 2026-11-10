# -*- coding: utf-8 -*-
"""Разовая правка 10 ноября 2026 (владелец о карточке g075e9738: «что это название? что это за цена?»).

1. VK/«Р7»: заголовок по стандарту — доля числом, без «Холдинг» и «четверти»; продавца не
   раскрыл никто — где искали, записано в accepted_notes.no_profile.seller.
2. Сумма свыше миллиарда писалась «2 500 млн ₽» в восьми карточках — пишется «2,5 млрд ₽»
   (docs/card_money.md). Теперь это держит test_data.test_sum_over_billion_in_mlrd.

    python3 pipeline/archive/2026-11/fix_vk_r7_and_mln_sums_2026_11_10.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SUMS = {
    'gcd2b0954': ('41 500 млн ₽', '41,5 млрд ₽'),
    'gef7d4e54': ('4 390 млн ₽', '4,39 млрд ₽'),
    'gf23149cf': ('2 500 млн ₽', '2,5 млрд ₽'),
    'ga80371a8': ('2 200 млн ₽', '2,2 млрд ₽'),
    'g075e9738': ('2 500 млн ₽', '2,5 млрд ₽'),
    'ga4abadd2': ('18 400 млн ₽', '18,4 млрд ₽'),
    'g06a7a1c3': ('4 597 млн ₽', '4,597 млрд ₽'),
    'g91606f1b': ('20 964,5 млн ₽', '20,9645 млрд ₽'),
}
TITLE = ('g075e9738', 'Холдинг VK купил четверть акций «Р7»', 'VK купил 25% «Р7»')
SELLER_NOTE = ('Продавец не назван: ни VK (отчетность МСФО за 2024 год, Интерфакс 20 марта 2025), '
               'ни «Р7», ни ALUMNI Partners, ни РБК, «Ведомости», Forbes, CNews, ComNews и AK&M его '
               'не называют; АО — участники в ЕГРЮЛ не видны. На конец 2023 года акционерами были '
               'Артур Акопьян, Игорь Колпаков и АО «Технологии распределенных коммуникаций»')


def main(write):
    d = json.load(open(DATA, encoding='utf-8'))
    by = {x['id']: x for x in d['deals']}
    for cid, (old, new) in SUMS.items():
        c = by[cid]
        assert c['sum'] == old, (cid, c['sum'])
        assert c['eco']['sum'] == old, (cid, c['eco']['sum'])
        c['sum'] = c['eco']['sum'] = new
        print(cid, old, '→', new)
    cid, old, new = TITLE
    c = by[cid]
    assert c['title'] == old, c['title']
    c['title'] = new
    assert not c.get('seller')
    c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = SELLER_NOTE
    print(cid, old, '→', new)
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
