# -*- coding: utf-8 -*-
"""Приток 9 сентября 2026 (12:20 МСК) — две карточки прошли ворота ошибочно,
у обеих нет ни одного российского элемента.

g6caadf4e («Месси договорился о приобретении «Эльденсе» из второго
испанского дивизиона») — Лионель Месси покупает 100% испанского футбольного
клуба «Эльденсе» (Аликанте). Прочитан полный текст источника (Коммерсантъ) —
ни стороны, ни предмет, ни валюта, ни один факт статьи не касаются России;
это спортивная новость об аргентинском футболисте и испанском клубе.

gcd697849 («Google выкупил половину мощности финской АЭС "Ловииса" под
дата-центры») — Google заключил 22-летний контракт на выкуп до 50% мощности
финской АЭС у финского концерна Fortum, плюс инвестиции в дата-центры в
Финляндии. Прочитан полный текст (dp.ru): единственное упоминание России —
что Fortum переводит реакторы на западное топливо, ЧТОБЫ НЕ ЗАВИСЕТЬ от
российского ТВЭЛ («Росатома») — то есть российский элемент здесь означает
уход от российского поставщика, а не участие российской стороны в сделке.
К тому же по существу это не сделка M&A (смены владельца/доли нет), а
долгосрочный контракт на закупку энергии (power purchase agreement).

Запуск: python3 pipeline/fix_discard_messi_and_google_loviisa.py [--write]
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
    'g6caadf4e': 'https://www.kommersant.ru/doc/8939773',
    'gcd697849': 'https://www.dp.ru/a/2026/09/09/google-vikupil-polovinu-moshhnosti',
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

    print('Сняты карточки', ', '.join(TARGETS), '— иностранный контур без российского элемента (Месси/футбол, Google/финская АЭС).')

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
