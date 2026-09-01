# -*- coding: utf-8 -*-
"""Сбербанк/Summit Towers (`g0ff8c5c4`): третий черновик притока того же
дня (Frank Media) добавил факт, которого не было в двух уже привязанных
источниках, — план Сбербанка открыть 10 новых филиалов в Индии
(заявление зампреда Анатолия Попова в июне 2026 года). Дополнение к уже
занятому полю `eco.context` — не через review.py (цитата покрывает
только новое предложение, а не старое+новое целиком).

ВТОРАЯ ПОПЫТКА этого дополнения за тот же час: первая версия скрипта
писала в `static/data/pending.json`, но рутина публикации сняла
карточку из pending.json снимком, сделанным РАНЬШЕ, чем та правка
успела примениться, — карточка уже была в `deals_promoted.json`, а
дополнение осталось только в снятой версии pending.json и пропало.
Эта версия пишет прямо в базу, куда карточка уже переехала.

Запуск: python3 pipeline/fix_sberbank_summit_towers_branches_plan.py           # проверка
        python3 pipeline/fix_sberbank_summit_towers_branches_plan.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g0ff8c5c4'
OLD_CONTEXT = (
    'Башни будут готовы к 2028 году, и там банк создаст центр '
    'российско-индийского сотрудничества, взаимодействия и торговли. '
    '«Он находится прямо с Мировым торговым центром — это огромнейший '
    'центр в самом сердце Дели. Поэтому мы тоже рядом, и это пространство '
    'посвящено только России и Индии. Мы ждём всех партнёров, российские '
    'компании, которые, мы надеемся, там также разместятся вместе с нами», '
    '- сказал Ведяхин. Летом о создании Центра российского бизнеса в '
    'Индии говорил зампредправления Сбербанка Анатолий Попов. Он не '
    'озвучивал объем инвестиций, но отмечал, что на площадке идут '
    'строительные работы.'
)
ADDITION = (
    'В июне зампред правления Сбербанка Анатолий Попов заявил, что банк '
    'планирует открыть 10 новых филиалов в Индии в дополнение к двум уже '
    'работающим офисам в Нью-Дели и Мумбаи.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
