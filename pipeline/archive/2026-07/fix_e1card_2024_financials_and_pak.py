# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g6822cbf4 (Антон Пак приобрел процессинговую компанию E1 Card у
Кирилла Бохана) — финансовые показатели цели после сделки не были
отражены, а покупатель с тех пор совершил более крупную сделку тем же
консультантом. Проверено лично прямым WebFetch двух источников.

`eco.target_fin` (дополнено). Дословно (companies.rbc.ru): «Выручка:
81 424 628 000 ₽; Чистая прибыль: 1 785 740 000 ₽» за 2024 год —
рост от уже известных 66,4 млрд ₽/1,2 млрд ₽ за 2023 год.

`eco.context` (дополнено). Антон Пак 14 августа 2025 года купил
ювелирный холдинг Sokolov — с тем же финансовым консультантом
(Aspring Capital), что и в сделке с E1 Card, то есть это постоянный
M&A-консультант структур Пака, а не разовое совпадение.

НЕ ВКЛЮЧЕНО: точная сумма сделки Sokolov (30-40 млрд ₽) — это оценка
для ДРУГОЙ сделки, не относится к карточке E1 Card, не переносится
сюда даже контекстом ради полноты. Судьба Кирилла Бохана после продажи
— не найдена ни в одном источнике. Юридические консультанты сделки —
не упоминаются нигде. Развитие продукта E1 Card (сеть АЗС, оплата
навигационных пломб) — единственный источник собственный блог
компании, независимой статьи не нашлось, дословность не подтверждена
второй стороной.

Запуск: python3 pipeline/fix_e1card_2024_financials_and_pak.py
        python3 pipeline/fix_e1card_2024_financials_and_pak.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g6822cbf4'

OLD_TARGET_FIN = (
    'Выручка «Онлайн Кардс» по итогам 2023 года выросла на 48,5%, до '
    '66,4 млрд руб., чистая прибыль — в 2,6 раза, до 1,2 млрд руб.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + (
    ' По итогам 2024 года выручка составила 81,4 млрд руб., чистая '
    'прибыль — 1,79 млрд руб. (companies.rbc.ru).'
)

OLD_CONTEXT = (
    'После начала военных действий на Украине E100 сообщила о '
    'прекращении работы в РФ и Белоруссии, а весной 2022 года продала '
    'бизнес в РФ, Белоруссии и Казахстане Кириллу Бохану — бывшему '
    'главе направления продаж E100 в восточном регионе.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' 14 августа 2025 года Антон Пак купил ювелирный холдинг Sokolov — '
    'финансовым консультантом сделки снова выступила Aspring Capital, '
    'уже работавшая с Паком на сделке с E1 Card.'
)

NEW_SRC = [
    ['РБК Компании', 'https://companies.rbc.ru/id/1146733011105-ooo-e100-onlajn/'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7959262'],
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
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
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
