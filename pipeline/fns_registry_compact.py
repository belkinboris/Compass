# -*- coding: utf-8 -*-
"""Свернуть хвост `pipeline/fns_registry.py` в `pipeline/fns_registry.json`.

ЗАЧЕМ. С 31 октября 2026 принятые решения «профиль -> юрлицо» лежат в JSON,
а скрипты (`accept_card.py`, `fns_unresolved_queue.py`,
`fns_notes_to_registry.py`) по-прежнему дописывают свежие записи в .py
блоками `REGISTRY += [...]` перед `def by_company_id` — формат, который они
знали и до переезда. Этот скрипт переносит такие блоки в JSON (в конец, в
порядке файла) и убирает их из .py, чтобы модуль не отрастил снова 1,66 МБ
кода. Порядок `REGISTRY` после сворачивания тот же, что и до него.

    python3 pipeline/fns_registry_compact.py            # план
    python3 pipeline/fns_registry_compact.py --write    # перенести
"""
from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, "pipeline", "fns_registry.py")
JSON_PATH = os.path.join(ROOT, "pipeline", "fns_registry.json")
MARKER = "\n\ndef by_company_id() -> dict[str, dict]:"


def tail_blocks(src: str) -> list:
    """[(start, end, rows)] — блоки `REGISTRY += [...]` в тексте модуля,
    границы в символах, записи — разобранные литералы."""
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)

    def offset(lineno, col):
        # col_offset у ast — в БАЙТАХ utf-8, не в знаках: строка с кириллицей
        # до конца словаря сдвигала границу (31 октября 2026).
        head = lines[lineno - 1].encode("utf-8")[:col].decode("utf-8")
        return sum(len(line) for line in lines[:lineno - 1]) + len(head)

    out = []
    for node in tree.body:
        if (isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
                and node.target.id == "REGISTRY" and isinstance(node.op, ast.Add)):
            rows = ast.literal_eval(node.value)
            out.append((offset(node.lineno, node.col_offset),
                        offset(node.end_lineno, node.end_col_offset), rows))
    return out


def _strip_block(src: str, start: int, end: int) -> str:
    """Снять блок вместе с комментарием-шапкой над ним (строки `#` подряд)
    и пустыми строками, чтобы в .py не копились осиротевшие заголовки."""
    pos = src.rfind("\n", 0, start)
    while pos > 0:
        prev = src.rfind("\n", 0, pos)
        line = src[prev + 1:pos]
        if line.startswith("#") or not line.strip():
            pos = prev
        else:
            break
    return src[:pos].rstrip("\n") + "\n\n\n" + src[end:].lstrip("\n")


def compact(py_path=PY, json_path=JSON_PATH, write=False) -> int:
    src = open(py_path, encoding="utf-8").read()
    assert MARKER in src, "не нашли конец REGISTRY в fns_registry.py — формат файла изменился"
    blocks = tail_blocks(src)
    if not blocks:
        print("Хвост пуст: все записи уже в %s." % os.path.relpath(json_path, ROOT))
        return 0
    rows = json.load(open(json_path, encoding="utf-8"))
    known = {r["company_id"] for r in rows}
    moved = []
    for _s, _e, batch in blocks:
        for row in batch:
            assert row["company_id"] not in known, (
                "запись %r есть и в JSON, и в хвосте — сначала разобрать руками" % row["company_id"])
            known.add(row["company_id"])
            moved.append(row)
    print("Блоков в хвосте: %d, записей: %d -> %s"
          % (len(blocks), len(moved), os.path.relpath(json_path, ROOT)))
    for row in moved:
        print("  %s  %s  %s" % (row["company_id"], row["decision"], row.get("inn") or ""))
    if not write:
        print("Сухой прогон. Перенос — с ключом --write.")
        return len(moved)
    for start, end, _batch in reversed(blocks):
        src = _strip_block(src, start, end)
    ast.parse(src)  # модуль после правки обязан остаться верным Python
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(rows + moved, fh, ensure_ascii=False, indent=1)
    open(py_path, "w", encoding="utf-8").write(src)
    print("Перенесено: %d." % len(moved))
    return len(moved)


if __name__ == "__main__":
    compact(write="--write" in sys.argv[1:])
