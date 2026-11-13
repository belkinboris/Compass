# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m109a, вторая часть (марафон, 13 ноября 2026): сумма — оценка эксперта.

Находка приемки sum_is_expert_estimate: в sum стояло «N (по оценке)», а цифру в источнике называет
эксперт, аналитик или консультант, а не стороны и не источники о самой сделке. По решению
13 ноября 2026 (docs/card_money.md, «Что идет в сумму») sum и eco.sum — «Не раскрыта», цифра с
автором остается в eco.val, прежнее значение — в retracted.sum, sum_basis «estimate» снят.

    python3 pipeline/archive/2026-11/reread_oneoff_m109ab.py [--write]

Повторный запуск ничего не ломает: правка, у которой поле уже равно новому значению,
пропускается («уже применено»); иначе — assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m109ab', '2026-11-13'
FACT = {'date', 'title', 'status', 'sum', 'eco.sum', 'seller', 'buyer', 'buyer_name', 'target',
        'asset', 'asset_id', 'seller_id', 'stake_acquired', 'eco.share', 'law.adv', 'eco.finadv'}

# (id, путь, старое, новое, цитата, адрес); новое DROP — убрать ключ
DROP = object()
EDITS = [
    # g2b22dae9: сумма — оценка эксперта (Бурмистров (Infoline)) -> «Не раскрыта».
    ('g2b22dae9', 'sum', '2,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Стоимость сделки в компании не разглашают. Генеральный директор агентства «Infoline-Аналитика» Михаил Бурмистров оценивает ее в не менее чем 2,5 млрд рублей.',
     'https://www.kommersant.ru/doc/6865950'),
    ('g2b22dae9', 'eco.sum', '2,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Стоимость сделки в компании не разглашают. Генеральный директор агентства «Infoline-Аналитика» Михаил Бурмистров оценивает ее в не менее чем 2,5 млрд рублей.',
     'https://www.kommersant.ru/doc/6865950'),
    ('g2b22dae9', '+retracted.sum', None, '2,5 млрд ₽ (по оценке)', None, None),
    ('g2b22dae9', 'sum_basis', 'estimate', DROP, None, None),
    # g162c155f: сумма — оценка эксперта (Шумов, инвестбанкир: стоимость всего бизнеса) -> «Не раскрыта».
    ('g162c155f', 'sum', '5 млрд ₽ (по оценке)', 'Не раскрыта',
     'По оценке инвестиционного банкира Ильи Шумова, с учетом того, что у компании отсутствуют долговые обязательства, стоимость всего бизнеса могла составить около 5 млрд руб.',
     'https://www.kommersant.ru/doc/7446674'),
    ('g162c155f', 'eco.sum', '5 млрд ₽ (по оценке)', 'Не раскрыта',
     'По оценке инвестиционного банкира Ильи Шумова, с учетом того, что у компании отсутствуют долговые обязательства, стоимость всего бизнеса могла составить около 5 млрд руб.',
     'https://www.kommersant.ru/doc/7446674'),
    ('g162c155f', '+retracted.sum', None, '5 млрд ₽ (по оценке)', None, None),
    # g69437311: сумма — оценка эксперта (Авакимян («Регблок»)) -> «Не раскрыта».
    ('g69437311', 'sum', '150–250 млн ₽ (по оценке)', 'Не раскрыта',
     'Главный аналитик компании «Регблок» Анна Авакимян считает, что «объем сделки мог составить 150−250 млн руб.».',
     'https://www.sostav.ru/publication/izdatel-imadzhinariuma-kupil-kompaniyu-prostye-pravila-69652.html'),
    ('g69437311', 'eco.sum', '150–250 млн ₽ (по оценке)', 'Не раскрыта',
     'Главный аналитик компании «Регблок» Анна Авакимян считает, что «объем сделки мог составить 150−250 млн руб.».',
     'https://www.sostav.ru/publication/izdatel-imadzhinariuma-kupil-kompaniyu-prostye-pravila-69652.html'),
    ('g69437311', '+retracted.sum', None, '150–250 млн ₽ (по оценке)', None, None),
    # g15b9d8e2: сумма — оценка эксперта (Бурмистров (INFOLine)) -> «Не раскрыта».
    ('g15b9d8e2', 'sum', '300–350 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумму сделки бизнесмен разглашать не стал. По оценке гендиректора «INFOLine-Аналитики» Михаила Бурмистрова, покупка могла обойтись в 300–350 млн руб.',
     'https://www.rbc.ru/business/12/12/2025/693a82719a7947be28583811'),
    ('g15b9d8e2', 'eco.sum', '300–350 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумму сделки бизнесмен разглашать не стал. По оценке гендиректора «INFOLine-Аналитики» Михаила Бурмистрова, покупка могла обойтись в 300–350 млн руб.',
     'https://www.rbc.ru/business/12/12/2025/693a82719a7947be28583811'),
    ('g15b9d8e2', '+retracted.sum', None, '300–350 млн ₽ (по оценке)', None, None),
    # gadb5b474: сумма — оценка эксперта (Пешков (BGP Capital): стоимость актива $500 млн — $1 млрд) -> «Не раскрыта».
    ('gadb5b474', 'sum', '$500 млн (по оценке)', 'Не раскрыта',
     'По словам Ивана Пешкова, при текущих котировках золота актив может оцениваться в диапазоне от $500 млн до $1 млрд, но, вероятно, стоит ближе к нижней границе из-за удаленного расположения.',
     'https://www.kommersant.ru/doc/8100314'),
    ('gadb5b474', 'eco.sum', '$500 млн (по оценке)', 'Не раскрыта',
     'По словам Ивана Пешкова, при текущих котировках золота актив может оцениваться в диапазоне от $500 млн до $1 млрд, но, вероятно, стоит ближе к нижней границе из-за удаленного расположения.',
     'https://www.kommersant.ru/doc/8100314'),
    ('gadb5b474', '+retracted.sum', None, '$500 млн (по оценке)', None, None),
    ('gadb5b474', 'sum_basis', 'estimate', DROP, None, None),
    # g92c06203: сумма — оценка эксперта (Бурмистров (Infoline): стоимость всего бизнеса Forward) -> «Не раскрыта».
    ('g92c06203', 'sum', 'Более 1 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров считает, что стоимость всего российского бизнеса Forward могла составить не менее 1 млрд руб.',
     'https://www.kommersant.ru/doc/8497943'),
    ('g92c06203', 'eco.sum', 'Более 1 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров считает, что стоимость всего российского бизнеса Forward могла составить не менее 1 млрд руб.',
     'https://www.kommersant.ru/doc/8497943'),
    ('g92c06203', '+retracted.sum', None, 'Более 1 млрд ₽ (по оценке)', None, None),
    # g0e7acc4d: сумма — оценка эксперта (Варламова (Neo)) -> «Не раскрыта».
    ('g0e7acc4d', 'sum', '3–3,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки по покупке группой «Технониколь» компании ООО ТД ЛТМ может достигать порядка 3–3,5 млрд руб., считает партнер практики оценки бизнеса и активов консалтинговой компании Neo Елена Варламова.',
     'https://www.kommersant.ru/doc/8078553'),
    ('g0e7acc4d', 'eco.sum', '3–3,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки по покупке группой «Технониколь» компании ООО ТД ЛТМ может достигать порядка 3–3,5 млрд руб., считает партнер практики оценки бизнеса и активов консалтинговой компании Neo Елена Варламова.',
     'https://www.kommersant.ru/doc/8078553'),
    ('g0e7acc4d', '+retracted.sum', None, '3–3,5 млрд ₽ (по оценке)', None, None),
]


def _get(card, path):
    cur = card
    for p in path.split('.'):
        if cur is None:
            return None
        cur = cur[int(p)] if isinstance(cur, list) else cur.get(p)
    return cur


def _set(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur.setdefault(p, {})
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def apply(data, verbose=False):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, path, old, new, quote, url in EDITS:
        c = data['companies'][cid[1:]] if cid.startswith('@') else by[cid]
        if path.startswith('+'):
            # дописать в список (retracted.<поле>): снятое значение не вернется обогащением
            box = c.setdefault('retracted', {}).setdefault(path.split('.', 1)[1], [])
            if new not in box:
                box.append(new)
                done += 1
            continue
        cur = _get(c, path)
        if cur == new:
            if verbose:
                print('  уже применено  %s %s' % (cid, path))
            continue
        if new is DROP:
            if path not in c:
                continue
            assert cur == old, (cid, path, cur)
            del c[path]
            done += 1
            if verbose:
                print('  УБИРАЕМ  %s %s' % (cid, path))
            continue
        assert cur == old, (cid, path, cur)
        _set(c, path, new)
        if path.startswith(('eco.', 'law.', 'extra')) and path not in FACT and isinstance(old, str):
            # поле прозы правили записи FIXES: отпечаток прежнего текста — в proofread_absorbed
            fp = review.fix_fingerprint(old)
            box = c.setdefault('proofread_absorbed', {}).setdefault(path, [])
            if fp not in box:
                box.append(fp)
        if quote and path in FACT:
            fact_edit_guard.log(c, path, new, quote, url or '', BY, DAY)
        done += 1
        if verbose:
            print('  ПРАВИМ  %s %s: %r -> %r' % (cid, path, str(old)[:50], str(new)[:60]))
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
