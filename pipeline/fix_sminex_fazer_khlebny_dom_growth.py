# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g0dea398b` («Sminex приобрел финскую Fazer у производителя хлеба»,
2022, Закрыта) — судьба актива после сделки не прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- audit-it.ru/contragent/1157847198926_ooo-khlebnyy-dom: учредитель
  «ООО БКХ "КОЛОМЕНСКИЙ"» — «с даты 04.05.2022», не менялся с тех пор
  (проверка на дату отчёта); выручка 2025 года «32,7 млрд руб.» (рост
  на 41,1% год к году), прибыль «1,6 млрд руб.» (на 16,6% больше, чем
  в 2024 г.); выручка 2024 года ~23,2 млрд ₽, прибыль ~1,37 млрд ₽
  (рассчитано из разницы и коэффициента, отдельно не процитировано).

НЕ ВНЕСЕНО: (1) точные абсолютные цифры выручки/прибыли 2024 года —
сайт даёт их только через дельту к 2025-му, не прямой цитатой, поэтому
в карточку идёт только подтверждённая пара «выручка/прибыль 2025» и
факт роста; (2) утверждение о замене SAP на 1С и пересмотре
ассортимента — это уже стоит в `extra` карточки с 2022 года, не
трогается; (3) сведения об открытии новых площадок или расширении
производства — не искал специально, не для этого прогона.

Запуск: python3 pipeline/fix_sminex_fazer_khlebny_dom_growth.py
        python3 pipeline/fix_sminex_fazer_khlebny_dom_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0dea398b'

OLD_ECO_CONTEXT = (
    'С учётом этой покупки доля БКХ «Коломенский» на рынке Санкт-Петербурга '
    'составила около 35%, а в Москве — почти 30%, подсчитал генеральный '
    'директор «Infoline-аналитики» Михаил Бурмистров.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По данным ЕГРЮЛ, с 4 мая 2022 года и по настоящее '
    'время единственный учредитель — ООО БКХ «Коломенский», перепродажи не '
    'было. Бизнес продолжает расти: выручка 2025 года — 32,7 млрд ₽ (рост '
    'на 41,1% год к году), прибыль — 1,6 млрд ₽ (на 16,6% больше, чем в '
    '2024 году).'
)

OLD_SRC = [
    ['РБК', 'https://www.rbc.ru/business/30/06/2025/685bc6639a7947f614b98842'],
]
NEW_SRC = OLD_SRC + [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1157847198926_ooo-khlebnyy-dom'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
