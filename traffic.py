# -*- coding: utf-8 -*-
"""Своя статистика посещений сайта — без Яндекса и без личных данных.

ЗАЧЕМ. 14 октября 2026 Яндекс Метрика перестала отвечать, и владелец попросил
«полезный сервис, чтобы мы смогли мониторить статистику посещений, может ещё
видеть, куда люди заходят и смотрят». Страница сайта сама шлёт сюда «открыли
такой-то экран» (`POST /api/t`, см. `trackView` в static/index.html); здесь —
приём, подсчёт и человеческий вид: `/ops/traffic` и строки для консоли.

ЧТО ХРАНИМ (db.models.PageView). Время, случайный номер браузера (его
придумывает сам браузер), номер визита, адрес экрана внутри сайта, имя сайта,
с которого пришли (только на первом экране визита), тип устройства по ширине
экрана и «вошёл ли человек». Ни IP, ни браузера, ни почты.

ЧТО НЕ СЧИТАЕМ. Роботов поисковиков и наши собственные проверки — безголовый
браузер (`HeadlessChrome`) снимает скриншоты для макетов и тестов, и без
фильтра каждая наша проверка выглядела бы живым посетителем. Черновики карточек
(`/preview/…`) — их открывают только владелец и партнёр из консоли.
"""
from __future__ import annotations

import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.parse import unquote

KEEP_DAYS = 400
MSK = timedelta(hours=3)
BOT_UA = re.compile(r"bot|crawl|spider|slurp|preview|headless|lighthouse|python-|curl/|wget|httpx|"
                    r"facebookexternalhit|telegrambot|yandex(?!browser)|bingpreview|vkshare", re.I)
SKIP_SECTIONS = {"preview"}
SECTION_NAMES = {
    "home": "Главная", "deals": "Лента сделок", "search": "Поиск", "ind": "Отрасль в ленте",
    "theme": "Тема", "deal": "Карточки сделок", "companies": "Каталог компаний", "company": "Профили компаний",
    "advisors": "Каталог консультантов", "advisor": "Профили консультантов", "industry": "Сводки по отраслям",
    "analytics": "Аналитика", "assistant": "Ассистент", "materials": "Материалы", "account": "Личный кабинет",
    "compare": "Сравнение компаний", "about": "О проекте", "other": "Другое",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_hits: dict[str, list[float]] = defaultdict(list)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_bot(user_agent: str) -> bool:
    ua = str(user_agent or "")
    return not ua or bool(BOT_UA.search(ua))


def too_fast(key: str, limit: int = 120, window: float = 60.0) -> bool:
    """Не больше `limit` отметок в минуту с одного адреса — защита таблицы от
    накрутки. Адрес живёт только в памяти процесса и никуда не пишется."""
    now = time.monotonic()
    hits = [t for t in _hits[key] if now - t < window]
    hits.append(now)
    _hits[key] = hits
    if len(_hits) > 5000:
        for k in list(_hits)[:2500]:
            _hits.pop(k, None)
    return len(hits) > limit


def normalize(path: str) -> tuple[str, str] | None:
    """(адрес, раздел) или None, если считать не надо."""
    p = unquote(str(path or "/")).split("?", 1)[0].strip() or "/"
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"\s+", " ", p)[:200]
    parts = [x for x in p.split("/") if x]
    page = parts[0] if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    if page in SKIP_SECTIONS:
        return None
    if not page:
        return "/", "home"
    if page in ("deal", "companies", "advisors") and arg:
        if not _SAFE_ID.match(arg):
            return None
        section = {"deal": "deal", "companies": "company", "advisors": "advisor"}[page]
        return "/%s/%s" % (page, arg), section
    if page in ("search", "ind", "industry", "theme"):
        return ("/%s/%s" % (page, arg[:80])) if arg else "/" + page, page
    if page in SECTION_NAMES:
        return "/" + page, page
    return "/" + page[:40], "other"


def device_of(width) -> str:
    try:
        w = int(width)
    except (TypeError, ValueError):
        return "desktop"
    return "phone" if w < 700 else "tablet" if w < 1100 else "desktop"


def ref_host(ref: str, own_host: str) -> str | None:
    m = re.match(r"^https?://([^/:?#]+)", str(ref or "").strip(), re.I)
    if not m:
        return None
    host = m.group(1).lower()
    host = host[4:] if host.startswith("www.") else host
    if own_host and (host == own_host or host.endswith("." + own_host)):
        return None
    return host[:120]


def source_name(host: str | None) -> str:
    if not host:
        return "Прямые заходы и закладки"
    if host in ("t.me", "telegram.org", "web.telegram.org") or "telegram" in host:
        return "Telegram"
    if "yandex" in host or host == "ya.ru":
        return "Яндекс"
    if "google" in host:
        return "Google"
    if host in ("vk.com", "vk.ru", "m.vk.com") or host.endswith(".vk.com"):
        return "ВКонтакте"
    if "linkedin" in host:
        return "LinkedIn"
    return host


# ------------------------------------------------------------------ подсчёт --

def stats(db, PageView, days: int = 7, base: dict | None = None, now: datetime | None = None) -> dict:
    """Всё для страницы и консоли за последние `days` суток (скользящее окно)."""
    from sqlalchemy import select
    now = now or _now()
    span = max(days, 30)
    since_all = now - timedelta(days=span)
    rows = db.execute(select(PageView.created_at, PageView.visitor, PageView.session, PageView.path,
                             PageView.section, PageView.ref_host, PageView.device, PageView.logged_in)
                      .where(PageView.created_at >= since_all)
                      .order_by(PageView.created_at)).all()
    since = now - timedelta(days=days)
    cur = [r for r in rows if r.created_at >= since]
    first_seen = {}
    for r in db.execute(select(PageView.visitor, PageView.created_at)
                        .where(PageView.visitor.in_({r.visitor for r in cur} or {""}))
                        .order_by(PageView.created_at)).all():
        first_seen.setdefault(r.visitor, r.created_at)

    visitors = {r.visitor for r in cur}
    sessions: dict[str, list] = defaultdict(list)
    for r in cur:
        sessions[r.session].append(r)
    new_visitors = {v for v in visitors if first_seen.get(v, now) >= since}
    online = {r.visitor for r in rows if r.created_at >= now - timedelta(minutes=5)}
    dev = Counter()
    for v_dev in {(r.visitor, r.device) for r in cur}:
        dev[v_dev[1]] += 1
    entry = Counter(s[0].path for s in sessions.values())
    sources = Counter(source_name(s[0].ref_host) for s in sessions.values())
    durations = sorted((s[-1].created_at - s[0].created_at).total_seconds() for s in sessions.values() if len(s) > 1)

    def top(section, n=10):
        c = Counter(r.path for r in cur if r.section == section)
        return [(p, k, len({r.visitor for r in cur if r.path == p})) for p, k in c.most_common(n)]

    by_day = []
    for back in range(29, -1, -1):
        d = (now + MSK - timedelta(days=back)).date()
        day_rows = [r for r in rows if (r.created_at + MSK).date() == d]
        by_day.append({"day": d.isoformat(), "visitors": len({r.visitor for r in day_rows}),
                       "views": len(day_rows), "sessions": len({r.session for r in day_rows})})

    recent = sorted(sessions.values(), key=lambda s: s[-1].created_at, reverse=True)[:20]
    out = {
        "days": days,
        "views": len(cur), "visitors": len(visitors), "sessions": len(sessions),
        "new_visitors": len(new_visitors), "returning": len(visitors - new_visitors),
        "online": len(online),
        "logged_in_visitors": len({r.visitor for r in cur if r.logged_in}),
        "views_per_session": (lambda x: int(x) if x == int(x) else x)(round(len(cur) / len(sessions), 1)) if sessions else 0,
        "single_page_share": round(100 * sum(1 for s in sessions.values() if len(s) == 1) / len(sessions)) if sessions else 0,
        "median_visit_seconds": int(durations[len(durations) // 2]) if durations else 0,
        "devices": dict(dev),
        "sections": Counter(r.section for r in cur).most_common(),
        "top_deals": top("deal"), "top_companies": top("company"), "top_advisors": top("advisor"),
        "top_searches": top("search", 15), "top_industries": top("ind", 8) + top("industry", 8),
        "entry_pages": entry.most_common(10),
        "sources": sources.most_common(10),
        "by_day": by_day,
        "recent": [{"start": s[0].created_at.isoformat(), "end": s[-1].created_at.isoformat(),
                    "device": s[0].device, "source": source_name(s[0].ref_host), "logged_in": any(r.logged_in for r in s),
                    "returning": s[0].visitor not in new_visitors,
                    "paths": [r.path for r in s][:12], "more": max(0, len(s) - 12)} for s in recent],
    }
    out["labels"] = labels(base or {}, out)
    return out


_FIRM_NAMES: dict | None = None


def firm_names() -> dict:
    """Имена консультантов из справочника страницы (FIRMS/INV_FIRMS/EXEC_FIRMS
    живут в static/index.html, базы фирм на сервере нет)."""
    global _FIRM_NAMES
    if _FIRM_NAMES is None:
        import os
        try:
            src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html"), encoding="utf-8").read()
            _FIRM_NAMES = dict(re.findall(r'\{id:"([\w-]+)",n:"([^"]+)"', src))
        except OSError:
            _FIRM_NAMES = {}
    return _FIRM_NAMES


def labels(base: dict, st: dict) -> dict:
    deals = {str(d.get("id")): str(d.get("title") or "") for d in base.get("deals") or []}
    comps = base.get("companies") or {}
    paths = {p for p, *_ in st["top_deals"] + st["top_companies"] + st["top_advisors"]
             + st["top_searches"] + st["top_industries"]}
    paths |= {p for p, _ in st["entry_pages"]}
    for s in st["recent"]:
        paths |= set(s["paths"])
    return {p: label(p, deals, comps) for p in paths}


def label(path: str, deals: dict, comps: dict) -> str:
    parts = [x for x in path.split("/") if x]
    if not parts:
        return "Главная"
    page, arg = parts[0], (parts[1] if len(parts) > 1 else "")
    if page == "deal" and arg:
        return deals.get(arg) or "Сделка " + arg
    if page == "companies" and arg:
        c = comps.get(arg) or {}
        return (c.get("name") if isinstance(c, dict) else None) or "Компания " + arg
    if page == "advisors" and arg:
        return firm_names().get(arg) or "Консультант " + arg
    if page == "search" and arg:
        return "Поиск «%s»" % arg
    if page in ("ind", "industry") and arg:
        return "Отрасль «%s»" % arg
    if page == "theme" and arg:
        return "Тема «%s»" % arg
    return SECTION_NAMES.get(page, path)


# ------------------------------------------------------------------ текст ----

def _pct(a, b):
    return round(100 * a / b) if b else 0


def _plural(n, one, few, many):
    n = abs(int(n)) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def console_lines(st: dict) -> list[str]:
    """Блок для сообщения в консоль — словами."""
    if not st["views"]:
        return ["📊 <b>Наш счётчик</b>: за сутки заходов не записано (счётчик работает с 14 октября)."]
    phone = st["devices"].get("phone", 0)
    lines = ["📊 <b>Сайт за сутки</b> (наш счётчик, без Яндекса)",
             "Посетителей — %d (новых — %d), визитов — %d, просмотров — %d. С телефона — %d%%."
             % (st["visitors"], st["new_visitors"], st["sessions"], st["views"], _pct(phone, st["visitors"]))]
    lab = st["labels"]
    tops = [lab.get(p, p) for p, *_ in (st["top_deals"][:3] + st["top_companies"][:2])]
    if tops:
        lines.append("Чаще всего открывали: " + "; ".join(tops) + ".")
    if st["sources"]:
        lines.append("Откуда пришли (визиты): " + ", ".join("%s — %d" % (n, k) for n, k in st["sources"][:4]) + ".")
    if st["top_searches"]:
        lines.append("Искали: " + ", ".join("«%s»" % p.split("/", 2)[2] for p, *_ in st["top_searches"][:5]) + ".")
    return lines


def page_html(st: dict, token: str, metrika_lines: list[str] | None = None) -> str:
    lab = st["labels"]
    q = lambda d: "?token=%s&days=%d" % (escape(token), d)

    def link(p):
        return '<a href="/#%s" target="_blank">%s</a>' % (escape(p), escape(lab.get(p, p)))

    def table(title, rows, cols, empty="Пока пусто."):
        if not rows:
            return "<h2>%s</h2><p class=\"empty\">%s</p>" % (title, empty)
        head = "".join("<th>%s</th>" % c for c in cols)
        body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
        return "<h2>%s</h2><table><tr>%s</tr>%s</table>" % (title, head, body)

    v = st["visitors"]
    cards = [(v, "посетителей"), (st["new_visitors"], "из них новых"), (st["sessions"], "визитов"),
             (st["views"], "просмотров страниц"), (st["views_per_session"], "страниц за визит"),
             ("%d%%" % _pct(st["devices"].get("phone", 0), v), "с телефона"),
             ("%d%%" % st["single_page_share"], "ушли после одной страницы"),
             (st["logged_in_visitors"], "заходили с аккаунтом")]
    grid = "".join('<div class="c"><div class="n">%s</div><div class="l">%s</div></div>' % (escape(str(a)), b) for a, b in cards)
    mx = max([d["visitors"] for d in st["by_day"]] + [1])
    bars = "".join('<div class="bar" title="%s: %d посетителей, %d просмотров"><i style="height:%d%%"></i><span>%s</span></div>'
                   % (d["day"], d["visitors"], d["views"], max(2, round(100 * d["visitors"] / mx)) if d["visitors"] else 0,
                      d["day"][8:]) for d in st["by_day"])
    sect = [(SECTION_NAMES.get(s, s), k) for s, k in st["sections"]]
    recent_rows = []
    for s in st["recent"]:
        start = datetime.fromisoformat(s["start"]) + MSK
        mins = round((datetime.fromisoformat(s["end"]) - datetime.fromisoformat(s["start"])).total_seconds() / 60)
        path = " → ".join(link(p) for p in s["paths"]) + (" … ещё %d" % s["more"] if s["more"] else "")
        who = {"phone": "телефон", "tablet": "планшет", "desktop": "компьютер"}.get(s["device"], s["device"])
        who += " · " + escape(s["source"]) + (" · вернулся" if s["returning"] else " · впервые") + (" · с аккаунтом" if s["logged_in"] else "")
        recent_rows.append((start.strftime("%d.%m %H:%M"), "%s<br><small>%s%s</small>" % (path, who, (" · %d мин" % mins) if mins else "")))
    period = " ".join('<a class="%s" href="%s">%s</a>' % ("on" if st["days"] == d else "", q(d), t)
                      for d, t in ((1, "Сутки"), (7, "7 дней"), (30, "30 дней")))
    metrika = ""
    if metrika_lines:
        metrika = '<div class="mk">%s</div>' % "<br>".join(metrika_lines)
    html = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Компас — посещаемость</title><style>
:root{--bg:#f7f3e9;--card:#fff;--ink:#201c14;--dim:#6b6353;--line:rgba(32,28,20,.14);--acc:#a9824c;--grn:#1D5A44}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 16px 64px}
.w{max-width:1000px;margin:0 auto}h1{font:600 26px/1.2 Georgia,serif;margin:0 0 4px}h2{font:600 18px/1.3 Georgia,serif;margin:30px 0 10px}
.sub{color:var(--dim);font-size:14px;margin:0 0 16px;max-width:700px}
.per{display:flex;gap:18px;margin:0 0 18px;flex-wrap:wrap}.per a{color:var(--dim);text-decoration:none;padding-bottom:3px;border-bottom:1px solid var(--line)}.per a.on{color:var(--grn);border-color:var(--grn)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.c{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.n{font:700 26px/1.1 Georgia,serif}.l{font-size:12.5px;color:var(--dim);margin-top:4px}
.live{display:inline-block;margin-left:8px;font-size:13px;color:var(--grn)}
.chart{display:flex;align-items:flex-end;gap:3px;height:150px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 10px 22px}
.bar{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;position:relative}.bar i{display:block;background:var(--grn);border-radius:3px 3px 0 0;min-height:0}
.bar span{position:absolute;bottom:-18px;left:0;right:0;text-align:center;font-size:10px;color:var(--dim)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}
table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
td,th{border-bottom:1px solid rgba(32,28,20,.08);padding:7px 10px;text-align:left;vertical-align:top}th{font-size:12px;color:var(--dim);font-weight:600}
td:not(:first-child),th:not(:first-child){text-align:right}.wide td:not(:first-child){text-align:left}
td small{color:var(--dim)}a{color:var(--ink)}.empty{color:var(--dim)}
.mk{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:14px;margin:0 0 8px}
@media(max-width:720px){.two{grid-template-columns:1fr}.n{font-size:22px}}
</style></head><body><div class="w">
<h1>Посещаемость сайта<span class="live">● сейчас на сайте: @@ONLINE@@</span></h1>
<p class="sub">Наш счётчик, без Яндекса и без личных данных: браузер сам придумывает себе случайный номер, мы видим только, какие экраны открывали и откуда пришли. Наши проверки и поисковые роботы не считаются. Работает с 14 октября 2026.</p>
<div class="per">@@PERIOD@@ <a href="/ops/activity?token=@@TOKEN@@">Аккаунты и ассистент →</a></div>
<div class="grid">@@GRID@@</div>
<h2>По дням (посетители, последние 30 дней)</h2><div class="chart">@@BARS@@</div>
@@ADV@@
<div class="two"><div>@@SECT@@</div><div>@@SRC@@</div></div>
<div class="two"><div>@@DEALS@@</div><div>@@COMPS@@</div></div>
<div class="two"><div>@@SEARCH@@</div><div>@@ENTRY@@</div></div>
<div class="wide">@@RECENT@@</div>
<h2>Яндекс Метрика</h2>@@METRIKA@@
</div></body></html>"""
    vals = (
        st["online"], period, escape(token), grid, bars,
        table("Самые просматриваемые консультанты", [(link(p), k, u) for p, k, u in st["top_advisors"]],
              ["Консультант", "Просмотров", "Людей"], "Страницы консультантов пока не открывали.") if st["top_advisors"] else "",
        table("Какие разделы смотрят", sect, ["Раздел", "Просмотров"]),
        table("Откуда приходят", st["sources"], ["Источник", "Визитов"]),
        table("Самые просматриваемые сделки", [(link(p), k, u) for p, k, u in st["top_deals"]], ["Сделка", "Просмотров", "Людей"]),
        table("Самые просматриваемые компании", [(link(p), k, u) for p, k, u in st["top_companies"]], ["Компания", "Просмотров", "Людей"]),
        table("Что ищут", [(link(p), k, u) for p, k, u in st["top_searches"]], ["Запрос", "Раз", "Людей"],
              "Поиском пока не пользовались."),
        table("С чего начинают визит", [(link(p), k) for p, k in st["entry_pages"]], ["Страница входа", "Визитов"]),
        table("Последние визиты: куда заходили", recent_rows, ["Начало (МСК)", "Путь по сайту"]),
        metrika or '<p class="empty">Метрика сейчас не отвечает — цифры выше считаются без неё.</p>')
    for name, val in zip(['ONLINE', 'PERIOD', 'TOKEN', 'GRID', 'BARS', 'ADV', 'SECT', 'SRC', 'DEALS', 'COMPS', 'SEARCH', 'ENTRY', 'RECENT', 'METRIKA'], vals):
        html = html.replace("@@" + name + "@@", str(val))
    return html
