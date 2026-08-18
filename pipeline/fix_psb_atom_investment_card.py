# -*- coding: utf-8 -*-
"""«ПСБ купил 16,9% акций... «Атом»» (gcaa03820) — четыре находки владельца
18 августа, все подтверждаются уже лежащими в самой карточке цитатами:

1. ТИП СДЕЛКИ. Карточка несла `type: "M&A"` и показывала «Продавец: не
   раскрыт» / «Покупатель: ПСБ» — но собственная цитата в `events[0].note`
   говорит прямо: «пакет выкуплен в рамках дополнительной эмиссии за
   денежные средства» — это допэмиссия ЗА ДЕНЬГИ (cash-in): деньги идут
   САМОЙ компании, а не продающему акционеру (cash-out, как было бы при
   продаже уже существующего пакета). У допэмиссии за деньги нет продавца
   в принципе — сторона, названная «продавец не раскрыт», для такой сделки
   не пустое поле, а несуществующая роль. Правильный тип — «Инвестиция»
   (128 таких карточек уже в базе): `isRound()`/`buyerRole()` в
   static/index.html сами переключают плашку на «Инвестор» и убирают
   пустой «Продавец», без правок кода — только `type`.

2. ПОКУПАТЕЛЬ КАК ТЕКСТ, НЕ ССЫЛКА. `buyer_name: "ПСБ"` без `buyer` —
   профиль «Промсвязьбанк» (g8bafde28) уже есть в базе, просто не связан.

3. ПРЕДМЕТ — БРЕНД+ОПИСАНИЕ ВМЕСТО ИМЕНИ КОМПАНИИ. `asset` нёс «российский
   производитель электромобилей "Атом" [АО "Кама"]» — пересказ вместо
   имени юрлица. Профиля «Кама» в базе уже ЕСТЬ (gcc2d3689) — но это
   СОВСЕМ ДРУГАЯ компания (Камский ЦБК, картон, продан «Свезе» в 2024-м):
   линковать target на неё значило бы записать чужую сторону в чужую
   сделку, тот же класс дефекта, что уже ловили на профиле Домодедово/
   Селегеня. Заводим новый профиль под другим именем («Кама» (Атом)) —
   `test_no_company_twins` не совпадает с ним по транслитерационному
   ключу, отдельного исключения заводить не нужно.

4. МЕТКА ИСТОЧНИКА. «tg:rusven» — отдельный, более общий баг, чинится
   pipeline/fix_raw_feed_id_source_labels.py, не этим скриптом.

Кто продал долю (действующий акционер или ТОЛЬКО компания получила деньги)
источник не называет — оставляем честной пустотой, не домысливаем.

Запуск: python3 pipeline/fix_psb_atom_investment_card.py           # проверка
        python3 pipeline/fix_psb_atom_investment_card.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gcaa03820'
OLD_TYPE = 'M&A'
NEW_TYPE = 'Инвестиция'
OLD_BUYER_NAME = 'ПСБ'
BUYER_ID = 'g8bafde28'  # существующий профиль «Промсвязьбанк»
OLD_ASSET = 'российский производитель электромобилей “Атом” [АО “Кама”]'
NEW_COMPANY_ID = 'kama_atom'
NEW_COMPANY = {
    'name': '«Кама» (Атом)',
    'ind': 'Автопром',
    'desc': ('Российский производитель электромобилей под брендом «Атом»; '
             'среди стратегических партнёров проекта — КамАЗ и «Росатом».'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]

    assert card.get('type') == OLD_TYPE, (
        'ожидался type=%r, сейчас %r — состояние изменилось' % (OLD_TYPE, card.get('type')))
    assert card.get('buyer_name') == OLD_BUYER_NAME and not card.get('buyer'), (
        'ожидался buyer_name=%r без buyer, сейчас buyer_name=%r buyer=%r — состояние изменилось'
        % (OLD_BUYER_NAME, card.get('buyer_name'), card.get('buyer')))
    assert card.get('asset') == OLD_ASSET and not card.get('target'), (
        'ожидался asset=%r без target, сейчас asset=%r target=%r — состояние изменилось'
        % (OLD_ASSET, card.get('asset'), card.get('target')))
    assert BUYER_ID in data['companies'], '%r должен уже существовать в базе' % BUYER_ID
    assert NEW_COMPANY_ID not in data['companies'], (
        'профиль %r уже существует — не перезаписываем' % NEW_COMPANY_ID)

    print('ПРАВИМ %s:' % CARD_ID)
    print('  type: %r -> %r' % (OLD_TYPE, NEW_TYPE))
    print('  buyer_name %r -> buyer=%r (профиль «Промсвязьбанк»)' % (OLD_BUYER_NAME, BUYER_ID))
    print('  + новый профиль %r' % NEW_COMPANY_ID)
    print('  asset %r -> target=%r' % (OLD_ASSET, NEW_COMPANY_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['type'] = NEW_TYPE
    card['buyer'] = BUYER_ID
    del card['buyer_name']
    data['companies'][NEW_COMPANY_ID] = NEW_COMPANY
    card['target'] = NEW_COMPANY_ID
    del card['asset']

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
