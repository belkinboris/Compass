# -*- coding: utf-8 -*-
"""Второе чтение (пять карточек «Центр Капитал»/указ №738): цитаты в
eco.target_fin/eco.context/law.terms опираются на телеграм-канал
Dealsma и Вести.ru, которых не было в `src` ни у одной из пяти
карточек — находка найдена читателем. Добавляет оба источника всем
пяти; Tarkett (g8a599c40) также получает URA.RU — она упоминает
Tarkett прямо («также оказались акции компании «Таркетт»») и несет
цитату Пескова, которая пойдет в eco.rationale.

Запуск:
    python3 pipeline/fix_centr_kapital_sources_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_centr_kapital_sources_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'

DEALSMA = ['Телеграм-канал Dealsma', 'https://t.me/dealsma/7475']
VESTI = ['Вести.ru', 'https://www.vesti.ru/ns/putin-peredal-vo-vremennoe-upravlenie-aktivy-kompanij-s-vyruchkoj-bolee-rub50-mlrd']
URA = ['URA.RU', 'https://ura.news/news/1053136498']

ADDITIONS = {
    'g8a599c40': [DEALSMA, VESTI, URA],
    'g19410fc2': [DEALSMA, VESTI],
    'gb3837d4d': [DEALSMA, VESTI],
    'gfc3e1ae2': [DEALSMA, VESTI],
    'gf803c055': [DEALSMA, VESTI],
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    for cid, adds in ADDITIONS.items():
        card = cards[cid]
        urls = {s[1] for s in card['src']}
        for a in adds:
            assert a[1] not in urls, '%s: источник уже стоит: %r' % (cid, a)
        print('%s: += %s' % (cid, [a[0] for a in adds]))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_cards = {c['id']: c for c in fresh['cards']}
    for cid, adds in ADDITIONS.items():
        fc = fresh_cards[cid]
        urls = {s[1] for s in fc['src']}
        for a in adds:
            assert a[1] not in urls, '%s: источник поменяли параллельно — перечитайте' % cid
            fc['src'].append(a)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
