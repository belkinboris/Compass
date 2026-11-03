# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партия nc): то, что review.py не умеет.

1. СУММА gad633118 («Каталитик Пипл»/Selectel): «16 млрд ₽ (по оценке)» и «Оценивается примерно
   в 16 млрд руб.» → «≈16 млрд ₽» в обоих полях. Цену назвали сами стороны (сообщение Т-Банка,
   Sostav: «Полная стоимость 25% акций в уставном капитале компании составит около 16 млрд
   руб.»; AK&M, РИА — то же), а «оценивается» — пересказ «Ведомостей» в CNews; пометка «(по
   оценке)» неверна (docs/card_money.md). review.py «≈» без «(по оценке)» не разбирает. Записи
   прежних значений лежат в архиве (batch_a_2025) — их отпечатки кладутся в proofread_absorbed.
2. LEGAL_SHORT (находки приемки party_legal_form): party_legal_names.py для «Каталитик Пипл»
   формы не дал («→ —»), для «Роснефть — Артаг» предложил сломанное «АО «НК "роснефть"- Артаг»» —
   вручную по реестру (/api/companies/<id>/fns): МКООО "КАТАЛИТИК ПИПЛ", АО "НК "РОСНЕФТЬ"- АРТАГ".
3. DESC профилей:
   - «Каталитик Пипл»: «купило 25% акций Selectel у структур Мирилашвили и Вермишяна» — структур
     Мирилашвили среди продавцов нет ни в одной статье (Selectel в CNews, Interfax, White Square:
     «у инвестиционных структур Геворка Вермишяна и прочих акционеров»).
   - Prosto Barista: «в 2026 году поглощена сетью «Точка Черного»» — все статьи (19–22 декабря
     2025) пишут «выкупит до конца года», закрытия ни одна не подтверждает, и год не тот.
4. ИМЯ профиля gd4a7c612 «ООО «Селектел»» — неверная форма: по реестру АО «Селектел» (ИНН
   7810962785, legal_short уже стоит), в статьях — бренд Selectel. Переименование на месте
   (docs/company_profiles.md, «Обрывок заголовка чинится переименованием на месте»): тот же id и
   те же 6 сделок; близнеца нет (поиск «селектел/selectel» по именам и описаниям: Servertech,
   Tier 5, «Единая сеть», «Каталитик Пипл» — другие компании), в match_keys имени нет.
5. KIND g9cb22c51 (SK Capital/«Сайберус»): тип стал «Инвестиция» записью FIXES партии nc (доля «в
   обмен на инвестиции», деньги идут в фонд) — kind «acquisition» → «financing», как у других
   раундов базы.

После записи — python3 pipeline/facts_derive.py --write.

    python3 <этот файл>            # сухой прогон
    python3 <этот файл> --write    # записать (из корня репозитория, после review.py --write)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SUMS = [  # id, поле, старое, новое
    ('gad633118', 'sum', '16 млрд ₽ (по оценке)', '≈16 млрд ₽'),
    ('gad633118', 'eco.sum', 'Оценивается примерно в 16 млрд руб.', '≈16 млрд ₽'),
]
LEGAL = [  # профиль, имя (для сверки), legal_short
    ('g62dd02d2', 'Каталитик Пипл', 'МКООО «Каталитик Пипл»'),
    ('ge0d53bd2', 'Роснефть — Артаг', 'АО «НК „Роснефть“ — Артаг»'),
]
DESC = [
    ('g62dd02d2',
     'СП Т-Технологий и Интерроса; в 2025 году купило 25% акций Selectel у структур Мирилашвили и '
     'Вермишяна.',
     'Совместное предприятие «Т-Технологий» и «Интерроса» для вложений в технологические компании; '
     'в 2025 году купило 25% акций Selectel.'),
    ('gprostobarista',
     'Сеть кофеен самообслуживания (более 1000 точек в России и СНГ); в 2026 году поглощена сетью '
     '«Точка Черного».',
     'Сеть кофеен самообслуживания: больше 1000 точек в России и СНГ.'),
]
RENAME = [('gd4a7c612', 'ООО «Селектел»', 'Selectel')]
KIND = [('g9cb22c51', 'Инвестиция', 'acquisition', 'financing')]


def get(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        return (card.get(a) or {}).get(b)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        a, b = field.split('.', 1)
        card.setdefault(a, {})[b] = value
    else:
        card[field] = value


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for did, field, old, new in SUMS:
        d = deals[did]
        cur = get(d, field)
        assert cur in (old, new), '%s.%s: %r, ожидали %r' % (did, field, cur, old)
        if cur != new:
            print('%s.%s: %r -> %r' % (did, field, cur, new))
            put(d, field, new)
        fp = review.fix_fingerprint(old)
        lst = d.setdefault('proofread_absorbed', {}).setdefault(field, [])
        if fp not in lst:
            lst.append(fp)
            print('%s: proofread_absorbed.%s += %s' % (did, field, fp))
    for cid, name, legal in LEGAL:
        p = comps[cid]
        assert p.get('name') == name, '%s: имя %r' % (cid, p.get('name'))
        assert p.get('legal_short') in (None, legal), '%s: legal_short уже %r' % (cid, p.get('legal_short'))
        if p.get('legal_short') != legal:
            print('%s: legal_short -> %s' % (cid, legal))
            p['legal_short'] = legal
    for cid, old, new in DESC:
        p = comps[cid]
        assert p.get('desc') in (old, new), '%s: desc %r' % (cid, p.get('desc'))
        if p['desc'] != new:
            print('%s: desc -> %s' % (cid, new))
            p['desc'] = new
    for cid, old, new in RENAME:
        p = comps[cid]
        assert p.get('name') in (old, new), '%s: имя %r' % (cid, p.get('name'))
        if p['name'] != new:
            print('%s: name %s -> %s' % (cid, p['name'], new))
            p['name'] = new
    for did, typ, old, new in KIND:
        d = deals[did]
        assert d.get('kind') in (old, new), '%s: kind %r' % (did, d.get('kind'))
        if d.get('type') != typ:
            assert not write, '%s: тип %r — сначала review.py --write' % (did, d.get('type'))
            print('%s: тип еще %r (сухой прогон до review.py --write)' % (did, d.get('type')))
        if d.get('kind') != new:
            print('%s: kind %s -> %s' % (did, d.get('kind'), new))
            d['kind'] = new
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
