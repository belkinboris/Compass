# -*- coding: utf-8 -*-
"""Новая карточка: Альфа-банк ведет переговоры о покупке доли в «Циане»
(Коммерсантъ, 16 ноября 2026, https://www.kommersant.ru/doc/9110774).

Почему вручную. Черновики d28885343 (пересказ vc.ru) и d77249084 (Frank
Media) ворота не прошли («не установлен предмет»), а send_drafts.py снял их
как повтор уже решенной новости о «Циане» ('auto-drop') — владельцу они не
показывались. Решение владельца не подделывается: карточка идет в очередь
(pending.json) обычным порядком и ждет его кнопки.

Почему отдельная карточка, а не этап g9b4c2e71 («Т-Технологии» собираются
купить до 100% «Циана»): другой покупатель (Альфа-банк, а не
«Т-Технологии»), другой продавец (структуры, связанные с Elbrus Capital, а
не все акционеры по публичному предложению), другой предмет (часть пакета,
а не до 100%) и свой исход — одна сделка может закрыться, а другая нет.
Карточки связаны через related_deal_ids.

Сверка на дубль (docs/base_duplicates.md, «Перед ручной сборкой»): в deals
и в очереди нет карточки с покупателем Альфа-банк и предметом «Циан».

Скрипт создает оболочку со структурными полями; текст — write_card.py.

Запуск:
    python3 pipeline/build_alfa_cian_2026_11_17.py            # сухой прогон
    python3 pipeline/build_alfa_cian_2026_11_17.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4290fc7a'     # id ручной сборки — константой (docs/intake_gates.md)
RELATED = 'g9b4c2e71'
KOMM = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9110774']

DRAFT = {
    'date': '2026-11-16',
    'title': 'Альфа-банк может купить долю в «Циане»',
    'ind': 'ИТ и интернет',
    'type': 'M&A',
    'status': 'Обсуждается',
    'src': [KOMM,
            ['Frank Media', 'https://frankmedia.ru/316227'],
            ['Эксперт', 'https://expert.ru/news/kommersant-uznal-o-planakh-alfa-banka-kupit-dolyu-v-tsiane']],
    'buyer_name': 'Альфа-банк',
    'asset': 'Акции МКПАО «Циан»',
}


def twin(cards):
    return [c['id'] for c in cards
            if 'иан' in json.dumps(c, ensure_ascii=False) and c['id'] != RELATED
            and 'льфа-банк' in (str(c.get('title')) + str(c.get('buyer_name'))).lower()]


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    base = json.load(open(DATA, encoding='utf-8'))
    found = twin(pending['cards'] + base['deals'])
    if found:
        print('ОТКАЗ: похожая карточка уже есть: %s' % ', '.join(found))
        return 1
    assert any(d['id'] == RELATED for d in base['deals']), 'связанной карточки нет в базе'
    ids = {c['id'] for c in pending['cards']} | {d['id'] for d in base['deals']}
    if CARD_ID.startswith('CARD'):
        print('id еще не выбран; предлагаю: %s' % promote.new_id(ids))
        return 0
    assert CARD_ID not in ids, 'id занят'
    card = promote.to_card(DRAFT, CARD_ID)
    card['related_deal_ids'] = [RELATED]
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in fresh['cards']) or twin(fresh['cards']):
        print('ОТКАЗ: карточка уже в очереди')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
