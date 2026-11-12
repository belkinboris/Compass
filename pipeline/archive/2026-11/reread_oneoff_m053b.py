# -*- coding: utf-8 -*-
"""Вычитка, партия m053, вторая часть (марафон 12 ноября 2026): правки, которые review.py не принимает.

gc9e8bb60 Marcegaglia / SSD: дата 2023-04-01 (заглушка) → 2023-04-21, день закрытия (пресс-релиз
  Marcegaglia «April 21, 2023», «Коммерсантъ» 21.04.2023).
gf219222a разделение Group-IB: дата 2023-04-01 (заглушка) → 2023-04-20 — день, на который Group-IB объявила
  финальный этап разделения (CNews, Интерфакс).
g68500c4a «Мосэлектрощит» / УТЗ: дня сделки нет ни в одном источнике («на прошлой неделе» в заметке
  14 апреля) — дата годом; около 10 млрд ₽ — со слов источников «Коммерсанта», «(по оценке)».
g0bbefe0f Новиков / «Литнет»: 500 млн ₽ — расчет от неофициальной оценки всего сервиса в 1 млрд ₽,
  сумма «официально не раскрывалась» («Ведомости», 2024) — «Не раскрыта».

    python3 pipeline/archive/2026-11/reread_oneoff_m053b.py [--write]
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
DAY, BY = '2026-11-12', 'reread_oneoff_m053b'
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


def marc(card, comps):
    U = ('https://www.marcegaglia.com/officialwebsite/wp-content/uploads/2023/05/'
         '21.04.2023-MARCEGAGLIA-CLOSED-PURCHASE-OF-SSD-TODAY-MARCEGAGLIA-BALTICS.pdf')
    q = ('Gazoldo degli Ippoliti, April 21, 2023 - Marcegaglia Carbon Steel signed the purchase of 100% of Sia Severstal '
         'Distribution (SSD)')
    put(card, 'date', '2023-04-01', '2023-04-21', q, U)
    put(card, 'date_basis', None, 'closing')


def gib(card, comps):
    U = 'https://www.cnews.ru/news/top/2023-04-20_group-ibosnovatel_kotoroj'
    q = '«По состоянию на 20 апреля 2023 г. в России больше не работают сотрудники Group-IB, – сообщается на сайте компании.'
    put(card, 'date', '2023-04-01', '2023-04-20', q, U)
    put(card, 'date_basis', None, 'closing')


def utz(card, comps):
    U = 'https://www.dp.ru/a/2023/04/14/renova-prodala-krupnejsh'
    q = 'Как пишет издание со ссылкой на источники, сделка по покупке крупнейшего производителя паровых турбин в РФ была совершена на прошлой неделе.'
    put(card, 'date', '2023-04-01', '2023', q, U)
    E = 'https://eanews.ru/ekaterinburg/20230414125505/smi-renova-prodala-uralskiy-turbinnyy-zavod-moskovskomu-predpriyatiyu-bankrotu'
    qs = 'Стоимость сделки составила около 10 млрд руб, сообщает «КоммерсантЪ» со ссылкой на свои источники.'
    put(card, 'sum', 'Около 10 млрд ₽', 'Около 10 млрд ₽ (по оценке)', qs, E)
    put(card, 'eco.sum', 'Около 10 млрд ₽', 'Около 10 млрд ₽ (по оценке)', qs, E)


def litnet(card, comps):
    U = 'https://www.vedomosti.ru/media/news/2024/10/29/1071663-knizhnie-servisi'
    q = 'В апреле 2023 г. контроль в «Литнете» (51%) получил совладелец крупнейшей в России издательской группы «Эксмо-АСТ» Новиков. Сумма сделки официально не раскрывалась.'
    put(card, 'sum', '500 млн ₽ (по оценке)', 'Не раскрыта', q, U)
    put(card, 'eco.sum', '500 млн ₽ (по оценке)', 'Не раскрыта', q, U)


PLAN = {
    'gc9e8bb60': marc,
    'gf219222a': gib,
    'g68500c4a': utz,
    'g0bbefe0f': litnet,
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    for cid, fn in PLAN.items():
        card = by[cid]
        if any(e.get('by') == BY for e in card.get('fact_log') or []):
            continue          # уже применено: повторный запуск ничего не меняет
        fn(card, data['companies'])


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    apply(data)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    by = {d['id']: d for d in data['deals']}
    for cid in PLAN:
        print(cid, by[cid]['title'], by[cid]['date'], by[cid].get('sum'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
