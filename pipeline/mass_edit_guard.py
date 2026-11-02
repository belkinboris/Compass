# -*- coding: utf-8 -*-
"""Массовая правка опубликованных карточек — только после пробы на десяти.

ЗАЧЕМ. 14–26 октября 2026 пересказ переписал текст 1169 опубликованных
карточек (76% базы) одной партией, и никто, кроме пишущего, этих текстов не
видел: ВТБ/«Деметра» вышла с прогнозом, записанным как факт. Владелец,
2 ноября 2026: проверки должны быть такими же, как при создании карточки;
массовую правку сначала смотрит человек.

ПРАВИЛО. Запись, которая меняет текст (отпечаток `readiness.fingerprint`)
больше чем `LIMIT` опубликованных карточек, отказывает, пока в
`pipeline/mass_edit_approvals.json` нет записи о пробе: какие десять карточек
владелец посмотрел и что ответил. Ключ записи передается скрипту
(`MASS_OK=<ключ> review.py --write`, у этой команды — `--mass-ok <ключ>`). Правки сверх пробы тоже попадают в
очередь вычитки (`readiness.changed_after_check`), так что проба не заменяет
проверку каждой карточки, а только не дает выкатить партию вслепую.

    python3 pipeline/mass_edit_guard.py            # рабочая копия против HEAD
    python3 pipeline/mass_edit_guard.py --base origin/main [--mass-ok <ключ>]

Разовый скрипт, который пишет базу, зовет `check(old_data, new_data, key)`
перед `json.dump` — или прогоняется этой командой до коммита
(docs/card_editing.md, «Безопасная запись базы»).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))
import readiness  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
APPROVALS = os.path.join(HERE, 'mass_edit_approvals.json')
LIMIT = 10


def changed_cards(old_data, new_data):
    """id опубликованных карточек, у которых изменился текст."""
    old_comps, new_comps = old_data.get('companies') or {}, new_data.get('companies') or {}
    before = {d['id']: readiness.fingerprint(d, old_comps) for d in old_data.get('deals') or []}
    out = []
    for d in new_data.get('deals') or []:
        was = before.get(d['id'])
        if was and not readiness.hash_matches(was, readiness.fingerprint(d, new_comps)):
            out.append(d['id'])
    return out


def approvals(path=APPROVALS):
    if not os.path.exists(path):
        return {}
    return {a['key']: a for a in json.load(open(path, encoding='utf-8'))}


def problem(old_data, new_data, key=None, path=APPROVALS):
    """Текст отказа или None."""
    ids = changed_cards(old_data, new_data)
    if len(ids) <= LIMIT:
        return None
    if key:
        a = approvals(path).get(key)
        if not a:
            return 'ключа пробы %r нет в %s' % (key, os.path.relpath(path, ROOT))
        if not (a.get('pilot') and a.get('owner')):
            return 'запись пробы %r без карточек пробы (pilot) или без ответа владельца (owner)' % key
        return None
    return ('правка меняет текст %d опубликованных карточек (больше %d): сначала проба на десяти — '
            'показать владельцу, записать его ответ в pipeline/mass_edit_approvals.json и передать ключ '
            '(--mass-ok <ключ>). Первые: %s' % (len(ids), LIMIT, ', '.join(ids[:12])))


def check(old_data, new_data, key=None):
    p = problem(old_data, new_data, key)
    if p:
        raise SystemExit('ОТКАЗ (массовая правка): ' + p)


def _self_check():
    old = {'companies': {}, 'deals': [{'id': 'g%d' % i, 'title': 'т%d' % i} for i in range(12)]}
    few = {'companies': {}, 'deals': [dict(d, title=d['title'] + ' x') if i < 3 else d
                                      for i, d in enumerate(old['deals'])]}
    many = {'companies': {}, 'deals': [dict(d, title=d['title'] + ' x') for d in old['deals']]}
    assert problem(old, few) is None
    assert problem(old, many) and 'больше 10' in problem(old, many)
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump([{'key': 'k', 'pilot': ['g0'], 'owner': 'да'}, {'key': 'bad'}], f)
    assert problem(old, many, 'k', f.name) is None
    assert 'без карточек' in problem(old, many, 'bad', f.name)
    assert 'нет в' in problem(old, many, 'zzz', f.name)
    os.unlink(f.name)


def main(argv):
    _self_check()
    base = argv[argv.index('--base') + 1] if '--base' in argv else 'HEAD'
    key = argv[argv.index('--mass-ok') + 1] if '--mass-ok' in argv else None
    old = json.loads(subprocess.run(['git', 'show', '%s:static/data/deals_promoted.json' % base],
                                    capture_output=True, text=True, cwd=ROOT, check=True).stdout)
    new = json.load(open(DATA, encoding='utf-8'))
    ids = changed_cards(old, new)
    print('Изменен текст опубликованных карточек против %s: %d' % (base, len(ids)))
    p = problem(old, new, key)
    if p:
        print('ОТКАЗ: ' + p)
        return 1
    print('Можно.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
