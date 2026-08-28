# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g08b7a4e1 (МТС приобрела
права на персонажей «Фиксики» у ГК «Рики», октябрь 2024): дельта-поиск
нашёл реальный кейс использования прав ПОСЛЕ сделки — заголовок и `law.terms`
говорили только об анонсированном намерении (маскоты детских цифровых
сервисов на 3 года), а спустя 9 месяцев права уже применены на практике.
Цитата подтверждена лично прямым WebFetch.

Симка (персонаж «Фиксиков») стала маскотом карты «МТС Деньги»: «Маскотом
МТС Деньги станет Симка ‒ умная и активная, готовая всегда прийти на
выручку друзьям», с акцией кешбэка 30% в категории «Развлечения» до
1 сентября 2025 года (riki.team).

Сумму сделки и консультантов дельта-поиск не нашёл ни в одном источнике —
честная пустота, не тронуто. Финансовые показатели ГК «Рики» за 2023 год
(Коммерсантъ) не включены: они датированы АПРЕЛЕМ 2024 года — то есть ДО
сделки (октябрь 2024) и не говорят о ней ни слова, использовать их как
последствие сделки было бы неверной привязкой по времени.

Запуск: python3 pipeline/fix_mts_fiksiki_riki_postdeal_context.py
        python3 pipeline/fix_mts_fiksiki_riki_postdeal_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g08b7a4e1'

OLD_CONTEXT = (
    'Согласно исследованию «МТС Медиа», в 2024 г. потребление детского '
    'контента на контентных сервисах медиахолдинга выросло на 10–50% в '
    'зависимости от типа платформы.'
)
CONTEXT_ADDITION = (
    ' Спустя девять месяцев права уже использовались на практике: '
    '«Маскотом МТС Деньги станет Симка ‒ умная и активная, готовая всегда '
    'прийти на выручку друзьям», а держатели карты получили повышенный '
    'кешбэк 30% в категории «Развлечения» (парки аттракционов, театры, '
    'музеи) сроком до 1 сентября 2025 года (riki.team, 10 июля 2025).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Riki.team', 'https://ru.riki.team/news/fiksiki-rekomenduyut-karta-mts-dengi-s-30-keshbeka-na-razvlecheniya/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
