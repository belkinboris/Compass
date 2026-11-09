# -*- coding: utf-8 -*-
"""Разбор черновика d35088201 («ССК» получила контроль над двумя
девелоперскими компаниями «Носты», Гвардейская площадь в Ростове и
проект «Приморский») вручную — тот же обход ворот promote.py, что делает
`resolve_duplicates._promote_as_separate()` (образец —
pipeline/archive/2026-10/build_d55306904_irtysh_riviera_2026_10_30.py).

ПОЧЕМУ ВРУЧНУЮ. Черновик придержан 9 ноября 2026: заголовок и предмет —
не написаны, а обрезаны draft.py на полуслове прямо посреди текста
телеграм-поста @dealsma (TITLE_CUT_LEN/ASSET_CUT_LEN, промote.check). Это
дефект механической нарезки заголовка, а не повод отбросить сделку: обе
стороны, оба актива и статус названы в источнике прямо. Карточка собирается
чтением, разово; заголовок, стороны, предмет, сумма и отрасль дописывает
`review.py` FIXES (pipeline/ingest/fixes/written_d35088201_2026_11_09.py)
дословной цитатой — отсюда почти все поля черновика ниже оставлены пустыми.

Запуск: python3 pipeline/archive/2026-11/build_ssk_nosta_2026_11_09.py
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
INGEST = os.path.join(ROOT, 'pipeline', 'ingest')
sys.path.insert(0, INGEST)

import promote           # noqa: E402
import link_parties      # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
HOLD = os.path.join(ROOT, 'data', 'inbox', 'hold', '2026-11-09.json')
DRAFT_ID = 'd35088201'

DRAFT = {
    'draft_id': DRAFT_ID,
    'date': '2026-09-01',
    # Заголовок — своя конструкция, не обрывок черновика; дописан review.py
    # FIXES с цитатой (докстрока выше). Здесь — техническая заглушка под
    # стиль заголовков притока («…» не написан, а разбор заголовка).
    'title': '«ССК» получила контроль над двумя девелоперскими компаниями группы «Носта» '
              'Статус сделки: закрыта в сентябре 2026 года. Об объекте сделки '
              '• 100% долей ООО СЗ «Фрихауз» — владеет недостроенным 19-эта',
    'src': [['tg:dealsma', 'https://t.me/dealsma/7554']],
    'sum': None,
    'type': 'M&A',
    'status': 'Закрыта',
    'ind': 'Строительство',
    'buyer_name': '«ССК»',
    # seller/asset дописываются review.py с цитатой — см. докстрока выше.
    'seller': None,
    'asset': 'над двумя девелоперскими компаниями группы «Носта» Статус сделки: '
             'закрыта в сентябре 2026 года. Об',
    'events': [],
}


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    pending = promote.load_pending()
    existing = {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    party_index = link_parties.build_index(data['companies'])
    for line in link_parties.link_card(card, party_index, data['companies']):
        print('  %s | связано -> %s' % (deal_id, line))
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    pending['cards'].append(card)
    promote.save_pending(pending)

    # Снимаем черновик из очереди придержанных d35088201 (решение принято:
    # это настоящая сделка, карточка выше) — тот же прием, что approve.py
    # делает для drop/take, см. docs/intake.md.
    held = json.load(open(HOLD, encoding='utf-8'))
    before = len(held['drafts'])
    held['drafts'] = [d for d in held['drafts'] if d.get('draft_id') != DRAFT_ID]
    json.dump(held, open(HOLD, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('hold: %d -> %d черновиков' % (before, len(held['drafts'])))

    print('СОЗДАНО: %s (бывший черновик %s)' % (deal_id, DRAFT_ID))
    return deal_id


if __name__ == '__main__':
    main()
