# -*- coding: utf-8 -*-
"""Приток 18.09.2026, часовой прогон 12:20 МСК — карточка `gc53a8bd6`
(«Экс-ведущий Top Gear Джереми Кларксон продаст три авто из своей
коллекции», Известия) прошла ворота `promote.py` из-за той же болезни,
что уже трижды чинилась в этом же прогоне для Тодда Бёли/«Челси»:
транслитерированное иностранное имя («Джереми») читалось как доказательство
российского рынка. Источник (Iconic Auctioneers) — британский аукционный
дом, продавец — британский телеведущий, ни одного российского признака в
тексте нет. Корень починен в `promote.py` (NOT_RUSSIAN_PERSON пополнен
«джереми»/«кларксон»), эта карточка снимается тем же приёмом, что и
Chelsea-карточки ранее сегодня.
"""
import json
import sys

DATA_PATH = 'static/data/pending.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    cards = data['cards']
    target = [c for c in cards if c.get('id') == 'gc53a8bd6']
    assert len(target) == 1, target
    card = target[0]
    assert 'Кларксон' in str(card.get('title') or ''), card.get('title')
    assert not card.get('draft_sent'), card

    data['cards'] = [c for c in cards if c.get('id') != 'gc53a8bd6']

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gc53a8bd6 (Кларксон, нероссийская сделка) удалена из pending.json. ЗАПИСАНО.')
    else:
        print('Сухой прогон: удалил бы gc53a8bd6 из pending.json. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
