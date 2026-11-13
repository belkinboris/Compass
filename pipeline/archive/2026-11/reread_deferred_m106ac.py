# -*- coding: utf-8 -*-
"""Вычитка, партия m106a (13 ноября 2026), часть 3: три карточки — не сделки, одна —
этап сделки. Механика — как у части 2 (reread_deferred_m106ab.py): снятие из deals,
записи таблицы правок (strip_fixes — архив и живые файлы), signals.json,
facts_discrepancies; слияние — merge_duplicate_deals_batch.Merge.

СНЯТИЕ:
  * ca7a871ee — «Ростелеком запускает венчурный фонд «Консоль» объемом 8 млрд руб.»
    (Коммерсантъ 13.06.2024: «„Ростелеком“ в 2024 году запустит венчурный фонд „Консоль“
    объемом 8 млрд руб.») — создание своего фонда, доли ни в одной компании не переходили;
    вложения фонда, если они попадут в новости, — отдельные карточки.
  * ca599969b — «Полюс рассматривал размещение GDR на Astana International Exchange»
    (Bloomberg в пересказе Коммерсанта и Forbes, 2023): «рассматривает листинг» — план
    листинга уже обращающихся акций, без размещения новых бумаг и без покупателя; карточки
    о самом листинге в базе нет. Не сделка.
  * c59db5494 — «Sk Capital запустила венчурный фонд … объемом 4 млрд руб.» (РБК, Sk.ru,
    ноябрь 2023) — создание фонда, не сделка (тот же случай, что «Консоль»).

СЛИЯНИЕ:
  * c2adff6d3 → g0fadc207 (Fusion Factor Fintech купил российский бизнес Qiwi): разделение
    бизнеса Qiwi на российский и международный — подготовка этой продажи. Frank Media
    30.06.2023: «Группа Qiwi сообщила о завершении первого этапа консолидации российских
    активов, которые практически все были переданы на баланс акционерного общества (АО)
    «КИВИ»» — сам АО «КИВИ» и продан в январе 2024 года. Внутригрупповой перевод активов
    отдельной сделкой не считается (прецедент — cfdb3878d «Ростеха», часть 2) — этап.

У c2adff6d3 есть запись в живом файле правок written_titles_g3_2026_11_01.py; файл назван
в плане рядом со скриптом, чтобы уйти в тот же коммит.

    python3 pipeline/archive/2026-11/reread_deferred_m106ac.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m106ac.py --write   # запись
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DISCREP = os.path.join(ROOT, 'pipeline', 'facts_discrepancies.json')
SIGNALS = os.path.join(ROOT, 'static', 'data', 'signals.json')
QUESTIONS = os.path.join(ROOT, 'pipeline', 'open_questions.json')
MISSING = object()

FM_QIWI = 'https://frankmedia.ru/129878?ysclid=ljmhofd7qc627147966'

REMOVE = {
    'ca7a871ee': '«Консоль»',
    'ca599969b': 'Astana International Exchange',
    'c59db5494': 'венчурный фонд',
}

MERGES = [
    {'keep': 'g0fadc207', 'drop': 'c2adff6d3',
     'reason': 'Qiwi: перевод российских активов на баланс АО «КИВИ» (июнь 2023) — подготовка продажи АО «КИВИ» Fusion Factor Fintech.',
     'add_src': [['Frank Media', FM_QIWI],
                 ['Банк России', 'https://www.cbr.ru/press/pr/?file=638441030839855571BANK_SECTOR.htm']],
     'events': [{'kind': 'other', 'date': '2023-06-30', 'title': 'Российские активы Qiwi собраны в АО «КИВИ»',
                 'note': 'Qiwi перевела российские активы, в том числе ROWI и RealWeb, на баланс АО «КИВИ»; разделить российский и международный бизнес планировалось до 30 августа 2023 года.',
                 'source': ['Frank Media', FM_QIWI]}]},
]

QUESTION_KEYS = set()
EDITS = []
ADD_SRC = []


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    obj[keys[-1]] = value


def merge_step(data, write):
    import merge_duplicate_deals_batch as mdb
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    todo, errors = [], []
    for spec in MERGES:
        if (data.get('merged') or {}).get(spec['drop']) == spec['keep']:
            continue
        m = mdb.Merge(data, spec, known_ind, known_themes)
        m.check()
        for line in m.plan:
            print(line)
        errors += m.errors
        todo.append(m)
    if errors:
        raise SystemExit('ОТКАЗ слияния: %s' % '; '.join(errors))
    for m in todo:
        m.apply()
        print('  слито %s -> %s' % (m.drop_id, m.keep_id))
    return {m.drop_id for m in todo}


def remove_step(data):
    cards = {d['id']: d for d in data['deals']}
    targets = set((data.get('merged') or {}).values())
    gone = set()
    for cid, expect in REMOVE.items():
        card = cards.get(cid)
        if card is None:
            continue
        assert expect in str(card.get('title')), (cid, card.get('title'))
        assert cid not in targets, '%s — цель слияния' % cid
        gone.add(cid)
        print('  СНИМАЕМ %s %s' % (cid, str(card.get('title'))[:80]))
    if gone:
        data['deals'] = [d for d in data['deals'] if d['id'] not in gone]
    return gone


def edit_step(data):
    cards = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new in EDITS:
        cur = get(cards[cid], field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(cards[cid], field, new)
        done += 1
    for cid, item in ADD_SRC:
        src = cards[cid].setdefault('src', [])
        if item[1] not in [s[1] for s in src if isinstance(s, list) and len(s) > 1]:
            src.append(item)
            done += 1
    return done


def _rewrite(path, fn, write):
    if not os.path.exists(path):
        return
    raw = open(path, encoding='utf-8').read()
    store = json.loads(raw)
    new, n = fn(store)
    if n:
        print('  %s: снять %d строк' % (os.path.basename(path), n))
        if write:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(new, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))


def side_files(ids, write):
    """facts_discrepancies, признаки signals.json и вопросы open_questions.json на снятые и слитые id."""
    def discrep(rows):
        kept = [r for r in rows if r.get('id') not in ids]
        return kept, len(rows) - len(kept)

    def signals(store):
        kept = [r for r in store['signals'] if r.get('deal_id') not in ids]
        n = len(store['signals']) - len(kept)
        store['signals'] = kept
        return store, n

    def questions(rows):
        kept = [r for r in rows if not (r.get('id') in ids and (not QUESTION_KEYS or r.get('key') in QUESTION_KEYS
                                                                   or not r.get('key')))]
        return kept, len(rows) - len(kept)
    _rewrite(DISCREP, discrep, write)
    _rewrite(SIGNALS, signals, write)
    _rewrite(QUESTIONS, questions, write)


def run(data, write):
    merged = merge_step(data, write)
    gone = remove_step(data)
    n = len(merged) + len(gone) + edit_step(data)
    if merged | gone:
        import merge_duplicate_deals_batch as mdb
        mdb.strip_fixes(merged | gone, write=write)
    side_files(merged | gone, write)
    return n


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    n = run(copy.deepcopy(data), write=False)
    if not n:
        print('Уже применено.')
        return 0
    if not write:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % n)
        return 0
    import mass_edit_guard
    raw = open(DATA, encoding='utf-8').read()     # перечитать прямо перед записью
    old = json.loads(raw)
    data = copy.deepcopy(old)
    run(data, write=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('Записано изменений: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
