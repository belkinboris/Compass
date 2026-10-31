# -*- coding: utf-8 -*-
"""Файлы правок `fixes/`, относящиеся к одной карточке.

ЗАЧЕМ. «Выкинуть» убирает карточку из очереди, но файлы правок, написанные
для нее (`written_<id>_*.py` приемки и чтения), оставались лежать в
`pipeline/ingest/fixes/`: каждый `import review` грузил их и дальше, а
`review.py --write` на каждом прогоне печатал по ним «карточки нет в базе»
(бэклог A25, 31 октября 2026). Модуль нарочно без тяжелых импортов —
его зовут `approve.py` и `drop_pending.py`, которым `review` не нужен.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FIXES_DIR = os.path.join(HERE, 'fixes')

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


def drop_fixes_for(deal_id, folder=None, write=True):
    """Снять файлы правок выкинутой карточки. Возвращает список путей."""
    paths = files_only_about(deal_id, folder)
    if write:
        for p in paths:
            os.remove(p)
    return paths
