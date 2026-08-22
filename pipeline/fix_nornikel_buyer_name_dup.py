# -*- coding: utf-8 -*-
"""Прогон публикации 22 августа: карточка g0e2f181f («Норникель» выкупил по
оферте 95,5% выпуска облигаций) вышла из очереди по таймауту молчания и
тут же уронила test_buyer_is_named_once — у покупателя одновременно
стояли `buyer` (профиль g72e3b46f) и `buyer_name` («Норникель» текстом).

Профиль g72e3b46f — это тот же «Норникель» (проверено: co(g72e3b46f).name
== "Норникель"), связывание сделал автолинк по точному совпадению имени
(`party_evidence.buyer[0].linked_by == "exact_profile_name_match"`), но
текстовое поле не снял — тот же класс дефекта, что уже описан в CLAUDE.md
(«У покупателя две формы записи... одновременно заполнять обе нельзя»).
Раз профиль есть и назван верно, снимаем дублирующий `buyer_name`.

Запуск:
    python3 pipeline/fix_nornikel_buyer_name_dup.py            # сухой прогон
    python3 pipeline/fix_nornikel_buyer_name_dup.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0e2f181f'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('buyer') == 'g72e3b46f', 'buyer уже не тот, что ожидался'
    assert deal.get('buyer_name') == '«Норникель»', 'buyer_name уже не тот, что ожидался'
    company = data['companies'].get(deal['buyer'])
    assert company and company.get('name') == 'Норникель', \
        'профиль buyer больше не называется «Норникель» — проверьте вручную'

    print('%s: buyer_name=%r будет снят, buyer=%s (%s) остаётся'
          % (DEAL_ID, deal['buyer_name'], deal['buyer'], company['name']))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    del deal['buyer_name']
    json.dump(data, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
