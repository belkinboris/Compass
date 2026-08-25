# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gb3211ae8 (IPO Группы «ВИС» на
Московской бирже): дельта-поиск нашёл, что IPO, которое источник в
базе описывал как возможное «до конца 2025 года», перенесено на 2026
год — сам гендиректор группы подтвердил это 15 декабря 2025 года,
новость независимо разошлась минимум по пяти изданиям (TASS, Финам,
Cbonds, Fomag, Smart-lab). Дата карточки (год объявления, 2025)
намеренно не менялась: перенос — отдельное более позднее событие, а не
исправление исходной даты.

Не через `review.py`: новый источник (Smart-lab) не образует с уже
записанным текстом `eco.context` непрерывный кусок.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена):
https://smart-lab.ru/blog/news/1242966.php

Запуск: python3 pipeline/fix_vis_ipo_postponed_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb3211ae8'

OLD_CONTEXT = (
    'Группа ВИС планирует войти в первый или второй уровень листинга '
    'Московской биржи, но окончательное решение также пока не принято.'
)
CONTEXT_ADDITION = (
    ' 15 декабря 2025 года генеральный директор компании «ВИС» Сергей '
    'Юдин заявил: «Мы планируем выйти на IPO в 2026 году. [Объем '
    'размещения] будет зависеть от конъюнктуры рынка» — размещение, '
    'которое ранее ожидалось до конца 2025 года, перенесено на 2026-й.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: {OLD_CONTEXT!r} -> IPO перенесено '
          f'на 2026 год')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal.setdefault('src', [])
        entry = ['Smart-lab', 'https://smart-lab.ru/blog/news/1242966.php']
        if entry not in deal['src']:
            deal['src'].append(entry)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
