# -*- coding: utf-8 -*-
"""Приток 9 сентября 2026 (14:20 МСК) — карточка gf2daa082 («77-летняя
россиянка выкупила у террористов британского морского офицера») прошла
ворота ошибочно: это романтическое телефонное мошенничество (кировская
пенсионерка 3,5 года переводила деньги мошеннику, выдававшему себя за
британского офицера, включая «выкуп» за вымышленный захват террористами) —
криминальная история, не сделка рынка M&A. Тот же сюжет уже отсеян этим же
прогоном ранее под другим заголовком («Жительница Кирова заплатила
"террористам" выкуп за "морского офицера"»).

Запуск: python3 pipeline/fix_discard_kirov_romance_scam.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://lenta.ru/news/2026/09/09/77-letnyaya-rossiyanka-vykupila-u-terroristov-britanskogo-morskogo-ofitsera/'
CARD_ID = 'gf2daa082'


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

    print(f'Снята карточка {CARD_ID} — телефонное мошенничество, не сделка рынка M&A.')

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
