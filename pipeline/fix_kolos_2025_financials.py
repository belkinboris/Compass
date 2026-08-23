# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ga218f75c (Акульчев/
кондитерская фабрика «Колос»): дельта-поиск нашёл итоги первого полного
года владения — chelny-biz.ru (27.04.2026) со ссылкой на «Контур Фокус».
Не через review.py: eco.target_fin уже несёт данные 2024 года из ДРУГОГО
источника (РБК Компании), а review.py требует, чтобы итоговое значение
поля лежало дословно в ОДНОЙ цитате — здесь источники два.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
chelny-biz.ru (27.04.2026), со ссылкой на систему «Контур Фокус».
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga218f75c'
OLD_TARGET_FIN = (
    'За 2024 год прибыль компании составляет — 26 346 000 ₽, выручка за '
    '2024 год — 684 516 000 ₽.'
)
ADDITION = (
    'Приобретенная компанией «Акульчев» челябинская кондитерская фабрика '
    '«Колос» по итогам 2025 года показала чистый убыток в 175,7 млн '
    'рублей. При этом сумма оказалась в шесть раз выше, чем годом ранее, '
    'а выручка сократилась на 42% – до 393,5 млн рублей. Такие данные '
    'указаны в системе «Контур Фокус».'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"

    print(f"{CARD_ID} eco.target_fin: += финансовые итоги 2025 года (chelny-biz.ru)")
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
