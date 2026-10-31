# -*- coding: utf-8 -*-
"""Ложное совпадение в очереди дублей: «Дима Билан продал особняк в
Подмосковье за 250 млн рублей и купил усадьбу» (`d74403830`) попал в
`data/inbox/duplicates/2026-10-16.json` как кандидат на дубль карточки
`g5aabf462` («Дом.РФ» выставил на конкурс усадьбу, где родился нарком
Чичерин) — ворота сработали по общему слову «усадьба», предметы и
продавцы разные (личный особняк певца в Подмосковье за 250 млн ₽ против
усадьбы «Дом.РФ» в Тамбовской области за 2,48 млн ₽).

Но это не дубль И не отдельная сделка для базы: продажа личного особняка
и покупка усадьбы артистом — частная жилая недвижимость, не корпоративный
M&A-актив (нет компании-покупателя, нет рыночного продавца). Ни один из
пяти исходов `resolve_duplicates.py` (`same_fact`/`new_stage`/`enrich`/
`separate`/`unclear`) не подходит: `separate` создал бы карточку для
не-сделки (как уже чинили у `g3bd97268`/Текслера), `same_fact` соврал бы
про совпадение факта. Выкидываем вручную: убираем запись из очереди
дублей и отмечаем источник как отказ — тем же механизмом, что
`discard_g3bd97268_...py` (raw_titles='drop' в moderation_state.json).

Запуск:
    python3 pipeline/discard_bilan_not_corporate_deal_2026_10_16.py            # сухой прогон
    python3 pipeline/discard_bilan_not_corporate_deal_2026_10_16.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUPLICATES = os.path.join(ROOT, 'data', 'inbox', 'duplicates', '2026-10-16.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

DRAFT_ID = 'd74403830'
URL = ('https://iz.ru/2185416/dima-bilan-prodal-osobniak-v-podmoskove-za-250-mln-rublei-i-kupil-usadbu/ize')
TITLE = 'Дима Билан продал особняк в Подмосковье за 250 млн рублей и купил усадьбу'
RAW_TITLE_KEY = promote.raw_key(TITLE)
REASON = ('не сделка для этой базы: продажа личного особняка и покупка усадьбы '
          'певцом Димой Биланом — частная жилая недвижимость, не корпоративный '
          'M&A-актив; в очередь дублей попал ложно, по общему слову «усадьба» '
          'с карточкой g5aabf462 (предметы и продавцы разные)')


def main(write=False):
    dups = json.load(open(DUPLICATES, encoding='utf-8'))
    items = dups.get('items', [])
    match = [i for i in items if i.get('draft', {}).get('draft_id') == DRAFT_ID]
    assert match, '%s не найден в очереди дублей' % DRAFT_ID
    assert match[0]['draft']['title'] == TITLE, 'заголовок не совпал: %r' % match[0]['draft']['title']

    state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in state.get('discarded_urls', {}), 'URL уже отмечен в discarded_urls'

    print('ВЫКИДЫВАЮ %s: %s' % (DRAFT_ID, TITLE))
    print('  duplicates/2026-10-16.json: запись убрана из очереди')
    print('  discarded_urls += %s' % URL)
    print('  raw_titles += %s -> drop' % RAW_TITLE_KEY)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_dups = json.load(open(DUPLICATES, encoding='utf-8'))
    fresh_dups['items'] = [i for i in fresh_dups.get('items', [])
                           if i.get('draft', {}).get('draft_id') != DRAFT_ID]
    json.dump(fresh_dups, open(DUPLICATES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fresh_state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in fresh_state.get('discarded_urls', {}), 'URL отметили параллельно — перечитайте'
    fresh_state.setdefault('discarded_urls', {})[URL] = {
        'reason': REASON,
        'date': datetime.now(timezone.utc).date().isoformat(),
    }
    fresh_state.setdefault('raw_titles', {})[RAW_TITLE_KEY] = 'drop'
    json.dump(fresh_state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
