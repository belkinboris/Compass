# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g630c3361 (ГК «Медскан»/«Нетрика Медицина»,
статус «Обсуждается»): дельта-поиск ПОДТВЕРДИЛ, что статус не изменился
(интервью члена совета директоров «Медскана» от 30.01.2026 — переговоры о
вхождении «Нетрики» в контур «Медскана» всё ещё идут, см. отдельный
скрипт fix_medskan_netrika_negotiations_context.py), но при этом нашёл
свежую финансовую отчётность предмета сделки за 2025 год: рост выручки
и прибыли, известный карточке по 2024 году, в 2025-м сменился падением —
это может повлиять на восприятие оценки Exectica Capital (2-3 млрд руб.,
6-8 годовых прибылей), которая уже стоит в eco.val и считалась от
прибыли 2024 года. Не через review.py: поле eco.target_fin уже несёт
данные за 2024 год, новые данные — из другого источника (ГИР БО через
vaskov.pro), непрерывного куска текста с уже записанным не образуют.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://vaskov.pro/company/1001185123 — структурированные данные из
ГИР БО (государственный информационный ресурс бухгалтерской отчётности)
по ИНН 1001185123 (ООО «Нетрика Медицина»).

Запуск: python3 pipeline/fix_medskan_netrika_2025_financials.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g630c3361'

OLD_TARGET_FIN = (
    'В 2024 году выручка «Нетрика Медицина» выросла на 76,5% до 1,1 млрд '
    'руб., чистая прибыль составила 407 млн руб.'
)
ADDITION = (
    'По данным ГИР БО, в 2025 году рост сменился падением: выручка '
    'снизилась до 926,4 млн руб., чистая прибыль — до 316,6 млн руб.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"

    print(f"{CARD_ID} eco.target_fin: += финансы предмета за 2025 год "
          f"(рост 2024 года сменился падением)")
    deal['eco']['target_fin'] = NEW_TARGET_FIN

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
