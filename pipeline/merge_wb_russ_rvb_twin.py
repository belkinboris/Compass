#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`g2a395633` («WB-Russ») и `g549ab474` («ООО «РВБ» (Wildberries & Russ)»)
— один и тот же профиль объединённой компании Wildberries и Russ под двумя
именами (медийный алиас vs юридическое), а не сделка на разных стадиях: обе
даты (июль-ноябрь 2024) лежат внутри уже освоенного диапазона `g549ab474`
(11 сделок, июль 2024 — июль 2026) — в отличие от «Тинькофф»/«Т-Банк»
(g6b8f7488/g9e8a08b8), где смена имени хронологическая и обе записи нужны
для правильной подписи на разных датах, здесь имена не разделены во
времени. Найдено кампанией самопроверки ИНН, Этап 14, П3: попытка
подтвердить ИНН «WB-Russ» дала тот же ИНН 9714053621, что уже подтверждён
для `g549ab474`.

`g2a395633` держит единственную сделку (`gffed92e4`, покупка
«Дизайнмастер») — buyer переставлен на `g549ab474`, профиль-алиас удалён.

Запуск:
    python3 pipeline/merge_wb_russ_rvb_twin.py            # сухой прогон
    python3 pipeline/merge_wb_russ_rvb_twin.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

DEAL_ID = 'gffed92e4'
OLD_PROFILE = 'g2a395633'
NEW_PROFILE = 'g549ab474'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = deals[DEAL_ID]
    assert deal['buyer'] == OLD_PROFILE
    assert OLD_PROFILE in companies
    assert NEW_PROFILE in companies

    REFS = ('buyer', 'seller_id', 'target', 'asset_id')
    other_refs = [d['id'] for d in data['deals']
                  if d['id'] != DEAL_ID and OLD_PROFILE in {d.get(f) for f in REFS}]
    assert not other_refs, 'профиль ещё нужен другой сделке: %s' % other_refs

    print('Проверки прошли. План:')
    print('  %s: buyer %s -> %s' % (DEAL_ID, OLD_PROFILE, NEW_PROFILE))
    print('  удалить осиротевший профиль-алиас %s' % OLD_PROFILE)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    deal['buyer'] = NEW_PROFILE
    del companies[OLD_PROFILE]
    data['match_keys'].pop(OLD_PROFILE, None)

    assert deals[DEAL_ID]['buyer'] == NEW_PROFILE
    assert OLD_PROFILE not in companies
    assert OLD_PROFILE not in data['match_keys']

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
