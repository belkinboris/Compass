# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (12:20 МСК) — две карточки прошли ворота, но не
подходят по существу.

gddbadba2 «Банк России купил юани на 5,9 миллиарда рублей с расчетом на
7 сентября» (ПРАЙМ) — тот же класс, что уже дважды снимался сегодня
(TASS, 11:20): рутинная валютная операция ЦБ на бирже, не сделка M&A.
Разбор к тому же не справился с самим заголовком: buyer_name = «России»
(обрывок «Банка России») — бессмысленный фрагмент.

g2c770c5a «Израильская Aurelius купит завод Volkswagen в Оснабрюке»
(Коммерсантъ) — сделка про завод VW в Германии, покупатель — Aurelius
Capital (Израиль) с участием федеральной земли Нижняя Саксония; полный
текст статьи ни разу не упоминает Россию, российских лиц или активы —
нероссийский контур без российского элемента, публиковать не должны
(правило CLAUDE.md).

Запуск: python3 pipeline/fix_discard_cbr_yuan_and_vw_osnabruck.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

TO_DROP = [
    ('gddbadba2', 'https://1prime.ru/20260908/tsentrobank-873102830.html'),
    ('g2c770c5a', 'https://www.kommersant.ru/doc/8938794'),
]


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    for card_id, url in TO_DROP:
        matches = [c for c in pending['cards'] if c['id'] == card_id]
        assert len(matches) == 1, f'ожидалась ровно одна карточка {card_id}, найдено {len(matches)}'
        card = matches[0]
        assert any(len(s) > 1 and s[1] == url for s in (card.get('src') or []))
        assert url not in state.get('discarded_urls', {})

        pending['cards'] = [c for c in pending['cards'] if c['id'] != card_id]
        state.setdefault('discarded_urls', {})[url] = {
            'id': card_id, 'title': card.get('title'),
            'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        }
        print(f'Снята карточка {card_id} ({card.get("title")}).')

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
