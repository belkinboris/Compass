# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g412f413c` («ГК О3 приобрела финскую компанию КиилтоКлин», январь
2023, Закрыта) — переходный период после сделки и судьба сотрудников
не были отражены.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты источника-покупателя,
o3.com, публикация от 27 сентября 2022 года):
- Григорий Шифрин (гендиректор О3): «Приобретение высокоэффективного
  бизнеса профессиональной гигиены Kiilto в России полностью
  соответствует стратегии Компании О3»;
- Арто Райвио (управляющий директор Kiilto): «более 65 работников ООО
  «КиилтоКлин» сохранят трудовые отношения с новым собственником»;
- переходный период продукции под брендами Kiilto/Kiilto Pro/Erisan
  продлится «до 31 марта 2023 года, после чего будет произведён
  ребрендинг»; «До конца 2022 года также изменится название
  юридического лица ООО «КиилтоКлин»».

НЕ ВНЕСЕНО: итоговое новое имя юрлица (по агрегированным данным —
«Клинин», ИНН 7813326820, тот же ОГРН) и финансовые показатели 2024-
2025 годов — встретились только в сниппетах реестровых агрегаторов
(rusprofile.ru отдал 403 при прямой проверке), не подтверждены
дословным чтением.

Запуск: python3 pipeline/fix_o3_kiiltoklin_transition_details.py
        python3 pipeline/fix_o3_kiiltoklin_transition_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g412f413c'

OLD_ECO_CONTEXT = 'Kiilto — лидер рынка профессиональной гигиены в странах Северной Европы.'
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По условиям сделки более 65 сотрудников «КиилтоКлин» '
    'сохранили работу у нового собственника; переходный период с '
    'продажей продукции под прежними брендами продлился до 31 марта '
    '2023 года, после чего компанию ребрендировали.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5795855'],
]
NEW_SRC = OLD_SRC + [
    ['О3', 'https://o3.com/information/kompaniya-o3-priobretaet-100-doley-kiiltoklin/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
