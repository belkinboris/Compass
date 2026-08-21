#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки Альфа-Банк/Flocktory ссылался на профиль совсем другой
компании — «КИВИ».

ЧТО СЛОМАНО. Карточка `g113002a7` («Альфа-банк приобрел платформу
маркетинговой автоматизации Flocktory у Qiwi Group») хранит
`target: "gd5d02d09"`, а профиль `gd5d02d09` называется «КИВИ» — платёжный
холдинг, отдельный бизнес, не Flocktory. Сама карточка ПРАВИЛЬНО называет
предмет своими же полями («100% платформы Flocktory (ООО «Флоктори»)» в
`eco.share`, «Приобретение 100% долей ООО «Флоктори»» в `law.struct») —
только структурная ссылка `target` указывает не туда. Найдено 21 августа
при заполнении G8 (PRODUCT_ROADMAP.md): при чтении текста для проверки
доли в сделке текст и ссылка разошлись — та же категория дефекта, что уже
чинилась для ЛСР/Domina Пулково (`fix_pulkovo_target_profile.py`, тот же
приём применён здесь), только там ссылка вела на профиль ЧЕЛОВЕКА, а
здесь — на профиль ДРУГОГО, но похожего по контексту бизнеса (обе
компании исторически входили в периметр Qiwi/Fusion Factor, что и стало,
похоже, источником путаницы при разборе).

ПОЧЕМУ ПРОФИЛЬ КИВИ НЕ ТРОГАЕТСЯ. `gd5d02d09` используется и в другой,
корректной сделке — `g0fadc207` («Fusion Factor Fintech Limited приобрела
100% акций АО «КИВИ»»), где ссылка верна и профиль недавно (в этом же
прогоне качества) получил структурированную запись `ownership`. Профиль
КИВИ не удаляется и не переименовывается — только `g113002a7` получает
СВОЙ, новый и верный профиль.

Запуск:
    python3 pipeline/fix_alfabank_flocktory_target_profile.py            # сухой прогон
    python3 pipeline/fix_alfabank_flocktory_target_profile.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g113002a7'
BAD_PROFILE_ID = 'gd5d02d09'
BAD_PROFILE_NAME = 'КИВИ'
NEW_PROFILE_ID = 'g113002a7-target'
NEW_PROFILE_NAME = 'ООО «Флоктори» (Flocktory)'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']
    match_keys = data['match_keys']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == BAD_PROFILE_ID, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, BAD_PROFILE_ID, deal.get('target'))

    bad = companies.get(BAD_PROFILE_ID)
    assert bad is not None, 'нет профиля %s' % BAD_PROFILE_ID
    assert bad.get('name') == BAD_PROFILE_NAME, \
        '%s: имя профиля не совпадает дословно: %r' % (BAD_PROFILE_ID, bad.get('name'))

    # Профиль КИВИ используется в НЕСКОЛЬКИХ других сделках — не удаляем его,
    # только проверяем полный список ссылок перед правкой, чтобы не задеть
    # ничего непредвиденного. g8af20254 — второй, отдельный дефект того же
    # класса (target тоже указывает на КИВИ ошибочно) — чинится отдельным
    # скриптом (fix_zaimer_taxiaggregator_intellectmoney_target.py), не этим.
    refs = sorted(d['id'] for d in data['deals']
                  if BAD_PROFILE_ID in (d.get('target'), d.get('buyer'), d.get('seller_id'), d.get('asset_id')))
    expected_refs = sorted([DEAL_ID, 'g0fadc207', 'g0a6f7569', 'g5d9d8e6c',
                             'g6bccb70f', 'g8af20254'])
    assert refs == expected_refs, \
        'профиль %s используется не там, где ожидалось: %r' % (BAD_PROFILE_ID, refs)

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, BAD_PROFILE_ID, BAD_PROFILE_NAME))
    print('Станет: target=%s (%r)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Профиль %s (КИВИ) не трогается — верно используется в g0fadc207' % BAD_PROFILE_ID)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'E-commerce',
        'desc': 'Платформа маркетинговой автоматизации; исторически входила '
                'в российский периметр Qiwi, в 2026 году её купил Альфа-Банк.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    match_keys[NEW_PROFILE_ID] = ['флоктори', 'flocktory']
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert BAD_PROFILE_ID in companies  # КИВИ остаётся

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
