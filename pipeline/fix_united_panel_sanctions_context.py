# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gd1f94881 (United Panel Group/Жешартский
фанерный комбинат): дельта-поиск нашёл отраслевое объяснение кризиса —
производители фанеры пострадали от санкций сильнее других направлений
ЛПК, потеряв основные экспортные рынки. Не через review.py: поле
eco.context уже несёт содержание, новый источник не образует с ним
непрерывный кусок текста.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://mashnews.ru/zheshartskij-lpk-v-respublike-komi-okazalsya-na-grani-bankrotstva.html

Запуск: python3 pipeline/fix_united_panel_sanctions_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd1f94881'

OLD_CONTEXT = (
    'С 2009 года компания несколько раз находилась в банкротстве, '
    'испытывала дефицит оборотных средств и считалась одним из самых '
    'неэффективных предприятий отрасли.'
)
CONTEXT_ADDITION = (
    'Гендиректор Ассоциации предприятий мебельной и деревообрабатывающей '
    'промышленности России Тимур Иртуганов объясняет масштаб кризиса '
    'отраслевым фактором: «Производители фанеры в наибольшей степени из '
    'всех направлений ЛПК пострадали из-за санкций. Исторически '
    'экспортно ориентированная отрасль в одночасье лишилась основных '
    'рынков сбыта Европы и Северной Америки, куда до 2022 года уходило '
    'до 60% всей выпущенной в России березовой фанеры».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += отраслевой контекст (санкции, "
          f"потеря экспортных рынков)")
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
