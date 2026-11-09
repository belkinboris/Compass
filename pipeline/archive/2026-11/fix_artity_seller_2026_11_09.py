# -*- coding: utf-8 -*-
"""Продавец «АртАйТи» — Виталий Мальцев, по выписке ЕГРЮЛ от 9 ноября 2026, 22:17.

Владелец прислал выписку (egrul.nalog.ru): запись ГРН 2267802871950 от 09.11.2026 —
ООО «Ультиматек» (ИНН 9701083410) получил 50%, доля Виталия Мальцева 90% → 40%,
Андрей Сурков — 10% без изменений. Предыдущий скрипт (add_artity_profile_2026_11_09.py)
читал api-fns с данными до этой записи и написал «переход в реестре еще не записан» —
неверно. Дата сделки — день записи в ЕГРЮЛ, она же день новости CNews.

    python3 pipeline/archive/2026-11/fix_artity_seller_2026_11_09.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD_SELLER = 'Совладельцы «АртАйТи» (по ЕГРЮЛ — Виталий Мальцев и Андрей Сурков; кто продал долю, не сообщается)'
EVIDENCE = {'value': 'Виталий Мальцев (90% → 40%); ООО «Ультиматек» — 50% с 09.11.2026; Андрей Сурков — 10% без изменений',
            'method': 'registry_owner_history', 'url': 'https://egrul.nalog.ru (выписка 09.11.2026, ГРН 2267802871950)'}


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == 'gc3750bdb')
    assert card.get('seller') == OLD_SELLER, card.get('seller')
    card['seller'] = 'Виталий Мальцев'
    card['seller_src'] = 'registry'
    card.setdefault('party_evidence', {})['seller'] = [EVIDENCE]
    card['eco']['share'] = '50% доли в ООО «Артайти групп»'
    card['date_basis'] = 'registry'
    card.get('accepted_notes', {}).get('no_profile', {})['seller'] = (
        'Продавец — Виталий Мальцев, основатель «АртАйТи»: по выписке ЕГРЮЛ от 09.11.2026 его доля 90% → 40%, '
        'ООО «Ультиматек» получил 50%; частное лицо, профиль не заводим')


def main(argv):
    apply(json.load(open(PENDING, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон.')
        return 0
    fresh = json.load(open(PENDING, encoding='utf-8'))
    apply(fresh)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
