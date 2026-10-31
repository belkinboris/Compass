# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g7ca174fd (ЛВЗ «Саранский»/
Спиртзавод «Ромодановский»): заголовок называет долю «99%», хотя все пять
проверенных источников (Коммерсантъ, Alcoexpert, RuNews24, Retail.ru,
Агроэксперт) согласно называют 99,9% — то же число, что уже стояло в
`law.struct`. Заголовок — округление/упрощение без опоры на источник,
исправлен на точную цифру.

НЕ РЕШЕНО этим скриптом: источники расходятся в ДАТЕ смены собственника
(Коммерсантъ — 22 июня 2025, Агроэксперт и `extra` карточки — 22 июля
2025) — записано в журнале как открытый вопрос, не выбрано произвольно
в одну сторону.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g7ca174fd'
OLD_TITLE = 'ЛВЗ «Саранский» приобрел 99% ООО «Спиртзавод «Ромодановский»»'
NEW_TITLE = 'ЛВЗ «Саранский» приобрел 99,9% ООО «Спиртзавод «Ромодановский»»'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['title'] == OLD_TITLE, f"title: неожиданное значение {deal['title']!r}"

    print(f"{CARD_ID} title: {OLD_TITLE!r} -> {NEW_TITLE!r}")
    deal['title'] = NEW_TITLE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
