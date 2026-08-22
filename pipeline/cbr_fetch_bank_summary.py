# -*- coding: utf-8 -*-
"""Живой прогон: тянет форму 101 у ЦБ по нескольким банкам, классифицирует
счета (`cbr_account_types.py`) и печатает итог активов/капитала с проверкой
по независимому числу. НИЧЕГО НЕ ПИШЕТ — ни в базу, ни на сайт.

ЗАЧЕМ ЭТОТ СКРИПТ. Сеть разработки Claude Code, закрытая к cbr.ru в одной
сессии (см. CLAUDE.md), не константа проекта — 22 августа 2026, в другой
сессии, сеть до cbr.ru и api-fns.ru оказалась открыта, и полный живой прогон
на всех трёх банках получился прямо здесь. Урок общий («сеть в среде
разработки работает — не значит, что она не работает» — и наоборот, не
значит, что не работает СЕЙЧАС, если не работала раньше): проверять самому в
конкретной сессии, а не переносить вывод из session в session как данность.
Если снова закрыто — тот же протокол собирается вручную через терминал
владельца, командами по одной (так теряли большую часть первого набора
данных 18 августа) — этот скрипт делает то же самое одной командой.

ЗАПУСК:
    python3 pipeline/cbr_fetch_bank_summary.py
    python3 pipeline/cbr_fetch_bank_summary.py --date 2026-07-01
    python3 pipeline/cbr_fetch_bank_summary.py --bank 1481:Сбербанк --bank 1000:ВТБ

ЖИВОЙ ПРОГОН 22 АВГУСТА 2026 (raздел 1 «Капитал» дочитан целиком по полному
тексту 809-П, см. cbr_account_types.py) — покрытие ~51-53% строк по всем
трём банкам (раздел 1 — почти всегда 4-5 строк из ~190, остальное не
классифицировано — разделы 5-9 ещё не сверены построчно), независимая
сверка активов: Сбербанк 109% (71,78 / 66,09 трлн ₽, TAdviser), ВТБ 99%
(37,64 / 38,0 трлн ₽, МСФО группы — не то же самое, что юрлицо по РСБУ,
сверка приблизительная), Альфа-Банк 108% (15,40 / 14,27 трлн ₽, TAdviser,
число впервые найдено в этом прогоне). Устойчивый лёгкий перебор
(108-109%) у ДВУХ банков из трёх, а не у одного, — не случайный шум с
одной выборки (урок «первая выборка не выбирает себя по самому
заметному»), но и не ошибка сегодняшней правки раздела 1: коды 105/109/111
(добавленные сегодня) не встретились НИ У ОДНОГО из трёх банков в сырых
данных на эту дату — раздел 1 не мог сместить итог. Источник перебора не
найден — вероятный кандидат: раздел 5-9 (ещё не сверен построчно с
законом), не раздел 1. Не гнаться за этим сегодня — задача была именно
«дочитать раздел 1, сверить на трёх банках», а не «добиться 100%».

ЧТО ДЕЛАТЬ С РЕЗУЛЬТАТОМ. Это диагностика, не источник для сайта. Прежде
чем подключать что-либо к `main.py`, нужно: (1) покрытие близко к 100%, не
51-53%; (2) источник устойчивого 108-109% перебора у Сбербанка/Альфа-Банка
найден и объяснён, не только измерен; (3) разделы 5-9 `cbr_account_types.py`
сверены построчно с действующим 809-П так же, как сегодня раздел 1 (и уже
были сверены разделы 2-4).
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
    (1326, "Альфа-Банк", 14.27),  # TAdviser, 2026 — найдено 22 августа (WebSearch/WebFetch),
                                   # прежде «точное число не найдено»
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
