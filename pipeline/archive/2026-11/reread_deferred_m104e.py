# -*- coding: utf-8 -*-
"""Вычитка, партия m104 (13 ноября 2026), часть 5: добавка координатора из партии m210 —
два этапа известных сделок и четыре карточки, которые не описывают сделку.

СЛИЯНИЯ (этап сделки, docs/base_duplicates.md; merge_duplicate_deals_batch.Merge):
  * c3bdd7fd4 → g94683ed2 («Рив Гош» / Wildberries & Russ): залог 100% долей ООО
    «Аромалюкс» и ООО «Ароматех» в пользу ООО «РВБ» — шаг той же покупки сети. Год —
    2025, а не 2024: Интерфакс опубликовал новость 2 октября 2025 года, «договоры
    залога действуют с 23 сентября, следует из ЕГРЮЛ» — этап 2025-09-23.
  * caeac8f4e → g323cf076 (Raven Russia / «Белая скала»): выставление портфеля на
    продажу за 90,09 млрд ₽ (Коммерсантъ, 29.10.2025) — этап торгов, которые выиграла
    «Белая скала»; этап — день карточки 2025-10-28.

СНЯТИЕ (как в части 1 — карточка уходит из deals, записи правок снимаются):
  * cc0e7565f — «Б1 оценила бизнес Russ в 460–500 млрд ₽»: оценка аудитора, сделки нет.
  * c2397cc97 — «Инвитро» готова выкупать медофисы у франчайзи (Ведомости, 11.07.2024):
    программа выкупа без конкретной сделки, сторон и предмета.
  * c6a6cb6ee — MTS StartUp Hub запускает акселератор и вложит до $5 млн в выпускников
    (Ведомости, 19.04.2024): запуск программы, доли никто не покупал.
  * c4534c6d1 — «Самолет» обратился за господдержкой и предложил государству пакет с
    правом обратного выкупа (Интерфакс, 04.02.2026): письмо-предложение, сделки нет
    (тот же класс, что снятое «предложение акционеров Альфа-Банка Украина»).
  Карточка cdbb80afb (план ФРИИ вложить до 3 млрд ₽ в 15 стартапов — тоже не сделка)
  снимается частью 4 (reread_deferred_m104d.py): у нее запись в чужом живом файле правок.

    python3 pipeline/archive/2026-11/reread_deferred_m104e.py [--write]
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
BY = 'вычитка m104'
MISSING = object()

IFX_RG = 'https://www.interfax.ru/business/1050425'
KOM_RAVEN = 'https://www.kommersant.ru/doc/8160509'

MERGES = [
    {'keep': 'g94683ed2', 'drop': 'c3bdd7fd4',
     'reason': 'Залог 100% долей операционных компаний «Рив Гош» в пользу ООО «РВБ» — этап покупки сети Wildberries & Russ.',
     'add_src': [['Интерфакс', IFX_RG]],
     'events': [{'kind': 'other', 'date': '2025-09-23',
                 'title': 'ООО «РВБ» получило в залог 100% долей «Аромалюкса» и «Ароматеха»',
                 'note': 'Договоры залога действуют с 23 сентября, следует из ЕГРЮЛ.',
                 'source': ['Интерфакс', IFX_RG]}]},
    {'keep': 'g323cf076', 'drop': 'caeac8f4e',
     'reason': 'Выставление портфеля Raven Russia на продажу — этап торгов, которые выиграла «Белая скала».',
     'add_src': [['Коммерсантъ', KOM_RAVEN]],
     'events': [{'kind': 'announced', 'date': '2025-10-28',
                 'title': 'Портфель Raven Russia выставлен на продажу за 90,09 млрд рублей',
                 'note': 'Начальная цена 90,09 млрд ₽ при рыночной оценке 120–160 млрд ₽.',
                 'source': ['Коммерсантъ', KOM_RAVEN]}]},
]

REMOVE = {
    'cc0e7565f': 'оценила бизнес Russ',
    'c2397cc97': 'выкупает медицинские офисы',
    'c6a6cb6ee': 'акселератор',
    'c4534c6d1': '«Самолет»',
}

EDITS = []

# test_assistant_retrieval.py::test_price_questions_are_not_deal_counts закреплял ответ карточкой
# cc0e7565f (оценка Russ от Б1). Карточка снята как не сделка; проверка намерения вопроса
# («во сколько» — о цене, а не счет сделок) остается, привязка к снятой карточке — нет.
TEST = os.path.join(ROOT, 'test_assistant_retrieval.py')
TEST_OLD = '    assert r.intent != "count" and r.docs[0].id == "cc0e7565f", [d.title for d in r.docs[:2]]\n'
TEST_NEW = ('    # карточка cc0e7565f (оценка Russ от Б1) снята как не сделка — вычитка m104, 13 ноября 2026\n'
            '    assert r.intent != "count", [d.title for d in r.docs[:2]]\n')


def test_apply(write):
    text = open(TEST, encoding='utf-8').read()
    if TEST_NEW in text:
        return 0
    assert text.count(TEST_OLD) == 1, 'строка с cc0e7565f в test_assistant_retrieval.py не найдена'
    if write:
        open(TEST, 'w', encoding='utf-8').write(text.replace(TEST_OLD, TEST_NEW))
    print('  test_assistant_retrieval.py: снята привязка к карточке cc0e7565f')
    return 1
RETRACT = []
COMPANY_EDITS = []


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
    if value is MISSING:
        obj.pop(keys[-1], None)
    else:
        obj[keys[-1]] = value


def merge_step(data, write):
    import merge_duplicate_deals_batch as mdb
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    todo, errors = [], []
    for spec in MERGES:
        if data.get('merged', {}).get(spec['drop']) == spec['keep']:
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
    if todo:
        mdb.strip_fixes({m.drop_id for m in todo}, write=write)
    return len(todo)


def remove_step(data, write):
    import fix_files
    cards = {d['id']: d for d in data['deals']}
    targets = set((data.get('merged') or {}).values())
    gone = []
    for cid, expect in REMOVE.items():
        card = cards.get(cid)
        if card is None:
            continue
        assert expect in str(card.get('title')), (cid, card.get('title'))
        assert cid not in targets, '%s — цель слияния' % cid
        gone.append(cid)
        print('  СНИМАЕМ %s %s' % (cid, str(card.get('title'))[:70]))
    if gone:
        data['deals'] = [d for d in data['deals'] if d['id'] not in gone]
        for cid in gone:
            pass
        import merge_duplicate_deals_batch as mdb
        mdb.strip_fixes(set(gone), write=write)
    return gone


def edit_step(data):
    import fact_edit_guard
    cards = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for cid, field, old, new, quote, url in EDITS:
        card = cards[cid]
        cur = get(card, field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS and new is not MISSING:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        done += 1
        print('  %s %s: %r → %r' % (cid, field, str(old)[:60], str(new)[:60]))
    for cid, field, value in RETRACT:
        lst = cards[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for pid, key, old, new in COMPANY_EDITS:
        p = comps[pid]
        cur = p.get(key, MISSING)
        if cur == new:
            continue
        assert cur == old, 'профиль %s %s: %r, ожидали %r' % (pid, key, cur, old)
        p[key] = new
        done += 1
        print('  профиль %s %s → %r' % (pid, key, str(new)[:70]))
    return done


def drop_discrepancies(gone, write):
    if not gone or not os.path.exists(DISCREP):
        return
    q = json.load(open(DISCREP, encoding='utf-8'))
    kept = [r for r in q if r.get('id') not in gone]
    if len(kept) != len(q):
        print('  facts_discrepancies: снять %d строк' % (len(q) - len(kept)))
        if write:
            json.dump(kept, open(DISCREP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def run(data, write):
    n = merge_step(data, write)
    gone = remove_step(data, write)
    n += len(gone) + edit_step(data)
    drop_discrepancies(gone + [m['drop'] for m in MERGES], write)
    return n


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    n = run(copy.deepcopy(data), write=False) + test_apply(write=False)
    if not n:
        print('Уже применено.')
        return 0
    if not write:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % n)
        return 0
    import mass_edit_guard
    old = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
    data = copy.deepcopy(old)
    run(data, write=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    test_apply(write=True)
    print('Записано изменений: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
