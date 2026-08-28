# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g995f83cf (Приобретение
российских компаний группы «Ренессанс Капитал» у «Группы Онэксим», ноябрь
2024): дельта-поиск нашёл, что «Ренессанс Капитал» (покупатель по этой
сделке — MBO менеджментом) сам стал покупателем в новой крупной сделке:
в феврале 2026 года завершил приобретение 100% АО «Ситибанк» (бывшая
«дочка» Citigroup), переименовав его в «РенКап банк» — подтверждено лично
прямым WebFetch «Коммерсанта». Также в уже цитируемом источнике
(kommersant.ru/doc/7498030) нашлись неизвлечённые прямые цитаты гендиректора
Максима Орловского о стратегии после MBO (фокус на элитных клиентах,
конкурентное поле после ухода иностранных банков). Не через review.py:
факт о новой, отдельной сделке компании — не про эту сделку с Онэксимом
напрямую, плюс дополнение уже процитированного источника.

Запуск: python3 pipeline/fix_renaissance_capital_citibank_acquisition_context.py
        python3 pipeline/fix_renaissance_capital_citibank_acquisition_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g995f83cf'

OLD_CONTEXT = (
    'В пресс-службе «Ренессанс Капитала» пояснили, что сделка состоялась в '
    'рамках двухлетнего плана. Первым этапом был перевод бизнеса в Россию, '
    'а вторым — продажа трех российских компаний группы менеджменту. Бренд '
    '«Ренессанс» остается.'
)
CONTEXT_ADDITION = (
    ' Гендиректор Максим Орловский описал стратегию после MBO: «Мы ушли '
    'туда, где наши банки не могли составить нам конкуренцию», ориентир — '
    '«самые богатые люди на рынке» («наша целевая группа — не более '
    '10 тыс. клиентов»), а движение — «очень постепенно», «от пакета до '
    'пакета» (Коммерсантъ). В феврале 2026 года «Ренессанс Капитал» сам '
    'стал покупателем в новой сделке: завершил приобретение 100% акций '
    'АО «Ситибанк» (бывшая «дочка» Citigroup) и переименовал его в '
    '«РенКап банк».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8499666'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
