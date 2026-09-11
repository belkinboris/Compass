# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (13:20 МСК) — карточка `gf080e8f0» собрана из
заголовка страницы-справочника TAdviser о компании «ЦОД СПб» (не статьи —
корпоративной вики-карточки с деревом собственников), поэтому в `asset`
попал хвост заголовка («…, которая строит дата-центры»), а сам факт тонкий:
единственное, что источник утверждает, — «Собственники: СберИнвест
(Сбербанк Инвестиции) - 30%» и рубрика «История 2025: Сбербанк купил долю
в «ЦОД СПб»». WebSearch не нашёл отдельной новостной статьи с датой и
суммой — сделка известна только по этой карточке-справочнику.

Покупатель — существующий профиль `gac30cf97» (СберИнвест, уже связан
`holding` с Сбербанком) — точнее, чем автоматически подставленный профиль
самого Сбербанка (`g28ff15bb`): инвестировала именно инвестподразделение,
а не банк напрямую.

Сумма не раскрыта нигде; дата — только год (2025), точный день/месяц
источник не называет. Заведён профиль предмета («ЦОД СПб»).

Запуск: python3 pipeline/fix_sberinvest_cod_spb.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf080e8f0'
BUYER_ID = 'gac30cf97'
TARGET_ID = 'gcodspb'
TARGET_NAME = '«ЦОД СПб»'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена в pending.json' % CARD_ID
    assert card.get('buyer') == 'g28ff15bb', 'покупатель уже другой: %r' % card.get('buyer')
    assert card['asset'] == '«ЦОД СПб», которая строит дата-центры'
    assert TARGET_ID not in base['companies']

    base['companies'][TARGET_ID] = {
        'name': TARGET_NAME,
        'ind': 'ИТ и интернет',
        'desc': 'Строит дата-центры в Санкт-Петербурге.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[TARGET_ID] = ['цод спб']

    card['title'] = 'СберИнвест приобрёл 30% в «ЦОД СПб»'
    card['buyer'] = BUYER_ID
    card['target'] = TARGET_ID
    card['asset'] = '30% «ЦОД СПб»'
    card['date'] = '2025'
    card['eco']['share'] = ('30% «ЦОД СПб». Точная дата сделки и сумма не '
                             'раскрыты — источник (TAdviser) называет только '
                             'год и долю.')
    card['events'][0]['date'] = '2025'
    card['events'][0]['note'] = ('СберИнвест (Сбербанк Инвестиции) владеет '
                                  '30% в компании «ЦОД СПб», которая строит '
                                  'дата-центры.')

    print('Карточка %s починена: %s' % (CARD_ID, card['title']))

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
