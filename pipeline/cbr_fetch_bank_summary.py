# -*- coding: utf-8 -*-
"""Живой прогон: тянет форму 101 у ЦБ по нескольким банкам, классифицирует
счета (`cbr_account_types.py`) и печатает итог активов/капитала с проверкой
по независимому числу. НИЧЕГО НЕ ПИШЕТ — ни в базу, ни на сайт.

ЗАЧЕМ ЭТОТ СКРИПТ. Сеть разработки Claude Code не пускает к cbr.ru совсем
(см. урок в CLAUDE.md), поэтому весь протокол собирался вручную через
терминал владельца — командами по одной, с реальным риском обрыва
соединения (так и потеряли большую часть первого набора данных 18 августа).
Этот скрипт делает то же самое ОДНОЙ командой на машине, у которой есть
сеть до cbr.ru (боевой сервер, любой сервер с обычным доступом в интернет),
без ручного набора SOAP-конвертов.

ЗАПУСК (там, где есть сеть до cbr.ru — НЕ в среде разработки Claude Code):
    python3 pipeline/cbr_fetch_bank_summary.py
    python3 pipeline/cbr_fetch_bank_summary.py --date 2026-07-01
    python3 pipeline/cbr_fetch_bank_summary.py --bank 1481:Сбербанк --bank 1000:ВТБ

ЧТО ДЕЛАТЬ С РЕЗУЛЬТАТОМ. Это диагностика, не источник для сайта. Прежде
чем подключать что-либо к `main.py`, нужно: (1) чтобы покрытие (доля
классифицированных счетов) было близко к 100%, не 83%, как на частичной
выборке 18 августа; (2) чтобы независимая сверка (столбец «сверка») была
близка для НЕСКОЛЬКИХ банков, а не только для Сбербанка (урок «первая
выборка не выбирает себя по самому заметному», CLAUDE.md); (3) чтобы
разделы 1 (капитал), 5-9 (ценные бумаги, средства и имущество, результаты)
`cbr_account_types.py` были сверены построчно с действующим 809-П, как уже
сделано для разделов 2-4 — сейчас капитал держится только на смысле
названия счёта, не на тексте закона.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cbr_client import CbrClientError, CbrCreditOrgClient  # noqa: E402
from pipeline.cbr_account_types import ASSET, CAPITAL_LIABILITY, EXCLUDED, UNKNOWN, classify  # noqa: E402

# (CredorgNumber, имя, независимая сверка по активам в трлн ₽ или None)
DEFAULT_BANKS = [
    (1481, "Сбербанк", 66.09),   # TAdviser, 2026
    (1000, "ВТБ", 38.0),         # МСФО, группа целиком, март 2026 — не то же самое,
                                  # что юрлицо по РСБУ (форма 101), сверка приблизительная
    (1326, "Альфа-Банк", None),  # точное число активов не найдено при подготовке скрипта
]


def parse_bank_arg(raw: str) -> tuple[int, str, float | None]:
    parts = raw.split(":")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError("формат --bank: НОМЕР:Имя[:сверка_трлн]")
    number = int(parts[0])
    name = parts[1]
    reference = float(parts[2]) if len(parts) > 2 and parts[2] else None
    return number, name, reference


def summarize(rows: list[dict]) -> dict:
    totals = {ASSET: 0.0, CAPITAL_LIABILITY: 0.0, EXCLUDED: 0.0, UNKNOWN: 0.0}
    counts = {ASSET: 0, CAPITAL_LIABILITY: 0, EXCLUDED: 0, UNKNOWN: 0}
    unknown_rows = []
    for row in rows:
        numsc = row.get("numsc", "")
        value = float(row.get("iitg") or 0)
        kind, confidence, reason = classify(numsc)
        totals[kind] += value
        counts[kind] += 1
        if kind == UNKNOWN:
            unknown_rows.append((numsc, value))
    return {"totals": totals, "counts": counts, "unknown_rows": unknown_rows, "n": len(rows)}


def latest_available_date(client: CbrCreditOrgClient, credorg: int) -> date | None:
    """Банки отчитываются на конкретные даты (обычно 1-е число месяца), не
    каждый день — по умолчанию `date.today()` почти всегда пустой ответ
    (ровно это и случилось при первом живом прогоне 18 августа: сегодня —
    не отчётная дата). `GetDatesForF101` уже написан для ровно этого случая
    — берём из него последнюю доступную дату вместо угадывания."""
    try:
        raw_dates = client.dates_for_f101(credorg)
    except Exception:                                                  # noqa: BLE001
        return None
    parsed = []
    for raw in raw_dates:
        try:
            parsed.append(date.fromisoformat(raw[:10]))
        except ValueError:
            continue
    return max(parsed) if parsed else None


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None,
                         help="дата ISO, например 2026-07-01; без неё скрипт сам берёт "
                              "последнюю доступную дату для КАЖДОГО банка через GetDatesForF101")
    parser.add_argument("--bank", action="append", type=parse_bank_arg,
                         help="НОМЕР:Имя[:сверка_трлн], можно несколько раз; по умолчанию — три банка ниже")
    args = parser.parse_args(argv)

    fixed_date = date.fromisoformat(args.date) if args.date else None
    banks = args.bank or DEFAULT_BANKS

    with CbrCreditOrgClient() as client:
        for credorg, name, reference in banks:
            on_date = fixed_date
            if on_date is None:
                on_date = latest_available_date(client, credorg)
                if on_date is None:
                    print(f"\n{'='*70}\n{name} (рег. номер {credorg})")
                    print("  ОШИБКА: не удалось определить отчётную дату через GetDatesForF101 — "
                          "укажите --date явно")
                    continue

            print(f"\n{'='*70}\n{name} (рег. номер {credorg}), на {on_date.isoformat()}")
            try:
                rows = client.data101fnew_xml(credorg, on_date)
            except CbrClientError as e:
                print(f"  ОШИБКА: {e}")
                continue
            except Exception as e:                                    # noqa: BLE001
                print(f"  ОШИБКА сети/разбора: {type(e).__name__}: {e}")
                continue

            if not rows:
                print(f"  Пустой ответ на дату {on_date.isoformat()}, хотя она числится в "
                      "GetDatesForF101 — сама форма 101 недоступна на эту дату для этого банка")
                continue

            summary = summarize(rows)
            n = summary["n"]
            classified = n - summary["counts"][UNKNOWN]
            asset_trillion = summary["totals"][ASSET] / 1_000_000_000
            capital_trillion = summary["totals"][CAPITAL_LIABILITY] / 1_000_000_000
            excluded_trillion = summary["totals"][EXCLUDED] / 1_000_000_000

            print(f"  Строк всего: {n}, классифицировано: {classified} ({classified/n*100:.0f}%)")
            print(f"  АКТИВ: {asset_trillion:.2f} трлн ₽")
            print(f"  КАПИТАЛ/ОБЯЗАТЕЛЬСТВА (частично, разделы 1/6/7 не полны): {capital_trillion:.2f} трлн ₽")
            print(f"  Исключено (не остаток, напр. счёт 303): {excluded_trillion:.2f} трлн ₽")
            if reference:
                coverage = asset_trillion / reference * 100
                print(f"  Независимая сверка активов: {reference:.2f} трлн ₽ — наш расчёт {coverage:.0f}% от неё")
            else:
                print("  Независимая сверка не найдена для этого банка — сравнить не с чем")
            if summary["unknown_rows"]:
                print(f"  Неклассифицированные счета ({len(summary['unknown_rows'])}), не вошли в сумму:")
                for numsc, value in summary["unknown_rows"][:20]:
                    print(f"    {numsc:10s} {value/1_000_000:>14,.1f} млрд ₽")


if __name__ == "__main__":
    main(sys.argv[1:])
