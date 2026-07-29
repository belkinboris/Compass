# -*- coding: utf-8 -*-
"""Единый справочник публичных профилей компаний «Компаса».

Пока часть кураторских карточек живёт в index.html, их зеркальная JSON-выгрузка
лежит рядом с основной базой. Backend и импорт ФНС никогда не разбирают HTML:
они читают только эти два JSON-файла. При последующей миграции в PostgreSQL
интерфейс этого модуля можно оставить без изменений.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROMOTED_PATH = ROOT / "static" / "data" / "deals_promoted.json"
CURATED_PATH = ROOT / "static" / "data" / "curated_companies.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_company_catalog() -> dict[str, dict[str, Any]]:
    promoted = _load(PROMOTED_PATH)
    rows: dict[str, dict[str, Any]] = {}
    for company_id, item in (promoted.get("companies") or {}).items():
        if not isinstance(item, dict):
            continue
        kpi = item.get("kpi") if isinstance(item.get("kpi"), list) else [None, None]
        rows[str(company_id)] = {
            "id": str(company_id),
            "name": str(item.get("name") or company_id),
            "legal_name": item.get("legal_name"),
            "industry": item.get("ind"),
            "description": item.get("desc"),
            "kpi_label": kpi[0] if len(kpi) > 0 else None,
            "kpi_value": kpi[1] if len(kpi) > 1 else None,
            "auto_generated": True,
            "aliases": list((promoted.get("match_keys") or {}).get(company_id) or []),
        }
    # Кураторские профили при совпадении id имеют приоритет над автоматическими.
    for company_id, item in _load(CURATED_PATH).items():
        if not isinstance(item, dict):
            continue
        kpi = item.get("kpi") if isinstance(item.get("kpi"), list) else [None, None]
        base = rows.get(str(company_id), {})
        rows[str(company_id)] = {
            **base,
            "id": str(company_id),
            "name": str(item.get("name") or base.get("name") or company_id),
            "legal_name": item.get("legal_name") or base.get("legal_name"),
            "industry": item.get("ind") or base.get("industry"),
            "description": item.get("desc") or base.get("description"),
            "kpi_label": kpi[0] if len(kpi) > 0 else base.get("kpi_label"),
            "kpi_value": kpi[1] if len(kpi) > 1 else base.get("kpi_value"),
            "auto_generated": False,
            "aliases": list(dict.fromkeys([*(base.get("aliases") or []), str(item.get("name") or "").lower()])),
        }
    return rows


def get_company_profile(company_id: str) -> dict[str, Any] | None:
    return load_company_catalog().get(company_id)
