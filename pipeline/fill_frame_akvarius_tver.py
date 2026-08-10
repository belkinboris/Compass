# -*- coding: utf-8 -*-
"""Карточка `c23732cd9` («ГК «Аквариус» покупает производственно-
логистический комплекс в Твери») пришла почти пустой: нет `buyer`, `sum`,
`status` (только `law.adv» с побочным упоминанием инвестиций). Профиль
покупателя («ГК «Аквариус»») уже есть в базе (`g1816256d`). `status`
«Закрыта» подтверждён источником («помогли... закрыть сделку по покупке»)
— добавлен отдельно от `buyer`/`sum`, потому что глагол в источнике стоит
в инфинитиве («закрыть»), а не в прошедшем времени («закрыл»), и не
проходит механическую проверку `STATUS_WORDS` в review.py: расширять
список триггеров инфинитивом рискованно (он используется и в
перспективных контекстах — «планирует закрыть», «рассчитывает закрыть»).

Запуск: python3 pipeline/fill_frame_akvarius_tver.py
        python3 pipeline/fill_frame_akvarius_tver.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c23732cd9'
BUYER_ID = 'g1816256d'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if (card.get('buyer') == BUYER_ID and card.get('sum') == 'Не раскрыта'
            and card.get('status') == 'Закрыта'):
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert 'buyer' not in card, '%s: buyer уже задан' % CARD_ID
    assert 'sum' not in card, '%s: sum уже задан' % CARD_ID
    assert 'status' not in card, '%s: status уже задан' % CARD_ID
    print('ПРАВИМ  %s: buyer=%s (ГК «Аквариус»), status=«Закрыта», '
          'sum-плейсхолдеры' % (CARD_ID, BUYER_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['buyer'] = BUYER_ID
    card['status'] = 'Закрыта'
    card['sum'] = 'Не раскрыта'
    card['eco']['sum'] = 'Не раскрыта'
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
