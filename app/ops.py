# -*- coding: utf-8 -*-
"""Служебное: /health с отпечатком сборки, дашборд основателей, посещаемость,
состояние данных, сводка притока в 18:00 (docs/server_layout.md)."""
import functools
import hashlib
import json
import logging
import mimetypes
import os
import pathlib
import random
import re
import threading
from collections import Counter
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from html import escape as html_escape

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

import assistant_policy
import assistant_product
import assistant_retrieval
import auth
import base_data
import company_finance
import data_refresh
import deal_catalog
import deal_multiples
import notification_service
import price_estimate
import context_analysis
import deal_analysis
import scrape_guard
import seo_pages
import telegram_endpoint
import subscription_feed
from company_catalog import get_company_profile, load_company_catalog
from deal_catalog import get_deal
from deal_export import render_companies_pdf, render_deal_pdf
from db.models import Base as DBBase
from db.models import (
    AppSetting,
    AssistantFeedback, AssistantMessage, AssistantThread, AuthSession, ClaudeMessage, Comment,
    CompanyClaim,
    CorrectionRequest,
    DealWatch, FinancialReport, FnsSyncRun, LegalEntity, LegalEntityMatchStatus,
    ModerationDecision, Notification,
    NotificationPreference, OwnershipSnapshot, OwnershipStake, PageView, RegistryEvent,
    SavedFilter, User, UserRole, UserTier, Webinar,
)
from db.session import engine, get_session
from fns_client import ApiFnsClient, ApiFnsError, change_text, full_lines_payload
from pipeline.fns_registry import by_company_id as fns_registry_by_company_id
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from yandex_search import SearchConfig, SearchError, SearchResult, build_search_block, yandex_search


from fastapi import APIRouter
from app import core, fns, assistant, accounts
from app.core import BASE_DIR, get_db, logger, _moderation_token_ok, _yandex_ready

router = APIRouter()


# HEAD, а не только GET: проверка живости у хостинга ходит методом HEAD, а
# FastAPI — в отличие от «голого» Starlette — сам HEAD к GET-маршруту НЕ
# добавляет. 6 сентября 2026 это уронило сайт на всю ночь: платформа стучалась
# «HEAD /», получала 405, считала приложение мертвым и перезапускала контейнер
# по кругу; живого процесса за прокси не было, и он даже не смог отдать
# сертификат — снаружи это выглядело как «сломался HTTPS», а не как 405.
# КАКОЙ КОД СЕЙЧАС НА САЙТЕ — ЭТО ДОЛЖЕН БЫТЬ ОДИН ЗАПРОС, А НЕ РАССЛЕДОВАНИЕ.
# 19 сентября 2026 выкладка встала: за день в git уехало восемь коммитов, а
# сайт продолжал отдавать сборку 18-го — в том числе без гейта, который
# перестает отвечать на «найди компромат на X». Чтобы это увидеть, пришлось
# сравнивать размер index.html, искать в нем признаки отдельных коммитов и
# в конце спрашивать сам ассистент. Теперь отпечаток отдает /health.
#
# Отпечаток считается ПО СОДЕРЖИМОМУ ФАЙЛОВ, а не по git: в развернутом
# контейнере каталога .git может не быть вовсе, а файлы есть всегда. Для
# сравнения «сайт и репозиторий совпадают» этого достаточно — рутине не
# нужно знать номер коммита, ей нужно знать, тот же это код или нет.
_BUILD_FILES = ("main.py", "static/index.html")


@functools.lru_cache(maxsize=1)
def build_fingerprint() -> dict:
    """Короткий отпечаток выложенного кода: по восемь знаков на файл."""
    out = {}
    for name in _BUILD_FILES:
        try:
            data = (pathlib.Path(BASE_DIR) / name).read_bytes()
            out[name] = hashlib.sha256(data).hexdigest()[:8]
        except OSError:
            out[name] = None
    return out


@router.api_route("/health", methods=["GET", "HEAD"])
def health():
    # МОДЕЛЬ НАЗВАНА ВСЛУХ. 22 сентября 2026 владелец спросил, не сменить ли
    # deepseek на другую модель, — а прод уже год мог работать на чем угодно:
    # `YANDEX_MODEL` задается переменной окружения хоста, и снаружи узнать ее
    # было нельзя. Догадка вместо факта стоит дороже строки в /health: это
    # идентификатор модели, а не секрет.
    return {"status": "ok", "ai": _yandex_ready(), "model": assistant.current_model(),
            "build": build_fingerprint()}


def _ops_numbers() -> dict:
    """Цифры для дашборда основателей — считаются из тех же файлов, что и сайт.

    Ни одной величины «на глаз»: каждая берется из данных, и рядом с ней в
    интерфейсе стоит подпись, ИЗ КАКОГО множества она получена (урок CLAUDE.md
    про то, что у числа на экране два свойства — величина и множество).
    """
    base = base_data.promoted()   # общий кэш, а не свой разбор 10 МБ на запрос
    deals = base.get("deals") or []
    pending = (core._read_json("static/data/pending.json", {}).get("cards") or [])

    def lens_len(card) -> int:
        eco, law = card.get("eco") or {}, card.get("law") or {}
        n = sum(len(str(v)) for v in list(eco.values())
                + [v for k, v in law.items() if k != "adv"] if v and str(v) != "—")
        n += sum(len(str(a)) for a in (law.get("adv") or []))
        return n + len(str(card.get("extra") or ""))

    # «Добавлено за неделю» обязано считать ПРИТОК, а не разовые импорты: в
    # день переноса архива приезжают сотни карточек, и число «211 за 7 дней»
    # выглядит бурным ростом рынка, хотя это мы сами залили старое. Правило
    # уже записано в CLAUDE.md по поводу метки «новое»: день, в который
    # добавлено больше 30 карточек, — это импорт, а не новости.
    today = datetime.now(timezone.utc).date()
    since = (today - timedelta(days=7)).isoformat()
    per_day: dict[str, int] = {}
    for d in deals:
        day = str(d.get("added") or "")
        if day:
            per_day[day] = per_day.get(day, 0) + 1
    week = [d for d in deals
            if str(d.get("added") or "") >= since
            and per_day.get(str(d.get("added") or ""), 0) <= 30]
    from_ingest = [d for d in deals if d.get("from_ingest")]
    unread = [d for d in from_ingest if not d.get("reviewed")]
    thin_2026 = [d for d in deals
                 if str(d.get("date") or "").startswith("2026") and lens_len(d) < 400]
    posts = base.get("telegram_posts") or {}
    realty_posts = base.get("telegram_posts_realty") or {}
    published = len({k for k, v in posts.items() if v} | {k for k, v in realty_posts.items() if v})

    return {
        "deals": len(deals),
        "companies": len(base.get("companies") or {}),
        "added_week": len(week),
        # «Скоро выйдет» — ТОЛЬКО прочитанные против источника: непрочитанная
        # карточка не публикуется по молчанию никогда (approve.py,
        # `plan_actions`), и раньше это число молча включало ее тоже —
        # владелец 18 августа поймал два таких «зависших» примера.
        "queue_soon": sum(1 for c in pending if not c.get("held") and c.get("reviewed") and c.get("accepted")
                         and c.get("draft_sent")),
        "queue_unread": sum(1 for c in pending if not c.get("held")
                            and not (c.get("reviewed") and c.get("accepted"))),
        "queue_held": sum(1 for c in pending if c.get("held")),
        "unread": len(unread),
        "from_ingest": len(from_ingest),
        "thin_2026": len(thin_2026),
        "published": published,
        "thin_examples": [str(d.get("title") or "")[:70] for d in thin_2026[:6]],
        "queue_titles": [str(c.get("title") or "")[:70] for c in pending[:6]],
        # ВСЯ очередь с id — чтобы каждую неопубликованную карточку можно было
        # открыть целиком, а не только увидеть заголовок в списке.
        "queue_cards": [{"id": str(c.get("id") or ""),
                         "title": str(c.get("title") or "без заголовка"),
                         "held": bool(c.get("held"))} for c in pending],
    }


OPS_PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Компас — панель основателей</title><style>
:root{--bg:#f7f3e9;--card:#fff;--ink:#201c14;--dim:#6b6353;--line:rgba(32,28,20,.14);--acc:#a9824c}
@media(prefers-color-scheme:dark){:root{--bg:#16181c;--card:#1d2025;--ink:#ece7d9;--dim:#a39c8b;--line:rgba(236,231,217,.12);--acc:#d3b17e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 16px 64px}
.w{max-width:900px;margin:0 auto}h1{font:600 24px/1.2 Georgia,serif;margin:0 0 4px}
.sub{color:var(--dim);font-size:14px;margin:0 0 24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}
.c{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.n{font:700 26px/1.1 Georgia,serif;font-variant-numeric:tabular-nums}
.l{font-size:12.5px;color:var(--dim);margin-top:4px}
.c.warn .n{color:var(--acc)}
h2{font:600 17px/1.3 Georgia,serif;margin:28px 0 10px}
ul{margin:0;padding-left:20px}li{font-size:14px;margin:4px 0}
.empty{color:var(--dim);font-size:14px}
.hint{color:var(--dim);font-size:13.5px;margin:-4px 0 12px;max-width:640px}
ol.prev{margin:0;padding-left:22px}ol.prev li{font-size:14.5px;margin:7px 0}
ol.prev a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--acc)}
ol.prev a:hover{color:var(--acc)}
ol.prev .tag{font-size:12px;color:var(--acc);margin-left:6px;white-space:nowrap}
</style></head><body><div class="w">
<h1>Компас — панель основателей</h1>
<p class="sub">Обновляется при каждом открытии. Все цифры считаются из тех же файлов, что отдает сайт.</p>
<div class="grid">
<div class="c"><div class="n">%(deals)d</div><div class="l">сделок на сайте</div></div>
<div class="c"><div class="n">%(companies)d</div><div class="l">профилей компаний</div></div>
<div class="c"><div class="n">%(added_week)d</div><div class="l">добавлено за 7 дней</div></div>
<div class="c"><div class="n">%(published)d</div><div class="l">постов в канале</div></div>
</div>
<h2>Ждет вашего решения</h2>
<div class="grid">
<div class="c"><div class="n">%(queue_soon)d</div><div class="l">выйдут сами в течение суток</div></div>
<div class="c"><div class="n">%(queue_unread)d</div><div class="l">ждут прочтения или приемки — сами не выйдут</div></div>
<div class="c"><div class="n">%(queue_held)d</div><div class="l">вы придержали</div></div>
</div>
%(queue_list)s
<h2>Все карточки, которые еще не опубликованы</h2>
<p class="hint">Их видно только здесь и в боте: на сайте они появятся после публикации.
Нажмите заголовок, чтобы открыть карточку целиком — ровно в том виде, в каком она выйдет.</p>
%(preview_list)s
<h2>Что еще не доделано</h2>
<div class="grid">
<div class="c warn"><div class="n">%(unread)d</div><div class="l">из %(from_ingest)d карточек притока не дополнены по источнику</div></div>
<div class="c warn"><div class="n">%(thin_2026)d</div><div class="l">карточек 2026 года с почти пустыми разборами</div></div>
</div>
%(thin_list)s
</div></body></html>"""


@router.get("/ops")
def ops_dashboard(token: str = ""):
    """Панель основателей: то же, что рутина шлет в Telegram, но целиком и
    сразу. Закрыта тем же токеном, что и мост решений, — состав очереди и
    незаконченная работа не для публичного показа."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    n = _ops_numbers()

    def as_list(items, empty_text):
        if not items:
            return '<p class="empty">%s</p>' % empty_text
        return "<ul>%s</ul>" % "".join(
            "<li>%s</li>" % html_escape(t) for t in items)

    def preview_items(cards):
        if not cards:
            return '<p class="empty">Сейчас в очереди пусто — все опубликовано или выкинуто.</p>'
        rows = []
        for c in cards:
            tag = ' <span class="tag">придержана</span>' if c["held"] else ""
            rows.append('<li><a href="/#/preview/%s">%s</a>%s</li>'
                        % (html_escape(c["id"]), html_escape(c["title"]), tag))
        return '<ol class="prev">%s</ol>' % "".join(rows)

    page = OPS_PAGE % {
        **{k: v for k, v in n.items() if isinstance(v, int)},
        "queue_list": as_list(n["queue_titles"], "Очередь пуста — все решено."),
        "thin_list": as_list(n["thin_examples"],
                             "Тонких карточек 2026 года не осталось."),
        "preview_list": preview_items(n["queue_cards"]),
    }
    return HTMLResponse(page)


@router.get("/api/ops/summary")
def ops_summary(token: str = ""):
    """Те же цифры машиночитаемо — чтобы рутина могла отчитаться, не считая
    их заново каждая по-своему."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return _ops_numbers()


def _activity_numbers(db) -> dict:
    """Посещаемость без Яндекса — из нашей же базы (14 октября 2026: Метрика
    перестала отвечать, владелец: «можешь посмотреть метрики сайта без
    Яндекса?»). Просмотров страниц сайт не пишет — их видит только Метрика;
    здесь то, что делают люди с аккаунтом: регистрации, входы, вопросы
    ассистенту, подписки, правки. Анонимного читателя эти цифры не видят."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)   # колонки — наивное UTC

    def since(days):
        return now - timedelta(days=days)

    def count(col, days=None, where=()):
        q = select(func.count()).select_from(col.class_)
        for w in where:
            q = q.where(w)
        if days is not None:
            q = q.where(col >= since(days))
        return int(db.scalar(q) or 0)

    def distinct(col_user, col_time, days, where=()):
        q = select(func.count(func.distinct(col_user))).where(col_time >= since(days))
        for w in where:
            q = q.where(w)
        return int(db.scalar(q) or 0)

    asked = (AssistantMessage.role == "user",)
    out = {"users": count(User.created_at)}
    for d in (1, 7, 30):
        out["new_users_%dd" % d] = count(User.created_at, d)
        out["logins_%dd" % d] = count(AuthSession.created_at, d)
        out["active_users_%dd" % d] = distinct(AuthSession.user_id, AuthSession.created_at, d)
        out["questions_%dd" % d] = count(AssistantMessage.created_at, d, asked)
        out["askers_%dd" % d] = int(db.scalar(
            select(func.count(func.distinct(AssistantThread.user_id)))
            .select_from(AssistantMessage).join(AssistantThread, AssistantMessage.thread_id == AssistantThread.id)
            .where(AssistantMessage.role == "user", AssistantMessage.created_at >= since(d))) or 0)
    out["watches"] = count(DealWatch.created_at, where=(DealWatch.active.is_(True),))
    out["saved_filters"] = count(SavedFilter.created_at, where=(SavedFilter.active.is_(True),))
    out["telegram_linked"] = int(db.scalar(select(func.count()).select_from(NotificationPreference)
                                           .where(NotificationPreference.telegram_chat_id.is_not(None))) or 0)
    out["corrections_7d"] = count(CorrectionRequest.created_at, 7)
    out["feedback_7d"] = count(AssistantFeedback.created_at, 7)
    # По дням за две недели: новые аккаунты, входы, вопросы ассистенту.
    days = []
    for back in range(13, -1, -1):
        start = (now - timedelta(days=back)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        def between(col, where=()):
            q = select(func.count()).select_from(col.class_).where(col >= start, col < end)
            for w in where:
                q = q.where(w)
            return int(db.scalar(q) or 0)
        days.append({"day": start.date().isoformat(), "new_users": between(User.created_at),
                     "logins": between(AuthSession.created_at),
                     "questions": between(AssistantMessage.created_at, asked)})
    out["by_day"] = days
    return out


@router.get("/api/ops/activity")
def ops_activity(token: str = "", db=Depends(get_db)):
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return _activity_numbers(db)


@router.get("/ops/activity")
def ops_activity_page(token: str = "", db=Depends(get_db)):
    """Та же активность страницей — для владельца, когда Метрика молчит."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    a = _activity_numbers(db)
    cards = [("Аккаунтов всего", a["users"]), ("Новых за сутки", a["new_users_1d"]),
             ("Новых за 7 дней", a["new_users_7d"]), ("Новых за 30 дней", a["new_users_30d"]),
             ("Заходили за сутки", a["active_users_1d"]), ("Заходили за 7 дней", a["active_users_7d"]),
             ("Заходили за 30 дней", a["active_users_30d"]),
             ("Вопросов ассистенту за сутки", a["questions_1d"]), ("Вопросов за 7 дней", a["questions_7d"]),
             ("Спрашивали за 7 дней, человек", a["askers_7d"]),
             ("Следят за сделками", a["watches"]), ("Подписок на компании и отрасли", a["saved_filters"]),
             ("Привязали Telegram", a["telegram_linked"]), ("Правок от читателей за 7 дней", a["corrections_7d"])]
    grid = "".join('<div class="c"><div class="n">%d</div><div class="l">%s</div></div>' % (v, html_escape(k)) for k, v in cards)
    rows = "".join("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>"
                   % (html_escape(d["day"]), d["new_users"], d["logins"], d["questions"]) for d in reversed(a["by_day"]))
    page = ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Компас — активность</title><style>body{margin:0;background:#f7f3e9;color:#201c14;font:16px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 16px 64px}'
            '.w{max-width:900px;margin:0 auto}h1{font:600 24px/1.2 Georgia,serif;margin:0 0 4px}.sub{color:#6b6353;font-size:14px;margin:0 0 20px;max-width:640px}'
            '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}'
            '.c{background:#fff;border:1px solid rgba(32,28,20,.14);border-radius:10px;padding:14px 16px}.n{font:700 26px/1.1 Georgia,serif}.l{font-size:12.5px;color:#6b6353;margin-top:4px}'
            'table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}td,th{border-bottom:1px solid rgba(32,28,20,.1);padding:7px 10px;text-align:right}td:first-child,th:first-child{text-align:left}</style></head>'
            '<body><div class="w"><h1>Активность на сайте</h1>'
            '<p class="sub">Из нашей базы, без Яндекс Метрики. Видны только люди с аккаунтом: регистрации, входы, вопросы ассистенту, подписки. '
            'Читателей без входа и просмотры страниц считает только Метрика.</p>'
            '<div class="grid">' + grid + '</div><h2 style="font:600 17px Georgia,serif">По дням (время UTC)</h2>'
            '<table><tr><th>День</th><th>Новые аккаунты</th><th>Входы</th><th>Вопросы ассистенту</th></tr>' + rows + '</table></div></body></html>')
    return HTMLResponse(page)


# ---------------------------------------------------------- посещаемость ----
# Свой счетчик (traffic.py): страница шлет «открыли экран», здесь прием и вид.
class TrackIn(BaseModel):
    path: str = "/"
    v: str = ""          # случайный номер браузера
    s: str = ""          # номер визита
    ref: str = ""        # откуда пришли — только на первом экране визита
    w: int = 0           # ширина экрана — телефон или компьютер
    auth: bool = False   # вошел ли человек


_TRACK_ID = re.compile(r"^[A-Za-z0-9]{8,32}$")


@router.post("/api/t")
def track_view(payload: TrackIn, request: Request, db=Depends(get_db)):
    import traffic
    if traffic.is_bot(request.headers.get("user-agent", "")):
        return Response(status_code=204)
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
    if traffic.too_fast(ip or "?"):
        return Response(status_code=204)
    if not (_TRACK_ID.match(payload.v or "") and _TRACK_ID.match(payload.s or "")):
        return Response(status_code=204)
    norm = traffic.normalize(payload.path)
    if not norm:
        return Response(status_code=204)
    own = (request.headers.get("host") or "").split(":")[0].lower()
    own = own[4:] if own.startswith("www.") else own
    db.add(PageView(visitor=payload.v, session=payload.s, path=norm[0], section=norm[1],
                    ref_host=traffic.ref_host(payload.ref, own), device=traffic.device_of(payload.w),
                    logged_in=bool(payload.auth)))
    if random.random() < 0.002:
        db.query(PageView).filter(PageView.created_at < traffic._now() - timedelta(days=traffic.KEEP_DAYS)) \
            .delete(synchronize_session=False)
    db.commit()
    return Response(status_code=204)


def _traffic_stats(db, days: int = 7) -> dict:
    import traffic
    return traffic.stats(db, PageView, days=max(1, min(int(days or 7), 90)), base=base_data.promoted() or {})


def _metrika_lines() -> list[str]:
    try:
        import metrika
        return metrika.render(metrika.day_stats("today"))
    except Exception as exc:                                 # noqa: BLE001
        logger.error("Яндекс Метрика не ответила: %s", exc)
        return ["📈 Яндекс Метрика сейчас не ответила."]


@router.get("/api/ops/traffic")
def ops_traffic(token: str = "", days: int = 7, db=Depends(get_db)):
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return _traffic_stats(db, days)


@router.get("/ops/traffic")
def ops_traffic_page(token: str = "", days: int = 7, metrika: int = 1, db=Depends(get_db)):
    """Посещаемость для владельца: наш счетчик и, если отвечает, Метрика."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    import traffic
    lines = _metrika_lines() if metrika else None
    lines = [re.sub(r"</?b>", "", x) for x in lines] if lines else lines
    return HTMLResponse(traffic.page_html(_traffic_stats(db, days), token, lines))


@router.post("/api/ops/traffic-report")
def ops_traffic_report(token: str = "", db=Depends(get_db)):
    """Отчет о посещаемости в консоль сейчас: Метрика (если отвечает) и наш
    счетчик за сутки, со ссылкой на страницу посещаемости."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    import traffic
    lines = _metrika_lines() + [""] + traffic.console_lines(_traffic_stats(db, 1))
    text = "\n".join(lines)
    chats = core._review_chat_ids(db)
    thread = core._console_thread_id(db, "update")
    sent = 0
    for chat in chats:
        res = notification_service.tg_api("sendMessage", chat_id=chat, text=text, parse_mode="HTML",
                                          disable_web_page_preview=True,
                                          **({"message_thread_id": thread} if thread else {}))
        if res and res.get("ok"):
            sent += 1
    return {"sent": sent, "text": text}


@router.get("/api/data/status")
def data_status(token: str = ""):
    """Как идет подтягивание свежих данных с GitHub (data_refresh.py).

    Нужен, чтобы «работает» и «молча не работает» различались снаружи: сеть до
    raw.githubusercontent.com из России бывает закрыта, и сайт в этом случае
    честно живет на файле, приехавшем деплоем, — но узнать об этом иначе как
    из лога одноразового контейнера было бы негде. Закрыт тем же токеном, что
    и мост решений: состав очереди и внутренняя механика не для публики."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    out = data_refresh.status()
    if isinstance(out, dict):
        out = dict(out, scrape_guard=scrape_guard.stats())
    return out


INTAKE_SUMMARY = os.environ.get("INTAKE_SUMMARY", "1") != "0"
INTAKE_SUMMARY_HOUR_MSK = 18
INTAKE_RUNS_SETTING = "intake_runs"
INTAKE_SUMMARY_LAST = "intake_summary_last_at"
_MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
               "сентября", "октября", "ноября", "декабря"]


class IntakeRunIn(BaseModel):
    token: str = ""
    looked: int = 0
    found: int = 0
    cards: int = 0
    screened: int = 0


def _load_intake_runs(db) -> list[dict]:
    row = db.get(AppSetting, INTAKE_RUNS_SETTING)
    try:
        return json.loads(row.value) if row and row.value else []
    except ValueError:
        return []


@router.post("/api/ops/intake-run")
def ops_intake_run(req: IntakeRunIn, db=Depends(get_db)):
    """Цифры одного прогона притока — копятся до вечерней сводки."""
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    runs = _load_intake_runs(db)
    runs.append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "looked": max(0, req.looked), "found": max(0, req.found),
                 "cards": max(0, req.cards), "screened": max(0, req.screened)})
    runs = runs[-400:]
    row = db.get(AppSetting, INTAKE_RUNS_SETTING)
    if row:
        row.value = json.dumps(runs, ensure_ascii=False)
    else:
        db.add(AppSetting(key=INTAKE_RUNS_SETTING, value=json.dumps(runs, ensure_ascii=False)))
    db.commit()
    return {"ok": True, "runs_today": len(runs)}


def _plural_ru(n: int, one: str, few: str, many: str) -> str:
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def _intake_summary_text(runs: list[dict], msk_day, metrika_lines: list[str]) -> str:
    """Текст сводки дня — словами, без устройства рутин."""
    lines = ["🌅 <b>Компас · день, %d %s</b>" % (msk_day.day, _MONTHS_GEN[msk_day.month - 1]), ""]
    if not runs:
        lines.append("⚠️ Приток сегодня ни разу не отчитался — возможно, рутина не работает. Проверим.")
    else:
        looked = sorted(r.get("looked", 0) for r in runs)
        typical = looked[len(looked) // 2]
        found = sum(r.get("found", 0) for r in runs)
        cards = sum(r.get("cards", 0) for r in runs)
        screened = sum(r.get("screened", 0) for r in runs)
        lines.append("Приток проверил ленты источников %d %s%s." % (
            len(runs), _plural_ru(len(runs), "раз", "раза", "раз"),
            (" — каждый раз около %s %s" % (f"{typical:,}".replace(",", " "),
                                             _plural_ru(typical, "новости", "новостей", "новостей"))) if typical else ""))
        lines.append("Отсеяли как явный мусор еще до консоли — %d. Похожих на сделки — %d." % (screened, found))
        if cards:
            lines.append("📋 <b>На вашу проверку ушло %d %s</b> — они в этой группе, с кнопками."
                         % (cards, _plural_ru(cards, "карточка", "карточки", "карточек")))
        else:
            lines.append("Новых сделок за день нет — бывают тихие дни.")
    lines.append("")
    lines.extend(metrika_lines)
    return "\n".join(lines)


def _intake_summary_once(db, now_utc: datetime | None = None, force: bool = False) -> bool:
    """Отправить сводку дня, если пора и сегодня ее еще не было (или `force`).
    Ключ дня пишется ДО отправки: перезапуск сайта в 18:05 не повторит ее."""
    now_utc = now_utc or datetime.now(timezone.utc)
    msk = now_utc.astimezone(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)
    if not force and msk.hour < INTAKE_SUMMARY_HOUR_MSK:
        return False
    key = "intake_summary:%s" % msk.date().isoformat()
    if not force:
        if db.get(AppSetting, key):
            return False
        db.add(AppSetting(key=key, value=now_utc.isoformat(timespec="seconds")))
        try:
            db.commit()
        except Exception:                                    # noqa: BLE001
            db.rollback()
            return False
    elif msk.hour >= INTAKE_SUMMARY_HOUR_MSK and not db.get(AppSetting, key):
        # Сводка по просьбе после 18:00 и есть сводка этого дня: вечерняя
        # вторым сообщением в тот же день не повторяется.
        db.add(AppSetting(key=key, value=now_utc.isoformat(timespec="seconds")))
        db.commit()
    last_row = db.get(AppSetting, INTAKE_SUMMARY_LAST)
    since = last_row.value if last_row and last_row.value else (now_utc - timedelta(hours=24)).isoformat(timespec="seconds")
    runs = [r for r in _load_intake_runs(db) if str(r.get("at", "")) > since]
    try:
        import metrika
        stats = metrika.day_stats("today")
        metrika_lines = metrika.render(stats)
    except Exception as exc:                                 # noqa: BLE001
        logger.error("Яндекс Метрика не ответила: %s", exc)
        metrika_lines = ["📈 Яндекс Метрика сегодня не ответила — посещаемость пришлем в следующей сводке."]
    try:
        import traffic
        metrika_lines = metrika_lines + [""] + traffic.console_lines(_traffic_stats(db, 1))
    except Exception as exc:                                 # noqa: BLE001
        logger.error("свой счетчик посещений не посчитался: %s", exc)
    text = _intake_summary_text(runs, msk.date(), metrika_lines)
    chats = core._review_chat_ids(db)
    thread = core._console_thread_id(db, "update")
    sent = 0
    for chat in chats:
        res = notification_service.tg_api("sendMessage", chat_id=chat, text=text, parse_mode="HTML",
                                          disable_web_page_preview=True,
                                          **({"message_thread_id": thread} if thread else {}))
        if res and res.get("ok"):
            sent += 1
    if sent:
        if last_row:
            last_row.value = now_utc.isoformat(timespec="seconds")
        else:
            db.add(AppSetting(key=INTAKE_SUMMARY_LAST, value=now_utc.isoformat(timespec="seconds")))
        db.commit()
    return bool(sent)


@router.post("/api/ops/intake-summary")
def ops_intake_summary(token: str = "", db=Depends(get_db)):
    """Отправить сводку дня прямо сейчас (по просьбе владельца, не дожидаясь 18:00)."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return {"sent": _intake_summary_once(db, force=True)}


def _start_intake_summary():
    if not INTAKE_SUMMARY or os.environ.get("PYTEST_CURRENT_TEST"):
        return
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return

    def _run():
        while True:
            time.sleep(300)
            db = get_session()
            try:
                if _intake_summary_once(db):
                    logger.info("сводка дня отправлена в консоль")
            except Exception as exc:                             # noqa: BLE001
                logger.error("сводка дня не отправлена: %s", exc)
            finally:
                db.close()

    threading.Thread(target=_run, daemon=True).start()


# ЭТАП СДЕЛКИ — В КАНАЛ СРАЗУ ПО КНОПКЕ (5 октября 2026). UniCredit: конкурент
# написал о разрешении президента в 19:30, мы — в 20:07. Владелец нажал «пост в
# канал» раньше, но кнопка только записывала решение, а публиковала рутина
# публикации — раз в час, в :05. Теперь приток, отправляя черновик этапа в
# консоль, кладет сюда же готовый текст поста и кнопки
# (`send_milestone_drafts.store_on_site`), и по «пост в канал» сайт публикует
# его в основной канал сразу. Номер поста пишется в само решение
# (`edited_text` = {"posted_message_id": …}): рутина публикации, увидев его,
# только отмечает этап вышедшим (`send_telegram.site_posted_milestones`) и
# второй раз не шлет. Пост в канал недвижимости и любой сбой — по-старому,
# рутиной: потерять скорость лучше, чем выпустить пост не туда или дважды.
