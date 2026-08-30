# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g7bffe474 (ООО «Арт-Финанс» приобрела завод Hyundai в Санкт-Петербурге)
— опцион на обратный выкуп, срок которого истекал в январе 2026-го (уже
записан в law.terms), истёк БЕЗ исполнения: Hyundai сам подтвердил
отказ, а завод с тех пор простаивает. Проверено лично прямым WebFetch
двух источников.

`law.terms` (дополнено). Дословно (РИА Новости, 02.02.2026): «Hyundai
Motor заявила РИА Новости, что не воспользовалась возможностью
обратного выкупа своего бывшего завода в России», «группа остается
единственным владельцем предприятий и несет полную ответственность за
их дальнейшее развитие» (позиция группы «АГР»).

`eco.context` (заполнено, было «—»). Дословно (МР7.ру, 25.06.2026): «В
2026 году бывшая площадка Hyundai в особой экономической зоне «Каменка»
не выпустила ни одной единицы Solaris» — завод простаивает после
исчерпания машинокомплектов.

НЕ ВКЛЮЧЕНО: какой бренд запустят на площадке вместо Solaris —
источник (74.ru, 02.08.2026) называет только предположение «возможно,
Tenet Plus», без подтверждения; расхождение суммы символической продажи
между источниками (140 тыс. вон против 160 тыс. вон/10 тыс. ₽) — обе
цифры символические, но не дословно совпадают, разбор оригинала Reuters
не проводился; консультанты сделки — не найдены.

Запуск: python3 pipeline/fix_arkady_hyundai_option_lapsed.py
        python3 pipeline/fix_arkady_hyundai_option_lapsed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7bffe474'

OLD_TERMS = (
    'В публикации указано, что при заключении сделки был предусмотрен '
    'опцион на обратный выкуп сроком на два года — срок его действия '
    'истекает в январе 2026-го.'
)
NEW_TERMS = OLD_TERMS + (
    ' Опцион истёк без исполнения: «Hyundai Motor заявила РИА Новости, '
    'что не воспользовалась возможностью обратного выкупа своего '
    'бывшего завода в России», а группа «АГР» заявила, что «остается '
    'единственным владельцем предприятий и несет полную ответственность '
    'за их дальнейшее развитие» (РИА Новости, 2 февраля 2026).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'После истечения опциона завод простаивает: «В 2026 году бывшая '
    'площадка Hyundai в особой экономической зоне «Каменка» не '
    'выпустила ни одной единицы Solaris» — машинокомплекты закончились '
    '(МР7.ру, 25 июня 2026).'
)

NEW_SRC = [
    ['РИА Новости', 'https://ria.ru/20260202/hyundai-2071723800.html'],
    ['МР7.ру', 'https://mr-7.ru/articles/2026/06/25/avtomobili-solaris-okonchatelno-perestali-vypuskat-v-peterburge-news'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['terms'] == OLD_TERMS
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.terms: станет ===')
    print(NEW_TERMS)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['terms'] = NEW_TERMS
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
