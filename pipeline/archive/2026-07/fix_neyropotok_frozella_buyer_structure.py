# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `g5647e100`
(«"Нейропоток" выкупил производство хлебобулочной продукции под
брендом Frozella», июль 2026) уже несла оценку суммы, финансы предмета
и мнение аналитика о природе сделки, но не называла СТРУКТУРУ самого
покупателя.

Личный WebFetch подтвердил дословно (Коммерсантъ,
https://www.kommersant.ru/doc/8862608): «Собственник АО «Нейропоток» в
СПАРК не указан. Компания зарегистрирована в августе 2025 года,
гендиректором является Сергей Жданов, владеющий также Новой
инвестиционной группой».

Согласование ФАС по сделке ни в одном из проверенных источников не
упоминается — это честная пустота, не заполняется.

Запуск:
    python3 pipeline/fix_neyropotok_frozella_buyer_structure.py            # сухой прогон
    python3 pipeline/fix_neyropotok_frozella_buyer_structure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_LAW_STRUCT = (
    'Собственник АО «Нейропоток» в СПАРК не указан. Компания '
    'зарегистрирована в августе 2025 года, гендиректором является '
    'Сергей Жданов, владеющий также Новой инвестиционной группой.'
)

NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8862608']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g5647e100']

    assert d.get('law', {}).get('struct') in (None, '—'), 'law.struct уже занят: %r' % (d.get('law', {}).get('struct'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g5647e100: law.struct заполнен (структура покупателя, связь с '
          'Новой инвестиционной группой); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d.setdefault('law', {})['struct'] = NEW_LAW_STRUCT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
