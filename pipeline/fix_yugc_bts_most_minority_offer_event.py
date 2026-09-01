# -*- coding: utf-8 -*-
"""ЮГК/«БТС-Мост Холдинг» (`cc16fce80`): почасовой приток 1 сентября 2026
нашёл продолжение сюжета — «БТС-Мост Холдинг» (структура Руслана
Байсарова, купившая контрольный пакет на аукционе Росимущества в июне)
сделала миноритариям ПАО «ЮГК» оферту о выкупе акций по 74,25 копейки за
акцию; совет директоров ЮГК дал НЕЙТРАЛЬНУЮ рекомендацию — не советует ни
принять, ни отклонить оферту, предлагая акционерам самим оценить риски
(1prime.ru, дословно проверено WebFetch). Это новый, самостоятельный факт
(корпоративное действие текущего покупателя, а не старый сюжет с отказом
Росимущества от выкупа, который уже стоит в law.appr) — добавлен НОВОЙ
записью events[], а не через review.py: FIXES не поддерживает добавление
элемента в список events (только скалярные поля и src).

Запуск: python3 pipeline/fix_yugc_bts_most_minority_offer_event.py           # проверка
        python3 pipeline/fix_yugc_bts_most_minority_offer_event.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cc16fce80'
NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-09-01',
    'title': 'Оферта миноритариям получила нейтральную рекомендацию',
    'note': ('АО «БТС-Мост Холдинг» сделало миноритарным акционерам ЮГК оферту '
             'о выкупе акций по 74,25 копейки за акцию. Совет директоров ПАО '
             '«ЮГК» дал нейтральные рекомендации миноритариям по оферте: не '
             'рекомендует ни принять, ни отклонить её, предлагая акционерам '
             'самим оценить риски продажи и учесть, что рыночная стоимость '
             'акций в будущем может измениться; оценить планы покупателя совет '
             'не смог «в связи с отсутствием указания на такие планы».'),
    'source': ['1prime.ru', 'https://1prime.ru/20260901/juzhuralzoloto-872876989.html'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    events = card.get('events') or []
    assert len(events) == 3, 'ожидали 3 события, в базе %d' % len(events)
    already = any(e.get('date') == NEW_EVENT['date'] and 'оферт' in (e.get('note') or '').lower()
                  for e in events)

    print('ДОБАВЛЯЕТСЯ СОБЫТИЕ: %r' % NEW_EVENT['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1
    if not already:
        card['events'].append(NEW_EVENT)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
