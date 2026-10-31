# -*- coding: utf-8 -*-
"""Приток 9 сентября 2026 (11:20 МСК) — карточки g110266ef и ge7301c4a
(«ЦБ купил юани на 1,9 млрд рублей с расчетами 8 сентября» / «Банк России
купил на внутреннем рынке юани на 1,9 миллиарда рублей») прошли ворота
ошибочно: это рутинная операция Банка России на внутреннем валютном рынке
в рамках бюджетного правила (регулярная покупка/продажа юаней, публикуется
ежедневно) — не сделка рынка M&A, покупателя и предмета в привычном смысле
нет. Механический разбор принял глагол «купил» с названным субъектом («ЦБ»/
«Банк России») за признак сделки. Обе карточки описывают ОДНО и то же
событие двумя источниками.

Запуск: python3 pipeline/fix_discard_cbr_yuan_purchase.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

TARGETS = {
    'g110266ef': 'https://tass.ru/ekonomika/28094225',
    'ge7301c4a': 'https://1prime.ru/20260909/tsb-873136562.html',
}


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] in TARGETS]
    assert len(matches) == 2, f'ожидались обе карточки, найдено {len(matches)}'
    for card in matches:
        url = TARGETS[card['id']]
        assert any(len(s) > 1 and s[1] == url for s in (card.get('src') or []))
        assert url not in state.get('discarded_urls', {})

    pending['cards'] = [c for c in pending['cards'] if c['id'] not in TARGETS]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for card in matches:
        state.setdefault('discarded_urls', {})[TARGETS[card['id']]] = {
            'id': card['id'], 'title': card.get('title'), 'at': now,
        }

    print('Сняты карточки', ', '.join(TARGETS), '— рутинная покупка юаней Банком России, не сделка M&A.')

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
