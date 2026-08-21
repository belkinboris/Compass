#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки МТС Банк/«РНКБ Страхование» ссылался на профиль совсем
другой компании — «РНКБ Банк».

ЧТО СЛОМАНО. Карточка `ge848daa0` («МТС-банк приобрел страховую компанию
АО «РНКБ Страхование»») хранит `target: "g37bf4386"`, а профиль
`g37bf4386` называется «РНКБ Банк» — крымский банк, чьи 100% акций уже
переданы Росимуществом в уставный капитал ВТБ (по описанию самого
профиля). Вся карточка (заголовок, `eco.share`, `extra`, `eco.target_fin`,
`eco.context`) — про страховую «дочку» «РНКБ Страхование», не про сам
банк; более того, банк и страховая компания даже не в одной группе на
момент сделки (страховая компания — отдельное юрлицо с лицензиями,
покупаемое отдельно от банка). Найдено 21 августа при заполнении G8
(PRODUCT_ROADMAP.md) — шестой случай этого класса дефекта за сессию
(после Flocktory/КИВИ, Таксиагрегатор/КИВИ, Спецзастройщик/Банк
«Санкт-Петербург») — приём тот же, что уже применялся для ЛСР/Domina
Пулково.

ПОЧЕМУ ПРОФИЛЬ РНКБ БАНК НЕ ТРОГАЕТСЯ. Верно используется в другой
сделке (`gbada7ff0`) — не удаляется и не переименовывается.

Запуск:
    python3 pipeline/fix_mtsbank_rnkb_strahovanie_target_profile.py            # сухой прогон
    python3 pipeline/fix_mtsbank_rnkb_strahovanie_target_profile.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'ge848daa0'
BAD_PROFILE_ID = 'g37bf4386'
BAD_PROFILE_NAME = 'РНКБ Банк'
NEW_PROFILE_ID = 'ge848daa0-target'
NEW_PROFILE_NAME = 'АО «РНКБ Страхование»'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == BAD_PROFILE_ID, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, BAD_PROFILE_ID, deal.get('target'))

    bad = companies.get(BAD_PROFILE_ID)
    assert bad is not None, 'нет профиля %s' % BAD_PROFILE_ID
    assert bad.get('name') == BAD_PROFILE_NAME, \
        '%s: имя профиля не совпадает дословно: %r' % (BAD_PROFILE_ID, bad.get('name'))

    refs = sorted(d['id'] for d in data['deals']
                  if BAD_PROFILE_ID in (d.get('target'), d.get('buyer'), d.get('seller_id'), d.get('asset_id')))
    expected_refs = sorted([DEAL_ID, 'gbada7ff0'])
    assert refs == expected_refs, \
        'профиль %s используется не там, где ожидалось: %r' % (BAD_PROFILE_ID, refs)

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, BAD_PROFILE_ID, BAD_PROFILE_NAME))
    print('Станет: target=%s (%r)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Профиль %s (РНКБ Банк) не трогается — верно используется в другой сделке' % BAD_PROFILE_ID)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'Страхование',
        'desc': 'Небольшая страховая компания с лицензиями на добровольное '
                'личное и имущественное страхование; в 2025 году её купил '
                'МТС Банк ради лицензий и ИТ-инфраструктуры.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert BAD_PROFILE_ID in companies  # РНКБ Банк остаётся

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
