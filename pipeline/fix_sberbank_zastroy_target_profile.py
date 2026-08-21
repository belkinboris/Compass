#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки Сбербанк/девелопер «Южный» ссылался на профиль совсем
другой компании — «Банк «Санкт-Петербург»».

ЧТО СЛОМАНО. Карточка `g52b8df38` («Сбербанк инвестиции приобрел 20% в
девелопере проекта «Южный» в Санкт-Петербурге») хранит
`target: "gf881a88f"`, а профиль `gf881a88f` называется «Банк
«Санкт-Петербург»» — совершенно не связанный с недвижимостью
региональный банк. Вся карточка (заголовок, `extra`, `eco.context`,
`eco.rationale`) говорит про застройщика проекта «Город-спутник Южный»
(«ООО «Спецзастройщик»», он же «ООО «"ЗаСтрой" Спецзастройщик»»), а не
про банк. Найдено 21 августа при заполнении G8 (PRODUCT_ROADMAP.md) —
пятый по счёту случай этого класса дефекта за сессию (после Flocktory/
КИВИ, Таксиагрегатор/КИВИ, РНКБ Страхование/РНКБ Банк) — см. журнал,
приём тот же, что уже применялся для ЛСР/Domina Пулково.

ПОЧЕМУ ПРОФИЛЬ БАНКА «САНКТ-ПЕТЕРБУРГ» НЕ ТРОГАЕТСЯ. Используется в трёх
других, корректных сделках — не удаляется и не переименовывается.

Запуск:
    python3 pipeline/fix_sberbank_zastroy_target_profile.py            # сухой прогон
    python3 pipeline/fix_sberbank_zastroy_target_profile.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g52b8df38'
BAD_PROFILE_ID = 'gf881a88f'
BAD_PROFILE_NAME = 'Банк «Санкт-Петербург»'
NEW_PROFILE_ID = 'g52b8df38-target'
NEW_PROFILE_NAME = 'ООО «"ЗаСтрой" Спецзастройщик» (проект «Город-спутник Южный»)'


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
    expected_refs = sorted([DEAL_ID, 'g499ed10e', 'g9da487d4', 'ga06c75e2'])
    assert refs == expected_refs, \
        'профиль %s используется не там, где ожидалось: %r' % (BAD_PROFILE_ID, refs)

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, BAD_PROFILE_ID, BAD_PROFILE_NAME))
    print('Станет: target=%s (%r)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Профиль %s (Банк «Санкт-Петербург») не трогается — верно используется в других сделках' % BAD_PROFILE_ID)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'Недвижимость',
        'desc': 'Специальный застройщик первого этапа проекта «Город-спутник '
                'Южный» под Санкт-Петербургом (девелопер Start Development); '
                '20% акций в 2024 году приобрёл Сбербанк.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert BAD_PROFILE_ID in companies  # банк остаётся

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
