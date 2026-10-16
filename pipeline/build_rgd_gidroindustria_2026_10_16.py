# -*- coding: utf-8 -*-
"""Новая карточка: «РусГазДобыча» (РГД) передала 49% ООО «Гидроиндустрия»
(головная компания группы ГМС, производитель нефтегазового оборудования)
компании «Гидромаш МСК» Артёма Молчанова — найдено Коммерсантом по ЕГРЮЛ
(запись от 14 октября), стороны на вопросы издания не ответили, сумма и
механизм (продажа, вклад в капитал и т. п.) не названы.

Фон: ГМС была передана под временное управление указом президента в
конце 2024 года, а годом позже президент разрешил РГД приобрести активы
группы, включая «Гидромашсервис» — т. е. РГД владела «Гидроиндустрией»
(головной компанией ГМС) полностью, а теперь рассталась с 49%.

Единственный источник — Коммерсантъ (без сети другие издания не нашли
эту историю на момент сборки).

Запуск:
    python3 pipeline/build_rgd_gidroindustria_2026_10_16.py            # сухой прогон
    python3 pipeline/build_rgd_gidroindustria_2026_10_16.py --write    # применить
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

SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9027728']

DRAFT = {
    'date': '2026-10-16',
    'title': '«РусГазДобыча» передала 49% ООО «Гидроиндустрия» (группа ГМС) компании Артёма Молчанова',
    'ind': 'Машиностроение',
    'type': 'M&A',
    'status': 'Закрыта',
    'src': [SRC],
    'seller': '«РусГазДобыча»',
    'buyer_name': '«Гидромаш МСК» (Артём Молчанов)',
    'asset': '49% ООО «Гидроиндустрия»',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Гидроиндустрия' in (c.get('title') or '') for c in pending['cards']):
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
