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
        'title': 'Подъемники Шерегеша перешли под контроль арабов',
        'ind': 'Гостиницы и туризм',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['web:ngs24.ru', 'https://ngs24.ru/text/business/2026/11/03/76741240/']],
        'events': [{'kind': 'closed', 'date': '2026-07-01', 'title': 'Сделка завершена',
                    'note': 'Контроль перешел к покупателю из ОАЭ, по данным «Контур.Фокуса».',
                    'source': ['web:ngs24.ru', 'https://ngs24.ru/text/business/2026/11/03/76741240/']}],
        'seller': 'Татьяна Прокудина',
        'buyer_name': '«Рокет Фандс Инвестмент Ин Коммершиал Энтерпрайзис Энд Менеджмент Л.Л.К»',
        'asset': 'ООО «Каскад восток»',
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
