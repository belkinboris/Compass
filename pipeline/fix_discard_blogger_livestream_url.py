# -*- coding: utf-8 -*-
"""Почасовой приток 4 сентября 2026 (~16:20) — ложная карточка «Блогер из
КНР Даньдань продала товары РФ ... за время ВЭФ» (tass.ru/ekonomika/28080427,
розничная выручка со стрима, не сделка M&A) уже снималась этим прогоном
однократно (`fix_remove_false_positive_blogger_livestream_card.py`, id
`ga42672ed`) — но простое удаление карточки из `pending.json` не оставило
следа в `discarded_urls`, а `promote.py` индексирует дубли ТОЛЬКО по тому,
что реально лежит в `pending['cards']`: как только карточка исчезла, её
адрес перестал быть «уже известным», и следующий же прогон разобрал тот же
адрес заново, под новым id (`g95cd6cf2`). Тот же класс памяти, что уже
описан в approve.py при вердикте «discard» (см. его комментарий там же):
адрес источника нужно занести в `discarded_urls` в `moderation_state.json`
— именно этот реестр `promote.py` проверяет перед тем, как разбирать
черновик (строки ~585-589), и именно так ведёт себя ручной вердикт 🗑
«Выкинуть» в консоли. Скрипт воспроизводит ровно тот же эффект для случая,
когда решение принимается автоматической рутиной, а не владельцем в
Telegram.

Запуск: python3 pipeline/fix_discard_blogger_livestream_url.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://tass.ru/ekonomika/28080427'
CARD_ID = 'g95cd6cf2'


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

    print(f'Снята карточка {CARD_ID}, адрес {URL} записан в discarded_urls — не вернётся под новым id.')

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
