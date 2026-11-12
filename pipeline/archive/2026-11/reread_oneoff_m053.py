# -*- coding: utf-8 -*-
"""Вычитка, партия m053 (марафон 12 ноября 2026): правки, которые review.py не принимает.

Дата по реестру (день записи ЕГРЮЛ, а не день пресс-релиза), «Не раскрыта» и прочее, что таблица
правок не пишет. Каждая правка факта — с цитатой (fact_edit_guard.log). Тексты статей сохранены
save_source.save(..., day='2026-11-12_m053').

g38129341 МТС / «СКАУТ-КР»: по ЕГРЮЛ доля МТС выросла с 15% до 51% записью 26.04.2023 (пресс-релиз —
  27 апреля): дата по реестру.
ga8cb5cab «Руском» / «Восходагро»: 300–400 млн ₽ — оценка эксперта Veta («Коммерсантъ»), а не цена: сумма
  «Не раскрыта», оценка — в eco.val (таблица правок).

    python3 pipeline/archive/2026-11/reread_oneoff_m053.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
os.environ.pop('REVIEW_ONLY', None)   # нужны ВСЕ записи таблицы правок: их отпечатки уходят в proofread_absorbed
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY, BY = '2026-11-12', 'reread_oneoff_m053'
FIXES = review.load_fixes()

DN = 'https://datanewton.ru/contragents/%s/history/timeline'


def absorb(card, field, new):
    """Прежние записи таблицы правок на это поле признаются примененными (docs/card_editing.md)."""
    marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    for r in FIXES:
        if r.get('id') == card['id'] and r.get('field') == field and r.get('new') is not None and r['new'] != new:
            fp = review.fix_fingerprint(r['new'])
            if fp not in marks:
                marks.append(fp)
    if not marks:
        card['proofread_absorbed'].pop(field)
    if not card['proofread_absorbed']:
        card.pop('proofread_absorbed')


def put(card, field, old, new, quote=None, url=None):
    """Поле: assert на старое (точно или началом — «старт:...»), запись, отпечатки, цитата факта."""
    cur = fact_edit_guard.get(card, field)
    if cur == new:
        return
    if isinstance(old, str) and old.startswith('старт:'):
        assert isinstance(cur, str) and cur.startswith(old[6:]), (card['id'], field, cur)
    else:
        assert cur == old, (card['id'], field, cur)
    if '.' in field:
        head, tail = field.split('.', 1)
        card.setdefault(head, {})[tail] = new
    elif new is None:
        card.pop(field, None)
    else:
        card[field] = new
    absorb(card, field, new)
    if field in fact_edit_guard.FACT_FIELDS:
        assert quote and url, (card['id'], field)
        fact_edit_guard.log(card, field, new, quote, url, BY, DAY)


def drop_src(card, url):
    before = len(card['src'])
    card['src'] = [s for s in card['src'] if s[1] != url]
    if len(card['src']) != before:
        marks = card.setdefault('proofread_absorbed', {}).setdefault('src', [])
        fp = review.fix_fingerprint(url)
        if any(r.get('id') == card['id'] and r.get('field') == 'src' and r['new'][1] == url for r in FIXES) \
                and fp not in marks:
            marks.append(fp)
        if not marks:
            card['proofread_absorbed'].pop('src')
        if not card['proofread_absorbed']:
            card.pop('proofread_absorbed')


def add_src(card, label, url, first=False):
    if any(s[1] == url for s in card['src']):
        return
    if first:
        card['src'].insert(0, [label, url])
    else:
        card['src'].append([label, url])


def note(card, role, text):
    card.setdefault('accepted_notes', {}).setdefault('no_profile', {})[role] = text


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def legal(comps, cid, short):
    if comps[cid].get('legal_short') != short:
        comps[cid]['legal_short'] = short


# ---------------------------------------------------------------------------------------------


def mts(card, comps):
    REG = DN % '1167847162120'
    q = ('ЕГРЮЛ, участники ООО "ПРОЕКТНАЯ СРЕДА" (ИНН 7820047859), запись 2023-04-26: ПАО "МТС" 15 -> 51%, '
         'Висневская Мария Алексеевна 76,5 -> 44,1%, Висневский Юрий Алексеевич 8,5 -> 4,9%.')
    put(card, 'date', '2023-04-27', '2023-04-26', q, REG)
    put(card, 'date_basis', 'publication', 'registry')



def voskhod(card, comps):
    K = 'https://www.kommersant.ru/doc/5928509'
    q = ('Партнер экспертной группы Veta Александр Терентьев … Возможную стоимость сделки он оценивает в 300–400 млн '
         'руб. в зависимости от состояния поголовья скота и других факторов производства')
    put(card, 'sum', '300–400 млн ₽ (по оценке)', 'Не раскрыта', q, K)
    put(card, 'eco.sum', '300–400 млн ₽ (по оценке)', 'Не раскрыта', q, K)


PLAN = {
    'g38129341': mts,
    'ga8cb5cab': voskhod,
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    for cid, fn in PLAN.items():
        card = by[cid]
        if any(e.get('by') == BY for e in card.get('fact_log') or []):
            continue          # уже применено: повторный запуск ничего не меняет
        fn(card, data['companies'])


GOLD = os.path.join(ROOT, 'pipeline', 'gold', 'analytics_gold.json')


def side_files():
    """Золотая выборка идет вслед за правкой карточки. g4764cf2b: «Предмет» теперь называет купленный
    пакет — 28,98% MLU B.V. («Коммерсантъ», «Интерфакс»: «Яндекс» купил оставшиеся 28,98%)."""
    gold = json.load(open(GOLD, encoding='utf-8'))
    for row in gold['deals']:
        if row['id'] == 'g4764cf2b' and row.get('share') is None:
            row['title'] = '«Яндекс» купил 28,98% MLU B.V. у Uber'
            row['share'] = 28.98
            row['why'] += ' 12 ноября 2026 (вычитка m053): купленный пакет назван в «Предмете» — 28,98%.'
    with open(GOLD, 'w', encoding='utf-8') as f:
        f.write(json.dumps(gold, ensure_ascii=False, indent=1) + '\n')


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    apply(data)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    by = {d['id']: d for d in data['deals']}
    for cid in PLAN:
        print(cid, by[cid]['title'], by[cid]['date'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    side_files()
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
