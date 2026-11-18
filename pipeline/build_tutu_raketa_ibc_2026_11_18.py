# -*- coding: utf-8 -*-
"""Карточка g5d3527dd, «Туту» покупает «Ракету» и IBC Corporate Travel: структурные поля,
которые не ложатся в таблицу review.py, — по просьбе партнера (тема «Клод», сообщение 3711,
18 ноября 2026).

ЧТО СТАВИТСЯ И ПОЧЕМУ:
  * предмет — «Ракета» и IBC Corporate Travel: так называют обе компании «Коммерсантъ»,
    «Ведомости» и сообщение «Туту» (ПРАЙМ); одной строкой в статьях не стоит. Юрлица —
    ООО «Ракета» (ИНН 2540137892) и ООО «Интернейшнл Бизнес Центр» (ИНН 6661060352) — по
    сайтам компаний (raketa.world, ct.ibc.ru), они названы в eco.share.
  * продавцы — Евгений Чупахин и Вера Барановская: участники ООО «Ракета» (72% и 28%,
    запись ЕГРЮЛ от 17.11.2026, datanewton) и оба участника ООО «Интернейшнл Бизнес Центр»
    (Saby, СПАРК); пресса продавцов не называет.
  * сумма не раскрыта («Коммерсантъ»: «Условия сделки и ее стоимость там не привели»);
    500–600 млн руб. из черновика — оценка аналитика Михаила Бурмистрова, она в eco.val
    (docs/card_money.md, «Что идет в сумму»).
  * отрасль — «Транспорт и логистика»: как у профиля Tutu.ru и карточки «Туту» / Trivio (gd2696c44);
    «Гостиницы и туризм» дает посту метки #недвижимость #гостиницы — они здесь неверны.
  * perimeter_beyond_target: профиль предмета несет ИНН одного общества (ООО «Интернейшнл
    Бизнес Центр»), а куплены два — в мультипликаторы сделка не идет (docs/analytics_acceptance.md).

Запуск:
    python3 pipeline/build_tutu_raketa_ibc_2026_11_18.py            # сухой прогон
    python3 pipeline/build_tutu_raketa_ibc_2026_11_18.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD_ID = 'g5d3527dd'
KOM = 'https://www.kommersant.ru/doc/9112419'
VED = 'https://www.vedomosti.ru/business/news/2026/11/18/1412899-prisoedinenie-k-tutu'
DN = 'https://datanewton.ru/contragents/'
SELLER = 'Евгений Чупахин и Вера Барановская'
ASSET = '«Ракета» и IBC Corporate Travel'
EXTRA_SRC = [
    ['ЕГРЮЛ: ООО «Ракета»', DN + '1072540010729'],
    ['ЕГРЮЛ: ООО «Интернейшнл Бизнес Центр»', DN + '1026605234391'],
]


def patch(card):
    assert card['title'] == '«Туту» покупает «Ракету» и IBC Corporate Travel', card['title']
    assert card.get('buyer_name') == '«Туту»' and not card.get('seller') and not card.get('asset'), \
        (card.get('buyer_name'), card.get('seller'), card.get('asset'))
    assert card['sum'] == '600 млн ₽' and card['eco']['sum'] == '600 млн ₽', (card['sum'], card['eco']['sum'])
    assert card['ind'] == 'Не определена', card['ind']
    assert [s[1] for s in card['src']][:2] == [KOM, VED], card['src']
    card['sum'] = 'Не раскрыта'
    card['eco']['sum'] = 'Не раскрыта'
    card['ind'] = 'Транспорт и логистика'
    card['perimeter_beyond_target'] = True
    card['asset'] = ASSET
    card['seller'] = SELLER
    card['seller_src'] = 'text'
    card['kind'] = 'acquisition'
    have = {s[1] for s in card['src']}
    card['src'] += [list(s) for s in EXTRA_SRC if s[1] not in have]
    ev = card.setdefault('party_evidence', {})
    ev['buyer'] = [{'value': '«Туту»', 'field': 'buyer_name', 'method': 'manual_source_review', 'url': VED}]
    ev['target'] = [{'value': ASSET, 'field': 'asset', 'method': 'manual_source_review', 'url': VED}]
    ev['seller'] = [{'value': SELLER, 'field': 'seller', 'method': 'manual_source_review',
                     'url': DN + '1072540010729'}]
    return card


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))   # читается прямо перед записью
    cards = [c for c in pending['cards'] if c['id'] == CARD_ID]
    if not cards:
        print('ОТКАЗ: %s нет в очереди' % CARD_ID)
        return 1
    if cards[0].get('seller') == SELLER and cards[0].get('ind') == 'Гостиницы и туризм':
        cards[0]['ind'] = 'Транспорт и логистика'      # первая запись ставила «Гостиницы и туризм»
        cards[0]['perimeter_beyond_target'] = True
        print('ind -> Транспорт и логистика, perimeter_beyond_target')
        if write:
            json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return 0
    if cards[0].get('seller') == SELLER:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    card = patch(cards[0])
    print(json.dumps({k: card.get(k) for k in ('date', 'sum', 'ind', 'buyer_name', 'seller', 'asset', 'src', 'kind')},
                     ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
