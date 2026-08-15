# -*- coding: utf-8 -*-
"""Откат двух ошибочных правок law.appr из партии 5 агентов, раунд 4.

g8a66f3c7 (Рег.ру/Reddock): цитата про поправки для хостинг-провайдеров не
называет орган и не подтверждает согласование ИМЕННО этой сделки — перенесена
в law.terms (pipeline/ingest/fixes/batch_agents100_r4.py), здесь только откат.

gd297770d (Daimler/КамАЗ): «все одобрения получены» без единого названного
органа — слишком расплывчато даже для широкой планки test_approval_names_a_body.
Не переносится никуда, остаётся честным прочерком.

ЗАПУСК:
    python3 pipeline/fix_r4_appr_misfields.py            # сухой прогон
    python3 pipeline/fix_r4_appr_misfields.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

REVERTS = {
    'g8a66f3c7': (
        'С 1 декабря в России вступили в силу поправки, регулирующие '
        'деятельность хостинг-провайдеров. Они должны гарантировать защиту '
        'информации в своей инфраструктуре, сотрудничать с государственной '
        'системой обнаружения, предупреждения и ликвидации последствий '
        'компьютерных атак (ГосСОПКА), оперативно реагировать на угрозы, '
        'принимать участие в учениях по обеспечению устойчивости '
        'российского сегмента интернета и др. Сформирован реестр '
        'хостингов, не вошедшим в него организациям с 1 февраля 2023 года '
        'запрещено оказывать услуги в России.'
    ),
    'gd297770d': (
        'Близкий к компании источник издания отмечает, что сделка прошла, '
        'все одобрения получены.'
    ),
}
CORRECT = 'Публично не сообщалось'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, wrong in REVERTS.items():
        deal = by_id[cid]
        assert deal.get('law', {}).get('appr') == wrong, \
            '%s: law.appr уже другой: %r' % (cid, deal.get('law', {}).get('appr'))
        print('ПРАВИМ %s: law.appr — откат к заглушке' % cid)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid in REVERTS:
        by_id[cid]['law']['appr'] = CORRECT
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
