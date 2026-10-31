# -*- coding: utf-8 -*-
"""Новая карточка: Москва выставила на торги право заключения договора о
КРТ двух участков (4,4 га) в Южном Тушине — победитель построит
29,3 тыс. кв. м (почти 16 тыс. кв. м жилья, технопарк, здание для
газового хозяйства) между улицей Фабрициуса, Походным и Цветочным
проездами. Начальная цена лота — 46,7 млн ₽, торги 19 ноября 2026.

Тот же класс, что уже решался 12 октября для Рижского рынка (g22d3599c,
accepted_notes): `triage.py`/`enrich.py` сводят московские лоты КРТ с
несвязанной карточкой `g6d711306` («ВымпелКом»/офисное здание) по
общим словам заголовка — собрано отдельным скриптом, как и там.

Источник (прочитан полностью, кэш data/inbox/raw/2026-10-15-articles.jsonl):
  РИА Недвижимость (15.10.2026)
  https://realty.ria.ru/20261015/vlasti-2124628420.html

Запуск:
    python3 pipeline/build_tushino_krt_2026_10_15.py            # сухой прогон
    python3 pipeline/build_tushino_krt_2026_10_15.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC = ['РИА Недвижимость', 'https://realty.ria.ru/20261015/vlasti-2124628420.html']

DRAFT = {
    'date': '2026-10-15',
    'title': 'Власти Москвы выставили на торги проект КРТ в Южном Тушине',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': 'Правительство Москвы',
    'sum': '46,7 млн ₽',
    'asset': ('право заключения договора о комплексном развитии территории (КРТ) площадью '
              '4,4 га в Южном Тушине, между улицей Фабрициуса, Походным и Цветочным проездами'),
    'events': [{
        'kind': 'negotiations',
        'date': '2026-10-15',
        'title': 'Торги объявлены',
        'note': 'Аукцион на право заключения договора о КРТ пройдет 19 ноября 2026 года.',
        'source': SRC,
    }],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Южном Тушине' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

    print('НОВАЯ КАРТОЧКА %s: %s' % (card_id, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == card_id for c in fresh['cards']):
        print('ОТКАЗ: id уже занят — перечитайте и повторите')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
