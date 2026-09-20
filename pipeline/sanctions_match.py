# -*- coding: utf-8 -*-
"""Санкционные списки: кто из людей в базе назван в официальных перечнях.

Три источника, все машиночитаемые и открытые:
  США  — OFAC SDN (Минфин США), CSV;
  ЕС   — сводный перечень Евросоюза, XML (в нём есть написание по-русски);
  Великобритания — сводный перечень OFSI, CSV (тоже с русским написанием).

Устройство такое же, как у слоя фактов: СКРИПТ ПРЕДЛАГАЕТ, ЧЕЛОВЕК РЕШАЕТ.
Совпадение имён — только повод открыть запись и сверить её с профилем;
на сайт попадает лишь то, что записано в pipeline/sanctions_confirmed.json
после сверки. Однофамилец в перечне — не основание написать о живом человеке,
что он под санкциями.

    python3 pipeline/sanctions_match.py --fetch          # скачать перечни
    python3 pipeline/sanctions_match.py --candidates     # что совпало по имени
    python3 pipeline/sanctions_match.py --write          # разнести сверенное по базе
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTS_DIR = os.path.join(ROOT, "data", "inbox", "sanctions")
DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
CONFIRMED = os.path.join(ROOT, "pipeline", "sanctions_confirmed.json")
REJECTED = os.path.join(ROOT, "pipeline", "sanctions_rejected.json")

SOURCES = {
    "us": (
        "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV",
        "SDN.CSV",
    ),
    "us_alt": (
        "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ALT.CSV",
        "ALT.CSV",
    ),
    "uk": (
        "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv",
        "ConList.csv",
    ),
    "eu": (
        "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/"
        "content?token=dG9rZW4tMjAxNw",
        "eu.xml",
    ),
}

LIST_LABEL = {"us": "Санкции США", "eu": "Санкции ЕС", "uk": "Санкции Великобритании"}

# ---------------------------------------------------------------- имена

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# Разные страны пишут одну и ту же русскую фамилию по-разному: Mordashov и
# Mordašov, Aleksej и Alexey. Обе стороны сводятся к одной огрублённой форме.
REDUCE = [
    ("shch", "s"), ("sch", "s"), ("sh", "s"), ("š", "s"), ("ch", "c"),
    ("č", "c"), ("tch", "c"), ("ts", "c"), ("tz", "c"), ("zh", "z"),
    ("ž", "z"), ("kh", "h"), ("ph", "f"), ("x", "ks"), ("w", "v"),
    ("yu", "u"), ("iu", "u"), ("ju", "u"), ("ya", "a"), ("ia", "a"),
    ("ja", "a"), ("yo", "o"), ("io", "o"), ("jo", "o"), ("ye", "e"),
    ("je", "e"), ("y", "i"), ("j", "i"), ("ee", "e"), ("oo", "u"),
]


def translit(word: str) -> str:
    return "".join(TRANSLIT.get(ch, ch) for ch in word.lower())


EXTRA_LETTERS = {"\u0142": "l", "\u0111": "d", "\u00f8": "o", "\u00df": "ss",
                 "\u00e6": "ae", "\u0153": "oe", "\u00fe": "th"}


def fold_latin(s: str) -> str:
    """Чешское Mordašov и шведское Mordasjov — про ту же фамилию."""
    s = "".join(EXTRA_LETTERS.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def reduce_latin(word: str) -> str:
    s = (word or "").lower()
    # Кириллицу нельзя раскладывать по NFKD: «ё» превратится в «е», и Фёдоров
    # перестанет сходиться сам с собой.
    s = translit(s) if re.search(r"[а-яё]", s) else fold_latin(s)
    s = re.sub(r"[^a-z]", "", s)
    for a, b in REDUCE:
        s = s.replace(a, b)
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def key_of(name: str) -> str:
    """Ключ имени: огрублённые слова по алфавиту, отчество отброшено."""
    words = [w for w in re.split(r"[\s,]+", name or "") if w]
    parts = []
    for w in words:
        low = w.lower().strip(".")
        if len(low) < 2 or low in TITLE_WORDS:
            continue
        if re.search(r"(ович|евич|ьич|инич|овна|евна|ична)$", low):
            continue  # отчество у нас в базе почти не встречается
        if re.search(r"(ovich|evich|ovna|evna|ovitch|ovits|ovitj|ovna)$", low):
            continue
        parts.append(reduce_latin(w))
    parts = [p for p in parts if len(p) >= 2]
    return " ".join(sorted(set(parts)))


TITLE_WORDS = {
    "mr", "mrs", "ms", "dr", "general", "colonel", "major", "lt", "gen",
    "г-н", "г-жа",
}

# --------------------------------------------------------- люди в базе

PATRONYMIC = re.compile(r"(ович|евич|ьич|инич|овна|евна|ична|инична)$")
GIVEN_NAMES = set("""
александр алексей анатолий андрей антон аркадий арсений артём артем борис вадим
валентин валерий василий виктор виталий владимир владислав вячеслав геннадий
георгий глеб григорий даниил данила денис дмитрий евгений егор иван игорь илья
кирилл константин лев леонид максим марат михаил никита николай олег павел пётр
петр роман руслан рустам сергей станислав степан тимур фёдор федор эдуард юрий
ярослав альберт артур вагит виктория алла анна валентина вера виктория галина
дарья екатерина елена жанна ирина ксения лариса лидия любовь людмила марина
мария надежда наталья наталия нина оксана ольга светлана софья татьяна юлия
яна алина алёна алена ануш анжела инна эльвира эльмира гузель лилия альфия
искандер иcкендер камиль рашид ринат фарит шамиль эмиль махмуд тимофей
""".split())
COMPANY_CUE = re.compile(
    r"(ООО|ОАО|ЗАО|ПАО|АО\b|НАО|ГК\b|УК\b|ИП\b|Групп|групп|Group|Holding|Invest|"
    r"Инвест|Фонд|Корпорац|Компан|Завод|Комбинат|Банк|банк|Лтд|Ltd|LLC|Inc|"
    r"Ойл|Медиа|Девелопмент|Петролеум|Технолог|Систем|Сервис|Проект|Логистик)"
)


def looks_like_person(name: str) -> bool:
    n = (name or "").strip()
    if not n or COMPANY_CUE.search(n):
        return False
    if re.search(r"[«»\"„(]", n):
        return False
    parts = n.split()
    if len(parts) not in (2, 3):
        return False
    if not all(re.fullmatch(r"[А-ЯЁ][а-яё\-]+", p) for p in parts):
        return False
    if len(parts) == 3 and PATRONYMIC.search(parts[-1].lower()):
        return True
    return any(p.lower() in GIVEN_NAMES for p in parts)


def base_persons(data: dict) -> dict:
    out = {}
    for cid, c in data.get("companies", {}).items():
        if looks_like_person(c.get("name", "")):
            out[cid] = c
    return out


# ------------------------------------------------------------ перечни


def _path(fname: str) -> str:
    return os.path.join(LISTS_DIR, fname)


def load_us() -> list:
    """OFAC SDN: только записи о людях, плюс запасные написания из ALT.CSV."""
    rows = []
    cols = ["ent_num", "name", "type", "program", "title", "call_sign",
            "vess_type", "tonnage", "grt", "vess_flag", "vess_owner", "remarks"]
    alts = {}
    if os.path.exists(_path("ALT.CSV")):
        with io.open(_path("ALT.CSV"), encoding="utf-8", errors="replace") as fh:
            for r in csv.reader(fh):
                if len(r) >= 4 and r[0].strip().isdigit():
                    alts.setdefault(int(r[0]), []).append(r[3].strip())
    with io.open(_path("SDN.CSV"), encoding="utf-8", errors="replace") as fh:
        for r in csv.reader(fh):
            if len(r) < len(cols) or not r[0].strip().isdigit():
                continue
            rec = dict(zip(cols, [x.strip().strip('"') for x in r]))
            if rec["type"] != "individual":
                continue
            num = int(rec["ent_num"])
            names = [rec["name"]] + alts.get(num, [])
            rows.append({
                "list": "us",
                "ident": rec["ent_num"],
                "name": rec["name"],
                "names": [x for x in names if x and x != "-0-"],
                "program": rec["program"],
                "remarks": rec["remarks"] if rec["remarks"] != "-0-" else "",
                "url": "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=%s" % rec["ent_num"],
            })
    return rows


def load_uk() -> list:
    raw = io.open(_path("ConList.csv"), encoding="utf-8-sig", errors="replace").read()
    body = raw.split("\n", 1)[1]
    rows, seen = [], {}
    for r in csv.DictReader(io.StringIO(body)):
        if (r.get("Group Type") or "").strip() != "Individual":
            continue
        gid = (r.get("Group ID") or "").strip()
        names = [" ".join(x for x in [r.get("Name 1"), r.get("Name 2"), r.get("Name 3"),
                                      r.get("Name 4"), r.get("Name 5"), r.get("Name 6")] if x)]
        if r.get("Name Non-Latin Script"):
            names.append(r["Name Non-Latin Script"])
        if gid in seen:
            seen[gid]["names"].extend(names)
            continue
        rec = {
            "list": "uk",
            "ident": gid,
            "name": names[0].strip(),
            "names": names,
            "program": (r.get("Regime") or "").strip(),
            "remarks": (r.get("Other Information") or "").strip()[:400],
            "since": (r.get("Listed On") or "").strip(),
            "url": "https://www.gov.uk/government/publications/"
                   "financial-sanctions-consolidated-list-of-targets",
        }
        seen[gid] = rec
        rows.append(rec)
    return rows


def load_eu() -> list:
    ns = {"e": "http://eu.europa.ec/fpi/fsd/export"}
    root = ET.parse(_path("eu.xml")).getroot()
    rows = []
    for se in root.findall("e:sanctionEntity", ns):
        sub = se.find("e:subjectType", ns)
        if sub is None or sub.get("code") != "person":
            continue
        names, funcs = [], []
        for a in se.findall("e:nameAlias", ns):
            w = a.get("wholeName") or " ".join(
                x for x in [a.get("firstName"), a.get("middleName"), a.get("lastName")] if x)
            if w:
                names.append(w.strip())
            if a.get("function"):
                funcs.append(a.get("function"))
        if not names:
            continue
        reg = se.find("e:regulation", ns)
        url = ""
        if reg is not None:
            pub = reg.find("e:publicationUrl", ns)
            url = (pub.text or "").strip() if pub is not None else ""
        rows.append({
            "list": "eu",
            "ident": se.get("logicalId") or "",
            "name": names[0],
            "names": names,
            "program": (reg.get("programme") if reg is not None else "") or "",
            "remarks": (funcs[0] if funcs else "")[:400],
            "since": se.get("designationDate") or "",
            "url": url or "https://www.sanctionsmap.eu/",
        })
    return rows


def load_all() -> list:
    out = []
    for fn, name in ((load_us, "SDN.CSV"), (load_uk, "ConList.csv"), (load_eu, "eu.xml")):
        if os.path.exists(_path(name)):
            out.extend(fn())
    return out


# ------------------------------------------------------------ сведение


def index(rows: list) -> dict:
    idx = {}
    for rec in rows:
        for n in rec.get("names", []):
            k = key_of(n)
            if k.count(" ") < 1:      # одно слово — слишком слабо
                continue
            idx.setdefault(k, []).append((n, rec))
    return idx


def candidates(data: dict, rows: list) -> list:
    """Совпадения по имени — повод прочитать запись, а не готовый ответ.

    Сверяются ВСЕ профили, а не только опознанные как люди: словарь имён
    ошибается (так однажды едва не потерялся «Арам Габрелянов»), а совпадение
    с записью о человеке само по себе говорит, что это человек.
    """
    idx = index(rows)
    known = set(load_confirmed()) | set(load_rejected())
    out = []
    for cid, c in sorted(data.get("companies", {}).items()):
        if cid in known:
            continue
        hits = idx.get(key_of(c.get("name", ""))) or []
        if not hits:
            continue
        by_list = {}
        for shown, rec in hits:
            by_list.setdefault(rec["list"], []).append((shown, rec))
        out.append({"id": cid, "name": c["name"], "desc": c.get("desc", ""),
                    "hits": by_list})
    return out


# ------------------------------------------------------------ запись


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    raw = json.load(io.open(path, encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_confirmed() -> dict:
    return _load_json(CONFIRMED)


def load_rejected() -> dict:
    return _load_json(REJECTED)


def apply_to_base(data: dict, confirmed: dict) -> int:
    changed = 0
    for cid, c in data.get("companies", {}).items():
        want = confirmed.get(cid)
        if want:
            marks = [{k: v for k, v in m.items() if k in
                      ("list", "name", "since", "url")} for m in want]
            if c.get("sanctions") != marks:
                c["sanctions"] = marks
                changed += 1
        elif "sanctions" in c:
            del c["sanctions"]
            changed += 1
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="скачать перечни")
    ap.add_argument("--candidates", action="store_true", help="совпадения по имени")
    ap.add_argument("--check", action="store_true",
                    help="проверить, что сверенные записи ещё есть в перечнях")
    ap.add_argument("--write", action="store_true", help="разнести сверенное по базе")
    a = ap.parse_args(argv)

    if a.fetch:
        import httpx
        os.makedirs(LISTS_DIR, exist_ok=True)
        for key, (url, fname) in SOURCES.items():
            r = httpx.get(url, follow_redirects=True, timeout=180.0)
            r.raise_for_status()
            io.open(_path(fname), "wb").write(r.content)
            print("%-7s %9d байт  %s" % (key, len(r.content), fname))
        return 0

    data = json.load(io.open(DATA, encoding="utf-8"))

    if a.candidates:
        rows = load_all()
        persons = base_persons(data)
        print("Людей в базе: %d. Записей о людях в перечнях: %d." % (len(persons), len(rows)))
        cands = candidates(data, rows)
        print("Совпало по имени: %d\n" % len(cands))
        for c in cands:
            print("%s  %s" % (c["id"], c["name"]))
            if c["desc"]:
                print("    в базе: %s" % c["desc"][:160])
            for lst, hits in sorted(c["hits"].items()):
                shown, rec = hits[0]
                print("    %-3s %s | %s | %s" % (lst, shown, rec.get("program", ""),
                                                 (rec.get("remarks") or "")[:110]))
                print("        %s" % rec.get("url", ""))
            print()
        return 0

    if a.check:
        rows = load_all()
        if not rows:
            print("Перечни не скачаны: сначала --fetch")
            return 1
        idx = index(rows)
        bad = 0
        for cid, marks in sorted(load_confirmed().items()):
            name = data.get("companies", {}).get(cid, {}).get("name", cid)
            hits = {rec["list"] for _, rec in (idx.get(key_of(name)) or [])}
            for m in marks:
                if m["list"] not in hits:
                    bad += 1
                    print("НЕ НАЙДЕН: %s (%s) — %s" % (name, cid, LIST_LABEL[m["list"]]))
        print("Сверено профилей: %d, записей не нашлось: %d"
              % (len(load_confirmed()), bad))
        return 1 if bad else 0

    confirmed = load_confirmed()
    n = apply_to_base(data, confirmed)
    print("Профилей с отметкой о санкциях: %d, изменено: %d" % (len(confirmed), n))
    if a.write and n:
        with io.open(DATA, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
