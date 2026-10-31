# -*- coding: utf-8 -*-
"""Файлы правок `fixes/`, относящиеся к одной карточке.

ЗАЧЕМ. «Выкинуть» убирает карточку из очереди, но файлы правок, написанные
для нее (`written_<id>_*.py` приемки и чтения), оставались лежать в
`pipeline/ingest/fixes/`: каждый `import review` грузил их и дальше, а
`review.py --write` на каждом прогоне печатал по ним «карточки нет в базе»
(бэклог A25, 31 октября 2026). Модуль нарочно без тяжелых импортов —
его зовут `approve.py` и `drop_pending.py`, которым `review` не нужен.
"""
import json
import os
import pprint
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FIXES_DIR = os.path.join(HERE, 'fixes')
ARCHIVE_DIR = os.path.join(HERE, 'fixes_archive')

_ID_RE = re.compile(r"""['"]id['"]\s*:\s*['"]([^'"]+)['"]""")


def files_only_about(deal_id, folder=None):
    """Файлы правок, в которых ВСЕ записи — про эту карточку.

    Смешанный файл партии (несколько карточек) не трогаем: его записи для
    других карточек еще нужны; запись выкинутой карточки там безвредна —
    `review.py` ее пропускает как «нет в базе»."""
    folder = folder or FIXES_DIR
    out = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.py') or name == '__init__.py':
            continue
        path = os.path.join(folder, name)
        ids = set(_ID_RE.findall(open(path, encoding='utf-8').read()))
        if ids and ids == {deal_id}:
            out.append(path)
    return out


def daily_files_mentioning(deal_id, folder=None):
    """Дневные файлы `written_<день>_<сессия>.py` (write_card.save_batch с
    31 октября 2026), где записи этой карточки лежат рядом с чужими: такой
    файл не удаляется, а переписывается без них."""
    folder = folder or FIXES_DIR
    out = []
    for name in sorted(os.listdir(folder)):
        if not name.startswith('written_') or not name.endswith('.py'):
            continue
        path = os.path.join(folder, name)
        ids = set(_ID_RE.findall(open(path, encoding='utf-8').read()))
        if deal_id in ids and ids != {deal_id}:
            out.append(path)
    return out


def _rewrite_daily_without(path, deal_id):
    ns = {}
    exec(open(path, encoding='utf-8').read(), ns)          # noqa: S102
    fixes = [f for f in (ns.get('FIXES') or []) if f.get('id') != deal_id]
    ids = [i for i in (ns.get('CARDS') or sorted({f['id'] for f in ns.get('FIXES') or []})) if i != deal_id]
    src = open(path, encoding='utf-8').read()
    head = src.split('CARDS = ', 1)[0] if 'CARDS = ' in src else src.split('FIXES = ', 1)[0]
    open(path, 'w', encoding='utf-8').write(
        head + 'CARDS = %r\n\nFIXES = %s\n' % (ids, pprint.pformat(fixes, width=100, sort_dicts=False)))


def drop_archived_fixes_for(deal_ids, archive=None, write=True):
    """Снять записи карточек из JSON-архива партий (`fixes_compact.py`).
    Возвращает {файл архива: сколько записей снято}."""
    archive = archive or ARCHIVE_DIR
    wanted = set(deal_ids if isinstance(deal_ids, (set, list, tuple)) else [deal_ids])
    out = {}
    if not os.path.isdir(archive):
        return out
    for name in sorted(os.listdir(archive)):
        if not name.endswith('.json'):
            continue
        path = os.path.join(archive, name)
        store = json.load(open(path, encoding='utf-8'))
        n = 0
        for batch in store['files'].values():
            kept = [f for f in batch['fixes'] if f.get('id') not in wanted]
            n += len(batch['fixes']) - len(kept)
            batch['fixes'] = kept
        if n:
            out[path] = n
            if write:
                with open(path, 'w', encoding='utf-8') as fh:
                    json.dump(store, fh, ensure_ascii=False, indent=1)
                    fh.write('\n')
    return out


def drop_fixes_for(deal_id, folder=None, write=True):
    """Снять правки выкинутой карточки: файлы только о ней — удалить, дневные
    файлы write_card — переписать без нее, JSON-архив — тоже без нее.
    Возвращает список путей тронутых файлов."""
    paths = files_only_about(deal_id, folder)
    daily = daily_files_mentioning(deal_id, folder)
    archived = drop_archived_fixes_for(deal_id, None if folder is None else os.path.join(folder, '..', 'fixes_archive'), write)
    if write:
        for p in paths:
            os.remove(p)
        for p in daily:
            _rewrite_daily_without(p, deal_id)
    return paths + daily + sorted(archived)
