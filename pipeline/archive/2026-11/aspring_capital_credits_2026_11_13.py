"""Aspring Capital — финансовый консультант в двух сделках базы (13 ноября 2026).

Владелец: «Проверь сайт advance capital, там сильно больше чем 5 сделок».
На aspring.capital/services с 2022 года шесть сделок M&A; две из них были в
базе без фирмы. Роль и сторона — со страницы «Сделки» и из пресс-релиза фирмы.
Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PR = 'https://aspring.capital/services'
ROWS = {
    'g94683ed2': ('продавца («Рив Гош»)', 0),
    'g64a94e27': ('продавца (VEON)', 0),
}
EMPTY = ('Не раскрывались', 'Не раскрывался', '—', '')


def main(write):
    base = json.load(open(BASE, encoding='utf-8'))      # читается прямо перед записью
    deals = {d['id']: d for d in base['deals']}
    for did, (side, n) in ROWS.items():
        d = deals[did]
        adv = d.setdefault('law', {}).get('adv') or []
        assert not any('aspring' in json.dumps(r, ensure_ascii=False).lower() for r in adv), did
        adv = [r for r in adv if not (len(r) > 1 and str(r[1]).strip() in EMPTY)]
        adv.append(['Финансовый консультант ' + side, 'Aspring Capital',
                    'Финансовый консультант в сделке, по сообщению самой фирмы. Источник: ' + PR])
        d['law']['adv'] = adv
        print(did, d['title'][:60], '→', adv[-1][0])
    if write:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: %d карточек.' % len(ROWS))


if __name__ == '__main__':
    main('--write' in sys.argv)
