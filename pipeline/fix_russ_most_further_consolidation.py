# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g981d090f (Группа Russ через ООО «РВБ» купила РА «Мост») — дальнейшая
консолидация Russ/RWB в наружной рекламе и рост инвентаря в Нижнем
Новгороде после сделки. Проверено лично прямым WebFetch двух
источников.

`eco.context` (заполнено, было «—»). Дословно (Sostav.ru, 30.01.2026):
«Группа Russ (входит в RWB) завершила приобретение оператора наружной
рекламы в городе Артеме Приморского края — "Артем-Кино Медиа"» — та же
скупочная стратегия, другой регион и цель. Дословно (ProGorodNN,
30.04.2026): «Группа Russ (входит в RWB) увеличила собственную сеть
цифровых экранов в Нижнем Новгороде c марта 2025 года по март 2026
года в 5,7 раза», «в результате приобретения одного из местных
операторов наружной рекламы» — источник НЕ называет «Мост» по имени
напрямую, честно указано с оговоркой.

НЕ ВКЛЮЧЕНО (решение за человеком, не механическая правка):
суб-агент нашёл возможное расхождение по ЕГРЮЛ — юрлицо «ООО
«Рекламное агентство «Мост»»» (ИНН 5260345990) ликвидировано 11 июля
2025 года, а его учредители по истории ЕГРЮЛ не включают Олесю
Шишкину (продавца по карточке); в городе минимум три разных юрлица под
вывеской «РА Мост». Это не проверено дословным чтением второго
независимого источника и требует ручной проверки, прежде чем менять
`seller`/`target` карточки — не внесено. Более точная сумма сделки и
судьба Олеси Шишкиной после продажи — не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_russ_most_further_consolidation.py
        python3 pipeline/fix_russ_most_further_consolidation.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g981d090f'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Дальнейшая консолидация Russ/RWB в наружной рекламе: «Группа Russ '
    '(входит в RWB) завершила приобретение оператора наружной рекламы в '
    'городе Артеме Приморского края — "Артем-Кино Медиа"» (Sostav.ru, '
    '30 января 2026). В Нижнем Новгороде рост инвентаря подтверждён '
    'количественно: «Группа Russ (входит в RWB) увеличила собственную '
    'сеть цифровых экранов в Нижнем Новгороде c марта 2025 года по март '
    '2026 года в 5,7 раза» — «в результате приобретения одного из '
    'местных операторов наружной рекламы» (ProGorodNN, 30 апреля 2026; '
    'источник не называет «Мост» по имени напрямую).'
)

NEW_SRC = [
    ['Sostav.ru', 'https://www.sostav.ru/publication/gruppa-russ-priobrela-primorskogo-operatora-naruzhnoj-reklamy-81354.html'],
    ['ProGorodNN', 'https://progorodnn.ru/companies/151371'],
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
    print('\n=== src добавится ===')
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
