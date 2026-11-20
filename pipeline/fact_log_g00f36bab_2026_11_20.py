# -*- coding: utf-8 -*-
"""Карточка g00f36bab («АО «Деловые связи» купило 100% ООО «Аппетит»») была
дополнена разовым скриптом (pipeline/archive/2026-11/enrich_appetit_delovye_
svyazi_2026_11_20.py) по истории участников ЕГРЮЛ — без записи подтверждения
через fact_edit_guard.log() — prepush_check.py отказал пушить («правка факта
без подтверждающей цитаты» у 2 полей: date, seller). Этот скрипт дописывает
недостающие записи в card['fact_log'] — значения полей уже стоят верно
(проверено assert), меняется только подтверждение.

Источник: ЕГРЮЛ (datanewton), история участников ООО «Аппетит» по ОГРН
1247800072740.

Запуск: python3 pipeline/fact_log_g00f36bab_2026_11_20.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g00f36bab'
URL = ('https://datanewton.ru/api/v2/history?ogrn=1247800072740'
       '&startDate=2000-01-01&attributes=OWNERS')
SRC_NAME = 'ЕГРЮЛ (datanewton): история участников ООО «Аппетит»'
BY = 'приток, 20 ноября 2026 (ЕГРЮЛ)'

QUOTE = ('2026-06-25: было — ДУЛОВ АНТОН СЕРГЕЕВИЧ 82,8%; стало — —. '
         '2026-06-25: было — МАГОМЕДОВ ВАДИМ ХУСАИНОВИЧ 17,2%; стало — —. '
         '2026-06-25: было — —; стало — АО "ДЕЛОВЫЕ СВЯЗИ" (ОГРН: 1197847182444) 100.0%.')

ENTRIES = [
    ('date', '2026-06-25', QUOTE),
    ('seller', 'Антон Дулов и Вадим Магомедов', QUOTE),
]


def main(write):
    base = json.loads(open(DATA, encoding='utf-8').read())
    cards = {d['id']: d for d in base['deals']}
    card = cards[CARD_ID]
    assert card.get('date') == '2026-06-25', card.get('date')
    assert card.get('seller') == 'Антон Дулов и Вадим Магомедов', card.get('seller')
    for field, new, quote in ENTRIES:
        fact_edit_guard.log(card, field, new, quote, URL, BY)
        print('fact_log: %s -> %r' % (field, new))
    if write:
        raw = open(DATA, encoding='utf-8').read()
        open(DATA, 'w', encoding='utf-8').write(
            json.dumps(base, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
