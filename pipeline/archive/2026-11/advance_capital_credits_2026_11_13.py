"""Advance Capital — финансовый консультант в десяти сделках базы (13 ноября 2026).

Владелец: «Проверь сайт advance capital, там сильно больше чем 5 сделок».
На advancecapital.ru/sdelki/ с 2022 года 28 сделок; десять из них уже были в
базе без фирмы. Роль и сторона — со страницы «Сделки» и из пресс-релиза фирмы.
Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PR = 'https://advancecapital.ru/news/news/press-releases/%d/'
ROWS = {
    'gf6c084b9': ('продавцов (основатели Swordfish Security)', 473),
    'gc65bacdf': ('покупателей (Алексей Дорофеев и Константин Леонович)', 471),
    'g7c2329a4': ('продавца («Русхим»)', 468),
    'gb0f1f736': ('компании (WhoIsBlogger)', 454),
    'gd3769bb9': ('продавца (акционеры Е-ПРОМ)', 433),
    'g165039a0': ('продавца («Академ-Онлайн»)', 431),
    'g300d56ed': ('продавца (сеть «Молния»)', 429),
    'g46c6e23f': ('продавца (Boxberry)', 427),
    'g399c1f98': ('продавца (Vinteo)', 422),
    'g5013525f': ('продавца («Парус электро»)', 421),
}
EMPTY = ('Не раскрывались', 'Не раскрывался', '—', '')


def main(write):
    base = json.load(open(BASE, encoding='utf-8'))      # читается прямо перед записью
    deals = {d['id']: d for d in base['deals']}
    for did, (side, n) in ROWS.items():
        d = deals[did]
        adv = d.setdefault('law', {}).get('adv') or []
        assert not any('advance' in json.dumps(r, ensure_ascii=False).lower() for r in adv), did
        adv = [r for r in adv if not (len(r) > 1 and str(r[1]).strip() in EMPTY)]
        adv.append(['Финансовый консультант ' + side, 'Advance Capital',
                    'Финансовый консультант в сделке, по сообщению самой фирмы. Источник: ' + PR % n])
        d['law']['adv'] = adv
        print(did, d['title'][:60], '→', adv[-1][0])
    if write:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: %d карточек.' % len(ROWS))


if __name__ == '__main__':
    main('--write' in sys.argv)
