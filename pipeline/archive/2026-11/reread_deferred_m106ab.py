# -*- coding: utf-8 -*-
"""Вычитка, партия m106a (13 ноября 2026), часть 2: три карточки — не сделки, одна —
этап сделки.

Владелец, 13 ноября 2026: «если после вычитки у тебя будут вопросы или отложенное
что-то, не жди моего ответа и постарайся сам все решить». Снятие — как
pipeline/archive/2026-11/reread_deferred_m104.py и reread_oneoff_m216b.py: карточка
уходит из deals, записи таблицы правок снимаются (merge_duplicate_deals_batch.strip_fixes —
архив и живые файлы), признаки signals.json и строки facts_discrepancies на ее id —
тоже; telegram_posts и consumed_urls остаются.

СНЯТИЕ:
  * c197ac551 — «ВЭБ.РФ выделяет 25 млрд ₽ … через «Вертикаль Инвестиции»»: ВЭБ.РФ
    зарегистрировал свой холдинг и объявил программу вложений (первый транш — 25 млрд ₽ на
    холдинги по 5–10 млрд ₽). Доли ни в одной компании не переходили; сами вложения
    программы — отдельные карточки базы (SK Capital в «Сайберус», g9cb22c51; SK Capital в
    Softline, ge9937266). Создание собственного инвестиционного холдинга — не сделка.
  * c59e65efb — «Роман Абрамович инвестировал $63 млн в европейские стартапы через Target
    Global»: вложения через фонд в десятки стартапов за 2015–2021 годы (Forbes, RB.RU:
    «Абрамович опосредованно вложил свыше $63 млн в европейских IT-«единорогов» через фонд
    Target Global») — не одна сделка, ни предмета, ни даты; к тому же до 2022 года (решение
    владельца 27 октября 2026 «база начинается с 2022 года»).
  * cfdb3878d — «Ростех создаст холдинг для импортозамещения в нефтехимии»: «Ростех»
    объединяет не менее 15 своих предприятий под «Союзхимэкспортом» (АК&М, URA.RU) —
    внутригрупповая реорганизация без смены собственника и к тому же план. Прецедент —
    приток 24 октября 2026 (присоединение «Останкино-Липецк» к «Останкино-Воронеж»:
    «внутригрупповая реорганизация без смены собственника, не сделка»).

СЛИЯНИЕ (merge_duplicate_deals_batch.Merge):
  * c7403d4db → g97679d43 («Просторы» покупают у ВТБ «Лабинский»): карточка о плане ВТБ
    создать агрохолдинг (Reuters, 01.12.2025) и о решении продать все сельхозактивы
    (Агроинвестор 08.04.2026: «ВТБ планирует продать все свои агроактивы. Об этом в кулуарах
    форума Data Fusion сказал глава ВТБ Андрей Костин»). Самый крупный из этих активов —
    «Лабинский», его продажа — g97679d43; решение ВТБ продавать — этап этой сделки.
    Вопрос vtb-agro-holding-vs-sale в pipeline/open_questions.json закрыт этим слиянием;
    признак sf662081c4 в signals.json (собран из c7403d4db) снимается.

У c7403d4db и cfdb3878d есть записи в живом файле правок written_titles_g3_2026_11_01.py;
скрипт их снимает, и файл обязан уйти в тот же коммит (он назван в плане партии рядом со
скриптом — так запись партии его добавит; запуск файла правок как скрипта ничего не делает).

    python3 pipeline/archive/2026-11/reread_deferred_m106ab.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m106ab.py --write   # запись

Повторный запуск ничего не ломает: слитое и снятое пропускается.
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

AI_SELL = 'https://www.agroinvestor.ru/companies/news/45794-vtb-reshil-prodat-agroaktivy/'

REMOVE = {
    'c197ac551': '«Вертикаль Инвестиции»',
    'c59e65efb': 'Target Global',
    'cfdb3878d': 'Ростех создаст холдинг',
}

MERGES = [
    {'keep': 'g97679d43', 'drop': 'c7403d4db',
     'reason': 'ВТБ: решение продать все сельхозактивы (апрель 2026) — этап продажи крупнейшего из них, «Лабинского», «Просторам».',
     'add_src': [['Агроинвестор', AI_SELL],
                 ['Агроинвестор', 'https://www.agroinvestor.ru/markets/news/45251-vtb-planiruet-sozdat-krupnyy-agrokholding/'],
                 ['Reuters', 'https://www.reuters.com/sustainability/boards-policy-regulation/russian-bank-vtb-create-agriculture-giant-nationalised-assets-ceo-says-2025-12-01/']],
     'events': [{'kind': 'announced', 'date': '2026-04-08', 'title': 'ВТБ решил продать все сельхозактивы',
                 'note': 'Глава ВТБ Андрей Костин объявил, что банк продаст все сельхозактивы и будет работать только в городе.',
                 'source': ['Агроинвестор', AI_SELL]}]},
]

QUESTION_KEYS = {'vtb-agro-holding-vs-sale'}
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
