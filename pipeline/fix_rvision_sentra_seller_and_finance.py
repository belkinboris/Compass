# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `gac1a0c11`
(«Совладелец R-Vision купил долю в ИБ-компании Sentra», август 2026) уже
называла структуру покупателя («Основание 2.718» — 50/50 Сметанев и
Авакянц), но не называла ПРОДАВЦА и финансы предмета.

Личный WebFetch/реестровые данные подтвердили дословно
(tbank.ru/business/contractor/legal/1257700056371/, реестр ООО
«Защищённые системы», ИНН 9701307068):
- «30 июля: Авакянц Александр Камоевич выбыл — его доля снизилась с 7% на
  0%», в тот же день появилась доля «Основания 2.718» (6%) — то есть
  прямая доля Авакянца в Sentra обнулилась ровно тогда, когда он стал
  совладельцем покупающей структуры: он и продавец прямой доли, и
  совладелец покупателя одновременно.
- «Выручка: 1,94 млн ₽», «Прибыль: 1,37 млн ₽» (2025 год).

Сумма сделки и согласование ФАС ни в одном источнике не названы — честная
пустота, не заполняется (по масштабу выручки цели согласование ФАС и не
требовалось бы).

Запуск:
    python3 pipeline/fix_rvision_sentra_seller_and_finance.py            # сухой прогон
    python3 pipeline/fix_rvision_sentra_seller_and_finance.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_SELLER = 'Александр Авакянц'

OLD_LAW_STRUCT = (
    'В состав учредителей ООО «Защищённые системы» вошла компания '
    '«Основание 2.718», которая в равных долях принадлежит Сметаневу и '
    'инвестору Александру Авакянцу.'
)

NEW_LAW_STRUCT = OLD_LAW_STRUCT + (
    ' До сделки Авакянц напрямую держал 7% ООО «Защищённые системы»: '
    '30 июля 2026 года эта доля обнулилась одновременно с появлением доли '
    '«Основания 2.718» — Авакянц одновременно продал свою прямую долю и '
    'стал совладельцем структуры-покупателя.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка Sentra («Защищённые системы») за 2025 год — 1,94 млн ₽, '
    'чистая прибыль — 1,37 млн ₽.'
)

NEW_SRC = ['Tbank.ru (реестр)', 'https://www.tbank.ru/business/contractor/legal/1257700056371/']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gac1a0c11']

    assert d.get('seller') is None, 'seller уже занят: %r' % (d.get('seller'),)
    assert d['law'].get('struct') == OLD_LAW_STRUCT, 'law.struct изменился: %r' % (d['law'].get('struct'),)
    assert d['eco'].get('target_fin') == OLD_ECO_TARGET_FIN, 'eco.target_fin уже занят: %r' % (d['eco'].get('target_fin'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('gac1a0c11: seller заполнен (Александр Авакянц); law.struct '
          'дополнен (прямая доля Авакянца обнулилась в день сделки); '
          'eco.target_fin заполнен (выручка/прибыль Sentra 2025); '
          'добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['seller'] = NEW_SELLER
    d['law']['struct'] = NEW_LAW_STRUCT
    d['eco']['target_fin'] = NEW_ECO_TARGET_FIN
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
