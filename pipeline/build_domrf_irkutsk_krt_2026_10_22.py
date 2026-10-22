# -*- coding: utf-8 -*-
"""Новая карточка: «Дом.РФ» выставил на торги право заключения договоров КРТ
по двум участкам в Иркутской области (берег Иркутского водохранилища).

Не дописывание карточки g49431b3c (особняк барона Штиглица) — та же
корзина совпадения «общие слова заголовка» (match.py) ложно связала эту
новость с ЧУЖОЙ сделкой (KNOWN_ISSUES.md, 22 октября 2026); это отдельный
актив, отдельный лот, отдельный город.

Источник: РИА Недвижимость, https://realty.ria.ru/20261022/angara-2126137548.html
(текст в data/inbox/raw/2026-10-22-articles.jsonl).

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, ROOT)

import promote  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DRAFT = {
    'date': '2026-10-22',
    'title': '«Дом.РФ» выставил на торги право заключения договоров КРТ в Иркутской области',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [['РИА Недвижимость', 'https://realty.ria.ru/20261022/angara-2126137548.html']],
    'seller': '«Дом.РФ»',
    'asset': 'право заключения договоров КРТ по двум участкам на берегу Иркутского водохранилища',
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    if any('angara-2126137548' in str(s[1]) for c in pending['cards'] for s in (c.get('src') or [])
           if len(s) > 1):
        print('Уже есть черновик с этим источником.')
        return 0
    card_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    print('новая карточка %s: %s' % (card_id, card['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    if any('angara-2126137548' in str(s[1]) for c in pending['cards'] for s in (c.get('src') or [])
           if len(s) > 1):
        print('Уже есть черновик с этим источником (перечитано перед записью).')
        return 0
    pending['cards'].append(card)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано: %s' % card_id)
    return 0


if __name__ == '__main__':
    sys.exit(main())
