# -*- coding: utf-8 -*-
"""Свернуть примененные партии правок `fixes/*.py` в архив `fixes_archive/<ГГГГ-ММ>.json`.

ЗАЧЕМ. К 31 октября 2026 в `fixes/` лежало 1815 файлов на 13,6 МБ (9040
записей, +1409 файлов за октябрь: `write_card.save_batch` писал файл на
каждую карточку), и все они импортировались как модули при каждом
`import review` — 0,7–1,5 с на пост, консоль, приемку. Записи при этом давно
применены: `review.already_applied` сравнивает `new` с базой, для прозы —
отпечаток в `card.proofread_absorbed`. Применённая партия нужна только как
память (вычитка, дубли, «снять правки выкинутой карточки») — ее держит JSON,
который читается за миллисекунды.

ЧТО ДЕЛАЕТ. Берет файлы `fixes/*.py` старше `--days` (дата — из имени файла
`..._ГГГГ_ММ_ДД...`; у файла без даты — день его первого коммита в git), у
которых КАЖДАЯ запись уже применена к карточке базы или очереди предпросмотра
(карточки нет вовсе — выкинута, запись тоже уезжает в архив), переносит их
записи в `fixes_archive/<ГГГГ-ММ>.json` (месяц — по дате файла) и снимает
.py через `git rm`. Порядок `review.FIXES` не меняется: `review.load_fixes`
складывает архив и живые файлы и сортирует партии по имени файла, как раньше.

Формат архива: `{"files": {"<имя файла без .py>": {"date": "ГГГГ-ММ-ДД",
"applied_on": "ГГГГ-ММ-ДД", "doc": "<первая строка докстринга>",
"fixes": [<те же словари, что были в FIXES>]}}}`. Полный докстринг партии
(где искали источники, что не нашли) — в истории git снятого файла.

    python3 pipeline/ingest/fixes_compact.py --days 14            # план
    python3 pipeline/ingest/fixes_compact.py --days 14 --write    # перенести

Шаг рутины качества — раз в неделю (routines/quality.md). Снять записи из
архива — `fix_files.drop_fixes_for` / `pipeline/remove_fixes_for_id.py`,
они смотрят и в .py, и в JSON.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXES_DIR = os.path.join(HERE, 'fixes')
ARCHIVE_DIR = os.path.join(HERE, 'fixes_archive')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

_DATE_IN_NAME = re.compile(r'(20\d{2})[_-](\d{2})[_-](\d{2})')
_DAY_IN_NAME = re.compile(r'(20\d{2})(\d{2})(\d{2})')


def file_date(name, folder=FIXES_DIR):
    """Дата партии: из имени, иначе — первый коммит файла в git; None — не знаем."""
    m = _DATE_IN_NAME.search(name) or _DAY_IN_NAME.search(name)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    try:
        out = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%as', '--', name],
                             cwd=folder, capture_output=True, text=True, check=True).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return datetime.strptime(out[-1], '%Y-%m-%d').date() if out else None


def _cards():
    cards = {}
    if os.path.exists(DATA):
        data = json.load(open(DATA, encoding='utf-8'))
        cards = {d['id']: d for d in data['deals']}
        companies = data.get('companies') or {}
    else:
        companies = {}
    if os.path.exists(PENDING):
        cards.update({c['id']: c for c in json.load(open(PENDING, encoding='utf-8'))['cards']})
    return cards, companies


def _roundtrip(fixes):
    """Записи после JSON: кортежи становятся списками, остальное — как было."""
    return json.loads(json.dumps(fixes, ensure_ascii=False))


def _load_batch(folder, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location('fixes.%s' % name, os.path.join(folder, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plan(days, folder=FIXES_DIR, today=None, cards=None, companies=None):
    """[(имя партии, дата, записи, причина-отказа-или-None, первая строка докстринга)]."""
    sys.path.insert(0, HERE)
    import review  # noqa: F401  (already_applied)
    today = today or date.today()
    if cards is None:
        cards, companies = _cards()
    companies = companies or {}
    out = []
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith('.py') or fn == '__init__.py':
            continue
        name = fn[:-3]
        day = file_date(fn, folder)
        if day is None:
            out.append((name, None, [], 'дата неизвестна (нет в имени и в git)', ''))
            continue
        if (today - day).days <= days:
            out.append((name, day, [], 'моложе %d дней' % days, ''))
            continue
        mod = _load_batch(folder, name)
        doc = (mod.__doc__ or '').strip().split('\n')[0]
        fixes = mod.FIXES
        try:
            rt = _roundtrip(fixes)
        except (TypeError, ValueError) as e:
            out.append((name, day, [], 'не кладется в JSON: %s' % e, doc))
            continue
        pending = []
        for f, g in zip(fixes, rt):
            card = cards.get(f['id'])
            if card is None:
                continue  # карточка выкинута — запись уезжает вместе с остальными
            if not (review.already_applied(f, card, companies) and review.already_applied(g, card, companies)):
                pending.append('%s.%s' % (f['id'], f['field']))
        if pending:
            out.append((name, day, [], 'не применены: %s' % ', '.join(pending[:3]), doc))
            continue
        out.append((name, day, rt, None, doc))  # пустую партию тоже снимаем
    return out


def compact(days, write=False, folder=FIXES_DIR, archive=ARCHIVE_DIR, today=None,
            cards=None, companies=None):
    today = today or date.today()
    rows = plan(days, folder, today, cards, companies)
    ready = [(n, d, fx, doc) for n, d, fx, why, doc in rows if why is None]
    kept = [(n, why) for n, _d, _fx, why, _doc in rows if why]
    print('Файлов в fixes/: %d; переносится: %d (%d записей); остается: %d'
          % (len(rows), len(ready), sum(len(fx) for _n, _d, fx, _doc in ready), len(kept)))
    for n, why in kept:
        if not why.startswith('моложе'):
            print('  остается %s — %s' % (n, why))
    if not write:
        print('Сухой прогон. Перенос — с ключом --write.')
        return len(ready)
    os.makedirs(archive, exist_ok=True)
    by_month = {}
    for name, day, fixes, doc in ready:
        by_month.setdefault(day.strftime('%Y-%m'), []).append((name, day, fixes, doc))
    for month, batch in sorted(by_month.items()):
        path = os.path.join(archive, '%s.json' % month)
        store = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {'files': {}}
        for name, day, fixes, doc in batch:
            assert name not in store['files'], 'партия %s уже в архиве %s' % (name, month)
            store['files'][name] = {'date': day.isoformat(), 'applied_on': today.isoformat(),
                                    'doc': doc, 'fixes': fixes}
        store['files'] = dict(sorted(store['files'].items()))
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(store, fh, ensure_ascii=False, indent=1)
            fh.write('\n')
    names = [name + '.py' for name, _day, _fixes, _doc in ready]
    for i in range(0, len(names), 200):  # одним вызовом на партию: по файлу — минуты
        subprocess.run(['git', 'rm', '-q', '--', *names[i:i + 200]], cwd=folder, capture_output=True)
    for fn in names:
        if os.path.exists(os.path.join(folder, fn)):  # не репозиторий git — снимаем сами
            os.remove(os.path.join(folder, fn))
    print('Перенесено партий: %d, в архив: %s' % (len(ready), ', '.join(sorted(by_month))))
    return len(ready)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--days', type=int, default=14, help='старше скольких дней сворачивать (по умолчанию 14)')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    compact(a.days, write=a.write)
    return 0


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    sys.exit(main())
