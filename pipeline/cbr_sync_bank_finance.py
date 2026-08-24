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

ПОЛНЫЙ БАЛАНС — ОТДЕЛЬНЫЙ ФАЙЛ (Этап 8, П2-8). Просьба владельца и партнёра
живьём после показа сводных плиток: «Нужен бухгалтерский баланс… Активы и
пассивы, 1-2 странички» — все строки разделов I-III формы 806, не только
два итога. Пишем `bank_full_balance.json` ОТДЕЛЬНО от `bank_finance.json`
(который грузится для плиток на каждой из ~13 банковских страниц) — полная
таблица нужна только на самой странице банка по клику/прокрутке, грузить
её вместе со сводкой было бы лишним весом для случая, когда посетитель
хочет только плитки. Обе идемпотентности проверяются НЕЗАВИСИМО: смена
чистой прибыли (форма 102, помесячно) не должна перезаписывать полную
таблицу баланса (форма 806, поквартально), и наоборот.

`find_latest_page()` (см. `cbr_f806.py`) выполняет ОДИН сетевой запрос на
банк за квартал-попытку и отдаёт сырой HTML — `parse_balance()` и
`parse_full_table()` разбирают его дважды, без второго похода в сеть.

ЗАПУСК:
    python3 pipeline/cbr_sync_bank_finance.py           # сухой прогон, только печать
    python3 pipeline/cbr_sync_bank_finance.py --write    # запись static/data/bank_finance.json и bank_full_balance.json (только если есть изменения)
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
from pipeline.cbr_f806 import find_latest_page, parse_balance, parse_full_table  # noqa: E402

OUTPUT_PATH = ROOT / "static" / "data" / "bank_finance.json"
FULL_BALANCE_OUTPUT_PATH = ROOT / "static" / "data" / "bank_full_balance.json"
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


def collect(today: date) -> tuple[dict[str, dict], dict[str, dict]]:
    """(сводка для плиток, полный баланс разделов I-III) — оба словаря
    ключом company_id. Один HTTP-запрос на банк на форму 806 (см. докстроку
    модуля), не два."""
    finance: dict[str, dict] = {}
    full_balance: dict[str, dict] = {}
    with httpx.Client() as f806_client, CbrCreditOrgClient() as f102_client:
        for row in bank_entries():
            regnum = row["cbr_regnum"]
            html = find_latest_page(regnum, f806_client, today=today)
            balance = parse_balance(html, regnum) if html is not None else None
            full = parse_full_table(html) if html is not None else None
            profit = latest_net_profit(regnum, f102_client)
            if balance is None and profit is None:
                continue
            entry: dict = {"regnum": regnum}
            if balance is not None:
                entry["legal_name"] = balance.legal_name
                entry["as_of_balance"] = balance.as_of.isoformat()
                entry["assets_rub"] = balance.assets_rub
                entry["assets_rub_prior_year"] = balance.assets_rub_prior_year
                entry["equity_rub"] = balance.equity_rub
                entry["equity_rub_prior_year"] = balance.equity_rub_prior_year
            if profit is not None:
                entry["as_of_profit"] = profit[0].isoformat()
                entry["net_profit_rub"] = profit[1]
            finance[row["company_id"]] = entry
            if full is not None:
                full_balance[row["company_id"]] = {
                    "regnum": regnum,
                    "legal_name": full["legal_name"],
                    "as_of": full["as_of"].isoformat(),
                    "sections": full["sections"],
                }
    return finance, full_balance


def _write_if_changed(path: Path, data: dict, write: bool, label: str) -> None:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if data == existing:
        print(f"{label}: без изменений — квартал/месяц те же, что уже записаны, ничего не пишем.")
        return
    if write:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{label}: записано {path} ({len(data)} банков, изменения есть)")
    else:
        print(f"{label}: есть изменения — для записи добавьте --write")


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                         help="записать static/data/bank_finance.json и bank_full_balance.json")
    args = parser.parse_args(argv)

    today = date.today()
    data, full_balance_data = collect(today)

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

    _write_if_changed(OUTPUT_PATH, data, args.write, "Сводка (плитки)")
    _write_if_changed(FULL_BALANCE_OUTPUT_PATH, full_balance_data, args.write, "Полный баланс")


if __name__ == "__main__":
    main(sys.argv[1:])
