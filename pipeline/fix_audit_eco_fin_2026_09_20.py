# -*- coding: utf-8 -*-
"""«Форма расчётов» — про то, чем платили, а не про выручку покупателя.

Сквозной паттерн №1 аудита 13 сентября 2026 («eco.fin систематически несёт
финансы покупателя целиком, а не форму расчётов»), 29 находок класса
FIELD_MISPLACED. На карточке это поле подписано «Форма расчётов», и читатель
видел под ним строку вида «Выручка Совкомбанка в 2024 году выросла в два
раза» — ответ не на тот вопрос, который задаёт подпись.

Замер по базе: поле заполнено у 122 карточек, у 16 в нём стоит отчётность
без единого слова о способе оплаты. Разбор по одной: у восьми это показатели
ПОКУПАТЕЛЯ — они уезжают в «Историю и окружение»; у восьми показатели самой
покупаемой компании (или эмитента на размещении) — в «Финансы покупаемой
компании», где для них есть своё поле. Три из шестнадцати скрипт не трогает:
поле-назначение у них дословно записано в таблице правок review.py, то есть
поставлено чтением с цитатой, — такие поля правит чтение, а не скрипт.

Нового утверждения не появляется: текст остаётся тот же, меняется поле, под
какой подписью читатель его видит.

Чтобы не вернулось, признак `fin_is_reporting` добавлен в приёмку карточки.

    python3 pipeline/fix_audit_eco_fin_2026_09_20.py
    python3 pipeline/fix_audit_eco_fin_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
EMPTY = {"", "—", "-", "–"}

# Показатели ПОКУПАТЕЛЯ — это фон сделки, ему место в «Истории и окружении».
TO_CONTEXT = ["g0bbc9e9e", "g55ac5f34", "g5512a325", "gmru-arnest-reckitt",
              "gmru-mariholodmash-borsky"]
# Три карточки из шестнадцати оставлены чтению, а не скрипту: у них поле,
# куда предстояло переехать тексту, дословно записано в таблице правок
# review.py — то есть его поставило чтение с цитатой из источника. Машинная
# правка не спорит с прочитанным (урок того же дня), поэтому «Норникель»/РНК
# (g97e55758), Smartway/ATH (g8e71c525) и офис «Открытия» у ВТБ
# (gmru-vtb-otkrytie-office-rwb) остаются в очереди чтения.
LEFT_TO_READING = ["g97e55758", "g8e71c525", "gmru-vtb-otkrytie-office-rwb"]
# Показатели покупаемой компании (на размещении — самого эмитента).
TO_TARGET_FIN = ["g9c4b80a7", "gaa7602e7", "g4e3b91d7", "g7e470153",
                 "g71bd68cf", "gf9932079", "g2632677b", "g7ce0250d"]


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    moved = []
    for dest, ids in (("context", TO_CONTEXT), ("target_fin", TO_TARGET_FIN)):
        for cid in ids:
            eco = cards[cid]["eco"]
            text = str(eco.get("fin") or "").strip()
            assert text and text not in EMPTY, "%s: «Форма расчётов» уже пуста" % cid
            old = str(eco.get(dest) or "").strip()
            new = text if old in EMPTY else (old + " " + text)
            moved.append((cid, dest, text[:70], len(old)))
            if write:
                eco["fin"] = "—"
                eco[dest] = new
    print("Строк, переехавших из «Формы расчётов»: %d" % len(moved))
    print("Оставлено чтению (поле записано в таблице правок): %d"
          % len(LEFT_TO_READING))
    for cid, dest, text, had in moved:
        where = "Историю и окружение" if dest == "context" else "Финансы покупаемой компании"
        print("   %-30s → %-28s %s…" % (cid, where, text))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
