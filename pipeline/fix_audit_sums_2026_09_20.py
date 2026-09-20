# -*- coding: utf-8 -*-
"""Сумма на «Обзоре» и сумма в «Экономисте» — одна и та же цифра.

Что чинит (класс SUM_FIELDS_DIFFER из аудита 13 сентября 2026, и отдельно
сквозной паттерн №2 того же отчёта):

  A. `eco.sum` пуст, а `sum` заполнен — на вкладке «Экономист» суммы нет
     вовсе, хотя она известна и стоит на «Обзоре».
  B. `eco.sum` — начало `sum`, то есть голая цифра без оговорки, которая
     стоит рядом («230 млн ₽» против «230 млн ₽ за 49% (раскрыто в
     отчётности продавца)»). Читатель «Экономиста» видит цифру без того
     единственного, что объясняет, чем она является.

Нового утверждения тут нет: обе правки переносят внутрь карточки текст,
который в ней уже написан, — то же самое, что перенос условия сделки из
«Контекста» в `law.terms`. Случаи, где `eco.sum` НЕСЁТ БОЛЬШЕ (начальная
цена аукциона, «без учёта долга»), не трогаются: там подробность на своём
месте. Случаи, где поля спорят по существу (963,9 млн ₽ против
14 000 000 013,13 ₽), — это чтение, а не скрипт.

    python3 pipeline/fix_audit_sums_2026_09_20.py           # показать
    python3 pipeline/fix_audit_sums_2026_09_20.py --write   # записать
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
EMPTY = {"", "—", "-", "–"}


def norm(s) -> str:
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = (s.replace(" ", " ").replace("~", "≈")
          .replace("−", "-").replace("–", "-").replace("—", "-"))
    return re.sub(r"\s+", " ", s).strip().strip(".")


def tail_of(full: str, head: str) -> str:
    """Хвост `sum` после той части, которая уже стоит в `eco.sum`.

    Дописываем именно хвост, а не подменяем поле целиком: в «Экономисте»
    может стоять «≈1 млрд ₽», а на «Обзоре» — «~1 млрд ₽ (по оценке)», и
    замена поля целиком принесла бы на экран тильду вместо знака «≈».
    """
    need, got, i = norm(head), "", 0
    while i < len(full) and norm(got) != need:
        got += full[i]
        i += 1
    assert norm(got) == need, (full, head)
    return full[i:].strip()


def decided_by_a_reader() -> set:
    """Поля, по которым читатель уже принял решение (таблица FIXES в review.py).

    Урок того же дня: скрипт сначала переписал `eco.sum` у семи карточек,
    где чтение с цитатой из источника НАМЕРЕННО поставило голую цифру без
    оговорки «(по оценке)» — и сломал инвариант «строка таблицы правок
    применена к базе». Машинная правка не спорит с прочитанным: такие поля
    скрипт не трогает вовсе.
    """
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
    import review
    return {(f["id"], f.get("field")) for f in review.FIXES}


def plan(data: dict) -> tuple:
    decided = decided_by_a_reader()
    fill, widen, leave = [], [], []
    for d in data["deals"]:
        eco = d.get("eco")
        if not isinstance(eco, dict):
            continue
        s = (d.get("sum") or "").strip()
        e = (eco.get("sum") or "").strip()
        if not s or s == "Не раскрыта":
            continue
        if (d["id"], "eco.sum") in decided:
            continue
        ns, ne = norm(s), norm(e)
        if e in EMPTY:
            fill.append((d["id"], s))
        elif ns == ne:
            continue
        elif ns.startswith(ne) and len(ns) > len(ne):
            widen.append((d["id"], e, s))
        else:
            leave.append((d["id"], s, e))
    return fill, widen, leave


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    fill, widen, leave = plan(data)

    by_id = {d["id"]: d for d in data["deals"]}
    for cid, s in fill:
        assert (by_id[cid]["eco"].get("sum") or "").strip() in EMPTY
        if write:
            by_id[cid]["eco"]["sum"] = s
    widened = []
    for cid, old, s in widen:
        assert norm(s).startswith(norm(old)), (cid, old, s)
        new = ("%s %s" % (old, tail_of(s, old))).strip()
        assert norm(new) == norm(s), (cid, new, s)
        widened.append((cid, old, new))
        if write:
            by_id[cid]["eco"]["sum"] = new

    print("Пустая сумма в «Экономисте» заполнена с «Обзора»: %d" % len(fill))
    for cid, s in fill[:5]:
        print("   %s  → %s" % (cid, s[:60]))
    print("Голая цифра дополнена оговоркой с «Обзора»: %d" % len(widen))
    for cid, old, new in widened[:5]:
        print("   %s  «%s» → «%s»" % (cid, old[:32], new[:60]))
    print("Оставлено чтению (поля спорят по существу или «Экономист» "
          "подробнее): %d" % len(leave))

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
