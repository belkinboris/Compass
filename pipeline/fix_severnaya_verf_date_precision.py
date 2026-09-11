# -*- coding: utf-8 -*-
"""Карточка g0931ed04 («Северная верфь» получила 100% акций пяти
национализированных компаний) несла дату «2026-08» — формат
«год-месяц», не входящий в три допустимых вида (`YYYY-MM-DD`, `YYYY`,
`unknown`; см. test_data.py::test_dates_are_parseable). Источник (dp.ru)
называет ПЯТЬ разных дат регистрации права собственности в течение
двух месяцев (9 и 21 июля, 1, 4 и 13 августа 2026 года) — единого дня
для события нет, и выдумывать один было бы неверно. Тот же принцип, что
уже применяется к датам, где источник называет месяц и год, но не число
(fix_osnova_sviblovo_date.py): в `date` остаётся только год, подробность
(диапазон дат и то, что регистраций было пять) уже дословно стоит в
`law.struct` и не теряется. То же для `events[0].date` — единственное
событие карточки описывает тот же растянутый во времени факт.

Запуск: python3 pipeline/fix_severnaya_verf_date_precision.py [--write]
"""
import json
import sys

PATH = "static/data/deals_promoted.json"


def main(write: bool) -> None:
    data = json.load(open(PATH, encoding="utf-8"))
    card = next(d for d in data["deals"] if d["id"] == "g0931ed04")

    assert card["date"] == "2026-08", card["date"]
    assert card["events"][0]["date"] == "2026-08", card["events"][0]["date"]
    assert "9 и 21 июля, 1, 4 и 13 августа" in card["law"]["struct"]

    card["date"] = "2026"
    card["events"][0]["date"] = "2026"

    print("g0931ed04: date/events[0].date 2026-08 -> 2026")

    if write:
        json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(PATH, "a", encoding="utf-8").write("\n")
        print("Записано.")
    else:
        print("Сухой прогон. Запись — с ключом --write.")


if __name__ == "__main__":
    main("--write" in sys.argv)
