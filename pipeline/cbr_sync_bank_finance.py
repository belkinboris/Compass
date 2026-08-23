# -*- coding: utf-8 -*-
"""Собирает `static/data/bank_finance.json` — активы/капитал (форма 806,
чистые, см. `cbr_f806.py`) и чистая прибыль (форма 102, символ `61101`
«Прибыль после налогообложения», см. `cbr_client.py`) для банковских
профилей из `pipeline/fns_registry.py` (`decision == "bank"`, `cbr_regnum`
задан). Этап 6 плана `COMPANY_FINANCE_BRIEF.md`, П3-6.

ПОЧЕМУ СТАТИКА В GIT, А НЕ ЖИВОЙ ЗАПРОС С ПРОДА. Данные квартальные (форма
806) и помесячные (форма 102) — обновлять раз в сутки-двое более чем
достаточно, а сеть боевого хоста (Timeweb) до cbr.ru НЕ проверена (родня
уже записанного урока про api.telegram.org: «сеть в среде разработки
работает — не значит, что работает в бою»). Тот же путь, что
`deals_promoted.json`: файл коммитится, деплой доносит его до прода — сайт
сам никогда не ходит в cbr.ru.

ФОРМА 102 ИДЁТ НЕ ОТ ПОСЛЕДНЕГО КАЛЕНДАРНОГО МЕСЯЦА, А ОТ СПИСКА РЕАЛЬНО
ДОСТУПНЫХ ДАТ (`GetDatesForF102`) — тот же приём, что `latest_available` в
`cbr_f806.py` для формы 806, только там квартальный откат по шагу, здесь
готовый список дат уже есть в самом API.

ИДЕМПОТЕНТЕН — БЕЗОПАСНО ВЫЗЫВАТЬ ЧАСТО. Если собранные данные совпадают с
уже записанным файлом (обычный случай: банк квартал/месяц не обновлял),
скрипт ничего не пишет и не печатает «Записано» — это НЕ ошибка, а
ожидаемый результат для большинства прогонов между отчётными датами.
Рассчитан на шаг существующей ежечасной рутины «качество» (см.
`COMPANY_FINANCE_BRIEF.md`, этап 6, П3-6) — заводить для него отдельный
триггер не нужно, дешёвая проверка «есть ли новые данные» не жалко
хоть каждый час.

ЗАПУСК:
    python3 pipeline/cbr_sync_bank_finance.py           # сухой прогон, только печать
    python3 pipeline/cbr_sync_bank_finance.py --write    # запись static/data/bank_finance.json (только если есть изменения)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from cbr_client import CbrCreditOrgClient  # noqa: E402
from pipeline import fns_registry  # noqa: E402
from pipeline.cbr_f806 import latest_available  # noqa: E402

OUTPUT_PATH = ROOT / "static" / "data" / "bank_finance.json"
NET_PROFIT_SYMBOL = "61101"  # «Прибыль после налогообложения», форма 102


def bank_entries() -> list[dict]:
    return [row for row in fns_registry.REGISTRY
            if row["decision"] == "bank" and row.get("cbr_regnum")]


def _parse_iso_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def latest_net_profit(regnum: int, client: CbrCreditOrgClient) -> tuple[date, int] | None:
    """`None` — банк не отчитался по форме 102 ни на одну известную дату,
    или символ 61101 не встретился (не должно происходить для настоящей
    кредитной организации, но не гадаем, если так вышло)."""
    try:
        raw_dates = client.dates_for_f102(regnum)
    except Exception:                                                  # noqa: BLE001
        return None
    dates = sorted(filter(None, (_parse_iso_date(r) for r in raw_dates)), reverse=True)
    for on_date in dates:
        try:
            rows = client.data102f_xml(regnum, on_date)
        except Exception:                                              # noqa: BLE001
            continue
        for row in rows:
            if row.get("symbol") == NET_PROFIT_SYMBOL and row.get("tp3") is not None:
                return on_date, int(row["tp3"]) * 1000
    return None


def collect(today: date) -> dict[str, dict]:
    result: dict[str, dict] = {}
    with httpx.Client() as f806_client, CbrCreditOrgClient() as f102_client:
        for row in bank_entries():
            regnum = row["cbr_regnum"]
            balance = latest_available(regnum, f806_client, today=today)
            profit = latest_net_profit(regnum, f102_client)
            if balance is None and profit is None:
                continue
            entry: dict = {"regnum": regnum}
            if balance is not None:
                entry["legal_name"] = balance.legal_name
                entry["as_of_balance"] = balance.as_of.isoformat()
                entry["assets_rub"] = balance.assets_rub
                entry["equity_rub"] = balance.equity_rub
            if profit is not None:
                entry["as_of_profit"] = profit[0].isoformat()
                entry["net_profit_rub"] = profit[1]
            result[row["company_id"]] = entry
    return result


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="записать static/data/bank_finance.json")
    args = parser.parse_args(argv)

    today = date.today()
    data = collect(today)

    for company_id in sorted(data):
        entry = data[company_id]
        assets = entry.get("assets_rub")
        profit = entry.get("net_profit_rub")
        assets_str = (f"{assets / 1e12:.2f} трлн ₽ на {entry.get('as_of_balance')}"
                      if assets is not None else "нет данных формы 806")
        profit_str = (f"{profit / 1e9:.1f} млрд ₽ на {entry.get('as_of_profit')}"
                      if profit is not None else "нет данных формы 102")
        print(f"{company_id} ({entry.get('legal_name', '?')}): активы {assets_str}; прибыль {profit_str}")

    skipped = [row["company_id"] for row in bank_entries() if row["company_id"] not in data]
    if skipped:
        print(f"Без каких-либо данных (обе формы пусты): {skipped}")

    existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8")) if OUTPUT_PATH.exists() else {}
    if data == existing:
        print("Без изменений — квартал/месяц те же, что уже записаны, ничего не пишем.")
        return

    if args.write:
        OUTPUT_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Записано: {OUTPUT_PATH} ({len(data)} банков, изменения есть)")
    else:
        print("Есть изменения — для записи добавьте --write")


if __name__ == "__main__":
    main(sys.argv[1:])
