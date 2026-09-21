# -*- coding: utf-8 -*-
"""Очередь аудита: ROLE_WRONG — первая партия, только relink на уже
существующий в базе профиль (5 параллельных читателей, 96 находок). Заводить
новые профили здесь не входит в задачу (см. `link_parties.py`'s docstring —
это отдельная кампания с проверкой ИНН и однофамильцев); такие находки
остаются в очереди с пометкой, какое юрлицо нужно завести.

Одна находка (ga4d82b1c) — не просто relink, а перенос: профиль «Данон
Россия» стоял в `seller_id`, хотя это ПРЕДМЕТ сделки (проданный бизнес), а
не продавец — переносится в `target`, `seller_id` остаётся пустым (профиля
материнской Danone в базе нет, заводить его не входит в эту партию).

Находка на карточке `ksk` (target) НЕ применяется: `target` этой карточки
уже решено читателем через review.py — «машинная правка не спорит с
прочитанным».

ВТОРОЙ БАГ ЭТОЙ ПАРТИИ, пойманный полным `pytest` (`test_one_company_
holds_one_role_in_a_deal`, `test_buyer_is_named_once`), а не найден заранее:
relink чинит поле-НАЗНАЧЕНИЕ, но три находки прошлой ночи явно
предупреждали, что тот же профиль до этого ОШИБОЧНО стоял ещё и в СОСЕДНЕМ
поле («роль» перепутана, а не просто «связь отсутствует») — механический
relink это не чистит сам. Три карточки после relink оказались с одной
компанией в двух ролях сразу (`g0cf6a562`, `g5a1d102f`: buyer=target;
`gb0c3ddbf`: target=seller_id), и одна — с конфликтом свежего `buyer` и уже
решённого читателем `buyer_name` (`g1dc82018`). Починено вручную, не через
`--write` этого скрипта:
- `g0cf6a562`, `g5a1d102f`, `gb0c3ddbf`: `target` очищен (`None`) — старый
  профиль там был предметом ДРУГОЙ путаницы (актив без профиля/сам продавец
  по ошибке), верного профиля предмета ещё нет, заводить его — вне этой
  партии.
- `g1dc82018`: relink `buyer` отменён (снова `None`) — `buyer_name`
  («Садовое кольцо») уже стоит через `review.py`'s таблицу правок и
  заблокирован, а два источника имени покупателя сразу ловит отдельный
  тест; менять решение читателя отсюда нельзя.
См. `KNOWN_ISSUES.md`, «Relink роли не чистит тот же профиль в соседней
роли той же карточки».

    python3 pipeline/fix_audit_role_wrong_batch1_2026_09_21.py
    python3 pipeline/fix_audit_role_wrong_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "role_wrong_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402

SKIP_KEYS = {"87586109c96a"}  # ksk/target — решено читателем, см. docstring

# ga4d82b1c: relink target=g8cf40802 И seller_id -> None (перенос, не просто relink)
MOVE_NOT_JUST_RELINK = {"2284a194a46c"}


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
        if it["action"] != "relink" or it["key"] in SKIP_KEYS:
            continue
        key, cid, field, target_id = it["key"], it["card_id"], it.get("field"), it.get("correct_company_id")
        card = cards.get(cid)
        if card is None or target_id not in companies or field not in ("buyer", "target", "seller_id"):
            log.append("%s (%s): не удалось разрешить — пропущено" % (key, cid))
            skipped += 1
            continue
        if (cid, field) in decided:
            log.append("%s (%s): %s решено читателем review.py — пропущено" % (key, cid, field))
            skipped += 1
            continue
        old = card.get(field)
        log.append("%s (%s): %s %r -> %r (%s)" % (key, cid, field, old, target_id, companies[target_id]["name"]))
        applied += 1
        if write:
            card[field] = target_id
        if key in MOVE_NOT_JUST_RELINK:
            if (cid, "seller_id") in decided:
                log.append("%s (%s): seller_id решено читателем — старое значение НЕ снято" % (key, cid))
            else:
                log.append("%s (%s): seller_id очищен (перенесён в %s)" % (key, cid, field))
                if write:
                    card["seller_id"] = None

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
