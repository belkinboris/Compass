# -*- coding: utf-8 -*-
"""Шесть карточек несли год-заглушку («2025», иногда с придуманным днём),
а источники — все статьи «Коммерсанта», «Известий» и pro.rbc.ru — прямо
датируют события 2026 годом.

ЧТО СЛОМАНО. Тот же класс дефекта, что уже чинили `fix_2025_bulk_year_
placeholder.py` и `..._batch2.py`.

  - cdcc6f67f (ПЭК и «Деловые линии»/страховщики): kommersant.ru — «25.01.
    2026, 20:37» (стр. 5 номера от 26.01.2026).
  - g0b081bb7 («Брусника»/ФСК, два участка в Петербурге): kommersant.ru —
    «13.03.2026, 02:35».
  - g352523e0 (IPO компании 1С): pro.rbc.ru — «Опубликовано 18.03.2026,
    09:00».
  - g5e8fd721 (Газпромбанк/российские активы Sucden): у карточки стояла
    ложная точность — «2025-02-01» — хотя метаданные статьи iz.ru прямо
    называют другую дату: `article:published_time` = «2026-02-27T00:01:00»,
    в тексте — «27 февраля 2026». Расхождение не только в годе, но и в
    дне/месяце — старое значение придумано целиком, а не уточнено.
  - g6a4b0a2a (Сергей Шишкарев/УК «Дело», «Росатом», «Ростех»):
    kommersant.ru — «02.04.2026, 21:27» (стр. 1 номера от 03.04.2026).
  - g76983314 (Wildberries/«Ситимобил», «Таксовичкоф», «Грузовичкоф»):
    pro.rbc.ru — «Опубликовано 02.04.2026, 00:00».

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником, а не автоматической правкой в общей таблице.

Все шесть карточек этим переносом выходят из среза 2025 года.

Запуск:
    python3 pipeline/fix_2025_bulk_year_placeholder_batch3.py            # сухой прогон
    python3 pipeline/fix_2025_bulk_year_placeholder_batch3.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

FIXES = [
    dict(id='cdcc6f67f', old_date='2025', new_date='2026-01-25',
         quote='kommersant.ru датирует материал «25.01.2026, 20:37»'),
    dict(id='g0b081bb7', old_date='2025', new_date='2026-03-13',
         quote='kommersant.ru датирует материал «13.03.2026, 02:35»'),
    dict(id='g352523e0', old_date='2025', new_date='2026-03-18',
         quote='pro.rbc.ru: «Опубликовано 18.03.2026, 09:00»'),
    dict(id='g5e8fd721', old_date='2025-02-01', new_date='2026-02-27',
         quote='iz.ru: метатег published_time «2026-02-27T00:01:00», '
               'в тексте «27 февраля 2026»'),
    dict(id='g6a4b0a2a', old_date='2025', new_date='2026-04-02',
         quote='kommersant.ru датирует материал «02.04.2026, 21:27»'),
    dict(id='g76983314', old_date='2025', new_date='2026-04-02',
         quote='pro.rbc.ru: «Опубликовано 02.04.2026, 00:00»'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for fix in FIXES:
        deal = by_id.get(fix['id'])
        assert deal is not None, 'нет сделки %s' % fix['id']
        assert deal.get('date') == fix['old_date'], \
            '%s: дата уже другая: %r, ожидали %r' % (
                fix['id'], deal.get('date'), fix['old_date'])
        print('%s: date %r -> %r' % (fix['id'], fix['old_date'], fix['new_date']))
        print('  цитата: %r' % fix['quote'])

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for fix in FIXES:
        by_id[fix['id']]['date'] = fix['new_date']

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
