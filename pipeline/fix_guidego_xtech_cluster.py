# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ge1c0be95` («Ростелеком приобрёл 28% агрегатора экскурсий GuideGo»,
закрыта 28.12.2023) — судьба компании после сделки не прослежена.

Саб-агент проверил структуру сделки, согласование ФАС, консультантов и
дальнейший рост бизнеса по ~15 запросам и почти ничего не нашёл сверх
уже известного (обе стороны честно молчат о деталях, TAdviser
недоступен из этой сети — известное ограничение, см. CLAUDE.md).

Единственный новый факт, проверенный ЛИЧНО прямым WebFetch,
https://company.rt.ru/projects/startups/xTech/ (страница цифрового
кластера «X.Технологии» «Ростелекома»): «GuideGo... Система
индивидуального экскурсионного обслуживания... https://guidego.ru/» —
GuideGo числится портфельным проектом кластера в категории Travel.Tech
по состоянию на сентябрь 2026 года.

НЕ ВКЛЮЧЕНО: рост числа экскурсий/гидов в 2025 году (TAdviser) —
источник недоступен из этой сети, дословно не подтверждён; структура
сделки, согласование ФАС, консультанты — саб-агент не нашёл ничего
проверяемого ни по одному из этих пунктов.

Запуск: python3 pipeline/fix_guidego_xtech_cluster.py
        python3 pipeline/fix_guidego_xtech_cluster.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge1c0be95'

OLD_ECO_CONTEXT = 'До сделки 85% компании принадлежало Степану Винограденко, 15% — Жанату Бурабаеву.'
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По состоянию на сентябрь 2026 года GuideGo '
    'числится портфельным проектом цифрового кластера стартапов '
    '«Ростелекома» «X.Технологии» (категория Travel.Tech).'
)

NEW_SRC = [
    ['Ростелеком', 'https://company.rt.ru/projects/startups/xTech/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
