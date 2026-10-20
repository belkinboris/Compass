# -*- coding: utf-8 -*-
"""Новая карточка: «Газпром добыча Уренгой» (дочка «Газпрома») выставила на
торги гостиницу «Урал» в Новом Уренгое — непрофильный актив, не
эксплуатируется с 2019 года. Ворота отклонили черновик («не установлен
предмет сделки — из заголовка не видно, что продают»); карточка собрана
вручную, как «Москва/Рязанский проспект» (g1833e545).

Источник (прочитан полностью через fetch_article_texts.py --write):
  URA.RU, 20.10.2026
  https://ura.news/news/1053137347

Этот скрипт создаёт только карточку-оболочку со структурными полями;
текстовые поля (law.struct — условия торгов, eco.context — прежние
продажи «Газпромом» похожих активов) дописывает write_card.py отдельно.

Запуск:
    python3 pipeline/build_gazprom_ural_hotel_2026_10_20.py            # сухой прогон
    python3 pipeline/build_gazprom_ural_hotel_2026_10_20.py --write    # применить
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

SRC = ['URA.RU', 'https://ura.news/news/1053137347']

DRAFT = {
    'date': '2026-10-20',
    'title': '«Газпром» выставил на торги гостиницу «Урал» в Новом Уренгое',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': '«Газпром добыча Уренгой»',
    'asset': 'гостиница «Урал» площадью 3 тыс. кв. м в Новом Уренгое',
    'sum': '161,4 млн ₽ (начальная цена)',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Урал' in (c.get('title') or '') and 'Уренгое' in (c.get('title') or '')
           for c in pending['cards'] + promoted['deals']):
        print('ОТКАЗ: похожая карточка уже есть')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')

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
