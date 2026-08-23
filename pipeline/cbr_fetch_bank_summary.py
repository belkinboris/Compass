# -*- coding: utf-8 -*-
"""Живой прогон: тянет форму 101 у ЦБ по нескольким банкам, классифицирует
строки (`cbr_account_types.py`) и печатает итог активов/пассивов с проверкой
по независимому числу. НИЧЕГО НЕ ПИШЕТ — ни в базу, ни на сайт.

ЗАЧЕМ ЭТОТ СКРИПТ. Сеть разработки Claude Code, закрытая к cbr.ru в одной
сессии (см. CLAUDE.md), не константа проекта — в разных сессиях сеть до
cbr.ru то открыта, то закрыта, и это надо проверять самому в каждой
конкретной сессии, а не переносить вывод из session в session как данность.
Если закрыто — тот же протокол собирается вручную через терминал владельца,
командами по одной; этот скрипт делает то же самое одной командой, когда
сеть есть.

23 АВГУСТА 2026 — МЕТОД ПЕРЕПИСАН. Прежние прогоны (18-22 августа) угадывали
актив/пассив по тексту 809-П вручную для каждого счёта и не фильтровали
ответ по `pln` (глава плана счетов) — суммировали вместе балансовые счета
банка с внебалансовыми (гарантии, поручительства) и производными
инструментами. Официальный формат формы 0409101
(https://www.cbr.ru/vfs/credit/formats/101-20181201.PDF) показал, что поле
`ap` УЖЕ несёт разметку актив/пассив источника (1/2), а `pln` — что
`Data101FNewXML` отдаёт сразу пять глав плана счетов, из которых баланс
банка — только «А». Подробности и следующий нерешённый вопрос (gross vs
net — независимая сверка показывает ЧИСТЫЕ активы банка, наша сумма
по `ap` — ВАЛОВЫЕ, разница ~3-11%) — в докстроке `cbr_account_types.py`.

ЖИВОЙ ПРОГОН 23 АВГУСТА 2026 (после перехода на `ap`/`pln`, все три банка,
2026-07-01): покрытие строк `pln=="А"` — фактически 100% (ничего не остаётся
неклассифицированным, кроме проверочных строк ITGAP и 4 известных
счетов-транзитов). Независимая сверка активов: Сбербанк 111% (73,61 / 66,09
трлн ₽), ВТБ 103% (39,23 / 38,0 трлн ₽), Альфа-Банк 108% (15,49 / 14,27 трлн
₽). Тот же порядок переучёта, что и у прежнего, менее точного метода
(108-109%) — значит, причина не в старой ошибке фильтрации по `pln` (она
реальна и исправлена, но не была источником переучёта), а в чём-то другом:
рабочая гипотеза — gross/net, см. `cbr_account_types.py`.

ЧТО ДЕЛАТЬ С РЕЗУЛЬТАТОМ. Это диагностика, не источник для сайта. Прежде
чем подключать что-либо к `main.py`, нужно решить вопрос gross/net
(`cbr_account_types.py`, последний абзац докстроки) — либо найти и вычесть
резервы/корректировки, либо осознанно показывать валовую оценку с честной
пометкой погрешности.

ЗАПУСК:
    python3 pipeline/cbr_fetch_bank_summary.py
    python3 pipeline/cbr_fetch_bank_summary.py --date 2026-07-01
    python3 pipeline/cbr_fetch_bank_summary.py --bank 1481:Сбербанк --bank 1000:ВТБ
"""
import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cbr_client import CbrClientError, CbrCreditOrgClient  # noqa: E402
from pipeline.cbr_account_types import ASSET, CAPITAL_LIABILITY, EXCLUDED, UNKNOWN, classify_row  # noqa: E402

# (CredorgNumber, имя, независимая сверка по активам в трлн ₽ или None)
DEFAULT_BANKS = [
    (1481, "Сбербанк", 66.09),   # TAdviser, 2026
    (1000, "ВТБ", 38.0),         # МСФО, группа целиком, март 2026 — не то же самое,
                                  # что юрлицо по РСБУ (форма 101), сверка приблизительная
    (1326, "Альфа-Банк", 14.27),  # TAdviser, 2026
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
        pln = row.get("pln", "")
        numsc = row.get("numsc", "")
        ap = row.get("ap", "")
        value = float(row.get("iitg") or 0)
        kind, reason = classify_row(pln, numsc, ap)
        totals[kind] += value
        counts[kind] += 1
        if kind == UNKNOWN:
            unknown_rows.append((numsc, value, reason))
    return {"totals": totals, "counts": counts, "unknown_rows": unknown_rows, "n": len(rows)}


def latest_available_date(client: CbrCreditOrgClient, credorg: int) -> date | None:
    """Банки отчитываются на конкретные даты (обычно 1-е число месяца), не
    каждый день — по умолчанию `date.today()` почти всегда пустой ответ.
    `GetDatesForF101` уже написан для ровно этого случая — берём из него
    последнюю доступную дату вместо угадывания."""
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

            print(f"  Строк всего: {n}, классифицировано (не UNKNOWN): {classified} ({classified/n*100:.0f}%)")
            print(f"  АКТИВ (pln=А, ap=1, без счетов-транзитов): {asset_trillion:.2f} трлн ₽")
            print(f"  ПАССИВ (pln=А, ap=2, без счетов-транзитов): {capital_trillion:.2f} трлн ₽")
            print(f"  Исключено (внебаланс/производные/депо/счета-транзиты): {excluded_trillion:.2f} трлн ₽")
            if reference:
                coverage = asset_trillion / reference * 100
                print(f"  Независимая сверка активов: {reference:.2f} трлн ₽ — наш расчёт {coverage:.0f}% от неё "
                      "(gross vs net, см. докстроку cbr_account_types.py)")
            else:
                print("  Независимая сверка не найдена для этого банка — сравнить не с чем")
            if summary["unknown_rows"]:
                print(f"  Строки с неожиданным A_P ({len(summary['unknown_rows'])}), не вошли в сумму:")
                for numsc, value, reason in summary["unknown_rows"][:20]:
                    print(f"    {numsc:10s} {value/1_000_000:>14,.1f} млрд ₽  {reason}")


if __name__ == "__main__":
    main(sys.argv[1:])
