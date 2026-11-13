# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m109bb (13 ноября 2026): оценка эксперта в сумме сделки.

Находка приемки `sum_is_expert_estimate`: в sum и eco.sum стояло «N (по оценке)», а цифру в
источнике называет эксперт, аналитик или консультант, а не стороны и не источник о самой
сделке. Решение 13 ноября 2026 (docs/card_money.md, раздел «Что идет в сумму»): в sum — только
цена этой сделки; оценка эксперта — «Не раскрыта», цифра с автором остается в eco.val
(во всех карточках ниже она там уже есть), прежнее значение — в retracted.sum. Цитата у каждой
правки — слова источника, по которым видно, что цифру назвал эксперт.


review.py «Не раскрыта» не принимает — поэтому разовый скрипт.

    python3 pipeline/archive/2026-11/reread_oneoff_m109bb.py [--write]

Повторный запуск ничего не ломает: уже снятая сумма пропускается; иначе — assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
BY, DAY = "reread_oneoff_m109bb", "2026-11-13"
N = "Не раскрыта"

# (id, старая сумма, новая, sum_basis или None, цитата, адрес)
EDITS = [
    ('gc9a9d929', '≈300 млн ₽ (по оценке)', N, None,
     'По оценке гендиректора «Infoline-аналитики» Михаила Бурмистрова, сделка могла обойтись примерно в 300 млн руб.',
     'https://www.kommersant.ru/doc/7432236'),
    ('gad4a5636', '200–300 млн ₽ (по оценке)', N, None,
     'По оценке партнера экспертной группы Veta Дмитрия Жарского, покупка «Мебели Черноземья» могла обойтись «Ангстрему» в 200–300 млн руб.',
     'https://www.kommersant.ru/doc/6852638'),
    ('g8e78bbb2', 'До 200 млн ₽ (по оценке)', N, None,
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров предполагает, что «Технониколь» со временем выкупит и оставшуюся долю. Стоимость Scandic Construction, по его мнению, составила не более 200 млн руб.',
     'https://www.kommersant.ru/doc/6820661'),
    ('g8b512496', '700–850 млн ₽ (по оценке)', N, None,
     'Эксперты оценивают стоимость сделки в 700–850 млн рублей',
     'https://www.kommersant.ru/doc/6444215'),
    ('g81163284', '$20–50 млн (по оценке)', N, None,
     'Аналитики оценивали сумму сделки в диапазоне $20–50 млн.',
     'https://vademec.ru/news/2023/06/07/blizkaya-k-vmp-struktura-kupila-rossiyskiy-zavod-zm/'),
]


def _get(card, path):
    cur = card
    for p in path.split('.'):
        if cur is None:
            return None
        cur = cur.get(p)
    return cur


def _set(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def apply(data, verbose=False):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, old, new, basis, quote, url in EDITS:
        c = by[cid]
        if c.get('sum') == new and _get(c, 'eco.sum') == new:
            if verbose:
                print('  уже применено  %s' % cid)
            continue
        assert c.get('sum') == old, (cid, 'sum', c.get('sum'))
        assert _get(c, 'eco.sum') == old, (cid, 'eco.sum', _get(c, 'eco.sum'))
        for path in ('sum', 'eco.sum'):
            _set(c, path, new)
            # прежние записи таблицы правок на это поле погашены отпечатком прежнего значения
            box = c.setdefault('proofread_absorbed', {}).setdefault(path, [])
            fp = review.fix_fingerprint(old)
            if fp not in box:
                box.append(fp)
            fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        if basis and c.get('sum_basis') != basis:
            c['sum_basis'] = basis
            fact_edit_guard.log(c, 'sum_basis', basis, quote, url, BY, DAY)
        box = c.setdefault('retracted', {}).setdefault('sum', [])
        if old not in box:
            box.append(old)
        done += 1
        if verbose:
            print('  ПРАВИМ  %s sum: %r -> %r' % (cid, old, new))
    return done


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data, verbose=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    if not n:
        print('Все правки уже применены.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
