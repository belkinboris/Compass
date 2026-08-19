# -*- coding: utf-8 -*-
"""«ЦБ зарегистрировал допэмиссию акций «М.видео» по закрытой подписке»
(`gb5d8a18a`) — тот же класс дефекта, что ПСБ/«Атом» (18 августа), только с
другим неверным `type` и с более прямым сигналом.

Карточка несла `type: "Финансирование · структурная сделка"` и
`seller: "ПАО «М.видео»"` — то есть компания записана продавцом САМОЙ СЕБЯ:
`asset`/предмет сделки — тоже акции «М.видео», причём НОВОГО, дополнительного
выпуска, а не существующего пакета. Источник (`eco.rationale`) прямо
называет цель — «завершить процесс дофинансирования компании» — это cash-in
(деньги идут самой компании), а не продажа доли действующим акционером.
У допэмиссии за деньги продавца нет в принципе (см. урок ПСБ/«Атом» в
CLAUDE.md) — здесь для роли «продавец» подставили саму компанию-эмитента,
потому что её имя стоит в тексте источника рядом с формулировкой «выпуск
акций X».

Правильный тип — «Инвестиция» (как и у ПСБ/«Атом»): buyerRole()/isRound() в
static/index.html сами покажут «Инвестор» вместо «Покупатель» и уберут
пустой «Продавец», без правок кода — только данные. Профиль «М.Видео»
(`g444cac01`, ПАО «М.видео» — конкретное юрлицо, не холдинг «М.Видео-
Эльдорадо») уже есть в базе, просто не был связан как `target`.

Покупатель (`buyer_name`) остаётся текстом: четыре юрлица группы «Эсэфай»
(АО «Эсэфай», «Кэпиталгард», «Эсэфай Кэпитал», «Лэнбури») — ни одно не имеет
профиля в базе, заводить профиль ради одной сделки не стоит.

Запуск: python3 pipeline/fix_mvideo_investment_card.py           # проверка
        python3 pipeline/fix_mvideo_investment_card.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb5d8a18a'
OLD_TYPE = 'Финансирование · структурная сделка'
NEW_TYPE = 'Инвестиция'
OLD_SELLER = 'ПАО «М.видео»'
TARGET_ID = 'g444cac01'  # существующий профиль «М.Видео»
OLD_ASSET = 'дополнительный выпуск обыкновенных акций ПАО «М.видео» по закрытой подписке'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]

    assert card.get('type') == OLD_TYPE, (
        'ожидался type=%r, сейчас %r — состояние изменилось' % (OLD_TYPE, card.get('type')))
    assert card.get('seller') == OLD_SELLER and not card.get('seller_id'), (
        'ожидался seller=%r без seller_id, сейчас seller=%r seller_id=%r — состояние изменилось'
        % (OLD_SELLER, card.get('seller'), card.get('seller_id')))
    assert card.get('asset') == OLD_ASSET and not card.get('target'), (
        'ожидался asset=%r без target, сейчас asset=%r target=%r — состояние изменилось'
        % (OLD_ASSET, card.get('asset'), card.get('target')))
    assert TARGET_ID in data['companies'], '%r должен уже существовать в базе' % TARGET_ID

    print('ПРАВИМ %s:' % CARD_ID)
    print('  type: %r -> %r' % (OLD_TYPE, NEW_TYPE))
    print('  seller %r -> удалён (компания не может продавать саму себя)' % OLD_SELLER)
    print('  asset %r -> target=%r (профиль «М.Видео»)' % (OLD_ASSET, TARGET_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['type'] = NEW_TYPE
    del card['seller']
    del card['asset']
    card['target'] = TARGET_ID

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
