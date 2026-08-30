# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g088a43f9 (ГК «Монополия» приобрела 72% долей в пермской «Умная
логистика») — доля покупателя выросла после сделки, а финансовые
итоги под новым контролем не были отражены. Проверено лично прямым
WebFetch двух источников.

`eco.context` (дополнено). Дословно (Коммерсантъ): «доля федерального
холдинга ООО "Монополия.Онлайн" в организации увеличилась с 72 до
86%»; «Еще 13,44% "Умной логистики" находится во владении основателя
компании Ольги Поповой» — то есть после сделки 2024 года прошла ещё
одна операция по выкупу доли у основателя (её пакет снизился с 26,88%
до 13,44%), а 100% «Монополия» не выкупила.

`eco.target_fin` (дополнено). Дословно (РБК Компании): «выручка за
2025 год — 634 440 000 ₽», «прибыль компании составляет — 366 937 000
₽» — рост от уже известных 330,1 млн ₽ выручки и 143,2 млн ₽ прибыли
за 2023 год (выручка почти удвоилась, прибыль выросла более чем в 2,5
раза).

НЕ ВКЛЮЧЕНО: точная дата увеличения доли 72%→86% — ни один источник
её не называет, известно только, что по состоянию на дату проверки
СПАРК (используемой Коммерсантом) доля уже была 86%; падение
собственного капитала компании на конец 2025 года (по WebSearch-
сниппету, не подтверждено прямым WebFetch) — не переносится без
дословной цитаты. Судьба доли Сергея Мельницына, консультанты сделки,
другие сделки «Монополии» — не найдены.

Запуск: python3 pipeline/fix_monopoliya_umnaya_logistika_stake_growth.py
        python3 pipeline/fix_monopoliya_umnaya_logistika_stake_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g088a43f9'

OLD_CONTEXT = (
    'Как указано в Rusprofile, АО «Монополия» создано в Санкт-'
    'Петербурге в 2013 году. Владельцами являются петербургские '
    'предприниматели Илья Дмитриев и Екатерина Михайлова.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' К 2025 году доля «Монополии» в «Умной логистике» выросла с 72% '
    'до 86% — доля основателя Ольги Поповой снизилась до 13,44% '
    '(Коммерсантъ, со ссылкой на СПАРК-Интерфакс).'
)

OLD_TARGET_FIN = (
    'Согласно бухгалтерской отчетности, выручка компании в 2023 году '
    'составила 330,1 млн руб., чистая прибыль — 143,2 млн руб.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + (
    ' По итогам 2025 года выручка выросла до 634,44 млн руб., чистая '
    'прибыль — до 366,94 млн руб. (РБК Компании).'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7621140'],
    ['РБК Компании', 'https://companies.rbc.ru/id/1145958022572-umnaya-logistika/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
