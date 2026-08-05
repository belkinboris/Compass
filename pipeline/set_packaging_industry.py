# -*- coding: utf-8 -*-
"""Отдельная отрасль «Производство тары»: собрать в неё то, что было разбросано.

ЗАЧЕМ. До 5 августа упаковки как отрасли у нас не было, и 14 карточек про неё
лежали в четырёх разных: «Химия и удобрения» 6, «Пищепром и напитки» 4,
«Потребительские товары» 2, «Фармацевтика» 1. Это не небрежность разметчика, а
признак того, что в списке отраслей не хватало категории: одна и та же сделка
про завод упаковки попадала то в химию (материал), то в пищепром (что в неё
кладут), то в потребительские товары (кто в итоге покупает). Решение владельца
— завести «Производство тары».

ПОЧЕМУ ЭТО ОПРАВДАНО РАЗМЕРОМ. 12 карточек ставят новую отрасль вровень с
«Углём» (15) и «Финтехом» (9) и крупнее десяти уже существующих —
«Профессиональных услуг» (1), «Образования» (1), «Холдингов» (2), «Лесопрома»
(4), «Искусственного интеллекта» (6). Заводить отрасль ради двух записей было
бы дроблением, ради двенадцати — нет.

ГРАНИЦА, И ОНА НЕ ФОРМАЛЬНАЯ. В новую отрасль идёт тот, кто производит САМУ
упаковку: короб, банку, плёнку, преформу, мешок. Сырьё и материалы ДЛЯ упаковки
остаются химией — у Flint Group предметом сделки были лакокрасочные материалы,
а не тара; переработка отходов упаковки обратно в сырьё тоже остаётся
(«Технониколь» дробит ПЭТ-бутылки в хлопья). Обе эти карточки перечислены ниже
поимённо с причиной, чтобы следующий прогон не «дочистил» их заодно.

Запуск:
    python3 pipeline/set_packaging_industry.py            # сухой прогон
    python3 pipeline/set_packaging_industry.py --write    # записать
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')

NEW = 'Производство тары'

# id -> (кусок заголовка для сверки, отрасль, которая там стоит сейчас)
MOVE = {
    'g3c46e216':    ('Mondi продала три завода',          'Пищепром и напитки'),
    'g22b470f6':    ('Segezha Packaging',                 'Пищепром и напитки'),
    'tokk-metarus': ('ТОКК приобрёл имущественный',       'Пищепром и напитки'),
    'c1659a21f':    ('Tetra Pak передаёт',                'Пищепром и напитки'),
    'gb68699cf':    ('Amcor продал три завода',           'Потребительские товары'),
    'cb7eb501d':    ('Свеза» покупает упаковочные',       'Потребительские товары'),
    'g53bd1536':    ('Центр фармацевтической упаковки',   'Фармацевтика'),
    'g9c4b80a7':    ('CanPack',                           'Химия и удобрения'),
    'g57b3b93c':    ('MM Packaging',                      'Химия и удобрения'),
    'g766a4daf':    ('производство тары для агрохимии',   'Химия и удобрения'),
    'gbf6f6432':    ('продал производство упаковки',      'Химия и удобрения'),
    # Спорный, и решение записано: БОПП-плёнка — это гибкая упаковка, то есть
    # готовое упаковочное изделие, а не полимерное сырьё вроде гранул.
    'g2369d101':    ('БОПП-пленки Manucor',               'Химия и удобрения'),
}

# Карточки, которые ПОХОЖИ на упаковку и намеренно оставлены в химии.
KEEP = {
    'g97a4c417': 'переработка отходов ПЭТ и ПНД-упаковки в хлопья — это сырьё, а не тара',
    'g0df6c7c4': 'предмет сделки — лакокрасочные материалы ДЛЯ упаковки, а не сама упаковка',
}


def industries():
    html = open(INDEX, encoding='utf-8').read()
    raw = re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
    return [x.strip().strip('"') for x in raw.split(',') if x.strip()]


def main(write=False):
    inds = industries()
    if NEW not in inds:
        print('Отрасли «%s» нет в INDUSTRIES в static/index.html — сначала туда.' % NEW)
        return 1
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}

    plan, refused = [], []
    for deal_id, (title_part, was) in MOVE.items():
        card = cards.get(deal_id)
        if not card:
            refused.append((deal_id, 'карточки нет в базе'))
        elif card.get('ind') == NEW:
            continue                                   # уже перенесена
        elif title_part.lower() not in str(card.get('title') or '').lower():
            refused.append((deal_id, 'заголовок не совпадает: %r' % str(card.get('title'))[:56]))
        elif card.get('ind') != was:
            refused.append((deal_id, 'отрасль уже другая: %r, ожидали %r' % (card.get('ind'), was)))
        else:
            plan.append((card, was))

    print('Переносим в «%s»: %d из %d' % (NEW, len(plan), len(MOVE)))
    for card, was in plan:
        print('  %-12s %-24s -> %-20s %s'
              % (card['id'], was, NEW, str(card.get('title'))[:52]))
    print('Оставляем в химии намеренно: %d' % len(KEEP))
    for deal_id, why in KEEP.items():
        card = cards.get(deal_id)
        print('  %-12s %s' % (deal_id, why))
        if card and card.get('ind') == NEW:
            refused.append((deal_id, 'карточка уже помечена как тара, хотя должна остаться'))
    for deal_id, why in refused:
        print('  ОТКАЗ %-12s %s' % (deal_id, why))

    if refused:
        print('\nЕсть отказы — не пишем ничего: список надо починить целиком.')
        return 1
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    if not plan:
        print('\nПереносить нечего.')
        return 0
    for card, was in plan:
        assert card['ind'] == was, 'состояние поля изменилось'
        card['ind'] = NEW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО: %d карточек' % len(plan))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
