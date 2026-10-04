#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Качество, 4 октября 2026 — очередь находок аудита адреса фактов
(`audit_queue.py --queue`), находки `43754fbe5225`/`22f12b0164a0` на
карточке `gd3556cc0» («Промресурс» купил у «Распадской» 81,3% «УК
Межегейуголь» в Туве»): предмет сделки назван и в заголовке, и в
`eco.share`, но ни `asset_id`/`target`, ни профиля компании у него не
было — единственный из трёх участников сделки без привязки (у buyer и
seller профили уже есть). Поле `asset` (текст) заполнено раньше тем же
прогоном через `review.py`; этот скрипт создаёт профиль компании-предмета
и связывает его с `target`.

Запуск:
    python3 pipeline/fix_mezhegeyugol_target_profile_2026_10_04.py            # сухой прогон
    python3 pipeline/fix_mezhegeyugol_target_profile_2026_10_04.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'gd3556cc0'
NEW_PROFILE_ID = 'gd3556cc0-target'
NEW_PROFILE_NAME = 'ООО «УК Межегейуголь»'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') is None, \
        '%s: target уже не пуст (%r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, deal.get('target'))
    assert deal.get('asset') == '81,2769% доли в «УК Межегейуголь»', \
        '%s: asset стоит иначе (%r), чем ожидалось' % (DEAL_ID, deal.get('asset'))

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=None' % DEAL_ID)
    print('Станет: target=%s (%r)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'Уголь',
        'desc': 'Угольная компания в Туве, бывший актив «Распадской» '
                '(структура Evraz). Разрабатывает Межегейское месторождение '
                'мощностью 1 млн т коксующегося угля марки Ж в год, запасы '
                'по JORC — 86 млн т. С 3 сентября 2026 года 81,2769% долей '
                'принадлежат новосибирскому ООО «Промресурс».',
        'kpi': ['Профиль', 'Автоматический'],
    }
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
