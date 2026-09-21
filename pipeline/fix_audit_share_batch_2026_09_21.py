# -*- coding: utf-8 -*-
"""«Предмет / доля» (eco.share) пуст, хотя доля прямо названа рядом — партия
по eco.share (аудит 13 сентября). Из 17 находок этого поля 10 требуют
переноса ЧУЖОГО содержимого ИЗ eco.share (история, механика, хронология) —
почти все такие переносы упираются в занятое назначение (eco.context/
eco.rationale уже решены читателем) и остаются в очереди; здесь — 5
переносов extra→eco.share (поле пусто, доля уже названа в extra) плюс
одна очистка: eco.share нёс имя основателя предмета, а этот же факт уже
дословно стоит в desc профиля предмета — перенос никуда не нужен, поле
просто честно освобождается.

    python3 pipeline/fix_audit_share_batch_2026_09_21.py
    python3 pipeline/fix_audit_share_batch_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move  # noqa: E402

MOVES = [
    ("gf9b54ee7",
     "купил 20% акционерного капитала Tasty Coffee у основателей компании",
     "eco.share"),
    ("gca59a6b6",
     "РФПИ продал 15,9% в ООО «Ла Лоррен Рус» турецкому подразделению La "
     "Lorraine Bakery Group.",
     "eco.share"),
    ("gb21ab6d1",
     "Размещено 121 млн акций (13,14% капитала) по цене, определившей "
     "стоимость компании в 8,75 млрд ₽ (post-money).",
     "eco.share"),
    ("g2469d33a",
     "«СберИнвест», структура Сбера, приобрёл 12% акционерного капитала "
     "«Аквариуса» — производителя высокотехнологичного оборудования.",
     "eco.share"),
    ("gb6b5625e",
     "ГК «Первая Портовая Компания», принадлежащая Владимиру Лисину, "
     "продала 91,63% акций АО «Таганрогский морской торговый порт» "
     "компании «Лемар».",
     "eco.share"),
]

# gb0f1f736: eco.share нёс только имя основателя — этот же факт дословно
# уже стоит в desc профиля предмета (g71a251f8), переносить некуда и не
# нужно, поле освобождается.
FOUNDER_ID = "gb0f1f736"
FOUNDER_OLD = "Основатель и генеральный директор WhoIsBlogger — Лев Грунин."


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, quote, dst in MOVES:
        card = cards[cid]
        apply_move(card, "extra", quote, dst, write, decided, cid, log)

    card = cards[FOUNDER_ID]
    cur = (card.get("eco") or {}).get("share")
    if cur != FOUNDER_OLD:
        log.append("%s: eco.share не совпало — пропущено" % FOUNDER_ID)
    elif (FOUNDER_ID, "eco.share") in decided:
        log.append("%s: eco.share решено читателем — пропущено" % FOUNDER_ID)
    else:
        log.append("%s: eco.share очищен (факт уже в desc профиля предмета)" % FOUNDER_ID)
        if write:
            card["eco"]["share"] = "—"

    print("Записей: %d" % len(log))
    for line in log:
        print("   " + line)

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
