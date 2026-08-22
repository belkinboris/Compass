# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g1d28507c (Ростелеком/
«Рабочие Руки»): `eco.share` называл долю «Ростелекома» на момент
закрытия (12,3%, 23 декабря 2025). Дельта нашла, что опцион на довыкуп
(уже упомянутый в `law.terms`) частично исполнен уже через месяц: доля
выросла вдвое, до 25,3%, а доля основателя Олега Шилова упала с 45% до
38,5%.

Не через review.py: `eco.share` уже не пуст, а общая проверка
дословности требует, чтобы ВСЁ значение поля (старый текст + новый)
лежало в ОДНОЙ цитате — старый текст из ЕГРЮЛ/декабрьских источников,
новый — дословно из отдельной статьи (CNews, 26.01.2026).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g1d28507c'
OLD_SHARE = (
    'По данным ЕГРЮЛ, венчурный фонд «Ростелекома» — ООО «КоммИТ '
    'Кэпитал» — 23 декабря стал владельцем 12,3% в ООО «Рабочие руки».'
)
ADDITION = (
    'Доля «Ростелекома» в «Рабочие руки» выросла в два раза и достигла '
    '25,3%. Запись об этом в ЕГРЮЛ была внесена 12 января 2026 г. '
    'Одновременно доля основателя компании Олега Шилова сократилась с '
    '45% до 38,5%.'
)
NEW_SHARE = OLD_SHARE + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['share'] == OLD_SHARE, \
        f"eco.share: неожиданное значение {deal['eco']['share']!r}"

    print(f"{CARD_ID} eco.share: += доля «Ростелекома» выросла до "
          "25,3% (январь 2026, опцион частично исполнен)")
    deal['eco']['share'] = NEW_SHARE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
