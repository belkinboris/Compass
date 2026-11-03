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
        'date': '2026-11-02',
        'title': 'Химический холдинг «Концентрация» привлек 1,2 млрд рублей инвестиций',
        'ind': 'Химия и удобрения',
        'type': 'Инвестиция',
        'status': 'Закрыта',
        'src': [['web:mergers.ru',
                 'https://mergers.ru/news/Himicheskij-holding-Koncentraciya-privlek-12-mlrd-rublej-na-razrabotku-himicheskih-produktov-87729']],
        'events': [],
        'asset': 'АО «Концентрация»',
        'sum': '1,2 млрд ₽',
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
