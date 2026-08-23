# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g7c8f9112 (Softline
Venture Partners/HR Rocket): дельта-поиск нашёл полную структуру
капитала компании ПОСЛЕ сделки — в law.struct были названы только новые
инвесторы (Softline, Пантелеев, Ефремов, 20,8% на троих), а кто владеет
остальными ~79% (реальные основатели), карточка не говорила вовсе.

Источник: vc.ru («Русский Венчур», 14 января 2026) — читал напрямую.
Не через review.py: добавляемый факт про долю основателей — из ТОГО ЖЕ
источника, но контекст в law.struct собран из другого, более раннего
источника (CNews), и слепить оба в одну цитату для дословной проверки
нельзя, поэтому расширение — отдельным скриптом.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g7c8f9112'
OLD_STRUCT = (
    'ООО «Софтлайн инвест» и АО «Интернет проекты» (структуры Softline '
    'Venture Partners) получили по 7,14% в проекте. Одновременно в '
    'проект вошли предприниматели Андрей Пантелеев, ему досталось '
    '4,29%, и Алексей Ефремов, у него 2,23%. Всего новые инвесторы, с '
    'учетом миноритариев Пантелеева и Ефремова, которые не аффилированы '
    'с Softline Venture Partners, получили 20,8% в проекте.'
)
ADDITION = (
    'Остальные доли, по данным Rusprofile: гендиректору ООО «Эйчар '
    'Рокет» Дмитрию Саушкину принадлежит 22,82%, Константину Вечкаеву '
    '— 20,55%, ООО «Ханилидс» — 19,7%, Сергею Пономаренко — 4,33%, '
    'ООО «Фрии Инвест» — 3,22%.'
)
NEW_STRUCT = OLD_STRUCT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} law.struct: += доли основателей и остальных "
          "совладельцев после сделки")
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
