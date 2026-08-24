# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gdf51a7ca (Arenadata/«Убик»): дельта-поиск
нашёл дальнейшую судьбу привилегированных акций, которыми в 2024 году
была оплачена часть сделки — они конвертированы в обыкновенные акции
ПАО «Группа Аренадата». Не через review.py: поле eco.context уже несёт
содержание (структура собственников «Убик» до сделки, добавлено ранее),
а новый факт — из другого источника (arenadata.tech, объявление о
конвертации) и не образует с ним непрерывный кусок текста.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://arenadata.tech/about/news/gruppa-arenadata-obyavlyaet-o-konvertaczii-privilegirovannyh-akczij-vypuska-v/
Дата самого объявления в тексте страницы не названа (метаданные не
отдаются) — год выпуска акций (2024) назван в тексте, используется он,
а не гадание про дату публикации.

Запуск: python3 pipeline/fix_arenadata_ubik_preferred_shares_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gdf51a7ca'

OLD_CONTEXT = (
    'на начало текущего года основными владельцами УБИК являлись '
    'комбинированные ЗПИФ «Нафид фонд» (49%), «Атрия - ААА» (24,3%), '
    '«Турмалин инвест» (12,67%) и «Аврора капитал» (7,14%)'
)
CONTEXT_ADDITION = (
    'Привилегированные акции выпуска «В» (8 860 738 акций), выпущенные в '
    '2024 году для оплаты приобретаемых долей «Убик», впоследствии '
    'конвертированы в обыкновенные — по итогам конвертации количество '
    'обыкновенных голосующих акций ПАО «Группа Аренадата» составило '
    '218 021 202 акции.'
)
NEW_CONTEXT = OLD_CONTEXT + '. ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += конвертация привилегированных акций "
          f"выпуска «В» в обыкновенные")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
