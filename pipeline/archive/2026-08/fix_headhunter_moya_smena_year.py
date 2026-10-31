# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
ga6924cc4 (HeadHunter инвестировал в «Моя смена», получив 26% доли) —
ОДИННАДЦАТЫЙ подряд год-дефект в этой рутине: единственный источник
карточки сам датирован 2025-м, а не 2024-м. Проверено лично прямым
WebFetch.

Год сделки (2024 → 2025) — НЕ через `review.py` (смена года — отдельный
скрипт). Дословно (Ведомости, 09.10.2025, 20:23): «В рамках сделки
HeadHunter приобрел 26%-ную долю в сервисе, который принадлежит ГК
Verme» — та же дата уже стояла в самом URL источника, но карточка
несла год «2024».

`eco.context` (дополнено). Та же цитата называет продавца — «Моя
смена» принадлежит ГК Verme — факт, отсутствовавший в карточке
(продавец не был назван вовсе).

НЕ ВКЛЮЧЕНО: точная сумма сделки — не раскрывалась ни в одном
источнике; юридические консультанты — не найдены.

Запуск: python3 pipeline/fix_headhunter_moya_smena_year.py
        python3 pipeline/fix_headhunter_moya_smena_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga6924cc4'

OLD_DATE = '2024'
NEW_DATE = '2025'

OLD_CONTEXT = (
    'Сегодня в нее входят модульная HR-система для автоматизации найма '
    'и развития талантов Skillaz, облачная система управления '
    'взаимоотношениями с клиентами (CRM) для рекрутинга Talantix, '
    'платформа кадрового электронного документооборота (КЭДО) HRlink, '
    'а также сайт отзывов сотрудников Dream Job.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Продавец: «Моя смена» принадлежит ГК Verme (Ведомости, 9 октября '
    '2025).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_CONTEXT

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
