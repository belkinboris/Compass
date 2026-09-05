# -*- coding: utf-8 -*-
"""Почасовой приток 5 сентября 2026 (13:20) — ложная карточка «Больше
половины россиян (52,8%) лучше купят квартиру для ребенка, чем оплатят
престижный вуз» — это результат социологического опроса о семейных
финансовых привычках (smart-lab.ru), не сделка M&A. Заголовок с числом в
скобках и словом «купят» распарсился как «покупатель — предмет — сумма»:
`buyer_name` стал куском заголовка («Больше половины россиян (52,8%)
лучше»), `asset` — другим куском («квартира для ребенка, чем оплатят
престижный вуз»), `sum` — числом из статьи (6,8 млн ₽), не имеющим
отношения ни к какой сделке. Снимается тем же приёмом, что и предыдущие
ложные карточки сегодня (discarded_urls).

Запуск: python3 pipeline/fix_discard_survey_apartment_vs_college.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://smart-lab.ru/blog/1348211.php'
CARD_ID = 'g9b6b188d'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID}, найдено {len(matches)}'
    card = matches[0]
    assert any(len(s) > 1 and s[1] == URL for s in (card.get('src') or []))
    assert URL not in state.get('discarded_urls', {})

    pending['cards'] = [c for c in pending['cards'] if c['id'] != CARD_ID]
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID, 'title': card.get('title'),
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    }

    print(f'Снята карточка {CARD_ID} (социологический опрос, не сделка).')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
