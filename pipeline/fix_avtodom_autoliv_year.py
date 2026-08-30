# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g60c0956e («Автодом» приобрел завод автокомпонентов Autoliv в
Тольятти) — дата сделки стояла годом раньше реальной регистрации в
ЕГРЮЛ. Перенос в другой год сделан отдельным скриптом с `assert`, не
через `review.py` (см. правило CLAUDE.md «review.py не умеет
переносить сделку в другой год»). Проверено лично прямым WebFetch трёх
источников, включая источник, УЖЕ стоящий в `src` карточки.

`date` (исправлена: 2024-02-27 → 2025-02-27). Источник, уже указанный
в карточке (Интерфакс, https://www.interfax.ru/business/1011305),
опубликован 28 февраля 2025 года — на год позже даты, записанной в
карточке. Дословно: «Согласно ЕГРЮЛ, с 27 февраля контроль над 100%
долей ООО "Аутолив" перешел от шведской Autoliv AB к АО "Автодом"» —
статья датирована 2025 годом, и внутри неё «27 февраля» относится к
тому же 2025 году. Независимо подтверждено ПРАЙМ (1prime.ru): «Согласно
ЕГРЮЛ, 100% ООО "Аутолив"... с 27 февраля 2025 года принадлежит АО
"Автодом"». Оба источника согласуются: регистрация в ЕГРЮЛ — 27
февраля 2025 года, а не 2024-го.

`eco.context` (дополнено). Причина, по которой закрытие сделки заняло
больше года после анонса: дословно (fomag.ru): «Процесс продажи занял
больше времени, чем ожидалось, в связи с необходимостью получения
необходимых разрешений».

НЕ ВКЛЮЧЕНО: финансовые показатели цели за 2023-2025 годы — найдены
только через WebSearch-агрегированную выжимку (rusprofile/spark), а
прямой WebFetch rbc.ru и checko.ru дал 403 — без дословной цитаты из
первоисточника не переносятся. Возобновление производства, новые
заказчики (АвтоВАЗ/Москвич), переименование завода — ни один
источник не подтверждает. Консультанты сделки — не найдены.

Запуск: python3 pipeline/fix_avtodom_autoliv_year.py
        python3 pipeline/fix_avtodom_autoliv_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g60c0956e'

OLD_DATE = '2024-02-27'
NEW_DATE = '2025-02-27'

OLD_CONTEXT = (
    'Группа «Автодом» ранее получила контроль над активами '
    'Mercedes-Benz, включая автомобильный завод в Подмосковье.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Процесс продажи занял больше времени, чем ожидалось, в связи с '
    'необходимостью получения необходимых разрешений (fomag.ru).'
)

NEW_SRC = [
    ['ПРАЙМ', 'https://1prime.ru/20250228/autoliv-855362126.html'],
    ['Fomag.ru', 'https://fomag.ru/news-streem/shvedskaya_autoliv_prodala_rossiyskiy_biznes_gruppe_avtodom/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE, deal['date']
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== date: было / станет ===')
    print(OLD_DATE, '->', NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
