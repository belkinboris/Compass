# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (11:20 МСК) — карточка gc9f7769c прошла ворота
ошибочно: заголовок «ЦБ купил юани на 5,9 млрд рублей с расчетами
7 сентября» (ТАСС) — рутинная валютная операция Банка России на бирже
(покупка/продажа юаня в рамках операций на внутреннем рынке), а не сделка
M&A или инвестиция в компанию. Разбор заголовка вычленил «ЦБ» как
покупателя и «юани на 5,9 млрд рублей с расчетами 7 сентября» как
предмет — формально прошло ворота, по существу не наша тема (класс
«макроэкономика/курсы» из списка уверенного мусора). Тот же класс уже
встречался с покупкой юаней ЦБ 7 сентября (draft d8ccc9185 — тогда
отклонено на шаге 7, до ворот; сегодня то же по существу событие
получило новую подробность о дате расчётов и другой источник, и в этот
раз проскочило сами ворота).

Запуск: python3 pipeline/fix_discard_cbr_yuan_purchase_sept8.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://tass.ru/ekonomika/28090155'
CARD_ID = 'gc9f7769c'


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

    print(f'Снята карточка {CARD_ID} (рутинная валютная операция ЦБ, не M&A).')

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
