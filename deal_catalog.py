# -*- coding: utf-8 -*-
"""Чтение сделок из двух текущих источников данных без разбора HTML."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import base_data

ROOT = Path(__file__).resolve().parent
PROMOTED = base_data.PROMOTED_PATH
CURATED = ROOT / "static" / "data" / "curated_deals.json"


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


_CACHE: tuple[Any, dict[str, dict[str, Any]]] | None = None


def _curated_stamp() -> Any:
    try:
        st = CURATED.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def load_deals() -> dict[str, dict[str, Any]]:
    # Словарь на ~1560 сделок собирался заново на каждой странице /deal/<id>
    # (аудит 28 октября 2026); теперь — по отпечатку базы и curated_deals.json.
    global _CACHE
    key = (base_data._stamp(), _curated_stamp())
    if _CACHE is not None and _CACHE[0] == key and key[0] is not None:
        return _CACHE[1]
    rows = _build()
    _CACHE = (key, rows)
    return rows


def _build() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    # База — через общий кэш `base_data`: раньше ее разбирал заново каждый
    # вызов, и `get_deal()` на каждой странице сделки стоил ≈72 МБ.
    promoted = base_data.promoted()
    for item in promoted.get("deals") or []:
        if isinstance(item, dict) and item.get("id"):
            rows[str(item["id"])] = item
    for item in _read(CURATED) or []:
        if isinstance(item, dict) and item.get("id"):
            rows[str(item["id"])] = item
    return rows


def get_deal(deal_id: str) -> dict[str, Any] | None:
    return load_deals().get(deal_id)
