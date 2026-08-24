# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g8a86fc9b («VK Tech приобрела CedrusData»):
дата стояла «2025» (год без месяца/дня, единственный источник —
телеграм-агрегатор @dealsma), но независимые источники (официальный
блог VK Tech, CNews, RB.ru, vc.ru) единогласно датируют объявление
26-27 МАРТА 2026 года. `review.py`'s `date_is_supported()` не умеет
переносить сделку в другой год (см. правило в CLAUDE.md) — год меняется
отдельным скриптом со своим assert.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.cnews.ru/news/line/2026-03-26_vk_tech_usilivaet_napravlenie
https://rb.ru/news/vk-tech-kupila-cedrusdata-nezavisimogo-razrabotchika-reshenij-dlya-bolshih-dannyh-i-ii/

Запуск: python3 pipeline/fix_vk_tech_cedrusdata_year.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g8a86fc9b'
OLD_DATE = '2025'
NEW_DATE = '2026-03-26'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['date'] == OLD_DATE, f"date: неожиданное значение {deal['date']!r}"

    print(f'{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r} '
          f'(независимые источники единогласно называют март 2026, а не 2025)')

    if write:
        deal['date'] = NEW_DATE
        deal.setdefault('src', [])
        for entry in (
            ['CNews', 'https://www.cnews.ru/news/line/2026-03-26_vk_tech_usilivaet_napravlenie'],
            ['RB.ru', 'https://rb.ru/news/vk-tech-kupila-cedrusdata-nezavisimogo-razrabotchika-reshenij-dlya-bolshih-dannyh-i-ii/'],
        ):
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
