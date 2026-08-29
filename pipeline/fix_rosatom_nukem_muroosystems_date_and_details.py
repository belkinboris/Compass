# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gd96d269e
(Росатом продал немецкую структуру Nukem японской компании
Muroosystems) — дата-заглушка «1 июля» вместо реальной даты закрытия.
Проверено лично прямым WebFetch.

ДАТА. Карточка несла «2024-07-01» — источник (Коммерсантъ, 17.07.2024)
на момент публикации сам говорит, что «закрытие сделки ожидается к
середине августа», то есть ещё НЕ закрыта. Реальная дата закрытия —
World Nuclear News, дословно: «The effective date of the economic
transfer of the company to the new owner is 25 September 2024» —
подтверждено JAIF: «Following the necessary approval procedures, it
obtained authorization from the German government on September 9,
thereby completing all processes». Год тот же (2024), меняется только
месяц/день — это уточнение ВНУТРИ известного года, `review.py` умеет
такое (`date_is_supported`), но экономнее и нагляднее сделать это в
одном скрипте вместе с остальными правками той же карточки.

ДОБАВЛЕНО:
1) `law.struct` (новое поле) — юридический механизм выхода. Коммерсантъ,
дословно: «Весной 2024 года немецкий менеджмент по требованию
законодательства страны запустил процедуру самоуправляемого банкротства
структур Nukem Technologies», после чего «суд освободил компанию от
российской структуры собственности, что способствовало минимизации
соответствующих юридических рисков».
2) `eco.rationale` — причина продажи. Коммерсантъ, дословно: «в связи с
текущими геополитическими ограничениями и давлением на российских
собственников в странах ЕС приняли решение выйти из актива».
3) `eco.context` (новое поле) — судьба Nukem под Muroosystems: World
Nuclear News (09.01.2026), дословно: «Nukem Technologies Engineering
Services GmbH - a German subsidiary of Muroosystems - will provide
technical consulting services» по меморандуму с UzAtom (Узбекистан) для
проекта дата-центра, «designed for a power demand of about 50 MWe, which
is to be fully met by SMR-based power generation» — первый в мире проект
такого рода. Президент Nukem Томас Зайполт: «This collaboration in
Central Asia goes far beyond individual projects. It represents a
long-term partnership for the further development of nuclear energy».

НЕ включены: сумма сделки — Коммерсантъ прямо пишет «Условия трансакции
не разглашаются», независимой оценки не нашлось ни у одного источника;
консультанты сделки — не найдены.

Запуск: python3 pipeline/fix_rosatom_nukem_muroosystems_date_and_details.py
        python3 pipeline/fix_rosatom_nukem_muroosystems_date_and_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd96d269e'

OLD_DATE = '2024-07-01'
NEW_DATE = '2024-09-25'

NEW_STRUCT = (
    'Весной 2024 года немецкий менеджмент по требованию законодательства '
    'страны запустил процедуру самоуправляемого банкротства структур '
    'Nukem Technologies, после чего суд освободил компанию от российской '
    'структуры собственности, что способствовало минимизации '
    'соответствующих юридических рисков (Коммерсантъ).'
)

NEW_RATIONALE = (
    'В связи с текущими геополитическими ограничениями и давлением на '
    'российских собственников в странах ЕС приняли решение выйти из '
    'актива (Коммерсантъ).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В январе 2026 года Muroosystems подписала меморандум с UzAtom '
    '(Узбекистан): «Nukem Technologies Engineering Services GmbH - a '
    'German subsidiary of Muroosystems - will provide technical '
    'consulting services» для проекта дата-центра, «designed for a power '
    'demand of about 50 MWe, which is to be fully met by SMR-based power '
    'generation» — первый в мире подобный проект. Президент Nukem Томас '
    'Зайполт: «This collaboration in Central Asia goes far beyond '
    'individual projects. It represents a long-term partnership for the '
    'further development of nuclear energy» (World Nuclear News).'
)

NEW_SRC = [
    ['World Nuclear News', 'https://www.world-nuclear-news.org/articles/muroosystems-completes-purchase-of-nukem-technologies'],
    ['World Nuclear News', 'https://world-nuclear-news.org/articles/muroosystems-expands-nuclear-cooperation-in-central-asia'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['law']['struct'] == '—'
    assert not deal['eco'].get('rationale')
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== date: {OLD_DATE!r} -> {NEW_DATE!r} ===')
    print('=== law.struct (новое поле): станет ===')
    print(NEW_STRUCT)
    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
