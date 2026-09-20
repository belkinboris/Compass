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
    s = re.sub(r"[^a-z0-9]", "", s)
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

# У одного юрлица десяток написаний организационной формы: ПАО Сбербанк,
# PJSC Sberbank, Public Joint-Stock Company Sberbank. Ключ — то, что
# остаётся после формы.
LEGAL_FORMS = re.compile(
    r"\b(?:pao|oao|zao|nao|ooo|ao|pjsc|ojsc|jsc|cjsc|llc|ltd|limited|inc|plc|"
    r"corp|corporation|company|companies|joint|stock|publicly|traded|public|"
    r"private|open|closed|holding|holdings|group|obshchestvo|obshestvo|"
    r"obschestvo|aktsionernoe|aktsionernoye|akcionernoe|publichnoe|"
    r"publichnoye|ogranichennoi|ogranichennoy|otvetstvennostyu|"
    r"otvetstvennostiu|kompaniya|kompania|firma|concern|gmbh|s\.a|sa|ag|"
    r"\u043f\u0430\u043e|\u043e\u0430\u043e|\u0437\u0430\u043e|"
    r"\u043d\u0430\u043e|\u043e\u043e\u043e|\u0430\u043e|\u0433\u043a|"
    r"\u0443\u043a|\u043e\u0431\u0449\u0435\u0441\u0442\u0432\u043e|"
    r"\u0430\u043a\u0446\u0438\u043e\u043d\u0435\u0440\u043d\u043e\u0435|"
    r"\u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u0435|"
    r"\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044f|"
    r"\u0433\u0440\u0443\u043f\u043f\u0430|"
    r"\u043a\u043e\u0440\u043f\u043e\u0440\u0430\u0446\u0438\u044f|"
    r"\u0444\u0438\u0440\u043c\u0430|\u0445\u043e\u043b\u0434\u0438\u043d\u0433)\b",
    re.I)


GENERIC_WORDS = set("""
invest investments investment capital properties property real estate
security securities digital technology technologies tech systems system
service services trade trading energy energo oil gas bank banka banking
finance financial global international management development media
logistics transport construction industrial industries resources mining
gold silver steel metal metals telecom united national center centre
project projects partners partner fund funds asset assets business
enterprise enterprises production productions plant factory works agro
food retail store stores house home city town region regional federal
state russian russia rossii rossiya moscow sankt petersburg new first
second third alfa omega plus pro max prime top best smart
инвест капитал банк энерго тех строй пром агро
""".split())
# Слова стоп-списка сводятся тем же огрублением, что и имена: иначе
# «security» останется в списке, а из имени придёт «securiti».
GENERIC_KEYS = {reduce_latin(w) for w in GENERIC_WORDS}


def entity_key(name: str) -> str:
    """Ключ юрлица: форма, кавычки и общие деловые слова отброшены.

    Общие слова убраны не для красоты: без этого «РТ-Инвест» сходится с
    «M INVEST, OOO», а «KR Properties» — с «V.P. PROPERTIES, INC.». Имя,
    от которого после чистки ничего не осталось, ключа не получает вовсе —
    по такому имени искать нельзя.
    """
    s = re.sub(r"[\u00ab\u00bb\u201c\u201d\u201e\"'()]", " ", name or "")
    s = re.sub(r"[-/,.]", " ", s)
    s = LEGAL_FORMS.sub(" ", s)
    parts = []
    for w in s.split():
        r = reduce_latin(w)
        if r.isdigit() or len(r) >= 3:
            parts.append(r)          # «Сахалин-2» и «Сахалин-8» — не одно и то же
    own = [p for p in parts if not p.isdigit() and p not in GENERIC_KEYS]
    # Имя из одних общих слов («Капитал Групп», «KR Properties») ключа не
    # получает: по нему совпадёт что угодно. Но сами общие слова из ключа
    # НЕ выбрасываются — иначе «Почта Банк» сойдётся с «Почтой России»,
    # а «Газпромбанк-инвест» — с Газпромбанком.
    if not own or len("".join(own)) < 5:
        return ""
    return " ".join(sorted(set(parts)))


INN_RE = re.compile(r"\b(\d{10}|\d{12})\b")


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
    """OFAC SDN: и люди, и юрлица. У российских записей в примечаниях часто
    стоит ИНН — это и есть точный ключ, имя тут только подсказка."""
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
            kind = "person" if rec["type"] == "individual" else "entity"
            num = int(rec["ent_num"])
            names = [rec["name"]] + alts.get(num, [])
            remarks = rec["remarks"] if rec["remarks"] != "-0-" else ""
            inns = [m for m in INN_RE.findall(remarks)
                    if re.search(r"Tax ID No\.\s*%s\s*\(Russia\)" % m, remarks)]
            rows.append({
                "list": "us",
                "kind": kind,
                "ident": rec["ent_num"],
                "name": rec["name"],
                "names": [x for x in names if x and x != "-0-"],
                "inns": inns,
                "program": rec["program"],
                "remarks": remarks,
                "since": "",
                "url": "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=%s" % rec["ent_num"],
            })
    return rows


def _uk_date(s: str) -> str:
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", (s or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def load_uk() -> list:
    raw = io.open(_path("ConList.csv"), encoding="utf-8-sig", errors="replace").read()
    body = raw.split("\n", 1)[1]
    rows, seen = [], {}
    for r in csv.DictReader(io.StringIO(body)):
        gtype = (r.get("Group Type") or "").strip()
        if gtype not in ("Individual", "Entity"):
            continue
        gid = (r.get("Group ID") or "").strip()
        names = [" ".join(x for x in [r.get("Name 1"), r.get("Name 2"), r.get("Name 3"),
                                      r.get("Name 4"), r.get("Name 5"), r.get("Name 6")] if x)]
        if r.get("Name Non-Latin Script"):
            names.append(r["Name Non-Latin Script"])
        blob = " ".join(x for x in [r.get("National Identification Number"),
                                    r.get("National Identification Details"),
                                    r.get("Other Information")] if x)
        inns = INN_RE.findall(blob)
        if gid in seen:
            seen[gid]["names"].extend(names)
            seen[gid]["inns"].extend(inns)
            continue
        rec = {
            "list": "uk",
            "kind": "person" if gtype == "Individual" else "entity",
            "ident": gid,
            "name": names[0].strip(),
            "names": names,
            "inns": inns,
            "program": (r.get("Regime") or "").strip(),
            "remarks": (r.get("Other Information") or "").strip()[:400],
            "since": _uk_date(r.get("Listed On") or ""),
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
        kind = "person" if (sub is not None and sub.get("code") == "person") else "entity"
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
        inns = []
        for idn in se.findall("e:identification", ns):
            num = (idn.get("number") or "").strip()
            if INN_RE.fullmatch(num):
                inns.append(num)
        reg = se.find("e:regulation", ns)
        url = ""
        if reg is not None:
            pub = reg.find("e:publicationUrl", ns)
            url = (pub.text or "").strip() if pub is not None else ""
        rows.append({
            "list": "eu",
            "kind": kind,
            "ident": se.get("logicalId") or "",
            "name": names[0],
            "names": names,
            "inns": inns,
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
    """Два ключа: ИНН (точный) и имя (подсказка, требующая чтения)."""
    by_name, by_inn = {}, {}
    for rec in rows:
        for inn in rec.get("inns") or []:
            by_inn.setdefault(inn, []).append(rec)
        for n in rec.get("names", []):
            if rec.get("kind") == "entity":
                k = entity_key(n)
            else:
                k = key_of(n)
                if k.count(" ") < 1:      # одно слово — слишком слабо
                    k = ""
            if k:
                by_name.setdefault(k, []).append((n, rec))
    return {"name": by_name, "inn": by_inn}


def base_inns() -> dict:
    """ИНН профиля из реестра решений ФНС — уже подтверждённый человеком."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from pipeline import fns_registry
    return {cid: inn for cid, inn in fns_registry.confirmed_inns().items() if inn}


def candidates(data: dict, rows: list) -> list:
    """Совпадения — повод прочитать запись, а не готовый ответ.

    Сверяются ВСЕ профили, а не только опознанные как люди: словарь имён
    ошибается (так однажды едва не потерялся «Арам Габрелянов»), а совпадение
    с записью о человеке само по себе говорит, что это человек.
    """
    idx = index(rows)
    known = set(load_confirmed()) | set(load_rejected())
    inns = base_inns()
    out = []
    for cid, c in sorted(data.get("companies", {}).items()):
        if cid in known:
            continue
        name = c.get("name", "")
        person = looks_like_person(name)
        hits = []
        inn = inns.get(cid)
        if inn:
            for rec in idx["inn"].get(inn, []):
                hits.append((rec["name"], rec, "inn"))
        key = key_of(name) if person else entity_key(name)
        if key and (not person or key.count(" ") >= 1):
            for shown, rec in idx["name"].get(key, []):
                hits.append((shown, rec, "name"))
        if not hits:
            continue
        by_list = {}
        for shown, rec, how in hits:
            slot = by_list.setdefault(rec["list"], [])
            if not any(r["ident"] == rec["ident"] for _, r, _ in slot):
                slot.append((shown, rec, how))
        out.append({"id": cid, "name": name, "kind": "person" if person else "entity",
                    "inn": inn or "", "desc": c.get("desc", ""), "hits": by_list})
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
                      ("list", "kind", "name", "since", "url")} for m in want]
            if c.get("sanctions") != marks:
                c["sanctions"] = marks
                changed += 1
        elif "sanctions" in c:
            del c["sanctions"]
            changed += 1
    return changed


def inn_marks(data: dict, rows: list) -> dict:
    """Отметки, у которых доказательство механическое: ИНН.

    ИНН из реестра решений ФНС (он уже подтверждён человеком) совпал с ИНН,
    который сам санкционный список называет у своей записи. Это не догадка по
    имени — это один и тот же ИНН, поэтому такие отметки собираются скриптом,
    а не чтением. Имена при этом расходятся сплошь и рядом и расходиться
    должны: ОСК в списке США называется United Shipbuilding Corporation.
    """
    out = {}
    for c in candidates(data, rows):
        marks = []
        for lst in ("us", "eu", "uk"):
            for shown, rec, how in c["hits"].get(lst, []):
                if how != "inn":
                    continue
                marks.append({
                    "list": lst, "kind": "entity", "name": rec["name"],
                    "since": rec.get("since", ""), "url": rec["url"],
                    "matched_by": "inn", "inn": c["inn"],
                    "why": "ИНН %s в реестре ФНС совпал с ИНН этой же записи "
                           "санкционного списка." % c["inn"],
                })
                break
        if marks:
            out[c["id"]] = marks
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="скачать перечни")
    ap.add_argument("--candidates", action="store_true", help="совпадения по имени")
    ap.add_argument("--apply-inn", action="store_true",
                    help="добавить отметки, доказанные совпадением ИНН")
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
        print("Людей в базе: %d, профилей всего: %d. Записей в перечнях: %d."
              % (len(persons), len(data.get("companies", {})), len(rows)))
        cands = candidates(data, rows)
        print("Совпало по имени: %d\n" % len(cands))
        for c in cands:
            print("%s  %s" % (c["id"], c["name"]))
            if c["desc"]:
                print("    в базе: %s" % c["desc"][:160])
            for lst, hits in sorted(c["hits"].items()):
                shown, rec, how = hits[0]
                print("    %-3s [%s] %s | %s | %s"
                      % (lst, how, shown[:60], rec.get("program", ""),
                         (rec.get("remarks") or "")[:90]))
                print("        %s" % rec.get("url", ""))
            print()
        return 0

    if getattr(a, "apply_inn", False):
        rows = load_all()
        if not rows:
            print("Перечни не скачаны: сначала --fetch")
            return 1
        add = inn_marks(data, rows)
        conf = json.load(io.open(CONFIRMED, encoding="utf-8"))
        for cid, marks in sorted(add.items()):
            conf[cid] = marks
        print("Новых отметок по ИНН: %d, всего в файле: %d"
              % (len(add), len([k for k in conf if not k.startswith("_")])))
        if a.write:
            with io.open(CONFIRMED, "w", encoding="utf-8") as fh:
                json.dump(conf, fh, indent=1, ensure_ascii=False)
                fh.write("\n")
        return 0

    if a.check:
        rows = load_all()
        if not rows:
            print("Перечни не скачаны: сначала --fetch")
            return 1
        idx = index(rows)
        inns = base_inns()
        bad = 0
        for cid, marks in sorted(load_confirmed().items()):
            name = data.get("companies", {}).get(cid, {}).get("name", cid)
            person = looks_like_person(name)
            key = key_of(name) if person else entity_key(name)
            hits = {rec["list"] for _, rec in (idx["name"].get(key) or [])}
            hits |= {rec["list"] for rec in idx["inn"].get(inns.get(cid, ""), [])}
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
