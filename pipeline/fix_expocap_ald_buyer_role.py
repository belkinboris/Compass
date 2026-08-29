#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карточка `gecf3eca5` (ALD Automotive продаёт лизинговую компанию
«Экспокапу») несла `buyer = g6ba1b0c4` («Экспокап») — но собственное поле
карточки `law.appr` (дословная цитата, уже прошедшая review.py) говорит
прямо: «Владельцем 100% доли в уставном капитале лизинговой компании
«АЛД Автомотив»... стало АО «ЦК», следует из данных... ЕГРЮЛ». «Экспокап» —
инвестиционная платформа/бренд Игоря Кима (law.struct той же карточки:
«...бенефициаром... выступает Игорь Ким — совладелец Экспобанка и
«Экспокапа»» — это отдельная, но связанная структура), а конкретное юрлицо,
которое реально зарегистрировало на себя долю по ЕГРЮЛ, — «АО «ЦК»»
(gc0638d38, ИНН 5406187398, уже подтверждено кампанией самопроверки ИНН как
покупатель СОСЕДНЕЙ сделки — лизингового бизнеса Volkswagen Financial
Services). Тот же класс, что уже записан в CLAUDE.md: «Прямой юридический
покупатель и конечный бенефициар — разные роли» (Игорь Ким/МФО «Береке») —
только здесь роль спутана не с бенефициаром-физлицом, а с инвестиционным
брендом, под которым бенефициар известен шире.

Найдено кампанией Этап 14, П3 (партия 4/4): попытка подтвердить ИНН
«Экспокапа» напрямую дала ноль результатов (это не отдельное юрлицо, а
марка), и это совпало с ИНН, уже подтверждённым для gc0638d38 по другой
сделке той же группы Кима — коллизия задокументирована в fns_registry.py,
но правка структурного поля `buyer` карточки — отдельная задача, за
пределами файла реестра, решена здесь.

После правки `g6ba1b0c4` не используется ни одной сделкой, ни полем
`holding`/`ownership` ни одного профиля — профиль удалён как ошибочно
заведённый под несуществующее юрлицо (по образцу уже сделанных в этой же
кампании правок Guess/ГЕСС СИАЙЭС и АЛД Автомотив/seller_id). Запись о нём
в pipeline/fns_registry.py снимается отдельной правкой того же коммита.

Запуск:
    python3 pipeline/fix_expocap_ald_buyer_role.py            # сухой прогон
    python3 pipeline/fix_expocap_ald_buyer_role.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

DEAL_ID = 'gecf3eca5'
OLD_BUYER = 'g6ba1b0c4'
NEW_BUYER = 'gc0638d38'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = deals[DEAL_ID]
    assert deal['buyer'] == OLD_BUYER, 'buyer уже не %s' % OLD_BUYER
    assert OLD_BUYER in companies, 'профиль-бренд уже удалён'
    assert NEW_BUYER in companies, 'профиль «ЦК» не найден'
    assert 'стало АО «ЦК»' in deal['law']['appr'], \
        'дословная цитата про АО «ЦК» пропала из law.appr — проверьте карточку заново'

    REFS = ('buyer', 'seller_id', 'target', 'asset_id')
    other_refs = [d['id'] for d in data['deals']
                  if d['id'] != DEAL_ID and OLD_BUYER in {d.get(f) for f in REFS}]
    assert not other_refs, 'профиль ещё используется другими сделками: %s' % other_refs

    print('Проверки прошли. План:')
    print('  %s: buyer %s -> %s (АО «ЦК»)' % (DEAL_ID, OLD_BUYER, NEW_BUYER))
    print('  удалить осиротевший профиль %s («Экспокап»-бренд)' % OLD_BUYER)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['buyer'] = NEW_BUYER
    del companies[OLD_BUYER]
    data['match_keys'].pop(OLD_BUYER, None)

    assert deals[DEAL_ID]['buyer'] == NEW_BUYER
    assert OLD_BUYER not in companies
    assert OLD_BUYER not in data['match_keys']

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
