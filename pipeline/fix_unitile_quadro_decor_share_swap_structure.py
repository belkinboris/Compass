# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gca6c1eff
(Unitile приобрел Quadro Décor, сентябрь 2024). Дельта-поиск нашёл
структуру расчёта по сделке, которую единственный источник (Коммерсантъ,
июль 2024) знать не мог — она раскрылась только в январе 2025.

Коммерсантъ, «Proxima Capital Group и бывший топ-менеджер СИБУРа стали
совладельцами Unitile», 16.01.2025 (проверено лично прямым WebFetch):
«переход 5% долей в структуре Unitile ООО «Плитэксперт» — часть сделки
по продаже холдингу бизнеса Quadro Decor, заключенной осенью 2024 года».
То есть часть оплаты за Quadro Décor была структурирована не деньгами, а
встречной долей в самом Unitile Holding — Proxima Capital Group (продавец
Quadro Décor) стала совладельцем покупателя.

Состав нового совладения (та же статья): «70% в «Плитэксперте» у ООО
«Проксима кэпитал групп» (PCG)... 20% принадлежат Катарине Конкс, 10% у
Виталия Баранова» — Конкс и Баранов бывшие топ-менеджеры СИБУРа
(«Катарина Конкс — супруга бывшего председателя правления и совладельца
СИБУРа Дмитрия Конова», «Виталий Баранов был вице-президентом СИБУРа»),
но это про НОВЫХ совладельцев доли в Unitile, а не про саму сделку с
Quadro Décor — в карточку не переносится, это отдельный факт про третьих
лиц.

НЕ включены (сабагент нашёл, но не прошло проверку дословностью): причины
продажи со стороны Proxima Capital Group (источники пишут «от
комментариев отказались»), завершение передачи оставшихся ~87% Quadro
Holding (только агрегированная сводка поиска по реестрам, без прямой
цитаты с датой), консультанты сделки — не названы ни в одном источнике.

Запуск: python3 pipeline/fix_unitile_quadro_decor_share_swap_structure.py
        python3 pipeline/fix_unitile_quadro_decor_share_swap_structure.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gca6c1eff'

OLD_STRUCT = (
    'Согласно СПАРК, пока формально произошла передача 13% компании. Это '
    'связано с техническими этапами прохождения сделки, пояснил '
    '«Коммерсанту» представитель «Юнитайл».'
)
STRUCT_ADDITION = (
    ' В январе 2025 года стало известно, что часть расчёта была '
    'структурирована не деньгами: «переход 5% долей в структуре Unitile '
    'ООО «Плитэксперт» — часть сделки по продаже холдингу бизнеса Quadro '
    'Decor, заключенной осенью 2024 года» (Коммерсантъ) — продавец, '
    'Proxima Capital Group, получил встречную долю в самом Unitile Holding.'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7432619'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
