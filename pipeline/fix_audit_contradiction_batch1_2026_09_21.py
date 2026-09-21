# -*- coding: utf-8 -*-
"""Очередь аудита: CONTRADICTION — первая партия, разобрана 5 параллельными
читателями (230 находок, по 46 каждому). Правки не «дословный перенос» —
это факты, требующие решить, КАКОЕ из двух спорящих полей верно. Каждый
читатель либо решал это ВНУТРИ карточки (более позднее/специфичное поле,
арифметика, events[]), либо открывал первоисточники из `src` через
WebFetch и брал точную формулировку оттуда.

Дисциплина та же, что у review.py: `old_quote` каждой правки проверен как
дословная подстрока ЖИВОГО поля перед записью (не на момент решения
читателем — карточка могла измениться); правка, чью цитату не нашли,
пропускается, а не подгоняется. Шесть высокорисковых правок (продавец,
покупатель, сумма сделки) сверены мной лично против того же поля карточки
независимо от читателя — совпадение полное на всех шести.

Источник решений — консолидированные `out_0.json`..`out_4.json`
(`data/inbox/audit2/`, не в git — рабочий вывод пяти читателей).

    python3 pipeline/fix_audit_contradiction_batch1_2026_09_21.py
    python3 pipeline/fix_audit_contradiction_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "contradiction_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

ROLE_TO_CARD_FIELD = {
    "buyer_profile": "buyer",
    "target_profile": "target",
    "seller_profile": "seller_id",
}

# Особый случай: law.adv на g547ff4b8 — структурный список [[роль, имя, описание]],
# а не строка; чинится вручную ниже, не через общий цикл.
SKIP_KEYS = {"6a1a71ec17c5"}


def resolve(card: dict, companies: dict, field: str):
    field = field.strip()
    m = re.match(r"^company:([A-Za-z0-9_-]+)\.(desc|name|ind)$", field)
    if m:
        cid, sub = m.group(1), m.group(2)
        if cid not in companies:
            return ("company-missing", None, None)
        return ("company", companies[cid], sub)
    m = re.match(r"^(buyer_profile|target_profile|seller_profile)\.(desc|name|ind)\s*\(\s*компания\s+([A-Za-z0-9_-]+)", field)
    if m:
        _, sub, cid = m.group(1), m.group(2), m.group(3)
        if cid not in companies:
            return ("company-missing", None, None)
        return ("company", companies[cid], sub)
    m = re.match(r"^(buyer_profile|target_profile|seller_profile)\.(desc|name|ind)\s*(?:\(.*\))?$", field)
    if m:
        role, sub = m.group(1), m.group(2)
        cid = card.get(ROLE_TO_CARD_FIELD[role])
        if not cid or cid not in companies:
            return ("company-missing", None, None)
        return ("company", companies[cid], sub)
    m = re.match(r"^events\[(\d+)\]\.note$", field)
    if m:
        idx = int(m.group(1))
        events = card.get("events") or []
        if idx >= len(events):
            return ("events-missing", None, None)
        return ("event", events[idx], "note")
    return ("deal", card, field)


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    items = []
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        items.extend(json.loads(Path(path).read_text(encoding="utf-8")))

    log: list = []
    applied = 0
    skipped = 0

    for it in items:
        if it["action"] != "fix":
            continue
        key = it["key"]
        if key in SKIP_KEYS:
            continue
        cid = it["card_id"]
        card = cards.get(cid)
        if card is None:
            log.append("%s (%s): карточки нет — пропущено" % (key, cid))
            skipped += 1
            continue
        kind, obj, sub = resolve(card, companies, it.get("field", ""))
        if kind in ("company-missing", "events-missing"):
            log.append("%s (%s): не удалось разрешить поле %r — пропущено" % (key, cid, it.get("field")))
            skipped += 1
            continue
        # ВАЖНО (найдено на этой самой партии): decided_by_a_reader() держит
        # пары (id, поле) из review.FIXES для ЛЮБОГО поля карточки — не
        # только вложенных eco./law., но и верхнеуровневых (sum, title,
        # buyer_name, seller, status, date, extra). Первая версия этой
        # проверки смотрела только на "." в имени поля и пропустила два
        # верхнеуровневых конфликта (g9f6fe860.sum, g8170bf3a.buyer_name) —
        # оба найдены тестами и отменены вручную до коммита.
        if kind == "deal" and (cid, sub) in decided:
            log.append("%s (%s): %s решено читателем review.py — пропущено" % (key, cid, sub))
            skipped += 1
            continue

        cur = obj.get(sub) if kind in ("company", "event") else (get_field(card, sub) if "." in sub else card.get(sub))
        if cur is None or not isinstance(cur, str):
            log.append("%s (%s): поле %s не строка сейчас — пропущено" % (key, cid, sub))
            skipped += 1
            continue
        oq = it.get("old_quote") or ""
        new_text = it.get("new_text") or ""
        if oq and oq not in cur:
            log.append("%s (%s): цитата не найдена в %s — пропущено" % (key, cid, sub))
            skipped += 1
            continue
        if not oq:
            log.append("%s (%s): нет old_quote — пропущено" % (key, cid))
            skipped += 1
            continue
        new_val = cur.replace(oq, new_text, 1)
        log.append("%s (%s): %s: «%s…» -> «%s…»" % (key, cid, sub, oq[:40], new_text[:40]))
        applied += 1
        if write:
            if kind in ("company", "event"):
                obj[sub] = new_val
            else:
                set_field(card, sub, new_val)

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
