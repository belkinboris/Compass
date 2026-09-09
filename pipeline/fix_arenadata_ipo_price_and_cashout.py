# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g3acbe2ec»
(«IPO "Группа Аренадата" на Московской бирже», добавлена в базу
3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл важный структурный
факт, которого не было в карточке: это IPO — cash-out, а не cash-in.
Личный WebFetch (interfax.ru/business/984558, 1 октября 2024) подтвердил
дословно: цена размещения — «95 рублей за акцию» (верхняя граница
диапазона 85–95 ₽, уже известного); «Общий размер IPO с учетом
стабилизационного пакета — 2,7 млрд рублей»; «В рамках размещения
действующие владельцы компании продают 28 млн акций… сама компания
средств не привлекает»; «По итогам IPO… free-float составит 14%
капитала». Добавлено в `eco.val` (цена и объём) и `eco.share` (природа
размещения — продажа акций действующими акционерами, не привлечение
капитала компанией).

Организатор/андеррайтер размещения по-прежнему нигде не назван —
карточка права, что оставляет его как есть.

Запуск:
    python3 pipeline/fix_arenadata_ipo_price_and_cashout.py            # сухой прогон
    python3 pipeline/fix_arenadata_ipo_price_and_cashout.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_VAL = (
    'Ценовой интервал первичного публичного предложения — от 85 до 95 ₽ '
    'за одну акцию, что соответствует оценке компании в 17–19 млрд ₽.'
)
NEW_ECO_VAL = OLD_ECO_VAL + (
    ' Итоговая цена размещения установлена по верхней границе диапазона '
    '— 95 ₽ за акцию; общий размер IPO с учётом стабилизационного пакета '
    '— 2,7 млрд ₽.'
)

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'В рамках размещения действующие владельцы компании продали 28 млн '
    'акций — сама компания средств не привлекала. По итогам IPO и до '
    'завершения стабилизационного периода free-float составил 14% '
    'капитала.'
)

NEW_SRC = ['Интерфакс', 'https://www.interfax.ru/business/984558']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g3acbe2ec']

    assert d['eco']['val'] == OLD_ECO_VAL, \
        'g3acbe2ec eco.val уже другой: %r' % (d['eco']['val'],)
    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'g3acbe2ec eco.share уже другой: %r' % (d['eco']['share'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g3acbe2ec: eco.val дополнен (итоговая цена, объём IPO); '
          'eco.share заполнен (cash-out, free-float 14%); добавлен '
          'источник interfax.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['val'] = NEW_ECO_VAL
    d['eco']['share'] = NEW_ECO_SHARE
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
