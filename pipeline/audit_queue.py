# -*- coding: utf-8 -*-
"""Очередь находок аудита адреса фактов (13 сентября 2026, 2420 записей).

ЗАЧЕМ ОТДЕЛЬНЫЙ ФАЙЛ. Сам аудит данные не менял — он оставил список. Список
без памяти о сделанном перечитывается каждым прогоном заново и дорожает сам
(тот же урок, что про журнал в PRODUCT_ROADMAP). Здесь три вещи, которых у
списка не было:

1. ЖИВОЕ СОСТОЯНИЕ. Находка сентября могла уже не описывать сегодняшнюю
   карточку: карточку дополнили, слили с другой, поле починили. Для тех
   классов, где дефект виден из самих данных, состояние считается заново —
   поэтому очередь не заставляет открывать то, что уже в порядке.
2. ПАМЯТЬ. Разобранная находка записывается в audit_queue_done.json вместе с
   тем, чем она закрыта. Прочитанное и отклонённое («это не дефект») тоже
   закрывается — иначе оно вернётся в очередь следующим прогоном.
3. ПОРЯДОК. Сначала то, что искажает факт сделки (роль не туда, поля спорят),
   потом косметика. Приоритет взят из самого отчёта аудита.

    python3 pipeline/audit_queue.py --stats
    python3 pipeline/audit_queue.py --queue --class CONTRADICTION --limit 20
    python3 pipeline/audit_queue.py --mark <ключ> --note "чем закрыто"
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS = os.path.join(ROOT, "pipeline", "audit_field_placement", "findings.json")
DONE = os.path.join(ROOT, "pipeline", "audit_queue_done.json")
DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")

# Порядок разбора: сверху то, что врёт о сделке, снизу — то, что её не искажает.
PRIORITY = [
    "SELF_SALE", "ROLE_WRONG", "CONTRADICTION", "STATUS_MISMATCH",
    "DATE_MISMATCH", "SUM_NOT_PRICE", "TYPE_MISMATCH", "FIELD_MISPLACED",
    "FALSE_PLACEHOLDER", "ROLE_MISSING", "UNLINKED_PARTY",
    "PROFILE_DESC_IS_EVENT", "ASSET_IS_DESCRIPTION", "SUM_FIELDS_DIFFER",
    "STALE_STATEMENT", "PARTY_IN_ASSET_NAME", "TRUNCATED", "JARGON",
    "DUPLICATE_TEXT", "SOURCE_MISMATCH", "PRESS_LANGUAGE", "LONG_QUOTE",
    "OTHER", "UNREADABLE",
]

ROLE_FIELDS = {"asset": "target", "buyer_name": "buyer", "seller": "seller_id"}
JARGON_RE = re.compile(r"(Компания:|Персона:|История \d{4}:|Продукт:)")
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def key_of(f: dict) -> str:
    raw = "%s|%s|%s" % (f.get("card_id"), f.get("class"), f.get("quote"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def load_findings() -> list:
    return json.load(io.open(FINDINGS, encoding="utf-8"))["findings"]


def load_done() -> dict:
    if not os.path.exists(DONE):
        return {}
    raw = json.load(io.open(DONE, encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_base() -> tuple:
    data = json.load(io.open(DATA, encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    return data, cards


def _sentences(text) -> list:
    return [s.strip() for s in SENTENCE.split(str(text or "")) if len(s.strip()) >= 40]


def still_broken(card: dict, cls: str) -> bool:
    """Виден ли дефект этого класса в сегодняшних данных.

    Отвечает только за те классы, которые ВИДНЫ из самой карточки. Для
    остальных (смысл поля, спор полей, роль указывает не туда) возвращает
    True: решить это может только чтение, и очередь обязана их показать.
    """
    eco = card.get("eco") or {}
    if cls == "SUM_FIELDS_DIFFER":
        s = (card.get("sum") or "").strip()
        e = (eco.get("sum") or "").strip()
        return bool(s) and s != e
    if cls == "TRUNCATED":
        return any((e.get("note") or "").rstrip().endswith(("…", "..."))
                   for e in card.get("events") or [])
    if cls == "JARGON":
        return any(JARGON_RE.search(e.get("note") or "")
                   for e in card.get("events") or [])
    if cls == "SELF_SALE":
        return bool(card.get("seller_id")) and card["seller_id"] in (
            card.get("target"), card.get("asset_id"))
    if cls in ("ROLE_MISSING", "UNLINKED_PARTY"):
        return any((card.get(t) or "").strip() and not card.get(link)
                   for t, link in ROLE_FIELDS.items())
    if cls == "DUPLICATE_TEXT":
        # Клиент сам не показывает «Дополнительный контекст», повторяющий
        # соседние поля (extraHtml), поэтому дефектом считается повтор ВНУТРИ
        # тех полей, которые читатель видит рядом.
        seen = set()
        for v in (eco.get("rationale"), eco.get("share"), eco.get("context")):
            for s in _sentences(v):
                if s in seen:
                    return True
                seen.add(s)
        return False
    return True


def state_of(f: dict, cards: dict, merged: dict, done: dict) -> str:
    k = key_of(f)
    if k in done:
        return "done"
    cid = f["card_id"]
    if cid not in cards:
        return "ушла" if cid in merged or True else "ушла"
    if not still_broken(cards[cid], f["class"]):
        return "неактуальна"
    return "ждёт"


def rows(cards=None, merged=None, done=None) -> list:
    data, c = load_base()
    cards = cards or c
    merged = merged if merged is not None else (data.get("merged") or {})
    done = done if done is not None else load_done()
    out = []
    for f in load_findings():
        r = dict(f)
        r["key"] = key_of(f)
        r["state"] = state_of(f, cards, merged, done)
        out.append(r)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--class", dest="cls", default="")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--no-source", action="store_true",
                    help="только то, что решается по самой карточке")
    ap.add_argument("--mark", default="", help="ключ находки")
    ap.add_argument("--note", default="", help="чем закрыта")
    a = ap.parse_args(argv)

    if a.mark:
        if not a.note:
            print("Нужно сказать, чем закрыта: --note")
            return 1
        done = json.load(io.open(DONE, encoding="utf-8")) if os.path.exists(DONE) else {}
        done[a.mark] = a.note
        with io.open(DONE, "w", encoding="utf-8") as fh:
            json.dump(done, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print("Закрыто: %s" % a.mark)
        return 0

    rs = rows()
    if a.queue:
        want = [r for r in rs if r["state"] == "ждёт"]
        if a.cls:
            want = [r for r in want if r["class"] == a.cls.upper()]
        if a.no_source:
            want = [r for r in want if not r.get("needs_source")
                    and r.get("confidence") == "high"]
        want.sort(key=lambda r: (PRIORITY.index(r["class"])
                                 if r["class"] in PRIORITY else 99, r["card_id"]))
        print("Ждут разбора: %d, показано: %d\n" % (len(want), min(a.limit, len(want))))
        for r in want[:a.limit]:
            print("%s  %s  %s  поле %s" % (r["key"], r["card_id"], r["class"], r["field"]))
            print("    видно: %s" % (r["quote"] or "")[:200])
            print("    в чём дело: %s" % (r["problem"] or "")[:260])
            print("    что сделать: %s" % (r["action"] or "")[:200])
            print()
        return 0

    from collections import Counter
    per = {}
    for r in rs:
        per.setdefault(r["class"], Counter())[r["state"]] += 1
    tot = Counter(r["state"] for r in rs)
    print("%-22s %6s %6s %6s %6s" % ("класс", "всего", "ждёт", "закрыто", "неакт."))
    for cls in sorted(per, key=lambda c: PRIORITY.index(c) if c in PRIORITY else 99):
        c = per[cls]
        print("%-22s %6d %6d %6d %6d"
              % (cls, sum(c.values()), c["ждёт"], c["done"], c["неактуальна"] + c["ушла"]))
    print("-" * 50)
    print("%-22s %6d %6d %6d %6d"
          % ("итого", len(rs), tot["ждёт"], tot["done"], tot["неактуальна"] + tot["ушла"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
