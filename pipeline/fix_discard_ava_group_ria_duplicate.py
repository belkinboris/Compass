# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (13:20 МСК) — карточка g993cd00d («Ava Group
продала земельный участок на Белоостровской улице в Петербурге», РИА
Недвижимость) — та же сделка, что уже собрана как gc52a53dd (РАД/AVA
Group, Деловой Петербург, 09:24 МСК того же дня). Новый факт этого
источника (стартовая цена торгов 634,7 млн руб.) уже перенесён в
gc52a53dd вместе со ссылкой на этот источник как на второй (см.
pipeline/ingest/fixes/batch_2026_09_08_rad_ava_beloostrovskaya.py) —
карточка-дубль снимается.

Запуск: python3 pipeline/fix_discard_ava_group_ria_duplicate.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://realty.ria.ru/20260908/peterburg-2116286206.html'
CARD_ID = 'g993cd00d'
PRIOR_ID = 'gc52a53dd'


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
    prior = [c for c in pending['cards'] if c['id'] == PRIOR_ID]
    assert prior, f'ожидалась карточка {PRIOR_ID} в очереди предпросмотра'
    assert any(len(s) > 1 and s[1] == URL for s in (prior[0].get('src') or [])), \
        f'факт {URL} должен уже быть перенесён в src карточки {PRIOR_ID}'

    pending['cards'] = [c for c in pending['cards'] if c['id'] != CARD_ID]
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID, 'title': card.get('title'),
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    }

    print(f'Снята карточка {CARD_ID} (тот же сюжет, что {PRIOR_ID}; новый факт уже перенесён).')

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
