# -*- coding: utf-8 -*-
"""Дубли и этапы одной сделки ВНУТРИ базы — теми же правилами, что ворота.

ЗАЧЕМ (31 октября 2026). «Росатом» в Мали прошел ворота новой карточкой при
живой карточке 2024 года: все проверки были ограничены 7–90 днями. Починив
ворота (`promote.whole_base_twin`, `match.is_strong`), мы прогнали ту же
проверку по самой базе — и в ней нашлись дубли, пришедшие раньше: Qiwi/
RealWeb, Danone/«Вамин Р», «Севергрупп»/«Кордиант», Selectel/servers.ru и др.

Каждая карточка проверяется против остальных как свежая новость: сильное
совпадение `match.py` или признак «по всей базе» из ворот. Пара — не приговор:
это либо дубль (слить), либо этап одной сделки (связать), либо разные сделки
(пометить `separate_transaction_reviewed`, чтобы пара больше не всплывала).
Решает человек или приток по `docs/duplicates.md`.

    python3 pipeline/base_duplicates_scan.py            # отчет в консоль
    python3 pipeline/base_duplicates_scan.py --json F   # и в файл
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import match as matcher   # noqa: E402
import promote            # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def as_draft(deal, companies):
    def name(id_field, text_field):
        return deal.get(text_field) or (companies.get(deal.get(id_field)) or {}).get('name')
    return {'title': deal.get('title'), 'date': deal.get('date'),
            'buyer_name': name('buyer', 'buyer_name'), 'seller': name('seller_id', 'seller'),
            'asset': name('target', 'asset')}


def scan(data):
    deals, companies = data['deals'], data.get('companies') or {}
    idx = matcher.index_base(deals, companies, data.get('match_keys'))
    df = promote.stem_frequency(idx)
    by_id = {d['id']: d for d in deals}
    pairs = {}
    for deal in deals:
        if deal.get('separate_transaction_reviewed'):
            continue
        rest = [r for r in idx if r['id'] != deal['id']]
        draft = as_draft(deal, companies)
        found, why = matcher.match({'title': draft['title'], 'date': draft['date'], 'buyer': draft['buyer_name'],
                                    'asset': draft['asset'], 'seller': draft['seller']}, rest)
        if not (found and matcher.is_strong(why)):
            near = promote.whole_base_twin(draft, rest, df)
            found, why = near if near else (None, None)
        if not found or by_id.get(found, {}).get('separate_transaction_reviewed'):
            continue
        key = tuple(sorted((deal['id'], found)))
        pairs.setdefault(key, why)
    out = []
    for (a, b), why in sorted(pairs.items()):
        out.append({'a': a, 'b': b, 'why': why,
                    'a_title': by_id[a].get('title'), 'a_date': by_id[a].get('date'), 'a_status': by_id[a].get('status'),
                    'b_title': by_id[b].get('title'), 'b_date': by_id[b].get('date'), 'b_status': by_id[b].get('status')})
    return out


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    pairs = scan(data)
    print('Карточек: %d. Подозрительных пар (дубль или этап одной сделки): %d' % (len(data['deals']), len(pairs)))
    for p in pairs:
        print('%s ⇄ %s  [%s]\n   %s (%s, %s)\n   %s (%s, %s)' % (
            p['a'], p['b'], p['why'], str(p['a_title'])[:90], p['a_date'], p['a_status'],
            str(p['b_title'])[:90], p['b_date'], p['b_status']))
    if '--json' in argv:
        path = argv[argv.index('--json') + 1]
        json.dump(pairs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: %s' % path)


if __name__ == '__main__':
    main(sys.argv[1:])
