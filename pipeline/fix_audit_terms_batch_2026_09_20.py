# -*- coding: utf-8 -*-
"""«Условия сделки» несут механику торгов, планы после закрытия и чужие поля —
партия по law.terms (аудит 13 сентября). 67 находок по полю, у 55 источник
уже решён читателем (`decided_by_a_reader()`), у ещё 5 занято НАЗНАЧЕНИЕ —
эти 60 остаются в очереди. Здесь — оставшиеся 6, свободные с обеих сторон:

    python3 pipeline/fix_audit_terms_batch_2026_09_20.py
    python3 pipeline/fix_audit_terms_batch_2026_09_20.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move, get_field, set_field  # noqa: E402

# Поле целиком не о согласованном условии — переносится всё.
WHOLE_MOVES = [
    ("cc16fce80", "eco.context"),   # задаток на аукционе — процедура торгов
    ("gafe121ae", "eco.context"),   # капремонт после закрытия — план нового владельца
    ("g10f783e8", "law.struct"),    # шаг аукциона — механика торгов
    ("ce6b8c447", "eco.context"),   # спор Carlsberg с Кабмином — продолжение истории
]

# ektos: детализация сложности согласования — не условие сделки, а часть
# уже описанного разрешения (law.appr); дописывается, не дублирует его.
EKTOS_ID = "ektos"

# ga5b07998: объём работы консультанта продавца — уже назван в law.adv[0],
# но БЕЗ этой детали (только источник); дописывается в note, а не теряется.
ADV_ID = "ga5b07998"
ADV_QUOTE = ("Юридический консультант продавца Better Chance сопровождал HSBC "
             "по всему спектру корпоративных и регуляторных вопросов, включая "
             "интеграцию двух банков в течение переходного периода.")
ADV_DETAIL = ("сопровождал HSBC по всему спектру корпоративных и "
              "регуляторных вопросов, включая интеграцию двух банков в "
              "течение переходного периода")


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, dst in WHOLE_MOVES:
        card = cards[cid]
        full = (card.get("law") or {}).get("terms") or ""
        apply_move(card, "law.terms", full, dst, write, decided, cid, log)

    ektos = cards[EKTOS_ID]
    terms = (ektos.get("law") or {}).get("terms") or ""
    appr = (ektos.get("law") or {}).get("appr") or ""
    if ("ektos", "law.terms") in decided or ("ektos", "law.appr") in decided:
        log.append("ektos: law.terms или law.appr решены читателем — пропущено")
    elif not terms:
        log.append("ektos: law.terms уже пусто — пропущено")
    else:
        new_appr = appr + " " + terms if appr and appr not in ("—", "-") else terms
        log.append("ektos: law.terms → law.appr «%s…»" % terms[:50])
        if write:
            set_field(ektos, "law.appr", new_appr)
            set_field(ektos, "law.terms", "—")

    adv_card = cards[ADV_ID]
    terms = (adv_card.get("law") or {}).get("terms") or ""
    adv_list = (adv_card.get("law") or {}).get("adv") or []
    if ADV_QUOTE not in terms:
        log.append("%s: цитата не найдена дословно — пропущено" % ADV_ID)
    elif (ADV_ID, "law.terms") in decided or (ADV_ID, "law.adv") in decided:
        log.append("%s: law.terms или law.adv решены читателем — пропущено" % ADV_ID)
    elif not adv_list or ADV_DETAIL in (adv_list[0][2] if len(adv_list[0]) > 2 else ""):
        log.append("%s: law.adv не подходит по форме — пропущено" % ADV_ID)
    else:
        role, name, note = adv_list[0][0], adv_list[0][1], adv_list[0][2]
        new_note = note.rstrip(".") + "; " + ADV_DETAIL + "." if note else ADV_DETAIL
        log.append("%s: law.terms → law.adv[0].note «%s…»" % (ADV_ID, ADV_DETAIL[:50]))
        if write:
            adv_list[0] = [role, name, new_note]
            set_field(adv_card, "law.terms", "—")

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
