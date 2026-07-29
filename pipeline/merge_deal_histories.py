# -*- coding: utf-8 -*-
"""Слить прежние отдельные новости в канонические карточки сделок.

Первая миграция объединяет раннюю карточку о переговорах по покупке российского
Ситибанка с закрытой сделкой ``citibank``. История этапов хранится в
кураторской карточке, а старый id остаётся рабочим через ``merged``.

Запуск:
    python3 pipeline/merge_deal_histories.py          # сухой прогон
    python3 pipeline/merge_deal_histories.py --write  # записать JSON

Скрипт идемпотентен: повторный запуск не меняет уже исправленный файл.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

LEGACY_DEAL_ID = "gf57ea8cb"
CANONICAL_DEAL_ID = "citibank"
LEGACY_COMPANY_ID = "g32b8014f"
CANONICAL_COMPANY_ID = "citibank"


def migrate(payload: dict) -> tuple[dict, list[str]]:
    changes: list[str] = []

    deals = payload.setdefault("deals", [])
    kept = [deal for deal in deals if deal.get("id") != LEGACY_DEAL_ID]
    if len(kept) != len(deals):
        payload["deals"] = kept
        changes.append(f"удалена отдельная карточка этапа {LEGACY_DEAL_ID}")

    merged = payload.setdefault("merged", {})
    if merged.get(LEGACY_DEAL_ID) != CANONICAL_DEAL_ID:
        merged[LEGACY_DEAL_ID] = CANONICAL_DEAL_ID
        changes.append(f"добавлен редирект {LEGACY_DEAL_ID} → {CANONICAL_DEAL_ID}")

    merged_stages = payload.setdefault("merged_deal_stages", {})
    legacy_stage = "negotiations-2024-01-01"
    if merged_stages.get(LEGACY_DEAL_ID) != legacy_stage:
        merged_stages[LEGACY_DEAL_ID] = legacy_stage
        changes.append(f"старый адрес привязан к этапу {legacy_stage}")

    companies = payload.setdefault("companies", {})
    if LEGACY_COMPANY_ID in companies:
        del companies[LEGACY_COMPANY_ID]
        changes.append(f"удалён технический профиль компании {LEGACY_COMPANY_ID}")

    match_keys = payload.setdefault("match_keys", {})
    if LEGACY_COMPANY_ID in match_keys:
        del match_keys[LEGACY_COMPANY_ID]
        changes.append(f"удалены псевдонимы технического профиля {LEGACY_COMPANY_ID}")

    merged_companies = payload.setdefault("merged_companies", {})
    if merged_companies.get(LEGACY_COMPANY_ID) != CANONICAL_COMPANY_ID:
        merged_companies[LEGACY_COMPANY_ID] = CANONICAL_COMPANY_ID
        changes.append(
            f"добавлен редирект компании {LEGACY_COMPANY_ID} → {CANONICAL_COMPANY_ID}"
        )

    return payload, changes


def main(write: bool) -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    payload, changes = migrate(payload)
    if not changes:
        print("Изменений нет: история уже объединена.")
        return

    print("\n".join(f"- {item}" for item in changes))
    if write:
        DATA.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print("Записано:", DATA)
    else:
        print("Сухой прогон. Для записи добавьте --write.")


if __name__ == "__main__":
    main("--write" in sys.argv)
