# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ge848daa0 (МТС-банк
приобрел страховую компанию АО «РНКБ Страхование»): дельта-поиск
подтвердил, что план из карточки реализован по факту — компания
переименована и получила новые лицензии, запуск продаж страхования
не-жизни в 1П 2026 состоялся, как и планировалось. Не через review.py:
цитируемые куски не идут единым непрерывным фрагментом страницы (между
ними — карточка регистрационных данных).

Источник — читал напрямую (fetch_article_texts.py, закэширован):
сайт компании insurance.mts.ru.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge848daa0'
OLD_STRUCT = '—'
NEW_STRUCT = (
    'По данным сайта самой компании: «Декабрь 2025 года: ПАО «МТС-Банк» '
    'завершил сделку по приобретению ООО РНКБ Страхование. Февраль 2026 '
    'года: ООО РНКБ Страхование сменило наименование на ООО «МТС '
    'Страхование»». Компания получила новые лицензии — «Лицензия СЛ № '
    '4380 от 31 марта 2026 г.» и «Лицензия СИ № 4380 от 31 марта 2026 г.» '
    '— и запустила продажи страхования не-жизни (имущества, ипотеки, '
    'покупок, ДМС) под новым брендом, как и планировалось на первое '
    'полугодие 2026 года.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} law.struct: заполнено (переименование и новые лицензии)")
    deal['law']['struct'] = NEW_STRUCT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
