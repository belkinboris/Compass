# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m109a (марафон, 13 ноября 2026): сумма — оценка эксперта.

Находка приемки sum_is_expert_estimate: в sum стояло «N (по оценке)», а цифру в источнике называет
эксперт, аналитик или консультант, а не стороны и не источники о самой сделке. По решению
13 ноября 2026 (docs/card_money.md, «Что идет в сумму») sum и eco.sum — «Не раскрыта», цифра с
автором остается в eco.val, прежнее значение — в retracted.sum, sum_basis «estimate» снят.

    python3 pipeline/archive/2026-11/reread_oneoff_m109a.py [--write]

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
BY, DAY = 'reread_oneoff_m109a', '2026-11-13'
FACT = {'date', 'title', 'status', 'sum', 'eco.sum', 'seller', 'buyer', 'buyer_name', 'target',
        'asset', 'asset_id', 'seller_id', 'stake_acquired', 'eco.share', 'law.adv', 'eco.finadv'}

# (id, путь, старое, новое, цитата, адрес); новое DROP — убрать ключ
DROP = object()
EDITS = [
    # g8cf8098f: сумма — оценка эксперта (Бурмистров (INFOLine) оценил весь бизнес «Татспиртпрома»; неофициальные цены расходятся (около 9 млрд ₽ у «БИЗНЕС Online», до 20 млрд ₽ у источника РБК) — обе остаются в eco.val) -> «Не раскрыта».
    ('g8cf8098f', 'sum', '20–25 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор агентства «INFOLline-Аналитика» Михаил Бурмистров в комментарии «Коммерсанту» оценил бизнес «Татспиртпрома» в 20–25 млрд рублей.',
     'https://www.business-gazeta.ru/article/689191'),
    ('g8cf8098f', 'eco.sum', '20–25 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор агентства «INFOLline-Аналитика» Михаил Бурмистров в комментарии «Коммерсанту» оценил бизнес «Татспиртпрома» в 20–25 млрд рублей.',
     'https://www.business-gazeta.ru/article/689191'),
    ('g8cf8098f', '+retracted.sum', None, '20–25 млрд ₽ (по оценке)', None, None),
    # ge6e9c77a: сумма — оценка эксперта (Бурмистров (Infoline) о стоимости сети) -> «Не раскрыта».
    ('ge6e9c77a', 'sum', '200–300 млн ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров предполагает, что стоимость сети могла варьироваться в диапазоне от 200 млн до 300 млн руб.',
     'https://mergers.ru/news/Set-kofeen-One-Double-pereshla-pod-kontrol-fonda-Bumerang-Kapital-87101'),
    ('ge6e9c77a', 'eco.sum', '200–300 млн ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров предполагает, что стоимость сети могла варьироваться в диапазоне от 200 млн до 300 млн руб.',
     'https://mergers.ru/news/Set-kofeen-One-Double-pereshla-pod-kontrol-fonda-Bumerang-Kapital-87101'),
    ('ge6e9c77a', '+retracted.sum', None, '200–300 млн ₽ (по оценке)', None, None),
    # g18fd392a: сумма — оценка эксперта (эксперты «Ведомостей» без имен) -> «Не раскрыта».
    # Оценка без имени — назвать, чьи это эксперты (Sostav: «По словам экспертов… Об этом пишут «Ведомости»»).
    ('g18fd392a', 'eco.val', 'Сумму стороны не раскрывали; по оценке экспертов, она могла составить 330–500 млн ₽.',
     'Сумму стороны не раскрывали; по оценке экспертов, опрошенных «Ведомостями», она могла составить 330–500 млн ₽.', None, None),
    ('g18fd392a', 'sum', '330–500 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки не раскрывается. По словам экспертов, она могла составить 330−500 млн руб.',
     'https://www.sostav.ru/publication/prosveshchenie-poluchilo-kontrol-v-onlajn-shkole-karpov-courses-83687.html'),
    ('g18fd392a', 'eco.sum', '330–500 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки не раскрывается. По словам экспертов, она могла составить 330−500 млн руб.',
     'https://www.sostav.ru/publication/prosveshchenie-poluchilo-kontrol-v-onlajn-shkole-karpov-courses-83687.html'),
    ('g18fd392a', '+retracted.sum', None, '330–500 млн ₽ (по оценке)', None, None),
    # ge386fb20: сумма — оценка эксперта (расчет Левицкого (BGP Capital): сады плюс долг) -> «Не раскрыта».
    ('ge386fb20', 'sum', '1,8 млрд ₽ (по оценке)', 'Не раскрыта',
     'По оценке инвестиционного директора BGP Capital Юрия Левицкого, рыночная стоимость садов составляет 1–1,3 млрд руб., остальная сумма объясняется учетом долгов компании.',
     'https://www.kommersant.ru/doc/8477794'),
    ('ge386fb20', 'eco.sum', '1,8 млрд ₽ (по оценке)', 'Не раскрыта',
     'По оценке инвестиционного директора BGP Capital Юрия Левицкого, рыночная стоимость садов составляет 1–1,3 млрд руб., остальная сумма объясняется учетом долгов компании.',
     'https://www.kommersant.ru/doc/8477794'),
    ('ge386fb20', '+retracted.sum', None, '1,8 млрд ₽ (по оценке)', None, None),
    # g94683ed2: сумма — оценка эксперта (Бурмистров (Infoline), с учетом долга) -> «Не раскрыта».
    ('g94683ed2', 'sum', '5–6 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров полагает, что стоимость сделки с учетом долга составила 5–6 млрд руб.',
     'https://www.kommersant.ru/doc/8292342'),
    ('g94683ed2', 'eco.sum', '5–6 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров полагает, что стоимость сделки с учетом долга составила 5–6 млрд руб.',
     'https://www.kommersant.ru/doc/8292342'),
    ('g94683ed2', '+retracted.sum', None, '5–6 млрд ₽ (по оценке)', None, None),
    ('g94683ed2', 'sum_basis', 'estimate', DROP, None, None),
    # g68975b9d: сумма — оценка эксперта (Бурмистров (Infoline)) -> «Не раскрыта».
    ('g68975b9d', 'sum', '30–40 млрд ₽ (по оценке)', 'Не раскрыта',
     'Сопоставимые компании на российском рынке торгуются сейчас с мультипликаторами около 4–5 EBITDA, однако сумму сделки эксперт оценивает в широком диапазоне — от 30 млрд до 40 млрд руб.',
     'https://www.kommersant.ru/doc/7959262'),
    ('g68975b9d', 'eco.sum', '30–40 млрд ₽ (по оценке)', 'Не раскрыта',
     'Сопоставимые компании на российском рынке торгуются сейчас с мультипликаторами около 4–5 EBITDA, однако сумму сделки эксперт оценивает в широком диапазоне — от 30 млрд до 40 млрд руб.',
     'https://www.kommersant.ru/doc/7959262'),
    ('g68975b9d', '+retracted.sum', None, '30–40 млрд ₽ (по оценке)', None, None),
    # gbc0b68bd: сумма — оценка эксперта (Бурмистров (INFOLine) о стоимости актива) -> «Не раскрыта».
    ('gbc0b68bd', 'sum', 'До 150 млн ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «INFOLine-аналитики» Михаил Бурмистров оценил стоимость актива в сумму не более 150 млн руб.',
     'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'),
    ('gbc0b68bd', 'eco.sum', 'До 150 млн ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор «INFOLine-аналитики» Михаил Бурмистров оценил стоимость актива в сумму не более 150 млн руб.',
     'https://www.retail.ru/news/kompaniya-faberlik-prodala-fabriku-po-poshivu-odezhdy-strukture-voentorga-21-aprelya-2025-263762/'),
    ('gbc0b68bd', '+retracted.sum', None, 'До 150 млн ₽ (по оценке)', None, None),
    ('gbc0b68bd', 'sum_basis', 'estimate', DROP, None, None),
    # g181d7687: сумма — оценка эксперта (Делицын («Финам»)) -> «Не раскрыта».
    ('g181d7687', 'sum', '100 млн ₽ (по оценке)', 'Не раскрыта',
     'Аналитик ФГ "Финам" Леонид Делицын оценил сделку и предположил, во сколько могут обойтись в дальнейшем оставшиеся 62% долей "КБ Борей": Состоявшуюся сделку можно оценить в 100 млн руб.',
     'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
    ('g181d7687', 'eco.sum', '100 млн ₽ (по оценке)', 'Не раскрыта',
     'Аналитик ФГ "Финам" Леонид Делицын оценил сделку и предположил, во сколько могут обойтись в дальнейшем оставшиеся 62% долей "КБ Борей": Состоявшуюся сделку можно оценить в 100 млн руб.',
     'https://www.comnews.ru/content/237587/2025-02-05/2025-w06/1007/yadro-priobrela-38-doley-kb-borey'),
    ('g181d7687', '+retracted.sum', None, '100 млн ₽ (по оценке)', None, None),
    ('g181d7687', 'sum_basis', 'estimate', DROP, None, None),
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


GOLD = os.path.join(ROOT, 'pipeline', 'gold', 'analytics_gold.json')
GOLD_WHY = ('Сумма «Не раскрыта»: 30–40 млрд ₽ — оценка эксперта (Бурмистров, Infoline, в «Ъ»), стороны цену '
            'не называли; оценка — в eco.val (docs/card_money.md, «Что идет в сумму», 13 ноября 2026); куплен '
            'весь холдинг — 100% (вычитка 10 ноября 2026 по рэнкингу «Ъ» и The Bell)')


def gold_fix():
    """Строка золотой выборки g68975b9d: сумма снята, смысл суммы — undisclosed."""
    raw = open(GOLD, encoding='utf-8').read()
    gold = json.loads(raw)
    rows = gold if isinstance(gold, list) else next(v for v in gold.values() if isinstance(v, list))
    row = next(r for r in rows if r.get('id') == 'g68975b9d')
    if row['sum_basis'] == 'undisclosed':
        return
    assert row['sum_basis'] == 'range', row
    row['sum_basis'], row['why'] = 'undisclosed', GOLD_WHY
    with open(GOLD, 'w', encoding='utf-8') as f:
        f.write(json.dumps(gold, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('Золотая выборка: g68975b9d sum_basis range -> undisclosed.')


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
    gold_fix()
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
