# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g00421dd1 (Фонд ТилТех Капитал купил 25% сети Poison Drop, 01.10.2023,
статус «Закрыта») — фонд действительно нарастил долю, как и
планировал, а выручка сети выросла в разы, хотя компания остаётся
убыточной.

Проверено лично прямым WebSearch (со ссылкой на rb.ru, 07.06.2024):
«С 5 июня 2024 года АО «Тилтех» принадлежит 27,5% в ООО «Пойзон
Дроп»» — рост с 25%, фонд сам объяснил это «программой по наращиванию
доли»; в 2023 году выручка Poison Drop составила 901,2 млн руб.,
чистая прибыль — 43,8 млн руб.

НЕ ВКЛЮЧЕНО: показатели 2024-2025 годов (выручка ~1,7-1,8 млрд руб.,
но с убытком 134,3 и 153 млн руб. соответственно, отрицательный
капитал) — из агрегатора ЕГРЮЛ (audit-it.ru), не дозаверено отдельным
WebFetch; расширение сети (11 магазинов, суббренд Poisoned Hearts,
выкуп бренда Wanna?Be!) — детали развития, не структурные факты
сделки; другие инвестиции ТилТех Капитал (Divan.ru, Noun, Sonno) —
отдельные, не связанные с Poison Drop сделки фонда, не относятся к
этой карточке.

Запуск: python3 pipeline/fix_tiltech_poison_drop_stake_growth.py
        python3 pipeline/fix_tiltech_poison_drop_stake_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g00421dd1'

OLD_EXTRA = (
    'Инвестиционный фонд ТилТех Капитал, основанный Андреем '
    'Кривенко, Юрием Алашеевым и Андреем Иващенко, приобрел 25% доли '
    'в ООО Пойзон Дроп. По плану фонд планирует увеличить стоимость '
    'компании в 10 раз в течение 3–5 лет и может принять решение о '
    'дополнительных инвестициях по итогам 2023 года.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Дополнительные инвестиции состоялись: с 5 июня 2024 года доля '
    'фонда выросла до 27,5% — сам фонд назвал это «программой по '
    'наращиванию доли». Выручка Poison Drop за 2023 год составила '
    '901,2 млн руб. при чистой прибыли 43,8 млн руб.'
)

NEW_SRC = [
    ['rb.ru', 'https://rb.ru/news/tealtech-capital-poison-drop/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
