# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партия nf): то, что review.py не умеет.

1. СУММА g0591604d («Интеррос»/УК «Восход»): в sum и eco.sum стояли «10 млрд ₽» — это объем
   фонда «Восход» под управлением УК, а не цена. Коммерсантъ (6 июня 2023): «В УК «Восход»
   информацию подтвердили, добавив, что под ее управлением остается одноименный фонд объемом
   10 млрд руб. … Сумму сделки стороны не раскрыли.» → «Не раскрыта» (как у 472 карточек базы;
   review.py этот текст суммой не принимает), «10 млрд ₽» — в retracted.sum, чтобы enrich.py не
   вернул его по той же статье (docs/card_editing.md, «Снятое значение — в retracted»).
2. KIND g0591604d: тип сменен записью FIXES партии nf («Инвестиция» → «M&A»: «Интеррос» продал
   управляющую компанию менеджерам), kind «financing» → «acquisition» (promote_all.deal_kind).
3. ДАТЫ без дня (docs/card_status_dates.md, «Нет дня — только год»):
   - g0591604d: 2023-06-06 — день публикации «Ъ»; доли перешли «с весны» 2023 года → 2023.
   - g0cf6a562 (кофейни Starbucks): 2022-07-31 — дня в статьях нет («The deal was closed by the
     end of July», Leave-Russia) → 2022.
   - g40477661 («ЛабКвест»/«ФораЛаб»): 2023-06-01 — день статьи Vademecum. По ЕГРЮЛ (история
     участников ООО «ФораЛаб», ИНН 7810788537, party_legal_names.py): «2023-05-30 left: Марков
     Александр Иванович (90.0 → None); 2023-05-30 joined: Пикалюк Дарья Львовна (None → 90.0)»
     → 2023-05-30, date_basis 'registry'; этап closed стоял на выдуманном 2023-05-01 → 2023-05-30.
4. ОТРАСЛЬ g0591604d: «ИТ и интернет» → «Управление активами»: предмет — управляющая компания
   венчурного фонда (УК «Восход», «контролирует инвестиционный фонд «Восход»», Коммерсантъ), а не
   ИТ-компания (docs/card_parties.md#Отрасль). review.py отказывает: словарь отраслей не знает
   «УК фонда» — отрасль ставит читатель (там же, 2 ноября 2026).
5. RETRACTED продавцов, снятых записями FIXES партии nf: g0591604d «Интеррос капитал» (в статьях
   нет), g40477661 «Александр и Рашида Марковы» (по реестру Рашида Маркова вышла 28.04.2023,
   ее доля перешла Александру Маркову; 30.05.2023 продавец — он один).

Запускать ПОСЛЕ review.py --write (assert на type и seller), затем facts_derive.py --write.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nf.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nf.py --write    # записать (из корня)
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

SUMS = [('g0591604d', 'sum', '10 млрд ₽', 'Не раскрыта'),
        ('g0591604d', 'eco.sum', '10 млрд ₽', 'Не раскрыта')]
DATES = [  # id, старая дата, новая, старый date_basis, новый
    ('g0591604d', '2023-06-06', '2023', None, None),
    ('g0cf6a562', '2022-07-31', '2022', None, None),
    ('g40477661', '2023-06-01', '2023-05-30', None, 'registry'),
]
EVENTS = [('g40477661', 'closed', '2023-05-01', '2023-05-30')]
KINDS = [('g0591604d', 'M&A', 'financing', 'acquisition')]
INDS = [('g0591604d', 'ИТ и интернет', 'Управление активами')]
RETRACT = [('g0591604d', 'sum', '10 млрд ₽'),
           ('g0591604d', 'seller', '«Интеррос капитал»'),
           ('g40477661', 'seller', 'Александр и Рашида Марковы')]


def get(d, path):
    for k in path.split('.'):
        d = (d or {}).get(k)
    return d


def put(d, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    for did, field, old, new in SUMS:
        d = deals[did]
        cur = get(d, field)
        assert cur in (old, new), '%s: %s = %r' % (did, field, cur)
        if cur != new:
            print('%s: %s %r -> %r' % (did, field, old, new))
            put(d, field, new)
    for did, old, new, old_b, new_b in DATES:
        d = deals[did]
        assert d.get('date') in (old, new), '%s: дата уже %r, ожидали %r' % (did, d.get('date'), old)
        assert d.get('date_basis') in (old_b, new_b), '%s: date_basis %r' % (did, d.get('date_basis'))
        if d.get('date') != new or d.get('date_basis') != new_b:
            print('%s: date %s -> %s, date_basis %s -> %s' % (did, d.get('date'), new, d.get('date_basis'), new_b))
            d['date'] = new
            if new_b is None:
                d.pop('date_basis', None)
            else:
                d['date_basis'] = new_b
    for did, kind, old, new in EVENTS:
        ev = [e for e in deals[did].get('events') or [] if e.get('kind') == kind]
        assert len(ev) == 1 and ev[0].get('date') in (old, new), '%s: этап %s %r' % (did, kind, ev)
        if ev[0]['date'] != new:
            print('%s: events.%s.date %s -> %s' % (did, kind, old, new))
            ev[0]['date'] = new
    for did, typ, old, new in KINDS:
        d = deals[did]
        if d.get('type') != typ:
            assert not write, '%s: type %r — сначала review.py --write' % (did, d.get('type'))
            print('%s: type все еще %r (сухой прогон до review.py --write)' % (did, d.get('type')))
        assert d.get('kind') in (old, new), '%s: kind %r' % (did, d.get('kind'))
        if d.get('kind') != new:
            print('%s: kind %s -> %s' % (did, old, new))
            d['kind'] = new
    for did, old, new in INDS:
        d = deals[did]
        assert d.get('ind') in (old, new), '%s: ind %r' % (did, d.get('ind'))
        if d.get('ind') != new:
            print('%s: ind %s -> %s' % (did, old, new))
            d['ind'] = new
    for did, field, val in RETRACT:
        d = deals[did]
        if d.get(field) == val:
            assert not write, '%s: %s все еще %r — сначала review.py --write' % (did, field, val)
            print('%s: %s все еще %r (сухой прогон до review.py --write)' % (did, field, val))
        lst = d.setdefault('retracted', {}).setdefault(field, [])
        if val not in lst:
            lst.append(val)
            print('%s: retracted.%s += %r' % (did, field, val))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
