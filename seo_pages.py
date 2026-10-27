# -*- coding: utf-8 -*-
"""Открытые страницы для поисковиков и ИИ-ассистентов (23 октября 2026).

ЗАЧЕМ. Сайт — одна страница, сделки открываются по адресам `#/deal/<id>`, а
база подгружается скриптом из закрытой для роботов папки. Поисковик видел
только главную: на вопрос «кто купил Дмитровский металлоцентр» ни Яндекс,
ни ассистенты сюда не вели. Владелец спросил, расскажу ли я о «Компасе», если
спросят про платформы со сделками, — и попросил открытые страницы сделок и
компаний, карту сайта и описание для ИИ.

ЧТО ОТКРЫТО. Решение владельца: карточка в объёме поста канала — заголовок,
стороны, дата, статус, отрасль, сумма, описание сторон и первоисточники —
вписана в HTML для поисковика. Человек этого текста не видит: адрес отдаёт
обычную страницу сайта, ранний скрипт в <head> переводит его в `/#/deal/<id>`,
и приложение рисует настоящую карточку (владелец 23 октября 2026 увидел
первую, голую версию страниц и сказал, что людям такое показывать нельзя). Защита базы от копирования (`docs/scraping_protection.md`) не
ослабла: собрать с этих страниц можно ровно то, что уже лежит в канале.

Адреса: `/deal/<id>`, `/company/<id>`, `/sitemap.xml`, `/llms.txt`.
Слитая карточка или профиль отвечает 301 на действующий адрес.
Витрина та же, что у сайта: сделки до `SITE_MIN_YEAR` не показываются
(`isDealShownOnSite` в `static/index.html`).
"""
from __future__ import annotations

import html
import re
import threading
from typing import Any

import base_data

SITE_MIN_YEAR = 2022          # тот же порог, что в static/index.html
_LOCK = threading.Lock()
_CACHE: dict[str, Any] = {"src": None}

_MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля",
           "августа", "сентября", "октября", "ноября", "декабря")
_DASH = {"", "—", "-", "–", "None", "null"}
# Агрегаторы читателю как источник не показываются (правило владельца
# 3 октября 2026); на этих страницах — тем более.
try:
    from pipeline.source_names import is_aggregator
except Exception:  # pragma: no cover — сайт не должен падать из-за конвейера
    def is_aggregator(url):
        return False


def esc(v: Any) -> str:
    return html.escape(str(v or ""), quote=True)


def _shown(deal: dict) -> bool:
    try:
        return int(str(deal.get("date") or "")[:4]) >= SITE_MIN_YEAR
    except ValueError:
        return True


def _index() -> dict[str, Any]:
    """Сделки витрины, профили и связи компания → сделки. Пересобирается,
    только когда `base_data` перечитал файл (подмена `data_refresh`)."""
    data = base_data.promoted()
    with _LOCK:
        if _CACHE["src"] is data:
            return _CACHE
        deals = [d for d in data.get("deals") or [] if isinstance(d, dict) and d.get("id") and _shown(d)]
        deals.sort(key=lambda d: str(d.get("date") or ""), reverse=True)
        companies = data.get("companies") or {}
        by_company: dict[str, list[dict]] = {}
        for d in deals:
            for cid in {d.get("buyer"), d.get("seller_id"), d.get("target"), d.get("asset_id")}:
                if cid and cid in companies:
                    by_company.setdefault(cid, []).append(d)
        _CACHE.update(src=data, deals={d["id"]: d for d in deals}, order=deals,
                      companies=companies, by_company=by_company,
                      merged=data.get("merged") or {}, merged_companies=data.get("merged_companies") or {})
        return _CACHE


def deal_count() -> int:
    """Число сделок для людей — без торгов (владелец, 27 октября 2026); тот же
    счет, что на первом экране сайта (COUNTED_DEALS)."""
    return sum(1 for d in _index()["order"] if d.get("type") != "Продажа с торгов")


def rounded_count() -> int:
    """«1700+»: вниз до сотни, чтобы описание не обещало больше, чем есть."""
    n = deal_count()
    return n - n % 100 if n >= 100 else n


def resolve_deal(deal_id: str) -> tuple[str, dict | None]:
    """('ok', карточка) | ('moved', новый id) | ('missing', None)."""
    idx = _index()
    if deal_id in idx["deals"]:
        return "ok", idx["deals"][deal_id]
    seen = set()
    cur = deal_id
    while cur in idx["merged"] and cur not in seen:
        seen.add(cur)
        cur = idx["merged"][cur]
    if cur != deal_id and cur in idx["deals"]:
        return "moved", cur
    return "missing", None


def resolve_company(company_id: str) -> tuple[str, Any]:
    idx = _index()
    if company_id in idx["by_company"]:
        return "ok", idx["companies"][company_id]
    target = idx["merged_companies"].get(company_id)
    if isinstance(target, dict):
        target = target.get("into") or target.get("id")
    if target and target in idx["by_company"]:
        return "moved", target
    return "missing", None


def _date_text(value: Any) -> str:
    s = str(value or "")
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return "%d %s %s" % (int(m.group(3)), _MONTHS[int(m.group(2)) - 1], m.group(1))
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        return "%s %s" % (("январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
                           "сентябрь", "октябрь", "ноябрь", "декабрь")[int(m.group(2)) - 1], m.group(1))
    return s[:4] if re.match(r"^\d{4}", s) else ""


def _company(cid: Any) -> dict | None:
    return _index()["companies"].get(cid) if cid else None


def _party(deal: dict, id_key: str, name_key: str | None = None) -> tuple[str, str, str]:
    """(название, описание, id профиля для ссылки или '')."""
    cid = deal.get(id_key)
    c = _company(cid)
    if c:
        linked = cid if cid in _index()["by_company"] else ""
        return str(c.get("name") or ""), str(c.get("desc") or ""), linked
    raw = deal.get(name_key) if name_key else None
    return (str(raw or "") if str(raw or "") not in _DASH else ""), "", ""


def _sum(deal: dict) -> str:
    for v in (deal.get("sum"), (deal.get("eco") or {}).get("sum")):
        if v is not None and str(v).strip() not in _DASH:
            return str(v).strip()
    return ""


def _sources(deal: dict) -> list[tuple[str, str]]:
    out = []
    for s in deal.get("src") or []:
        if isinstance(s, (list, tuple)) and len(s) > 1 and str(s[1]).startswith("http") and not is_aggregator(s[1]):
            out.append((str(s[0] or s[1]), str(s[1])))
    return out


INDEX_PATH = str(base_data.ROOT / "static" / "index.html")
_APP_MAIN = '<main class="wrap" id="app"></main>'


def _page(base: str, path: str, title: str, description: str, body: str, json_ld: str = "") -> str:
    """Та же страница сайта, что видит человек, — с заголовком, описанием и
    текстом сделки, вписанными в HTML. Человек видит обычную карточку: ранний
    скрипт в <head> переводит /deal/<id> в /#/deal/<id>, и приложение рисует
    её поверх вписанного текста. Поисковик без скрипта читает вписанный текст.
    Владелец 23 октября 2026: голые страницы людям показывать нельзя."""
    page = index_html(INDEX_PATH)
    sub = lambda pattern, repl: re.sub(pattern, lambda m: repl, page, count=1, flags=re.S)
    page = sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>")
    page = sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(description)}"')
    page = sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(title)}"')
    page = sub(r'<meta property="og:description" content="[^"]*"',
               f'<meta property="og:description" content="{esc(description)}"')
    head = (f'<link rel="canonical" href="{esc(base + path)}">\n'
            f'<meta property="og:url" content="{esc(base + path)}">\n{json_ld}\n</head>')
    page = page.replace("</head>", head, 1)
    return page.replace(_APP_MAIN, f'<main class="wrap" id="app"><article class="seo-snapshot">{body}</article></main>', 1)


def _ld(obj: dict) -> str:
    import json
    text = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>'


def deal_html(deal: dict, base: str) -> str:
    did = str(deal["id"])
    title = str(deal.get("title") or "Сделка")
    buyer, buyer_desc, buyer_id = _party(deal, "buyer")
    seller, seller_desc, seller_id = _party(deal, "seller_id", "seller")
    target, target_desc, target_id = _party(deal, "target", "asset")
    if not target:
        target, target_desc, target_id = _party(deal, "asset_id", "asset")
    status = str(deal.get("status") or "")
    when = _date_text(deal.get("date"))
    total = _sum(deal)
    ind = str(deal.get("ind") or "")

    def party_row(label, name, desc, cid):
        if not name:
            return ""
        shown = f'<a href="/company/{esc(cid)}">{esc(name)}</a>' if cid else esc(name)
        return f"<div><dt>{label}</dt><dd>{shown}{f'<small>{esc(desc)}</small>' if desc else ''}</dd></div>"

    rows = "".join([
        party_row("Покупатель", buyer, buyer_desc, buyer_id),
        party_row("Продавец", seller, seller_desc, seller_id),
        party_row("Предмет сделки", target, target_desc, target_id),
        f"<div><dt>Статус</dt><dd>{esc(status)}</dd></div>" if status else "",
        f"<div><dt>Дата</dt><dd>{esc(when)}</dd></div>" if when else "",
        f"<div><dt>Сумма</dt><dd>{esc(total)}</dd></div>" if total else "",
        f"<div><dt>Отрасль</dt><dd>{esc(ind)}</dd></div>" if ind else "",
    ])
    srcs = _sources(deal)
    src_html = ("<h2>Первоисточники</h2><ul>" + "".join(
        f'<li><a href="{esc(u)}" rel="nofollow noopener" target="_blank">{esc(n)}</a></li>' for n, u in srcs)
        + "</ul>") if srcs else ""
    parts = [p for p in (status, when, ind) if p]
    who = ", ".join(x for x in (("покупатель — " + buyer) if buyer else "",
                                 ("продавец — " + seller) if seller else "",
                                 ("сумма: " + total) if total else "") if x)
    desc_bits = [title, who[:1].upper() + who[1:] if who else "", ", ".join(parts)]
    description = ". ".join(x for x in desc_bits if x)[:300]
    body = (f'<h1>{esc(title)}</h1><p>{esc(" · ".join(parts))}</p>'
            f"<dl>{rows}</dl>"
            f"{src_html}")
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": title[:110],
          "inLanguage": "ru", "url": f"{base}/deal/{did}", "description": description,
          "publisher": {"@type": "Organization", "name": "Компас", "url": base + "/"}}
    if re.match(r"^\d{4}-\d{2}-\d{2}$", str(deal.get("date") or "")):
        ld["datePublished"] = deal["date"]
    return _page(base, f"/deal/{did}", f"{title} — Компас", description, body, _ld(ld))


def company_html(company_id: str, company: dict, base: str) -> str:
    idx = _index()
    name = str(company.get("name") or "Компания")
    desc = str(company.get("desc") or "")
    deals = idx["by_company"].get(company_id, [])
    role_of = lambda d: ("покупатель" if d.get("buyer") == company_id else
                         "продавец" if d.get("seller_id") == company_id else "предмет сделки")
    items = "".join(
        f'<li><a href="/deal/{esc(d["id"])}">{esc(d.get("title"))}</a>'
        f' <small>— {esc(_date_text(d.get("date")) or "дата не раскрыта")}, {role_of(d)}</small></li>'
        for d in deals)
    n = len(deals)
    word = "сделка" if n % 10 == 1 and n % 100 != 11 else ("сделки" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "сделок")
    description = (f"{name}: {n} {word} M&A в базе «Компаса»" + (f". {desc}" if desc else ""))[:300]
    ind = str(company.get("ind") or "")
    body = (f"<h1>{esc(name)}</h1>"
            f'<p>{esc(" · ".join(p for p in (ind, f"{n} {word} в базе") if p))}</p>'
            + (f"<p>{esc(desc)}</p>" if desc else "")
            + f"<h2>Сделки</h2><ul>{items}</ul>")
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": name,
          "url": f"{base}/company/{company_id}", "description": desc or description}
    return _page(base, f"/company/{company_id}", f"{name} — сделки M&A — Компас", description, body, _ld(ld))


def sitemap_xml(base: str) -> str:
    idx = _index()
    urls = [f"<url><loc>{esc(base)}/</loc><changefreq>hourly</changefreq></url>"]
    for d in idx["order"]:
        stamp = str(d.get("reviewed") or d.get("added") or d.get("date") or "")
        lastmod = f"<lastmod>{stamp}</lastmod>" if re.match(r"^\d{4}-\d{2}-\d{2}$", stamp) else ""
        urls.append(f"<url><loc>{esc(base)}/deal/{esc(d['id'])}</loc>{lastmod}</url>")
    for cid in sorted(idx["by_company"]):
        urls.append(f"<url><loc>{esc(base)}/company/{esc(cid)}</loc></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def llms_txt(base: str) -> str:
    idx = _index()
    latest = "\n".join(f"- [{d.get('title')}]({base}/deal/{d['id']})" for d in idx["order"][:15])
    return f"""# Компас

> «Компас» ({base}) — база сделок M&A российского рынка: {rounded_count()}+ сделок с 2022 года
> со ссылками на первоисточники, профили компаний, каталог юридических и финансовых
> консультантов, аналитика рынка. Каждая сделка описана с точки зрения экономиста
> (сумма, оценка, финансы сторон, логика сделки) и юриста (структура, одобрения,
> консультанты). Новые сделки появляются каждый день.

Для кого: юристы и банкиры, работающие на сделках, инвесторы, корпоративное развитие,
журналисты и аналитики, которым нужна проверяемая история сделок по российским
компаниям и отраслям.

Чем отличается: у каждого факта — ссылка на первоисточник (СМИ, раскрытие эмитента,
реестр юрлиц), стороны сделок привязываются к юрлицам по ИНН, статус сделки обновляется
по мере новостей (обсуждается → подписана → закрыта или не состоялась).

## Как ссылаться

- Сделка: {base}/deal/<id> — открытая страница: стороны, дата, статус, сумма, первоисточники.
- Компания: {base}/company/<id> — все сделки компании в базе.
- Полная карточка с разбором — в приложении: {base}/#/deal/<id>.
- Список всех страниц: {base}/sitemap.xml

## Последние сделки

{latest}
"""


def missing_html(base: str) -> str:
    return _page(base, "/", "Страница не найдена — Компас", "Такой страницы в «Компасе» нет.",
                 '<h1>Такой страницы нет</h1><p>Возможно, карточку объединили с другой или адрес '
                 'набран с ошибкой.</p><a href="/">На главную «Компаса»</a>')


_COUNT_IN_META = re.compile(r'(<meta (?:name="description"|property="og:description") content="[^"]*?)\d[\d ]*\+ сделок')
_INDEX: dict[str, Any] = {"key": None, "html": ""}


def index_html(path: str) -> str:
    """index.html с живым числом сделок в описании страницы. Кэш — по файлу
    страницы и по разбору базы: пересборка только при подмене одного из них."""
    import os
    st = os.stat(path)
    key = (st.st_mtime, st.st_size, id(_index()["src"]))
    if _INDEX["key"] != key:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        n = rounded_count()
        _INDEX.update(key=key, html=_COUNT_IN_META.sub(lambda m: f"{m.group(1)}{n}+ сделок", text))
    return _INDEX["html"]
