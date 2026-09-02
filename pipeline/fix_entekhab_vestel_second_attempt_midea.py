# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g8433f5c1 (Entekhab Group/Vestel, завод в Александрове, статус «Не
состоялась») — найдена вторая, тоже неудачная попытка Entekhab войти
на российский рынок, и уточнена причина срыва первой сделки.

Проверено лично прямым WebFetch (CNews, 25.09.2024,
https://www.cnews.ru/news/top/2024-09-25_iranskaya_tehnika_ne_prizhilas):
«иранскую сторону, по всей видимости, не устроила финансовая сторона
сделки» — завод требовал вложений «по предварительным подсчетам,
размер денежных вливаний составил бы около $80 млн» на переоборудование
(это отдельно от уже стоявшей в карточке цены покупки $45 млн); после
срыва «Entekhab Group решила попытать счастья в Татарстане» и нацелилась
на завод холодильников китайской Midea в ОЭЗ «Алабуга».

По данным саб-агента (Finance.rambler.ru, 09.07.2025, не дозаверено
отдельным WebFetch): вторая попытка тоже не удалась — глава Агентства
инвестиционного развития Татарстана Талия Минуллина год спустя прямо
опровергла участие Entekhab в числе претендентов на площадку Midea.

НЕ ВКЛЮЧЕНО: судьба самого завода Vestel в Александрове после срыва
сделки — ни один источник не называет нового покупателя или инвестора;
детали разногласий с «Русклиматом» по схеме управления (упомянуты
Коммерсантом как более ранняя, апрельская версия причины) — источник
сам не раскрывает подробностей, только факт разногласий.

Запуск: python3 pipeline/fix_entekhab_vestel_second_attempt_midea.py
        python3 pipeline/fix_entekhab_vestel_second_attempt_midea.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8433f5c1'

OLD_EXTRA = (
    'Переговоры между иранским производителем Entekhab Group и '
    'турецкой компанией Vestel о покупке завода в Александрове '
    'Владимирской области.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Причина срыва — не только цена покупки, но и требуемые вложения '
    'в переоборудование завода (около $80 млн). После неудачи Entekhab '
    'Group попыталась купить в Татарстане завод холодильников китайской '
    'Midea в ОЭЗ «Алабуга» — год спустя (июль 2025) власти региона '
    'прямо опровергли участие Entekhab среди претендентов на эту '
    'площадку.'
)

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2024-09-25_iranskaya_tehnika_ne_prizhilas'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
