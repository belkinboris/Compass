# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (15:23 МСК) — карточка g3bb0602e («Rio Tinto
купит бокситовый проект Aurukun в австралийском Квинсленде») прошла ворота
ошибочно: сделка целиком иностранная — австрало-британская Rio Tinto Group
покупает бокситовый проект в Квинсленде (Австралия) у совместного
предприятия Glencore и Mitsubishi Development, одобрение требуется от
правительства штата Квинсленд и регуляторов Австралии. Ни одна сторона,
ни предмет сделки не имеют отношения к российскому рынку — источник
(ПРАЙМ) лишь пересказывает Рейтер без единого российского элемента.

Запуск: python3 pipeline/fix_discard_rio_tinto_aurukun.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://1prime.ru/20260908/kvinslend-873112335.html'
CARD_ID = 'g3bb0602e'


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

    print(f'Снята карточка {CARD_ID} — иностранный контур без российского элемента (Rio Tinto/Австралия).')

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
