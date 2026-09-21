# -*- coding: utf-8 -*-
"""Карточка, которую ворота не должны были пропустить, — обратно в сомнительные.

ЗАЧЕМ. 21 сентября владелец открыл консоль и увидел 🗂 «карточку», у которой
заголовок — обрезанный на полуслове кусок телеграм-поста («…В периметр сделки
вошли»), предмет — обрубок фразы («…и систем автом»), кавычки чужого
начертания, отрасль «Недвижимость» у производителя складских роботов. Рядом
стояла кнопка «Опубликовать». Его слова: «это не должно было как карточка
показаться, а должно было показаться как сомнительное» — то есть так же, как
ворота правильно поступили с новостью про выборы на Херсонщине в тот же час.

Причину чинит сам гейт (`promote.TITLE_CUT_LEN`/`ASSET_CUT_LEN`, замер там же)
и `draft.normalize_quotes` (направленные кавычки “ ” мимо неё проходили). Но
эта карточка проскочила ДО починки и уже лежит в очереди модерации — гейт
задним числом её не тронет. Скрипт переносит её туда, где ей место: из
`static/data/pending.json` (🗂, с кнопкой «Опубликовать») в очередь
придержанных черновиков (⚠️, кнопки «это сделка — в работу» / «не сделка»).

Ничего не теряется: все поля черновика сохраняются, решение остаётся за
владельцем — меняется только то, КАК вопрос задан. Молчание над сырьём не
публикует никогда, в отличие от карточки.

    python3 pipeline/move_cut_draft_back_to_doubtful_2026_09_21.py
    python3 pipeline/move_cut_draft_back_to_doubtful_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PENDING = ROOT / "static" / "data" / "pending.json"
HOLD = ROOT / "data" / "inbox" / "hold" / "2026-09-21.json"
CARD_ID = "g93c8bc42"
# draft_id выводится из id карточки, чтобы повторный запуск не завёл второй
# черновик и чтобы решение владельца («не сделка») запомнилось за ним же.
DRAFT_ID = "d" + CARD_ID[1:]


def main(write: bool) -> int:
    from pipeline.ingest import promote

    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    cards = pending.get("cards") or []
    card = next((c for c in cards if c.get("id") == CARD_ID), None)
    if card is None:
        print("Карточки %s в очереди нет — переносить нечего." % CARD_ID)
        return 0
    if card.get("accepted") or card.get("reviewed"):
        print("У карточки %s стоит штамп чтения — это уже не сырьё, "
              "перенос отменён." % CARD_ID)
        return 1

    base = json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))
    _bad, hold_reasons = promote.check(dict(card), base, {}, [card.get("ind")])
    hold_reasons = [r for r in hold_reasons if "отрасл" not in r]
    print("Причины, по которым ворота придержали бы её сегодня:")
    for r in hold_reasons:
        print("   • %s" % r)
    if not hold_reasons:
        print("Сегодняшние ворота её пропускают — перенос не нужен.")
        return 1

    draft = {k: v for k, v in card.items()
             if k not in ("id", "pending_since", "facts", "post_preview")}
    draft["draft_id"] = DRAFT_ID
    draft["hold_reasons"] = hold_reasons
    draft["moved_from_card"] = CARD_ID

    held = json.loads(HOLD.read_text(encoding="utf-8")) if HOLD.exists() else {"drafts": []}
    drafts = held.setdefault("drafts", [])
    if any(d.get("draft_id") == DRAFT_ID for d in drafts):
        print("\nЧерновик %s уже в очереди сомнительных." % DRAFT_ID)
    else:
        drafts.append(draft)
    rest = [c for c in cards if c.get("id") != CARD_ID]

    print("\nКарточек в очереди: %d -> %d; сомнительных: %d" % (len(cards), len(rest), len(drafts)))
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    pending["cards"] = rest
    PENDING.write_text(json.dumps(pending, ensure_ascii=False, indent=1), encoding="utf-8")
    HOLD.write_text(json.dumps(held, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
