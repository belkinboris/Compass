# -*- coding: utf-8 -*-
"""Карточка g4fc7af86 (Ipsos SA/«Ипсос Комкон»): структура созданного СП
не была описана нигде (law.struct пустое) — официальный пресс-релиз
самой Ipsos SA (на английском, русскоязычного пересказа этой детали не
нашлось) прямо называет долю продавца в СП и дату деконсолидации. Не
через review.py: источник на английском, `new` — перевод на русский, а
review.py проверяет ДОСЛОВНОЕ (посимвольное) совпадение `new` с `quote`,
что для перевода между языками невозможно в принципе — та же граница,
что уже описана в CLAUDE.md для экранирования между языками, только
здесь не синтаксис кода, а естественный язык.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.investegate.co.uk/announcement/gnw/ipsos-sa--0ka3/-press-release-sale-of-80-of-ipsos-comcon-l-/9451927
Дословная цитата (английский оригинал): «Ipsos SA will keep its 20%
minority passive participation in Ipsos Comcon LLC, which will be
deconsolidated from the group accounts starting January 1st, 2026.»

Запуск: python3 pipeline/fix_ipsos_comcon_structure_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4fc7af86'
OLD_STRUCT = '—'
NEW_STRUCT = (
    'Ipsos SA сохраняет 20%-ную миноритарную пассивную долю в «Ипсос '
    'Комкон» — компания деконсолидирована из группы с 1 января 2026 '
    'года.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} law.struct: структура СП (сохранённая доля "
          f"продавца), поле было пустым")
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
