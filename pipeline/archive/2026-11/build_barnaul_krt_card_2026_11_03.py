# -*- coding: utf-8 -*-
import json
import os
import sys
from datetime import datetime, timezone

HERE = '/home/user/Compass/pipeline/ingest'
sys.path.insert(0, HERE)
import promote  # noqa: E402

ROOT = '/home/user/Compass'
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main():
    write = '--write' in sys.argv[1:]
    pending = json.load(open(PENDING, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']} | {d['id'] for d in data['deals']}
    new_id = promote.new_id(existing)

    draft = {
        'date': '2026-11-03',
        'title': '«Дом.РФ» выставил на торги проект КРТ под Барнаулом',
        'ind': 'Недвижимость',
        'type': 'Продажа с торгов',
        'status': 'Обсуждается',
        'src': [['web:realty.ria.ru', 'https://realty.ria.ru/20261103/krt-2128868293.html']],
        'events': [],
        'seller': '«Дом.РФ»',
        'asset': 'право заключения договора о КРТ участков общей площадью 270,22 га у Барнаула',
    }
    card = promote.to_card(draft, new_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    pending['cards'].append(card)

    print('new_id=%s' % new_id)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон.')


if __name__ == '__main__':
    main()
