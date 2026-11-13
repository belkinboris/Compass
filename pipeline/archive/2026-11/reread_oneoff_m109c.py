# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m109c: находка приемки `sum_is_expert_estimate` (в sum —
«N (по оценке)», а цифру называет эксперт, аналитик или консультант) — первые десять карточек;
остальные четыре и «менеджмент» Kerry — в reread_oneoff_m109cb.py.

Правило (docs/card_money.md, «Что идет в сумму», 13 ноября 2026): в sum — только цена этой
сделки; оценка эксперта или аналитика — sum и eco.sum «Не раскрыта», цифра с автором — в eco.val,
снятое значение — в retracted.sum. Цитаты источников:

g595aca8d («Кулинарная лавка»): Inc. Russia — «Гендиректор компании «INFOLine-Аналитика» Михаил
  Бурмистров оценил сделку не более чем в 100 млн руб.»; eco.val уже с автором.
g37066bfe (Reima): Profashion — «по оценкам экспертов рынка, она могла достигать 1,5–2 млрд рублей»;
  eco.val называет Малахатько (CORE.XP) и Бурмистрова.
gde280a8d (PNK Park Медведково): Коммерсантъ — «Сумма сделки может составить 5–6 млрд руб.,
  подсчитал независимый эксперт Андрей Новиков».
ge9b4ba4d (OBI): Ведомости — «Сумма последней сделки ... могла составить не более 200–300 млн руб.,
  считает генеральный директор «Infoline-аналитики» Михаил Бурмистров».
g5d9d8e6c (Qiwi): Коммерсантъ — «Forbes на основе котировок бумаг Qiwi ... отмечает, что пакет
  «Открытия» мог оцениваться в 8,85 млрд руб.» — пересчет по бирже, не цена.
gadbed4b9 («Аэродиск»): ComNews — «Аналитики оценивают стоимость сделки в 1,5-2 млрд руб.» (Тузов,
  Делицын, Чернов — в eco.val).
gd39b4eaa («Лискимонтажконструкция»): Коммерсантъ — «Промышленный эксперт Леонид Хазанов оценивает
  сумму сделки в $150–200 млн».
g6023c156 («Дикта-О»): Коммерсантъ — оценки Новикова (NF Group) и Горюнова (IBC Real Estate).
g7aad7720 («Опора Телеком»): Коммерсантъ — «Сумму сделки в ГК не раскрыли»; 2 млрд ₽ — Денис Кусков
  (TelecomDaily).
g4a53d81b (Desport): Фонтанка.ру — «Как оценивают аналитики компании [IBC Real Estate], здание Desport
  обошлось покупателю ... в 458 млн рублей» — оценка консультанта; переносится из eco.context в
  eco.val, в контексте остается, что других таких сделок за девять месяцев не было.

Запись FIXES на снятые поля: отпечаток прежнего `new` — в proofread_absorbed (docs/card_editing.md,
«Правка поля мимо таблицы синхронизирует запись»). sum_basis «estimate» при «Не раскрыта» снимается.

    python3 pipeline/archive/2026-11/reread_oneoff_m109c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m109c', '2026-11-13'
NO = 'Не раскрыта'
DEL = '__DEL__'

# id: (старая сумма, цитата, адрес)
SUMS = {
    'g595aca8d': ('До 100 млн ₽ (по оценке)',
                  'Гендиректор компании «INFOLine-Аналитика» Михаил Бурмистров оценил сделку не более чем в 100 млн '
                  'руб. — оценка аналитика, не цена; условия сделки не уточняются.',
                  'https://incrussia.ru/news/neftmagistral-bratya-karavaevy/'),
    'g37066bfe': ('1,5–2 млрд ₽ (по оценке)',
                  'Сумма сделки не уточняется, но, по оценкам экспертов рынка, она могла достигать 1,5–2 млрд рублей. '
                  '— оценка экспертов, не цена.',
                  'https://profashion.ru/business/finance/finskiy-brend-detskoy-odezhdy-reima-prodal-aktivy-v-rossii/'),
    'gde280a8d': ('5–6 млрд ₽ (по оценке)',
                  'Сумма сделки может составить 5–6 млрд руб., подсчитал независимый эксперт Андрей Новиков. '
                  '— оценка эксперта, не цена.', 'https://www.kommersant.ru/doc/5873533'),
    'ge9b4ba4d': ('200–300 млн ₽ (по оценке)',
                  'Сумма последней сделки по продаже OBI могла составить не более 200–300 млн руб., считает '
                  'генеральный директор «Infoline-аналитики» Михаил Бурмистров. — оценка аналитика, не цена.',
                  'https://www.vedomosti.ru/business/articles/2023/01/09/958271-u-obi-v-tretii-raz-smenilis-sobstvenniki'),
    'g5d9d8e6c': ('8,85 млрд ₽ (по оценке)',
                  'Forbes на основе котировок бумаг Qiwi на закрытии торгов Мосбиржи 30 декабря отмечает, что пакет '
                  '«Открытия» мог оцениваться в 8,85 млрд руб. — пересчет по бирже, не цена сделки.',
                  'https://www.kommersant.ru/doc/5826320'),
    'gadbed4b9': ('1,5–2 млрд ₽ (по оценке)',
                  'Аналитики оценивают стоимость сделки в 1,5-2 млрд руб. — оценка аналитиков, не цена.',
                  'https://www.comnews.ru/content/227045/2023-06-27/2023-w26/aerodisk-priletel-k-akvariusu'),
    'gd39b4eaa': ('$150–200 млн (по оценке)',
                  'Промышленный эксперт Леонид Хазанов оценивает сумму сделки в $150–200 млн (10–13 млрд руб. — '
                  'оценка эксперта, не цена.', 'https://www.kommersant.ru/doc/5773012'),
    'g6023c156': ('600–900 млн ₽ (по оценке)',
                  'Площадка в Нагорном проезде могла стоить около 600 млн руб., считает управляющий партнер NF Group '
                  'Алексей Новиков. Директор департамента рынков капитала и инвестиций IBC Real Estate Николай Горюнов '
                  'оценивает актив дороже — в 800–900 млн руб. — оценки консультантов, не цена.',
                  'https://www.kommersant.ru/doc/5719027'),
    'g7aad7720': ('≈2 млрд ₽ (по оценке)',
                  'Сумму сделки в ГК не раскрыли. Усредненная цена одной башни на российском рынке составляет порядка '
                  '4 млн руб., поэтому сумма сделки могла составить порядка 2 млрд руб., говорит гендиректор '
                  'TelecomDaily Денис Кусков', 'https://www.kommersant.ru/doc/5748009'),
    'g4a53d81b': ('458 млн ₽ (по оценке)',
                  'Как оценивают аналитики компании, здание Desport обошлось покупателю, ООО «Сити Капитал», в 458 млн '
                  'рублей. — оценка IBC Real Estate, не цена, названная сторонами.',
                  'https://www.fontanka.ru/2026/10/26/76725747/'),
}

FT = 'https://www.fontanka.ru/2026/10/26/76725747/'
_CTX_OLD = ('По оценке аналитиков IBC Real Estate, здание обошлось покупателю в 458 млн рублей, и таких сделок на рынке '
            'торговой недвижимости Петербурга за девять месяцев 2026 года больше не было.')
_CTX_NEW = ('По данным IBC Real Estate, других сделок на рынке торговой недвижимости Петербурга за девять месяцев '
            '2026 года не было.')

# (id, путь, старое, новое, цитата, адрес); путь с «@» — замена части текста
SETS = [
    ('g4a53d81b', 'eco.val', '—', 'По оценке аналитиков IBC Real Estate, здание обошлось покупателю в 458 млн ₽.',
     'Об этом пишет РБК со ссылкой на IBC Real Estate. Как оценивают аналитики компании, здание Desport обошлось '
     'покупателю, ООО «Сити Капитал», в 458 млн рублей.', FT),
    ('g4a53d81b', 'eco.context@', _CTX_OLD, _CTX_NEW,
     'Это — единственная сделка на рынке торговой недвижимости Петербурга за 9 месяцев 2026 года Об этом пишет РБК '
     'со ссылкой на IBC Real Estate.', FT),
]

ESTIMATE_BASIS = ('g595aca8d', 'g5d9d8e6c', 'gadbed4b9')


def _absorb(card, field, final, fixes):
    """Запись FIXES на это поле, чей new уже не совпадет с полем, — отпечаток в proofread_absorbed."""
    import review
    for r in fixes:
        if r.get('id') == card['id'] and r.get('field') == field and r.get('new') not in (None, final) \
                and isinstance(r.get('new'), str):
            box = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(r['new'])
            if fp not in box:
                box.append(fp)


def apply(data, fixes):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, (old, quote, url) in SUMS.items():
        c = by[cid]
        eco = c['eco']
        if c.get('sum') != NO:
            assert c.get('sum') == old, (cid, c.get('sum'))
            c['sum'] = NO
            box = c.setdefault('retracted', {}).setdefault('sum', [])
            if old not in box:
                box.append(old)
            fact_edit_guard.log(c, 'sum', NO, quote, url, BY, DAY)
            n += 1
        if eco.get('sum') != NO:
            assert eco.get('sum') == old, (cid, eco.get('sum'))
            eco['sum'] = NO
            fact_edit_guard.log(c, 'eco.sum', NO, quote, url, BY, DAY)
            n += 1
        if cid in ESTIMATE_BASIS and c.get('sum_basis') == 'estimate':
            del c['sum_basis']
            n += 1
        _absorb(c, 'sum', NO, fixes)
        _absorb(c, 'eco.sum', NO, fixes)
    for cid, path, old, new, quote, url in SETS:
        c = by[cid]
        part = path.endswith('@')
        top, sub = path.rstrip('@').split('.')
        o = c[top]
        cur = o.get(sub)
        if part:
            if new in cur and old not in cur:
                continue
            assert cur.count(old) == 1, (cid, path, cur)
            o[sub] = cur.replace(old, new)
        else:
            if cur == new:
                continue
            assert cur == old, (cid, path, cur)
            o[sub] = new
        fact_edit_guard.log(c, path.rstrip('@'), o[sub], quote, url, BY, DAY)
        _absorb(c, path.rstrip('@'), o[sub], fixes)
        n += 1
    return n


def main(write):
    import review
    fixes = review.load_fixes()
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data, fixes)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh, fixes)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
