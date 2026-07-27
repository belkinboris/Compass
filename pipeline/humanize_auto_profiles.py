#!/usr/bin/env python3
"""Убирает внутреннюю кухню из описаний автоматических профилей компаний.

ЧТО СЛОМАНО
    У 516 профилей из 1846 (28%) поле `desc` — это описание нашего процесса
    разработки, показанное клиенту как описание компании:

        «Профиль сформирован по итогам чтения bulk-базы (партия 4, 2022+);
         уточняется по мере поступления информации.»

    Юрист, открывший карточку компании, читает про «bulk-базу», «партию 4» и
    «тестовый прогон» — слова, которые не значат для него ничего. Всего восемь
    таких формулировок, различаются они только номером партии, то есть несут
    информацию исключительно для нас.

ПОЧЕМУ ИМЕННО ТАК
    Описания компании у нас нет — и выдумывать его нельзя (принцип 1). Поэтому
    новая фраза не притворяется описанием, а честно говорит, чего не хватает и
    откуда профиль взялся. Одна формулировка на все: номер партии — наша
    внутренняя разметка, клиенту она не нужна.

КАК ЗАПУСКАТЬ
    python3 pipeline/humanize_auto_profiles.py            # сухой прогон
    python3 pipeline/humanize_auto_profiles.py --write    # записать
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "static" / "data" / "deals_promoted.json"

# Признак «описание — это рассказ о процессе», а не о компании. Якорим с начала:
# фраза всегда начинается со слов «Профиль сформирован», а внутри — bulk/партия.
PROCESS_DESC = re.compile(
    r"^Профиль\s+сформирован\s+по\s+итогам\s+.{0,80}?bulk[^.]*\.\s*$", re.I)

NEW_DESC = ("Описание компании пока не заполнено: профиль собран автоматически "
            "по сделкам, где она упоминается.")


def main() -> int:
    write = "--write" in sys.argv
    data = json.loads(SRC.read_text(encoding="utf-8"))
    companies = data["companies"]

    targets = {cid: c for cid, c in companies.items()
               if PROCESS_DESC.match(str(c.get("desc") or "").strip())}

    # Проверка исходного состояния: если данные уже другие, падаем, а не портим.
    assert targets, "не найдено ни одного профиля с описанием-процессом — данные уже изменены?"
    assert all(c.get("kpi") == ["Профиль", "Автоматический"] for c in targets.values()), \
        "ожидались только автоматические профили; найден выверенный вручную"
    assert NEW_DESC not in {c.get("desc") for c in companies.values()}, \
        "скрипт уже применён"

    variants = {}
    for c in targets.values():
        variants[c["desc"]] = variants.get(c["desc"], 0) + 1

    print(f"профилей всего: {len(companies)}")
    print(f"с описанием-процессом: {len(targets)} ({len(targets) * 100 // len(companies)}%)")
    print(f"формулировок: {len(variants)}")
    for text, n in sorted(variants.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4} × {text[:90]}")
    print(f"\nстанет одной строкой:\n  {NEW_DESC}")

    if not write:
        print("\nсухой прогон. Записать: --write")
        return 0

    for c in targets.values():
        c["desc"] = NEW_DESC
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nзаписано: {len(targets)} профилей")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
