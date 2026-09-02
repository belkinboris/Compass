# -*- coding: utf-8 -*-
"""Ассистент: поиск по базе и точные ответы — на сервере, а не в браузере.

ПОЧЕМУ ЭТОТ МОДУЛЬ ПОЯВИЛСЯ (1 сентября 2026). Партнёр владельца задал
ассистенту четыре вопроса и получил четыре неверных ответа:
  * «Много сделок у Orion?» — «в базе нет сделок с Orion» (в базе 15);
  * «Кто консультирует в сфере добычи угля?» — «сделок с углём нет» (9);
  * «Better Chance — какие сделки сопровождали?» — «в базе записей нет» (11);
  * «Какая самая крупная сделка?» — таймаут и ссылки на статьи «крупная
    сделка для ООО: нужно ли одобрение» из интернета.
Ни один из ответов не был враньём модели: ей передавали подборку сделок,
собранную В БРАУЗЕРЕ по словам ЗАГОЛОВКА (`relevantDeals` в index.html), а
консультанты, отрасли, имена компаний-сторон и темы в тот индекс не входили.
Не найдя слова «Orion» ни в одном заголовке, браузер отдавал сорок самых
свежих сделок — и модель честно сообщала, что в них Orion нет.

ЧТО ДЕЛАЕТ МОДУЛЬ. Держит индекс по всей видимой базе (заголовок, стороны,
предмет, отрасли, темы, консультанты, ключевые факты) и отвечает на вопрос
в два слоя:
  1. `route()` понимает, О ЧЁМ вопрос (фирма-консультант, компания, отрасль,
     «самая крупная», «сколько», тема вроде ухода иностранцев) и считает
     ТОЧНЫЙ ответ прямо по базе — числа, списки, ссылки. Это ответ, который
     верен без всякой модели и отдаётся пользователю, если модель молчит.
  2. Подборка сделок (не больше дюжины, компактно) плюс эта сводка уходят
     модели, чья работа — живой русский текст, а не арифметика по базе.
Правило простое: база отвечает на вопросы про базу, модель пишет прозу.

Зависимостей сверх стандартной библиотеки нет намеренно: модуль живёт в
веб-процессе на Timeweb, и лишний пакет — лишняя точка отказа при деплое.
Морфология — та же «общее начало ≥3 знаков и ≥60% длины короткого слова»,
что уже проверена в review.py и в поиске по ленте; копия здесь, а не импорт,
потому что review.py при импорте загружает все таблицы правок.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deal_multiples import is_estimate, parse_rub_sum

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "static" / "data" / "deals_promoted.json"
INDEX_HTML = ROOT / "static" / "index.html"
SITE_MIN_YEAR = 2022
MAX_DEALS_FOR_MODEL = 12
MAX_LISTED = 6

# --------------------------------------------------------------------------
# Слова и формы
# --------------------------------------------------------------------------

STOP = set((
    "кто что какие какая какой каких какую где когда сколько много мало есть был была были быть "
    "про по об о в на с у из для и а но или же ли не нет да все всё это эта этот эти там тут "
    "расскажи покажи назови найди дай список какие-нибудь какой-нибудь какая-нибудь "
    "сделка сделки сделку сделок сделке сделкой компания компании компаний компанию фирма фирмы фирму "
    "год года году годы лет рынок рынка рынке российский российского российском россии россия "
    "ооо пао ао оао зао гк ук нко ип ltd llc inc plc group the and for of "
    "известно информация данные база базе базы компас компаса "
    # Вопросные и родовые слова: сами по себе ничего не ищут, а по общему
    # началу цепляют чужие имена («так» → «Такси», «столько» → «Столичных»,
    # «почему» → «Почта»). Со страницы компании «Почему так много покупает?»
    # без них становится вопросом о самой компании (2 сентября 2026).
    "почему зачем отчего как так тоже уже еще ещё очень столько такой такая такие "
    "последние последних последний последняя последнюю новые новых новая новый свежие недавние "
    # Глаголы сделки стоят в сотнях заголовков — как признак они ничего не
    # различают, а как шум подмешивают к точному попаданию чужие карточки
    # («Кто купил Ситибанк?» тянул за «купил» ещё четыре сделки).
    "купил купила купили купит купить покупает покупают покупка покупке покупку "
    "приобрел приобрела приобрели приобретает приобретение приобретения приобрёл приобрела "
    "продал продала продали продает продаёт продажа продаже продажу продать "
    "выкупил выкупила выкупит выкуп выкупа инвестировал инвестировала инвестирует инвестиции "
    "получил получила получит стал стала станет вошел вошла войдет вышел вышла закрыл закрыла "
    "сопровождал сопровождала сопровождали сопровождает консультировал консультировала"
).split())

# Родовые слова названий компаний: сами по себе не опознают компанию.
GENERIC_NAME_WORDS = set((
    "ооо ао пао зао оао нао гк ук зпиф группа группы компания компании холдинг корпорация фонд банк "
    "инвест инвестиции капитал capital partners group holding invest ltd llc inc plc the and of "
    "россия российский русский международный национальный первый новый"
).split())

# Родовые слова в названиях консультантов — именем фирмы не считаются.
ADVISOR_GENERIC = set((
    "партнер партнеры партнеров партнёры partners partner legal law lawyers юридическ юрист юристы "
    "консалтинг consulting консультант консультанты бюро адвокат адвокаты коллегия компания фирма "
    "групп группа group services сервис офис office капитал capital advisory advisors"
).split())

_SUFFIXES = sorted((
    "иями ями ами ого его ому ему ыми ими ах ях ам ям ов ев ей ой ый ий ая яя ое ее ую юю ие ые ых их ом ем "
    "а я о е и ы у ю ь й"
).split(), key=len, reverse=True)


def norm(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zа-я0-9]+", norm(text)) if t]


def stem(word: str) -> str:
    """Грубая основа: одно окончание из списка, остаток не короче четырёх
    знаков. Латиницу и короткие слова не трогаем — у «VK», «Orion», «Гош»
    окончаний нет, а резать их — значит терять имя."""
    if len(word) < 5 or not re.fullmatch(r"[а-я]+", word):
        return word
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


def same_word(a: str, b: str) -> bool:
    """Одно слово в разных падежах — та же граница, что в review.py."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 3:
        return False
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    short = min(len(a), len(b))
    return n >= 3 and n >= 0.6 * short


def name_match(a: str, b: str) -> bool:
    """Совпадение ИМЕНИ, а не обычного слова: `same_word` для имён слишком
    мягок — «иванов» ложился на «иван» (Иван Пешков) и на «иванян». Имя
    считается тем же, если основы равны или одна начинается с другой и
    общая часть не короче пяти знаков («ивановым» → «иванов»)."""
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 5 and long_.startswith(short)


def query_words(question: str) -> list[str]:
    """Значимые слова вопроса как есть, без обрезки окончаний — для сверки
    ИМЁН: основа «иванов» → «иван» ложится на «Иван Пешков», а само слово — нет."""
    out = []
    for t in tokens(question):
        if t in STOP or (len(t) < 2) or (len(t) < 3 and not re.fullmatch(r"[a-z0-9]+", t)):
            continue
        if t not in out:
            out.append(t)
    return out


def query_terms(question: str) -> list[str]:
    out = []
    for t in query_words(question):
        s = stem(t)
        if s not in out:
            out.append(s)
    return out


def year_in(text: str) -> int | None:
    m = re.search(r"\b(20[2-9]\d)\b", text or "")
    return int(m.group(1)) if m else None


PLACEHOLDER = re.compile(
    r"^\s*(не\s+раскры[а-яё]*|публично\s+не\s+сообщал[а-яё]*|не\s+привлекал[а-яё]*|не\s+сообщал[а-яё]*|"
    r"нет\s+данных|—|-|n/?a|неизвестн[а-яё]*)?\s*\.?\s*$", re.I)


def has_fact(value: Any) -> bool:
    return bool(value) and not PLACEHOLDER.match(str(value))


# --------------------------------------------------------------------------
# Отрасли и темы: синонимы, по которым их узнаёт вопрос
# --------------------------------------------------------------------------

# Префиксы (без учёта регистра и ё). Короткие проверяются как целое слово —
# «ит» не должно узнаваться внутри «итог». ПОРЯДОК ВАЖЕН: узкие отрасли стоят
# раньше широких, и берётся первое совпадение — «добыча угля» должна давать
# «Уголь», а не «ГМК и добыча» (первая версия выбирала самый длинный префикс
# и отдавала общую отрасль). Ключи — точные подписи отраслей базы; те, что в
# базе не встретятся, отбрасываются при разборе вопроса.
INDUSTRY_HINTS: dict[str, list[str]] = {
    "Уголь": ["уголь", "угля", "углю", "углем", "угле", "угольн", "угледоб"],
    "Фармацевтика": ["фарм", "аптек", "лекарств"],
    "Страхование": ["страхов"],
    "Финтех": ["финтех", "fintech", "платежн", "эквайринг"],
    "Порты и инфраструктура": ["порт", "терминал", "инфраструктур"],
    "Производство тары": ["упаков", "тар"],
    "E-commerce": ["маркетплейс", "e-commerce", "ecommerce", "интернет-магазин"],
    "Телеком": ["телеком", "сотов", "мобильн", "оператор связи"],
    "Автопром": ["автопром", "автомобил", "автозавод", "дилер"],
    "Образование": ["образован", "школ", "университет", "edtech", "курс"],
    "Медиа": ["медиа", "издани", "телеканал", "кино", "музык"],
    "Гостиницы и туризм": ["гостиниц", "отел", "туризм", "турист", "курорт", "санатор"],
    "Развлечения": ["развлеч", "парк", "игров", "кинотеатр"],
    "Лесопром": ["лесопром", "лесн", "древес", "целлюлоз", "бумаж"],
    "ЖКХ и обращение с отходами": ["жкх", "отход", "мусор", "водоканал"],
    "Химия и удобрения": ["хими", "удобрен"],
    "Здравоохранение": ["клиник", "медицин", "здравоохран", "медцентр", "лаборатор"],
    "Рынок ценных бумаг": ["брокер", "ценных бумаг", "депозитар", "биржев"],
    "Управление активами": ["управляющ", "зпиф", "фонд", "управлени активами"],
    "Финансовые услуги": ["лизинг", "мфо", "микрофинанс", "финансов"],
    "Искусственный интеллект": ["нейросет", "искусственн", "ai-"],
    "Агро": ["агро", "сельхоз", "зерн", "ферм", "аграрн", "птицефабрик", "хозяйств"],
    "Пищепром и напитки": ["пищев", "пищепром", "напитк", "молочн", "мясн", "кондитер", "пивовар"],
    "Нефть и газ": ["нефт", "газ", "спг", "нефтегаз"],
    "Энергетика": ["энерг", "электро", "тэц", "генерац", "электростанц"],
    "Строительство": ["строител", "застройщ", "подрядчик"],
    "Недвижимость": ["недвижим", "девелоп", "жк", "бизнес-центр", "офис", "склад", "трц", "земл", "участ", "здани"],
    "Транспорт и логистика": ["транспорт", "логист", "перевоз", "грузов", "авиа", "аэропорт", "аэродром"],
    "ГМК и добыча": ["золот", "метал", "руд", "добыч", "горн", "гмк", "месторожд", "никел"],
    "Машиностроение": ["машиностро", "завод", "станк", "оборудован", "приборостро"],
    "Ритейл": ["ритейл", "розниц", "магазин", "супермаркет", "торгов сет"],
    "Потребительские товары": ["потребител", "бренд", "одежд", "косметик", "ювелир", "обув"],
    "Банки": ["банк"],
    "ИТ и интернет": ["ит", "it", "айти", "интернет", "софт", "программ", "разработчик", "цифров", "онлайн", "платформ"],
    "Холдинги": ["холдинг"],
    "Профессиональные услуги": ["консалтинг", "аудит", "юридическ услуг"],
}

THEME_HINTS: dict[str, list[str]] = {
    "Уход иностранного владельца": ["иностран", "уход", "уш", "выход", "выш", "покин", "зарубеж", "нерезидент"],
    "Правкомиссия / указ президента": ["правкомисс", "правительствен", "указ", "президент"],
    "Национализация / иск Генпрокуратуры": ["национализ", "генпрокурат", "изъят", "в доход государства"],
    "Продажа с торгов": ["торг", "аукцион"],
    "Банкротство / долги": ["банкрот", "долг", "конкурсн"],
    "IPO / SPO": ["ipo", "spo", "размещен", "бирж"],
    "Венчур / раунд": ["венчур", "раунд", "стартап", "инвестор"],
    "Консолидация доли": ["консолидац", "довел", "увелич", "доведен"],
    "Создание СП": ["совместн", "сп"],
    "Искусственный интеллект": ["ии", "искусственн", "нейросет", "ai"],
}

# Слова, которые значат «ищу условие сделки», а не тему — ищем по тексту полей.
TERM_HINTS: dict[str, str] = {
    "опцион": r"опцион",
    "обратн": r"обратн[а-яё]*\s+выкуп|опцион",
    "earn-out": r"earn-?out|отложенн[а-яё]*\s+платеж",
    "эскроу": r"эскроу|escrow",
    "заверен": r"заверен",
    "неконкурен": r"неконкурен",
}


# --------------------------------------------------------------------------
# Индекс
# --------------------------------------------------------------------------

@dataclass
class Firm:
    id: str
    name: str
    rx: re.Pattern


@dataclass
class Doc:
    id: str
    title: str
    date: str
    year: int
    status: str
    type: str
    sum_text: str
    sum_rub: float | None
    estimate: bool
    industries: list[str]
    themes: list[str]
    buyer: str
    seller: str
    target: str
    asset: str
    advisors: list[str]
    advisor_roles: list[tuple[str, str]]
    facts: str
    strong: set[str] = field(default_factory=set)
    weak: set[str] = field(default_factory=set)
    raw: dict = field(default_factory=dict)


@dataclass
class Index:
    docs: list[Doc]
    by_id: dict[str, Doc]
    companies: dict[str, dict]
    company_deals: dict[str, list[Doc]]
    firms: list[Firm]
    firm_deals: dict[str, list[Doc]]
    industries: list[str]
    df: Counter
    mtime: float


_LOCK = threading.Lock()
_INDEX: Index | None = None


def _js_regex_to_python(src: str) -> re.Pattern | None:
    try:
        return re.compile(src, re.I)
    except re.error:
        return None


def load_firms(html_path: Path = INDEX_HTML) -> list[Firm]:
    """Каталог консультантов живёт в index.html (массивы FIRMS/INV_FIRMS и
    регулярки FIRM_MATCH). Разбираем его регулярками, как уже делает
    pipeline/ingest/curated.py для кураторских сделок, — заводить второй
    каталог на сервере значило бы получить два расходящихся списка."""
    try:
        text = html_path.read_text(encoding="utf-8")
    except OSError:
        return []
    firms: dict[str, str] = {}
    for block in re.findall(r"const (?:FIRMS|INV_FIRMS) = \[(.*?)\n\];", text, re.S):
        for m in re.finditer(r'\{id:"([^"]+)",\s*n:"([^"]+)"', block):
            firms[m.group(1)] = m.group(2)
    matches: dict[str, re.Pattern] = {}
    m = re.search(r"const FIRM_MATCH = \{(.*?)\};", text, re.S)
    if m:
        for fid, src in re.findall(r"(\w+):/((?:\\/|[^/])+)/[a-z]*", m.group(1)):
            rx = _js_regex_to_python(src.replace("\\/", "/"))
            if rx:
                matches[fid] = rx
    out = []
    for fid, name in firms.items():
        rx = matches.get(fid)
        if rx is None:
            escaped = re.escape(name).replace(r"\ ", r"\s+")
            rx = re.compile(escaped, re.I)
        out.append(Firm(id=fid, name=name, rx=rx))
    return out


def _company_name(companies: dict, cid: str | None) -> str:
    if not cid:
        return ""
    c = companies.get(cid) or {}
    return c.get("name") or ""


def _advisors(deal: dict) -> tuple[list[str], list[tuple[str, str]]]:
    names, roles = [], []
    for row in (deal.get("law") or {}).get("adv") or []:
        if isinstance(row, (list, tuple)) and len(row) >= 2 and has_fact(row[1]):
            names.append(str(row[1]))
            roles.append((str(row[0] or ""), str(row[1])))
    fin = (deal.get("eco") or {}).get("finadv")
    if has_fact(fin):
        names.append(str(fin))
        roles.append(("Финансовый консультант", str(fin)))
    return names, roles


def _facts(deal: dict) -> str:
    eco, law = deal.get("eco") or {}, deal.get("law") or {}
    parts = [eco.get(k) for k in ("share", "val", "rationale", "context", "target_fin")]
    parts += [law.get(k) for k in ("struct", "appr", "terms")]
    parts.append(deal.get("extra"))
    return " ".join(str(p) for p in parts if has_fact(p))


def _build(data: dict, firms: list[Firm], mtime: float) -> Index:
    companies = data.get("companies") or {}
    match_keys = data.get("match_keys") or {}
    docs: list[Doc] = []
    company_deals: dict[str, list[Doc]] = defaultdict(list)
    for deal in data.get("deals") or []:
        ds = str(deal.get("date") or "")
        if not ds[:4].isdigit() or int(ds[:4]) < SITE_MIN_YEAR:
            continue
        year = int(ds[:4])
        buyer = _company_name(companies, deal.get("buyer")) or (deal.get("buyer_name") or "")
        seller = _company_name(companies, deal.get("seller_id")) or (deal.get("seller") or "")
        target = _company_name(companies, deal.get("target") or deal.get("asset_id"))
        advisors, roles = _advisors(deal)
        inds = deal.get("industries") if isinstance(deal.get("industries"), list) and deal.get("industries") else [deal.get("ind")]
        inds = [i for i in inds if i]
        doc = Doc(
            id=str(deal["id"]), title=deal.get("title") or "", date=ds, year=year,
            status=deal.get("status") or "", type=deal.get("type") or "",
            sum_text=str(deal.get("sum") or ""), sum_rub=parse_rub_sum(deal.get("sum")),
            estimate=is_estimate(deal.get("sum")), industries=inds,
            themes=list(deal.get("themes") or []), buyer=buyer, seller=seller,
            target=target, asset=deal.get("asset") or "", advisors=advisors,
            advisor_roles=roles, facts=_facts(deal), raw=deal,
        )
        strong_src = " ".join([doc.title, doc.buyer, doc.seller, doc.target, doc.asset,
                               " ".join(inds), " ".join(doc.themes), " ".join(advisors), doc.type])
        for cid in (deal.get("buyer"), deal.get("seller_id"), deal.get("target"), deal.get("asset_id")):
            if cid and cid in companies:
                company_deals[cid].append(doc)
                strong_src += " " + " ".join(match_keys.get(cid) or [])
        doc.strong = {stem(t) for t in tokens(strong_src) if t not in STOP and len(t) >= 2}
        doc.weak = {stem(t) for t in tokens(doc.facts) if t not in STOP and len(t) >= 3}
        docs.append(doc)
    docs.sort(key=lambda d: d.date, reverse=True)
    firm_deals: dict[str, list[Doc]] = defaultdict(list)
    for doc in docs:
        for f in firms:
            if any(f.rx.search(a) for a in doc.advisors):
                firm_deals[f.id].append(doc)
    df: Counter = Counter()
    for doc in docs:
        for t in doc.strong:
            df[t] += 1
    industries = sorted({i for d in docs for i in d.industries})
    return Index(docs=docs, by_id={d.id: d for d in docs}, companies=companies,
                 company_deals=dict(company_deals), firms=firms, firm_deals=dict(firm_deals),
                 industries=industries, df=df, mtime=mtime)


def get_index(force: bool = False) -> Index:
    """Индекс перестраивается, когда файл базы на диске поменялся (деплой
    приносит новый JSON), — без перезапуска сервера и без кэша навсегда."""
    global _INDEX
    try:
        mtime = os.path.getmtime(DATA_PATH)
    except OSError:
        mtime = 0.0
    with _LOCK:
        if _INDEX is not None and not force and _INDEX.mtime == mtime:
            return _INDEX
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        _INDEX = _build(data, load_firms(), mtime)
        return _INDEX


# --------------------------------------------------------------------------
# Понимание вопроса
# --------------------------------------------------------------------------

@dataclass
class Intent:
    kind: str                       # advisor | company | industry | largest | count | theme | term | search | empty
    firm: Firm | None = None
    company_id: str | None = None
    industry: str | None = None
    theme: str | None = None
    term_rx: str | None = None
    year: int | None = None
    wants_advisors: bool = False
    terms: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)   # слова вопроса, по которым узнали компанию
    words: list[str] = field(default_factory=list)     # те же слова без обрезки окончаний


ADVISOR_WORDS = re.compile(r"консультир|консультант|сопровожда|юрфирм|юридическ|инвестбанк|advis|law firm", re.I)
LARGEST_WORDS = re.compile(r"крупн|больш|дорог|максимальн|самая\s+больш|топ[- ]?\d*", re.I)
COUNT_WORDS = re.compile(r"сколько|как\s+много|число\s+сделок|количеств", re.I)


def _detect_industry(question: str, idx: Index) -> str | None:
    q_tokens = tokens(question)
    q_norm = " ".join(q_tokens)
    known = set(idx.industries)
    for ind, hints in INDUSTRY_HINTS.items():
        if ind not in known:
            continue
        for h in hints:
            hn = norm(h)
            if " " in hn:
                hit = hn in q_norm
            elif len(hn) <= 3:
                hit = hn in q_tokens
            else:
                hit = any(t.startswith(hn) for t in q_tokens)
            if hit:
                return ind
    return None


def _detect_theme(question: str) -> str | None:
    q = norm(question)
    q_tokens = tokens(question)
    # «уход/выход иностранцев» — самая частая тема, узнаём по двум признакам сразу.
    if re.search(r"иностран|зарубеж|нерезидент", q) and re.search(r"уход|уш|выход|выш|покин|продал", q):
        return "Уход иностранного владельца"
    if re.search(r"выходил[а-я]*\s+из\s+росси|уходил[а-я]*\s+из\s+росси|покидал[а-я]*\s+росси", q):
        return "Уход иностранного владельца"
    for theme, hints in THEME_HINTS.items():
        if theme == "Уход иностранного владельца":
            continue
        for h in hints:
            hn = norm(h)
            if len(hn) <= 3:
                if hn in q_tokens:
                    return theme
            elif any(t.startswith(hn) for t in q_tokens):
                return theme
    return None


def _detect_term(question: str) -> str | None:
    q = norm(question)
    for key, rx in TERM_HINTS.items():
        if key in q:
            return rx
    return None


def _declension_match(a: str, b: str) -> bool:
    """Одно слово в разных падежах: общее начало от шести знаков и хвосты не
    длиннее трёх («никольская» / «никольскую»). Строже `same_word`: имя фирмы
    не должно ловиться на общем корне («групп», «мед»)."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 6 and len(a) - n <= 3 and len(b) - n <= 3


def _detect_firm(question: str, idx: Index) -> Firm | None:
    hits = [f for f in idx.firms if f.rx.search(question)]
    if hits:
        return max(hits, key=lambda f: len(f.name))
    # Регулярки каталога знают именительный падеж («никольская»), а вопрос —
    # любой («Никольскую»): владелец 31 августа 2026 не нашёл фирму и получил
    # вместо неё компанию «Никольское». Сверяем значимые русские слова имени
    # фирмы со словами вопроса по общему началу.
    words = query_words(question)
    best: tuple[int, Firm] | None = None
    for f in idx.firms:
        # Родовые слова имени («Консалт», «Партнёры», «Групп») — не имя: по
        # ним «Никольской Консалтинг» узнавалась как «Б1 – Консалт».
        sig = [w for w in tokens(f.name)
               if len(w) >= 6 and re.fullmatch(r"[а-я]+", w) and not _generic_firm_word(w)]
        if not sig:
            continue
        if all(any(_declension_match(sw, w) for w in words) for sw in sig):
            score = sum(len(w) for w in sig)
            if best is None or score > best[0]:
                best = (score, f)
    return best[1] if best else None


_GENERIC_FIRM_ROOTS = ("консалт", "консульт", "партн", "групп", "юрид", "прав", "лигал", "адвокат", "бюро", "коллег", "компани")


def _generic_firm_word(word: str) -> bool:
    w = norm(word)
    return w in ADVISOR_GENERIC or any(w.startswith(r) for r in _GENERIC_FIRM_ROOTS)


def _significant(name: str) -> list[str]:
    return [stem(t) for t in tokens(name) if t not in GENERIC_NAME_WORDS and len(t) >= 3]


def _name_word_match(name_stem: str, term: str) -> bool:
    """Слово вопроса называет слово ИМЕНИ (компании, стороны, заголовка).
    `same_word` здесь слишком мягок: у него общее начало в три знака, и
    «почему» ложилось на «Почта» (Почта Банк), «получил» — на «Полюс», «так»
    — на «Такси»; вопрос «Почему так много покупает?» со страницы «Яндекса»
    отвечал про Почта Банк (2 сентября 2026). Имя — не обычное слово: требуем
    общее начало от четырёх знаков (или равенство — для коротких «ВТБ»,
    «МТС»)."""
    if name_stem == term:
        return True
    if not same_word(name_stem, term):
        return False
    n = 0
    for x, y in zip(name_stem, term):
        if x != y:
            break
        n += 1
    return n >= 4


def _detect_company(question: str, idx: Index, terms: list[str]) -> tuple[str, list[str]] | None:
    """Компания из вопроса — по значимым словам её имени. Возвращает id и те
    слова вопроса, по которым она узнана: `route` сверяет их с отраслевыми
    подсказками, иначе «сделки в фарме» узнавалось как ГК «Р-Фарм»."""
    if not terms:
        return None
    best: tuple[int, int, str, list[str]] | None = None
    for cid, c in idx.companies.items():
        sig = _significant(c.get("name") or "")
        if not sig or len(sig) > 4:
            continue
        matched_terms = [t for s in sig for t in terms if _name_word_match(s, t)]
        if len({s for s in sig if any(_name_word_match(s, t) for t in terms)}) < len(sig):
            continue
        n_deals = len(idx.company_deals.get(cid) or [])
        if n_deals == 0:
            continue
        # Больше значимых слов совпало — точнее; при равенстве — та, у кого сделок больше.
        score = (len(sig), n_deals)
        if best is None or score > (best[0], best[1]):
            best = (len(sig), n_deals, cid, matched_terms)
    return (best[2], best[3]) if best else None


def _industry_covers(token: str) -> bool:
    tn = norm(token)
    for hints in INDUSTRY_HINTS.values():
        for h in hints:
            hn = norm(h)
            if " " in hn:
                continue
            if (tn == hn) if len(hn) <= 3 else tn.startswith(hn):
                return True
    return False


def _without_firm_name(question: str, firm: Firm) -> str:
    """Вопрос без слов, которыми названа фирма (по регулярке каталога и по
    самим словам имени в любом падеже)."""
    text = firm.rx.sub(" ", question)
    name_words = [w for w in tokens(firm.name) if len(w) >= 4]
    kept = [w for w in re.split(r"(\s+)", text)
            if not any(_declension_match(norm(w).strip("«»\"()"), nw) or norm(w).strip("«»\"()") == nw for nw in name_words)]
    return "".join(kept)


def route(question: str, idx: Index | None = None) -> Intent:
    idx = idx or get_index()
    terms = query_terms(question)
    words = query_words(question)
    year = year_in(question)
    firm = _detect_firm(question, idx)
    # Слова из имени фирмы не должны читаться как отрасль: «Никольская
    # консалтинг» узнавалась фирмой, а «консалтинг» — отраслью, и список её
    # сделок фильтровался по отрасли до нуля (владелец 31 августа 2026:
    # «у Никольской вообще-то есть 2 сделки»).
    industry = _detect_industry(_without_firm_name(question, firm) if firm else question, idx)
    theme = _detect_theme(question)
    term_rx = _detect_term(question)
    wants_adv = bool(ADVISOR_WORDS.search(question))
    if firm:
        return Intent("advisor", firm=firm, year=year, industry=industry, terms=terms)
    if LARGEST_WORDS.search(question) and not wants_adv:
        return Intent("largest", year=year, industry=industry, terms=terms)
    if COUNT_WORDS.search(question):
        return Intent("count", year=year, industry=industry, theme=theme, terms=terms)
    if term_rx:
        return Intent("term", term_rx=term_rx, year=year, industry=industry, terms=terms)
    if theme:
        return Intent("theme", theme=theme, year=year, industry=industry, terms=terms)
    found = _detect_company(question, idx, terms)
    if found:
        company, matched = found
        # Компанию узнали по слову, которое одновременно называет отрасль
        # («фарм», «банк», «агро») — это вопрос про отрасль, а не про компанию.
        if industry and matched and all(_industry_covers(t) for t in matched):
            company = None
        if company:
            return Intent("company", company_id=company, year=year, wants_advisors=wants_adv,
                          terms=terms, matched=matched)
    if industry:
        return Intent("industry", industry=industry, year=year, wants_advisors=wants_adv, terms=terms)
    if not terms:
        # Признаки вопроса нужны и пустому маршруту: со страницы компании «кто
        # консультировал сделки?» — это вопрос о консультантах этой компании.
        return Intent("empty", year=year, wants_advisors=wants_adv, terms=terms)
    return Intent("search", year=year, wants_advisors=wants_adv, terms=terms, words=words)


# --------------------------------------------------------------------------
# Поиск по словам (когда вопрос не про конкретную сущность)
# --------------------------------------------------------------------------

def _term_weight(term: str, idx: Index) -> float:
    """Вес слова вопроса: редкое в заголовках — отличительное, частое — фон."""
    total = max(1, len(idx.docs))
    n = sum(cnt for t, cnt in idx.df.items() if same_word(term, t))
    if n == 0:
        return 0.0
    if n <= 5:
        return 6.0
    if n <= 40:
        return 3.0
    if n <= 0.15 * total:
        return 1.0
    return 0.3


def search(terms: list[str], idx: Index, limit: int = MAX_DEALS_FOR_MODEL) -> list[Doc]:
    if not terms:
        return idx.docs[:limit]

    weights = {t: _term_weight(t, idx) for t in terms}
    scored = []
    for doc in idx.docs:
        score = 0.0
        for t in terms:
            w = weights[t]
            if not w:
                continue
            if any(same_word(t, s) for s in doc.strong):
                score += w
            elif any(same_word(t, s) for s in doc.weak):
                score += w * 0.4
        if score:
            scored.append((score, doc))
    if not scored:
        return []
    scored.sort(key=lambda x: (-x[0], x[1].date))
    # Точное попадание не должно тянуть за собой хвост из карточек, совпавших
    # одним фоновым словом: оставляем те, что набрали хотя бы половину от
    # лучшего результата (и не меньше одного веса «редкого» совпадения).
    top = scored[0][0]
    floor = max(1.0, top * 0.5)
    kept = [d for s, d in scored if s >= floor]
    return kept[:limit]


# --------------------------------------------------------------------------
# Точные ответы
# --------------------------------------------------------------------------

def _link(doc: Doc) -> str:
    return f"[{doc.title}](#/deal/{doc.id})"


def _fmt_date(ds: str) -> str:
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ds):
        y, m, d = ds.split("-")
        return f"{int(d)} {months[int(m) - 1]} {y}"
    if re.fullmatch(r"\d{4}-\d{2}", ds):
        y, m = ds.split("-")
        return f"{months[int(m) - 1]} {y}"
    return ds[:4]


def _line(doc: Doc) -> str:
    bits = [_fmt_date(doc.date)]
    if has_fact(doc.sum_text):
        bits.append(doc.sum_text)
    if doc.status:
        bits.append(doc.status.lower())
    return f"- {_link(doc)} — {', '.join(bits)}"


def _plural(n: int, one: str, few: str, many: str) -> str:
    a, b = n % 100, n % 10
    if 10 < a < 20:
        return many
    if 1 < b < 5:
        return few
    if b == 1:
        return one
    return many


def _filter(docs: list[Doc], year: int | None = None, industry: str | None = None) -> list[Doc]:
    out = docs
    if year:
        out = [d for d in out if d.year == year]
    if industry:
        out = [d for d in out if industry in d.industries]
    return out


def _role_bucket(role: str) -> str | None:
    """Роль консультанта в карточке записана вольно («Юридический консультант
    покупателя (X5 Group)», «Продавец — ООО «Агрострой»»). Для ответа человеку
    нужна одна из нескольких понятных ролей, а не сырая строка."""
    r = norm(role)
    if not r:
        return None
    if "покупател" in r or "инвестор" in r or "приобретател" in r:
        return "консультант покупателя"
    if "продавц" in r or "продавец" in r:
        return "консультант продавца"
    if "эмитент" in r or "размещен" in r or "андеррайт" in r:
        return "консультант при размещении акций"
    if "финансов" in r:
        return "финансовый консультант"
    if "юридическ" in r or "консультант" in r:
        return "юридический консультант"
    return None


def _advisor_stats(docs: list[Doc], idx: Index) -> list[tuple[str, int]]:
    """Какие фирмы названы консультантами в этих сделках — по каталогу, а не
    по сырому тексту: одна фирма пишется по-разному («Orion», «Orion Law»)."""
    counts: Counter = Counter()
    for doc in docs:
        seen = set()
        for f in idx.firms:
            if f.id in seen:
                continue
            if any(f.rx.search(a) for a in doc.advisors):
                counts[f.name] += 1
                seen.add(f.id)
    return counts.most_common(8)


@dataclass
class Retrieval:
    intent: str
    answer: str | None          # точный ответ по базе (markdown) или None, если сказать нечего
    docs: list[Doc]             # что уходит модели
    subject: str | None = None  # о ком/о чём — для заголовка диалога

    def deal_ids(self) -> list[str]:
        return [d.id for d in self.docs]


NOTE_ADVISORS = ("Считаются сделки, где фирма названа консультантом в открытых источниках; "
                 "фирмы раскрывают не все проекты.")
NOTE_SUMS = "Сумма известна не у всех сделок: цену в России раскрывают меньше чем в половине случаев."


def _answer_advisor(intent: Intent, idx: Index) -> Retrieval:
    firm = intent.firm
    docs = _filter(idx.firm_deals.get(firm.id) or [], intent.year, intent.industry)
    if not docs:
        scope = f" за {intent.year} год" if intent.year else ""
        text = (f"В «Компасе» пока нет сделок{scope}, где [{firm.name}](#/advisors/{firm.id}) названа "
                f"консультантом: фирма есть в каталоге, но её проекты в открытых источниках не встретились. "
                f"{NOTE_ADVISORS} Каталог фирмы: [{firm.name}](#/advisors/{firm.id}).")
        return Retrieval("advisor", text, [], firm.name)
    n = len(docs)
    inds = Counter(i for d in docs for i in d.industries).most_common(4)
    roles = Counter(b for d in docs for r, name in d.advisor_roles
                    if firm.rx.search(name) and (b := _role_bucket(r))).most_common(3)
    head = (f"Консультант [{firm.name}](#/advisors/{firm.id}) в «Компасе»: {n} "
            f"{_plural(n, 'сделка', 'сделки', 'сделок')}"
            + (f" за {intent.year} год" if intent.year else "") + ".")
    lines = [head]
    if inds:
        lines.append("Отрасли: " + ", ".join(f"{i} ({c})" for i, c in inds) + ".")
    if roles:
        lines.append("Чаще всего в роли: " + ", ".join(f"{r.lower()} ({c})" for r, c in roles) + ".")
    lines.append("Последние:")
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED} — все на [странице фирмы](#/advisors/{firm.id}).")
    lines.append(NOTE_ADVISORS)
    return Retrieval("advisor", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], firm.name)


def _answer_company(intent: Intent, idx: Index) -> Retrieval:
    cid = intent.company_id
    name = _company_name(idx.companies, cid)
    docs = _filter(idx.company_deals.get(cid) or [], intent.year, None)
    docs = sorted(docs, key=lambda d: d.date, reverse=True)
    if not docs:
        return Retrieval("company", f"У компании [{name}](#/companies/{cid}) в «Компасе» нет сделок"
                         + (f" за {intent.year} год" if intent.year else "") + ".", [], name)
    n = len(docs)
    # «Сделка Яндекса с Uber» — вопрос про одну сделку компании, а не про
    # весь список: слова вопроса сверх имени компании отбирают подходящие.
    name_stems = [stem(t) for t in tokens(name)]
    extra = [t for t in intent.terms
             if t not in intent.matched and not t.isdigit() and not any(same_word(t, s) for s in name_stems)]
    picked = [d for d in docs if extra and any(
        any(same_word(t, s) for s in d.strong) or any(same_word(t, s) for s in d.weak) for t in extra)]
    if picked and len(picked) < n:
        k = len(picked)
        lines = [f"По вопросу {'подходит' if k == 1 else 'подходят'} {k} "
                 f"{_plural(k, 'сделка', 'сделки', 'сделок')} компании [{name}](#/companies/{cid}):"]
        lines += [_line(d) for d in picked[:MAX_LISTED]]
        if k > MAX_LISTED:
            lines.append(f"…и ещё {k - MAX_LISTED}.")
        lines.append(f"Всего у компании в «Компасе» {n} {_plural(n, 'сделка', 'сделки', 'сделок')}"
                     + (f" за {intent.year} год" if intent.year else "")
                     + f" — на [странице компании](#/companies/{cid}).")
        rest = [d for d in docs if d not in picked]
        docs = picked + rest
    else:
        lines = [f"Компания [{name}](#/companies/{cid}) в «Компасе»: {n} {_plural(n, 'сделка', 'сделки', 'сделок')}"
                 + (f" за {intent.year} год" if intent.year else "") + ":"]
        lines += [_line(d) for d in docs[:MAX_LISTED]]
        if n > MAX_LISTED:
            lines.append(f"…и ещё {n - MAX_LISTED} — на [странице компании](#/companies/{cid}).")
    if intent.wants_advisors:
        stats = _advisor_stats(docs, idx)
        if stats:
            lines.append("Консультанты, названные в этих сделках: " + ", ".join(f"{f} ({c})" for f, c in stats) + ".")
        else:
            lines.append("Консультанты в этих сделках публично не назывались.")
    return Retrieval("company", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], name)


def _answer_industry(intent: Intent, idx: Index) -> Retrieval:
    ind = intent.industry
    docs = _filter(idx.docs, intent.year, ind)
    if not docs:
        return Retrieval("industry", f"В отрасли «{ind}» в базе пока нет сделок"
                         + (f" за {intent.year} год" if intent.year else "") + ".", [], ind)
    n = len(docs)
    lines = [f"В отрасли [{ind}](#/industry/{ind}) в базе «Компаса» {n} {_plural(n, 'сделка', 'сделки', 'сделок')}"
             + (f" за {intent.year} год" if intent.year else "") + "."]
    if intent.wants_advisors:
        stats = _advisor_stats(docs, idx)
        named = sum(1 for d in docs if d.advisors)
        if stats:
            lines.append(f"Консультанты названы у {named} из них. Чаще других: "
                         + ", ".join(f"{f} ({c})" for f, c in stats) + ".")
        else:
            lines.append("Ни у одной из этих сделок консультанты публично не назывались.")
        lines.append(NOTE_ADVISORS)
    lines.append("Последние сделки:")
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED} — на [странице отрасли](#/industry/{ind}).")
    return Retrieval("industry", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], ind)


def _answer_largest(intent: Intent, idx: Index) -> Retrieval:
    pool = _filter(idx.docs, intent.year, intent.industry)
    with_sum = [d for d in pool if d.sum_rub]
    if not with_sum:
        return Retrieval("largest", "В этой выборке нет сделок с суммой в рублях — сравнить не по чему.", [], None)
    named = sorted([d for d in with_sum if not d.estimate], key=lambda d: -(d.sum_rub or 0))
    est = sorted([d for d in with_sum if d.estimate], key=lambda d: -(d.sum_rub or 0))
    scope = " ".join(x for x in [f"за {intent.year} год" if intent.year else "",
                                 f"в отрасли «{intent.industry}»" if intent.industry else ""] if x)
    lines = [f"Крупнейшие сделки {scope} по цене, которую назвали сами стороны:" if scope
             else "Крупнейшие сделки в базе по цене, которую назвали сами стороны:"]
    lines += [_line(d) for d in named[:5]]
    if est:
        lines.append("По оценкам экспертов (не подтверждённая цена):")
        lines += [_line(d) for d in est[:3]]
    lines.append(NOTE_SUMS + f" Здесь сравнивались {len(with_sum)} из {len(pool)}.")
    return Retrieval("largest", "\n".join(lines), (named[:8] + est[:4])[:MAX_DEALS_FOR_MODEL], None)


def _answer_count(intent: Intent, idx: Index) -> Retrieval:
    pool = _filter(idx.docs, intent.year, intent.industry)
    if intent.theme:
        pool = [d for d in pool if intent.theme in d.themes]
    n = len(pool)
    what = " ".join(x for x in [f"за {intent.year} год" if intent.year else "",
                                f"в отрасли «{intent.industry}»" if intent.industry else "",
                                f"по теме «{intent.theme}»" if intent.theme else ""] if x)
    lines = [f"В базе «Компаса» {n} {_plural(n, 'сделка', 'сделки', 'сделок')} {what}.".replace("  ", " ")]
    if pool:
        by_year = Counter(d.year for d in pool)
        if not intent.year and len(by_year) > 1:
            lines.append("По годам: " + ", ".join(f"{y} — {c}" for y, c in sorted(by_year.items())) + ".")
        lines.append("Последние:")
        lines += [_line(d) for d in pool[:MAX_LISTED]]
    lines.append("Это сделки, показанные на сайте (с 2022 года), а не вся статистика рынка.")
    return Retrieval("count", "\n".join(lines), pool[:MAX_DEALS_FOR_MODEL], None)


def _answer_theme(intent: Intent, idx: Index) -> Retrieval:
    docs = [d for d in _filter(idx.docs, intent.year, intent.industry) if intent.theme in d.themes]
    if not docs:
        return Retrieval("theme", f"По теме «{intent.theme}» сделок"
                         + (f" за {intent.year} год" if intent.year else "") + " в базе пока нет.", [], intent.theme)
    n = len(docs)
    lines = [f"По теме [{intent.theme}](#/theme/{intent.theme}) в базе «Компаса» {n} "
             f"{_plural(n, 'сделка', 'сделки', 'сделок')}"
             + (f" за {intent.year} год" if intent.year else "") + ". Последние:"]
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED} — [все по теме](#/theme/{intent.theme}).")
    return Retrieval("theme", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], intent.theme)


def _answer_term(intent: Intent, idx: Index) -> Retrieval:
    rx = re.compile(intent.term_rx, re.I)
    docs = [d for d in _filter(idx.docs, intent.year, intent.industry) if rx.search(d.facts) or rx.search(d.title)]
    if not docs:
        return Retrieval("term", "Такое условие в «Компасе» пока не описано ни у одной сделки.", [], None)
    n = len(docs)
    lines = [f"Такое условие названо у {n} {_plural(n, 'сделки', 'сделок', 'сделок')}. Последние:"]
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED}.")
    return Retrieval("term", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], None)


def _short_advisor(raw: str) -> str:
    """Имя консультанта из сырой строки карточки: до тире-пояснения и до
    скобки, не длиннее 60 знаков — на экран уходит имя, а не абзац."""
    name = re.split(r"\s+[—–-]\s+|\s*\(", raw, maxsplit=1)[0].strip(" ;,")
    return (name[:57] + "…") if len(name) > 60 else name


def _answer_search(intent: Intent, idx: Index) -> Retrieval:
    # Спросили про консультанта, которого нет в каталоге, — ищем его имя в
    # самих карточках: там названы и фирмы вне каталога. Родовые слова
    # («партнёры», legal, консалтинг) именем не считаются — иначе «Иванов и
    # партнёры» находил бы всех «…и партнёры» базы.
    if intent.wants_advisors and intent.terms:
        name_terms = [t for t in (intent.words or intent.terms)
                      if len(t) >= 4 and t not in ADVISOR_GENERIC and stem(t) not in ADVISOR_GENERIC]
        hits = [d for d in idx.docs
                if any(any(name_match(t, w) for w in tokens(a)) for t in name_terms for a in d.advisors)] if name_terms else []
        hits = _filter(hits, intent.year, intent.industry)
        if hits:
            names = Counter(_short_advisor(a) for d in hits for a in d.advisors
                            if any(any(name_match(t, w) for w in tokens(a)) for t in name_terms))
            n = len(hits)
            who = ", ".join(f"«{a}»" for a, _ in names.most_common(3))
            lines = [f"Консультант с таким именем ({who}) назван в {n} "
                     f"{_plural(n, 'сделке', 'сделках', 'сделках')}:"]
            lines += [_line(d) for d in hits[:MAX_LISTED]]
            if n > MAX_LISTED:
                lines.append(f"…и ещё {n - MAX_LISTED}.")
            lines.append(NOTE_ADVISORS)
            return Retrieval("advisor", "\n".join(lines), hits[:MAX_DEALS_FOR_MODEL], who)
        if name_terms:
            close = [f for f in idx.firms if any(name_match(t, w) for t in name_terms for w in tokens(f.name))]
            tail = (" Похожие по названию в каталоге: "
                    + ", ".join(f"[{f.name}](#/advisors/{f.id})" for f in close[:3]) + ".") if close else ""
            return Retrieval("advisor",
                             "В базе «Компаса» такой консультант не назван ни в одной сделке, и в каталоге "
                             "консультантов его нет." + tail + " " + NOTE_ADVISORS, [], None)
    docs = search(intent.terms, idx)
    if intent.year:
        by_year = [d for d in docs if d.year == intent.year]
        docs = by_year or docs
    if not docs:
        return Retrieval("search", None, [], None)
    lines = ["Похожие по словам вопроса сделки из базы:"]
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    return Retrieval("search", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], None)


def _answer_deal(doc: Doc) -> Retrieval:
    """Сводка одной сделки — для вопроса, заданного с её страницы."""
    bits = [_fmt_date(doc.date)]
    if doc.status:
        bits.append(doc.status.lower())
    lines = [f"Сделка {_link(doc)} — {', '.join(bits)}."]
    parties = []
    if doc.buyer:
        parties.append(f"покупатель — {doc.buyer}")
    if doc.seller:
        parties.append(f"продавец — {doc.seller}")
    if doc.target or doc.asset:
        parties.append(f"предмет — {doc.target or doc.asset}")
    if parties:
        lines.append("Стороны: " + "; ".join(parties) + ".")
    lines.append(f"Сумма: {doc.sum_text}." if has_fact(doc.sum_text) else "Сумму сделки не раскрывали.")
    if doc.advisor_roles:
        lines.append("Консультанты: " + ", ".join(f"{n} ({r.lower()})" if r else n
                                                 for r, n in doc.advisor_roles[:4]) + ".")
    else:
        lines.append("Консультанты в открытых источниках не назывались.")
    return Retrieval("deal", "\n".join(lines), [doc], doc.title)


def _answer_entity(context_type: str | None, context_id: str | None, intent: Intent, idx: Index) -> Retrieval | None:
    """Ответ о сущности страницы, с которой задан вопрос, — когда сам вопрос
    её не называет. «Что известно?» или «Кто консультировал сделки?» на
    странице «Яндекса» до 2 сентября 2026 давали пустой быстрый ответ (все
    слова вопроса — стоп-слова), и посетитель ждал модель 30–40 секунд, хотя
    точная сводка по компании считается за миллисекунды."""
    if not context_type or not context_id:
        return None
    if context_type == "company" and context_id in idx.companies:
        return _answer_company(Intent("company", company_id=context_id, year=intent.year,
                                      wants_advisors=intent.wants_advisors, terms=intent.terms), idx)
    if context_type == "advisor":
        firm = next((f for f in idx.firms if f.id == context_id), None)
        if firm:
            return _answer_advisor(Intent("advisor", firm=firm, year=intent.year, terms=intent.terms), idx)
    if context_type == "industry" and context_id in idx.industries:
        return _answer_industry(Intent("industry", industry=context_id, year=intent.year,
                                       wants_advisors=intent.wants_advisors, terms=intent.terms), idx)
    if context_type == "deal":
        doc = idx.by_id.get(context_id)
        if doc:
            return _answer_deal(doc)
    return None


def _search_is_specific(intent: Intent, docs: list[Doc], idx: Index) -> bool:
    """Поиск по словам попал во что-то конкретное: хотя бы одно отличительное
    (редкое) слово вопроса стоит в заголовке или сторонах первой найденной
    сделки. «Кто купил Ситибанк?» — да; «какие последние сделки?» — нет,
    это фоновые слова, и со страницы сущности такой вопрос про неё."""
    if not docs:
        return False
    top = docs[0]
    return any(len(t) >= 4 and _term_weight(t, idx) >= 3.0 and any(_name_word_match(s, t) for s in top.strong)
               for t in intent.terms)


def _scoped(context_type: str | None, context_id: str | None, idx: Index) -> list[Doc] | None:
    """Вопрос, заданный со страницы сделки/компании/фирмы/отрасли, — про неё."""
    if not context_type or not context_id:
        return None
    if context_type == "deal":
        d = idx.by_id.get(context_id)
        return [d] if d else None
    if context_type == "company":
        docs = idx.company_deals.get(context_id) or []
        return sorted(docs, key=lambda d: d.date, reverse=True)[:MAX_DEALS_FOR_MODEL] or None
    if context_type == "advisor":
        return (idx.firm_deals.get(context_id) or [])[:MAX_DEALS_FOR_MODEL] or None
    if context_type == "industry":
        return [d for d in idx.docs if context_id in d.industries][:MAX_DEALS_FOR_MODEL] or None
    return None


def retrieve(question: str, context_type: str | None = None, context_id: str | None = None,
             idx: Index | None = None) -> Retrieval:
    idx = idx or get_index()
    intent = route(question, idx)
    handlers = {
        "advisor": _answer_advisor, "company": _answer_company, "industry": _answer_industry,
        "largest": _answer_largest, "count": _answer_count, "theme": _answer_theme,
        "term": _answer_term, "search": _answer_search,
    }
    if intent.kind == "empty":
        own = _answer_entity(context_type, context_id, intent, idx)
        if own:
            return own
        scoped = _scoped(context_type, context_id, idx)
        return Retrieval("empty", None, scoped or [], None)
    result = handlers[intent.kind](intent, idx)
    # Со страницы сущности вопрос почти всегда про неё: если поиск по словам
    # не попал ни во что конкретное, быстрый ответ — сводка по самой
    # сущности, а модели уходят её сделки первыми. Конкретное попадание
    # («Кто купил Ситибанк?» со страницы «Яндекса») остаётся ответом на
    # заданный вопрос — сделки страницы лишь добавляются к нему.
    if intent.kind == "search":
        own = _answer_entity(context_type, context_id, intent, idx)
        if own and own.answer and result.intent == "search" and not _search_is_specific(intent, result.docs, idx):
            merged = own.docs + [d for d in result.docs if d not in own.docs]
            return Retrieval(own.intent, own.answer, merged[:MAX_DEALS_FOR_MODEL], own.subject)
        scoped = _scoped(context_type, context_id, idx)
        if scoped:
            # Найденное — первым: сводка говорит о нём; сделки страницы — контекст для модели.
            merged = result.docs + [d for d in scoped if d not in result.docs]
            result = Retrieval(result.intent, result.answer, merged[:MAX_DEALS_FOR_MODEL], result.subject)
    return result


# --------------------------------------------------------------------------
# Компактная карточка для модели
# --------------------------------------------------------------------------

def compact(doc: Doc, facts_chars: int = 320) -> dict[str, Any]:
    eco, law = doc.raw.get("eco") or {}, doc.raw.get("law") or {}
    out: dict[str, Any] = {"id": doc.id, "title": doc.title, "date": doc.date}
    if doc.status:
        out["status"] = doc.status
    if has_fact(doc.sum_text):
        out["sum"] = doc.sum_text
    if doc.industries:
        out["industry"] = ", ".join(doc.industries)
    if doc.buyer:
        out["buyer"] = doc.buyer
    if doc.seller:
        out["seller"] = doc.seller
    if doc.target or doc.asset:
        out["subject"] = doc.target or doc.asset
    if doc.advisor_roles:
        out["advisors"] = [f"{r}: {n}" if r else n for r, n in doc.advisor_roles][:4]
    facts = []
    for key in ("rationale", "share", "val", "context"):
        if has_fact(eco.get(key)):
            facts.append(str(eco[key]))
    for key in ("appr", "struct", "terms"):
        if has_fact(law.get(key)):
            facts.append(str(law[key]))
    if facts:
        out["facts"] = " ".join(facts)[:facts_chars]
    return out


def context_for_model(ret: Retrieval) -> str:
    cards = [compact(d) for d in ret.docs[:MAX_DEALS_FOR_MODEL]]
    return json.dumps(cards, ensure_ascii=False)


def suggestions(idx: Index | None = None) -> list[str]:
    """Примеры вопросов для экрана ассистента — из данных, а не из головы:
    у каждого примера гарантированно есть ответ по базе."""
    idx = idx or get_index()
    out: list[str] = []
    top_firm = max(idx.firm_deals.items(), key=lambda kv: len(kv[1]), default=None)
    if top_firm:
        firm = next((f for f in idx.firms if f.id == top_firm[0]), None)
        if firm:
            out.append(f"Какие сделки сопровождала {firm.name}?")
    years = sorted({d.year for d in idx.docs}, reverse=True)
    if years:
        y = years[1] if len(years) > 1 else years[0]
        out.append(f"Самые крупные сделки {y} года")
    top_company = max(idx.company_deals.items(), key=lambda kv: len(kv[1]), default=None)
    if top_company:
        name = _company_name(idx.companies, top_company[0])
        if name:
            # Имя не склоняем — «у компании «Яндекс»» верно при любом названии.
            out.append(f"Какие сделки были у компании «{name}»?")
    if any("Уход иностранного владельца" in d.themes for d in idx.docs):
        out.append("Кто из иностранных владельцев уходил из России?")
    return out[:4]
