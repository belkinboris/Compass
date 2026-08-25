# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gd2196acd (Совкомбанк
приобрёл финтех-платформу «Рокет»): дельта-поиск нашёл, что проект
реально перезапущен и работает почти год спустя — приложения вышли в
июле-августе 2025, экспансия в Екатеринбург в июле 2026, названы
руководители (Антон Захаров и Роберт Сабирянов, ранее — Модульбанк и
проект Blanc). Второй независимый источник (e1.ru) называет другую
сумму сделки ($1,5 млн против уже записанной оценки Ъ в $1 млн) — обе
оценки, не факт, добавлены рядом с атрибуцией. Не через review.py:
комбинация фактов из ТРЁХ новых источников (wikipedia, e1.ru, rb.ru) в
разных полях.

Запуск: python3 pipeline/fix_rocket_sovcombank_relaunch_context.py
        python3 pipeline/fix_rocket_sovcombank_relaunch_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd2196acd'

OLD_VAL = (
    'Собеседники «Ъ» оценивают ее сумму в $1 млн, при этом для '
    'перезапуска проекта потребуется 1–3 млрд руб., полагают они.'
)
VAL_ADDITION = (
    ' Издание e1.ru называет другую цифру: Совкомбанк «за 1,5 миллиона '
    'долларов выкупил права на бренд «Рокет» и финтех-платформу купил у '
    'Qiwi» — независимого подтверждения ни одной из двух оценок нет.'
)
NEW_VAL = OLD_VAL + VAL_ADDITION

OLD_CONTEXT = (
    'Совкомбанк завершил приобретение финтех-платформы «Рокет», ранее '
    'принадлежавшей группе Qiwi. До сделки платформа действовала на '
    'основе лицензии Киви-банка, но прекратила работу еще до того, как '
    'банк лишился лицензии. В сделку вошли бренд, команда проекта и, '
    'вероятно, клиентская база, состояние которой требует '
    'восстановления.'
)
CONTEXT_ADDITION = (
    ' Приложение для Android вышло 18 июля 2025 года, для iOS — 5 '
    'августа 2025 года; на старте сервис доступен в Москве, '
    'Санкт-Петербурге и Екатеринбурге, без физических офисов. '
    'Возобновлением занимаются сооснователи Антон Захаров и Роберт '
    'Сабирянов, ранее работавшие в банке «Бланк» и Модульбанке. В июле '
    '2026 года Екатеринбург стал первым нестоличным городом расширения '
    'сети после перезапуска бренда.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['ru.wikipedia.org', 'https://ru.wikipedia.org/wiki/Рокетбанк'],
    ['e1.ru', 'https://www.e1.ru/text/business/2026/07/02/76510041/'],
    ['rb.ru', 'https://rb.ru/stories/faundery-novogo-roketbanka-u-klientov-net-emocionalnoj-svyazi-s-bankami-my-hotim-zadat-novyj-trend/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_VAL
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
