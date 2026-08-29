# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g8c32cefd
(Севергрупп купила бывший завод Bosch у S8 Capital) — дата была
перепутана на несколько месяцев, а `extra` стояло буквально пустым.
Проверено лично прямым WebFetch.

ДАТА. Карточка несла «2024-06-24». Источник этой ошибки — сама ссылка в
`src` (РБК, путь URL содержит «25/06/2025») на самом деле описывает
ПОСЛЕДУЮЩУЮ, обратную сделку (перепродажу того же завода структуре
Softline в июне 2025 года), а не сделку S8 Capital → «Севергрупп».
Настоящая дата этой сделки нашлась в независимом источнике — Коммерсантъ,
дословно: «С 1 октября 2024 года «Севергрупп» получила права
собственности на активы предприятий группы «Метеор» в Энгельсе
Саратовской области... а также группы компаний «Кордиант»». Год тот же
(2024), меняется только месяц/день — уточнение внутри известного года.
Источник: https://www.kommersant.ru/doc/7198466

ДОБАВЛЕНО:
1) `extra` (было пустой строкой) — дословная цитата того же источника:
«Бывший завод Bosch в Энгельсе выкупила компания «Севергрупп»... По
данным «Коммерсанта», «Севергрупп» приобрела у S8 Capital группу
компаний «Кордиант», выпускающую шины, электроинструменты и
автокомпоненты».
2) `src` — добавлен Коммерсантъ (единственный источник, реально
описывающий ЭТУ сделку; уже стоявший РБК описывает другую, более
позднюю).

НЕ ТРОНУТО: `law.struct` (уже верно — «Метеор» и «Кордиант» относятся к
ЭТОЙ ЖЕ пакетной сделке, не к чужому предмету, подтверждено Коммерсантом
почти дословно); `eco.context`/`eco.rationale` — уже заполнены и не
требуют правки. Не включена оценка суммы «804 млн руб. (чистые активы на
конец 2023 года)» из mergers.ru — она относится к ИЮНЬСКОЙ 2025 продаже
(Севергрупп → Softline), а не к сделке октября 2024 года этой карточки
(родня уроку CLAUDE.md «Число может быть верным фактом и совсем не той
величиной/периметром»); консультанты не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_severgroup_bosch_meteor_date_and_extra.py
        python3 pipeline/fix_severgroup_bosch_meteor_date_and_extra.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8c32cefd'

OLD_DATE = '2024-06-24'
NEW_DATE = '2024-10-01'

OLD_EXTRA = ''
NEW_EXTRA = (
    'Бывший завод Bosch в Энгельсе выкупила компания «Севергрупп». По '
    'данным «Коммерсанта», «Севергрупп» приобрела у S8 Capital группу '
    'компаний «Кордиант», выпускающую шины, электроинструменты и '
    'автокомпоненты.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7198466'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['extra'] == OLD_EXTRA
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== date: {OLD_DATE!r} -> {NEW_DATE!r} ===')
    print('=== extra (было пусто): станет ===')
    print(NEW_EXTRA)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['extra'] = NEW_EXTRA
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
