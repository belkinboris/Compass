# -*- coding: utf-8 -*-
"""Очередь аудита: SUM_NOT_PRICE + TYPE_MISMATCH — первая партия, разобрана
5 параллельными читателями (134 находки: 78 SUM_NOT_PRICE + 56
TYPE_MISMATCH, 130 уникальных ключей — 4 дубля внутри партий). Итог: 76
уникальных fix, 27 not_wrong, 27 defer.

ГЛАВНЫЙ ПРИЁМ SUM_NOT_PRICE — не редактирование текста `sum`, а явное поле
`sum_basis` (deal_multiples.SUM_BASES): оно СИЛЬНЕЕ автоматического разбора
текста и не трогает саму строку `sum` (число остаётся видимым и полезным
читателю, просто помечено, что это не цена сделки). Явно ПЕРЕЗАПИСАН `sum`
(в null) — только когда число описывает нечто, вообще не относящееся к
предмету ЭТОЙ карточки (лимит на будущие сделки программы, объём фонда,
запрошенный отдельный кредит, чужая более ранняя сделка) — таких 6.

TYPE_MISMATCH чинится сменой `type` на другое значение из уже
используемого в базе закрытого списка (M&A, Инвестиция, Продажа с торгов,
IPO, Финансирование · структурная сделка, Создание СП, Реорганизация, СП,
Продажа недвижимости) — новых значений не заводили.

Источник решений — консолидированные `out_0.json`..`out_4.json`
(`data/inbox/audit2/sum_type_out/`, не в git — рабочий вывод пяти
читателей).

ОДНА НАХОДКА ПОЙМАНА ПОЛНЫМ `pytest`, А НЕ ЭТИМ СКРИПТОМ: type→«Продажа
с торгов» на `caeac8f4e` (портфель Raven Russia) уронил `test_data.py::
test_auction_deal_names_its_seller` — у сделки с торгов продавец обязан
быть назван (см. докстроку теста, правило владельца от 9 сентября 2026).
Карточка сама называет продавца дословно (`law.appr`: активы «подлежат
передаче Росимуществу»), и в базе уже есть профиль Росимущества
(`g9fd82fee`), используемый как `seller_id` у десятка похожих карточек с
торгов (`g097e34b2`, `g71aec6a5`, `g01e3fd26` и др.) — `seller`/`seller_id`
дописаны вручную по этому образцу, не этим скриптом.

    python3 pipeline/fix_audit_sum_type_batch1_2026_09_21.py
    python3 pipeline/fix_audit_sum_type_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "sum_type_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
import deal_multiples as dm  # noqa: E402

TYPES = {
    "M&A", "Инвестиция", "Продажа с торгов", "IPO",
    "Финансирование · структурная сделка", "Создание СП", "Реорганизация",
    "СП", "Продажа недвижимости",
}


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()

    by_key: dict = {}
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            by_key.setdefault(it["key"], it)  # первое вхождение — дубли внутри партий совпадают

    log: list = []
    applied = 0
    skipped = 0

    for key, it in by_key.items():
        if it["action"] != "fix":
            continue
        cid, field, new_value = it["card_id"], it["field"], it.get("new_value")
        card = cards.get(cid)
        if card is None:
            log.append("%s (%s): карточки нет — пропущено" % (key, cid))
            skipped += 1
            continue
        if (cid, field) in decided:
            log.append("%s (%s): %s решено читателем review.py — пропущено" % (key, cid, field))
            skipped += 1
            continue
        if field == "sum_basis":
            if new_value not in dm.SUM_BASES:
                log.append("%s (%s): sum_basis %r вне закрытого списка — пропущено" % (key, cid, new_value))
                skipped += 1
                continue
            log.append("%s (%s): sum_basis %r -> %r" % (key, cid, card.get("sum_basis"), new_value))
            applied += 1
            if write:
                card["sum_basis"] = new_value
        elif field == "type":
            if new_value not in TYPES:
                log.append("%s (%s): type %r вне закрытого списка — пропущено" % (key, cid, new_value))
                skipped += 1
                continue
            log.append("%s (%s): type %r -> %r" % (key, cid, card.get("type"), new_value))
            applied += 1
            if write:
                card["type"] = new_value
        elif field == "sum":
            if new_value is not None:
                log.append("%s (%s): sum-фикс с не-null значением вне области партии — пропущено" % (key, cid))
                skipped += 1
                continue
            log.append("%s (%s): sum %r -> None (sum_basis не трогаем)" % (key, cid, card.get("sum")))
            applied += 1
            if write:
                card["sum"] = None
        else:
            log.append("%s (%s): неизвестное поле %r — пропущено" % (key, cid, field))
            skipped += 1

    print("Применено: %d, пропущено: %d" % (applied, skipped))
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
