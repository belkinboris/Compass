# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g248d3c20 (Альфастрахование
приобретает сеть клиник «МК Семейный доктор», декабрь 2024): дельта-поиск
нашёл, что после смены владельца стагнация сменилась убытком — по итогам
2025 года выручка составила 546,3 млн ₽ (снижение примерно на 20%),
убыток — 125,3 млн ₽ (РБК Компании, живой реестр). Гендиректором с
декабря 2024 года вместо Александра Шлычкова стал Норайр Колоян
(«Медицина Альфастрахования» — единственный учредитель). Ребрендинг в
«Альфа-Центр Здоровья», о котором писали как о плане в декабре 2024,
частично реализован — клиника на 1-й Миусской улице уже работает под
новым брендом (сайт alfazdrav.ru), хотя точная дата смены неизвестна. Не
через review.py: цифры из НОВОГО источника (живой реестр РБК Компании) в
поле, уже содержащем текст за 2023 год.

Запуск: python3 pipeline/fix_semeyny_doktor_2025_loss_rebrand_context.py
        python3 pipeline/fix_semeyny_doktor_2025_loss_rebrand_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g248d3c20'

OLD_TARGET_FIN = (
    'Выручка в 2023 г. составила 691 млн руб. (-5% год к году) при '
    'близкой к нулевой рентабельности по отчетности. В целом, компания '
    'показывает стагнацию финансовых показателей с 2020 г.'
)
TARGET_FIN_ADDITION = (
    ' После смены владельца стагнация сменилась убытком: по итогам 2025 '
    'года выручка составила 546,3 млн ₽ (снижение примерно на 20%), '
    'чистый убыток — 125,3 млн ₽ (данные живого реестра РБК Компании).'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + TARGET_FIN_ADDITION

OLD_CONTEXT = (
    'До этого владельцами «Семейного доктора» были Александр Шлычков '
    '(32,9%), Андрей Дегтярев (28%), Алексей Ветров (23,5%), Игорь '
    'Жминько (15,6%).'
)
CONTEXT_ADDITION = (
    ' С декабря 2024 года гендиректором вместо Шлычкова стал Норайр '
    'Колоян (единственный учредитель — ООО «Медицина Альфастрахования»). '
    'Заявленный план интеграции в сеть «Альфа-Центр Здоровья» частично '
    'реализован: клиника на 1-й Миусской улице уже работает под новым '
    'брендом, хотя точная дата ребрендинга неизвестна.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['РБК Компании', 'https://companies.rbc.ru/id/1027700420076-ooo-obschestvo-s-ogranichennoj-otvetstvennostyu-meditsinskaya-klinika-semejnyij-doktor/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
