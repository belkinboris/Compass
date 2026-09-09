# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g1f302e4f`
(«Steplife разместила 9,1% капитала в рамках pre-IPO при оценке 2,2 млрд ₽»,
добавлена в базу 3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл два новых факта сверх уже
известного, оба со стороны структуры самого размещения:

1) Организатор/партнёр размещения — Nova VC, платформа — «ВТБ Регистратор».
   Личный WebFetch (cnews.ru/news/line/2026-01-20_kompaniya_steplife_
   privlekaet, 20 января 2026) подтвердил дословно: «Партнером размещения
   выступает Nova VC.» Личный WebFetch (akm.ru, тот же день, 16:29)
   подтвердил дословно: «Steplife начала сбор заявок в рамках закрытого
   раунда pre-IPO на инвестиционной платформе ВТБ Регистратор.»

2) Защитный механизм для инвесторов — put-опцион, привязанный к плановым
   финансовым показателям. Тот же источник cnews.ru дословно: «Для
   инвесторов предусмотрен защитный механизм в виде опциона на продажу
   (put-опцион), который привязан к достижению плановых финансовых
   показателей: поступлениям от продаж и чистой прибыли.» Это условие
   сделки (не описание продукта цели — put-опцион защищает именно
   инвесторов раунда, а не клиентов компании), поэтому идёт в `law.terms`,
   а не в описание бизнеса.

Побочная находка саб-агента (не вносится структурно — операционные
показатели компании, не факт сделки): продажи Steplife за I полугодие
2026 выросли на 89% год к году (593,3 млн ₽), но это контекст роста
бизнеса ПОСЛЕ раунда, а не условие самой сделки pre-IPO.

Запуск:
    python3 pipeline/fix_steplife_placement_details.py            # сухой прогон
    python3 pipeline/fix_steplife_placement_details.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_STRUCT = 'Pre-IPO-размещение 9,1% уставного капитала.'
NEW_LAW_STRUCT = (
    'Pre-IPO-размещение 9,1% уставного капитала. Партнёром размещения '
    'выступил Nova VC, сбор заявок шёл на инвестиционной платформе '
    '«ВТБ Регистратор».'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'Для инвесторов предусмотрен защитный механизм в виде опциона на '
    'продажу (put-опцион), который привязан к достижению плановых '
    'финансовых показателей: поступлениям от продаж и чистой прибыли.'
)

NEW_SRC = ['CNews', 'https://www.cnews.ru/news/line/2026-01-20_kompaniya_steplife_privlekaet']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g1f302e4f']

    assert d['law']['struct'] == OLD_LAW_STRUCT, \
        'g1f302e4f law.struct уже другой: %r' % (d['law']['struct'],)
    assert d['law']['terms'] == OLD_LAW_TERMS, \
        'g1f302e4f law.terms уже другой: %r' % (d['law']['terms'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g1f302e4f: law.struct дополнен (Nova VC, ВТБ Регистратор); '
          'law.terms заполнен (put-опцион); добавлен источник cnews.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['law']['terms'] = NEW_LAW_TERMS
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
