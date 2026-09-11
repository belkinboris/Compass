# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (15:20 МСК) — карточка `gdecabcde`
(«Экспобанк приобрел контрольный пакет акций СДМ-банка») прошла ворота
черновиком: `note` нёс необрезанный RSS-хвост («…Сообщение … появилось
сначала на Frank Media .»), у предмета не было профиля (СДМ-Банк — не
безымянный лот, а поднадзорный банк с реальным ИНН/лицензией, и профиль
для него заводится по той же логике, что уже заведён для Совкомбанка/
ВТБ/Альфа-Банка), а факт о росте доли (23,5% -> 86%) лежал только в
черновом `note` и не был перенесён в `eco.context`.

Источник (WebFetch, дословно): "По данным «СПАРК-Интерфакса», до этого
Экспобанку принадлежало 23,5% акций." + "По ее итогам доля Экспобанка
выросла до 86%." Продавец, сумма и консультанты в статье не названы —
честная пустота, не пробел.

Запуск: python3 pipeline/fix_expobank_sdm_bank.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbeb0dfe8'
TARGET_ID = 'gsdmbank'
SRC_URL = 'https://frankmedia.ru/304498'

QUOTE_STAKE = ('По данным «СПАРК-Интерфакса», до этого Экспобанку '
               'принадлежало 23,5% акций. По ее итогам доля Экспобанка '
               'выросла до 86%.')


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    assert TARGET_ID not in base['companies'], 'профиль %s уже есть' % TARGET_ID

    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена в pending.json' % CARD_ID
    assert card.get('target') is None, 'target уже проставлен'
    assert card['events'][0]['note'].startswith('По итогам сделки его доля'), \
        'note уже другой — правка неприменима повторно'

    card['target'] = TARGET_ID
    card['events'][0]['note'] = (
        'Экспобанк увеличил долю в СДМ-Банке с 23,5% до 86% и стал '
        'контролирующим акционером. Продавец и сумма сделки не раскрыты.'
    )
    card['eco']['context'] = QUOTE_STAKE
    card['reviewed'] = '2026-09-11'

    base['companies'][TARGET_ID] = {
        'name': 'СДМ-Банк',
        'ind': 'Банки',
        'desc': 'Российский коммерческий банк, работает с 1991 года.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[TARGET_ID] = ['сдм-банк', 'сдм банк']

    print('Правка %s: target=%s, note очищен, eco.context дописан.' %
          (CARD_ID, TARGET_ID))

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
