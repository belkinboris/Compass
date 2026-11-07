# -*- coding: utf-8 -*-
"""Указ № 520: какие компании базы стоят в перечнях обществ, сделки с долями
в которых иностранцам из недружественных стран разрешает только президент.

Устройство — как у санкций (pipeline/sanctions_match.py): СКРИПТ ПРЕДЛАГАЕТ,
ЧЕЛОВЕК РЕШАЕТ. Перечни — pipeline/decree520_list.json (действующая редакция,
у каждой записи акт, которым общество внесено). Отметка на профиле ставится
только по записи в pipeline/decree520_confirmed.json, и у записи — чем
доказано совпадение:

  matched_by = "name"  полное имя юрлица в профиле (с формой: АО, ООО, ПАО)
                       совпало с именем в перечне — проверяется механически;
  matched_by = "inn"   у профиля ИНН из реестра решений ФНС, и в `why`
                       сказано, что этот ИНН — то самое общество из перечня
                       (часто под новым именем: «Фортум» стал «Форвард
                       Энерго», «Энел Россия» — «ЭЛ5-Энерго»);
  matched_by = "read"  имя профиля короче юридического («РН Банк»), а
                       совпадение установлено чтением профиля и сделки.

Похожее имя — только повод прочитать: «АО «Бурсервис»» в базе — это НПП
«Бурсервис» из Уфы, а в перечне — СК «Бурсервис» и ООО «Бурсервис» из Москвы.
Отклоненные — в pipeline/decree520_rejected.json, чтобы их не предлагали снова.

    python3 pipeline/decree520.py --candidates   # что похоже и еще не решено
    python3 pipeline/decree520.py --check        # сверка файлов между собой
    python3 pipeline/decree520.py                # сухой прогон: что изменится в базе
    python3 pipeline/decree520.py --write        # разнести отметки по базе
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
LIST = os.path.join(ROOT, "pipeline", "decree520_list.json")
CONFIRMED = os.path.join(ROOT, "pipeline", "decree520_confirmed.json")
REJECTED = os.path.join(ROOT, "pipeline", "decree520_rejected.json")

FIELD = "decree520"
MATCHED_BY = ("name", "inn", "read")

FORMS = [
    ("публичное акционерное общество", "пао"),
    ("закрытое акционерное общество", "зао"),
    ("открытое акционерное общество", "оао"),
    ("акционерное общество", "ао"),
    ("общество с ограниченной ответственностью", "ооо"),
]


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    raw = json.load(io.open(path, encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_list() -> dict:
    return json.load(io.open(LIST, encoding="utf-8"))


def load_confirmed() -> dict:
    return _load(CONFIRMED)


def load_rejected() -> dict:
    return _load(REJECTED)


def entry_index(lst: dict) -> dict:
    """(акт, пункт) -> запись перечня."""
    return {(e["act"], e["item"]): e for e in lst["entries"]}


def legal_key(name: str) -> str:
    """Полное имя юрлица в одну строку: форма сокращена, кавычки и регистр сняты.

    «Публичное акционерное общество "Юнипро"» и «ПАО «Юнипро»» дают одно и то
    же; «Юнипро» без формы — другое (имени без формы механически не верим).
    """
    s = (name or "").lower().replace("ё", "е")
    for full, short in FORMS:
        s = s.replace(full, short)
    s = re.sub(r"[«»\"“”„']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def core_key(name: str) -> str:
    """Имя без формы — для подсказок, не для доказательства."""
    s = legal_key(name)
    s = re.sub(r"^(пао|зао|оао|ао|ооо)\s+", "", s)
    s = re.sub(r"\s*\((г|пос|дер|с)\.[^)]*\)\s*$", "", s)
    return re.sub(r"[\s\-.]+", "", s)


def candidates(data: dict, lst: dict) -> list:
    known = set(load_confirmed()) | set(load_rejected())
    by_core = {}
    for e in lst["entries"]:
        by_core.setdefault(core_key(e["name"]), []).append(e)
    out = []
    for cid, c in sorted(data.get("companies", {}).items()):
        if cid in known:
            continue
        names = [c.get("name", "")] + list(data.get("match_keys", {}).get(cid, []))
        hits = []
        for n in names:
            k = core_key(n)
            if len(k) >= 4:
                hits += [e for e in by_core.get(k, []) if e not in hits]
        if hits:
            out.append({"id": cid, "name": c.get("name", ""), "desc": c.get("desc", ""),
                        "hits": hits})
    return out


def problems(data: dict, lst: dict, confirmed: dict, rejected: dict) -> list:
    """Что не так со сверкой. Пустой список — все в порядке."""
    bad = []
    idx = entry_index(lst)
    acts = lst.get("acts", {})
    if set(confirmed) & set(rejected):
        bad.append("и подтвержден, и отклонен: %s" % sorted(set(confirmed) & set(rejected)))
    for cid, m in sorted(confirmed.items()):
        c = data.get("companies", {}).get(cid)
        if c is None:
            bad.append("%s: профиля нет в базе" % cid)
            continue
        refs = m.get("entries") or []
        if not refs:
            bad.append("%s: не названа запись перечня" % cid)
        for ref in refs:
            e = idx.get((ref.get("act"), ref.get("item")))
            if e is None:
                bad.append("%s: в перечне нет пункта %s %s" % (cid, ref.get("act"), ref.get("item")))
            elif ref.get("act") not in acts:
                bad.append("%s: акт %s не описан" % (cid, ref.get("act")))
        if m.get("matched_by") not in MATCHED_BY:
            bad.append("%s: matched_by=%r" % (cid, m.get("matched_by")))
        if not (m.get("why") or "").strip():
            bad.append("%s: не сказано, чем подтверждено" % cid)
        if m.get("matched_by") == "name":
            names = {legal_key(idx[(r["act"], r["item"])]["name"])
                     for r in refs if (r.get("act"), r.get("item")) in idx}
            if legal_key(c.get("name", "")) not in names:
                bad.append("%s: «совпало имя», но «%s» не равно имени в перечне"
                           % (cid, c.get("name")))
        if m.get("matched_by") == "inn":
            if ROOT not in sys.path:
                sys.path.insert(0, ROOT)
            from pipeline import fns_registry
            reg = fns_registry.by_company_id().get(cid) or {}
            if not m.get("inn") or reg.get("inn") != m.get("inn"):
                bad.append("%s: ИНН %s не совпал с реестром ФНС (%s)"
                           % (cid, m.get("inn"), reg.get("inn")))
    return bad


def marks_for(lst: dict, entry: dict) -> list:
    idx = entry_index(lst)
    acts = lst["acts"]
    out = []
    for ref in entry["entries"]:
        e = idx[(ref["act"], ref["item"])]
        a = acts[e["act"]]
        out.append({"act": e["act"], "item": e["item"], "name": e["name"],
                    "since": a["date"], "url": a["url"]})
    return out


def apply_to_base(data: dict, lst: dict, confirmed: dict) -> int:
    changed = 0
    for cid, c in data.get("companies", {}).items():
        want = confirmed.get(cid)
        if want:
            marks = marks_for(lst, want)
            if c.get(FIELD) != marks:
                c[FIELD] = marks
                changed += 1
        elif FIELD in c:
            del c[FIELD]
            changed += 1
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", action="store_true", help="похожие имена, еще не решенные")
    ap.add_argument("--check", action="store_true", help="сверить файлы между собой")
    ap.add_argument("--write", action="store_true", help="записать отметки в базу")
    a = ap.parse_args(argv)

    lst = load_list()
    data = json.load(io.open(DATA, encoding="utf-8"))
    confirmed, rejected = load_confirmed(), load_rejected()

    if a.candidates:
        cands = candidates(data, lst)
        print("Обществ в перечнях: %d. Не решено совпадений: %d\n"
              % (len(lst["entries"]), len(cands)))
        for c in cands:
            print("%s  %s\n    в базе: %s" % (c["id"], c["name"], c["desc"][:160]))
            for e in c["hits"]:
                print("    %s п. %s: %s (%s)" % (e["act"], e["item"], e["name"], e["place"]))
            print()
        return 0

    bad = problems(data, lst, confirmed, rejected)
    for b in bad:
        print("ОШИБКА:", b)
    if a.check or bad:
        print("Подтверждено профилей: %d, отклонено: %d, ошибок: %d"
              % (len(confirmed), len(rejected), len(bad)))
        return 1 if bad else 0

    n = apply_to_base(data, lst, confirmed)
    print("Профилей с отметкой «указ № 520»: %d, изменится: %d%s"
          % (len(confirmed), n, "" if a.write else " (сухой прогон, запись — --write)"))
    if a.write and n:
        # Перечитать базу прямо перед записью: за время работы ее мог
        # переписать параллельный прогон (docs/card_editing.md).
        fresh = json.load(io.open(DATA, encoding="utf-8"))
        m = apply_to_base(fresh, lst, confirmed)
        assert m == n, "база поменялась между чтением и записью: %d против %d" % (m, n)
        for cid, c in fresh["companies"].items():
            if cid not in confirmed:
                assert FIELD not in c, cid
        with io.open(DATA, "w", encoding="utf-8") as fh:
            json.dump(fresh, fh, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
