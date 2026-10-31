"""КОМПАС — MVP платформы о сделках и компаниях.

Статика + /api/ask с двумя режимами:
- mode="base" — ответ строго по базе платформы;
- mode="web"  — перед вызовом модели выполняется поиск Яндекса
  (yandex_search.py), выдача подкладывается в промпт. Если поиск
  упал или пуст — тихая деградация в режим base (с логом, без
  ошибки для пользователя).

LLM: DeepSeek 4 Flash через Yandex AI Studio Responses API.
Требуются YANDEX_API_KEY и YANDEX_FOLDER_ID; без них фронтенд
работает в демо-режиме (fallback=true).
"""
import functools
from contextlib import asynccontextmanager
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


from app import core, fns, assistant, accounts, ops, console
from app import reexport as _reexport
from app.core import BASE_DIR, STATIC_DIR, logger, get_db, _current_user, _plain, _moderation_token_ok, _yandex_ready, _is_reviewer, SITE_URL, _MD_LINK_RE, COOKIE_SECURE, CONSOLE_TOPIC_NAMES, CONSOLE_TOPIC_FALLBACK, _topic_slug, CHANNEL_SETTING, REALTY_CHANNEL_SETTING, REVIEW_GROUP_SETTING, _channel_chat_ids, _chat_is_channel  # noqa: F401


@asynccontextmanager
async def lifespan(_app):
    """Один порядок старта вместо восьми `on_event("startup")`: таблицы
    аккаунтов, сверка подписок, сводка за неделю, подтягивание данных,
    докачка ФНС, индекс ассистента, опрос Telegram, сводка притока. Все
    долгое — в своих потоках; остановка процессу не нужна (потоки daemon)."""
    accounts._create_account_tables()
    accounts._match_subscriptions_against_new_deals()
    accounts._start_weekly_digest()
    _start_data_refresh()
    fns._sync_fns_from_registry()
    assistant._warm_assistant_index()
    console._start_telegram_polling()
    ops._start_intake_summary()
    yield


app = FastAPI(title="КОМПАС", lifespan=lifespan)

# Роутеры — в порядке областей; ловилка всех адресов (site) подключается последней.
for _r in (fns.router, assistant.router, accounts.router, ops.router, console.router,):
    app.include_router(_r)

# Сжатие ответов. База сделок — 4,6 МБ текста, и до этого она уезжала в браузер
# как есть: 4695 КБ по сети на каждый первый заход. JSON сжимается в шесть раз,
# так что это самая дешевая правка из возможных — одна строка вместо дробления
# файла на части и переписывания загрузчика.
# minimum_size: мелочь сжимать дороже, чем отдать как есть.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Шрифт фирменной карточки каталога (static/fonts/*.woff2): на хостинге
# Python не знал этого расширения и отдавал шрифт как text/plain (6 октября
# 2026) — браузеры терпят, но тип должен быть честным.
mimetypes.add_type("font/woff2", ".woff2")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/robots.txt", include_in_schema=False)
def robots_txt():
    """Данные и API — не для роботов. База отдается сайтом одним файлом
    (`/static/data/deals_promoted.json`); файл robots.txt — первое, что
    посмотрит добросовестный сборщик, и единственное, что увидит
    индексатор. Юридическая опора — раздел «Права на базу данных»
    пользовательского соглашения (см. LEGAL_DOCS в static/index.html)."""
    body = ("User-agent: *\n"
            "Disallow: /static/data/\n"
            "Disallow: /api/\n"
            "Disallow: /api/data/\n"
            "Allow: /\n"
            "\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")
    return Response(body, media_type="text/plain; charset=utf-8")


# --------------------------------------------------------------------------
# Защита базы от легкого скачивания (16 октября 2026, scrape_guard.py,
# docs/scraping_protection.md). Выключатель — SCRAPE_GUARD=0.
# --------------------------------------------------------------------------
# www.projectcompass.ru отдавал ту же копию сайта со статусом 200 — для
# поисковика это два одинаковых сайта, и вес в выдаче делится (23 октября 2026,
# подключение Яндекс Вебмастера). Постоянный редирект на основной адрес.
@app.middleware("http")
async def www_to_apex_middleware(request: Request, call_next):
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host.startswith("www."):
        target = f"https://{host[4:]}{request.url.path}"
        if request.url.query:
            target += "?" + request.url.query
        return RedirectResponse(target, status_code=301)
    return await call_next(request)


@app.middleware("http")
async def scrape_guard_middleware(request: Request, call_next):
    if not scrape_guard.enabled():
        return await call_next(request)
    path = request.url.path
    # Старый публичный адрес базы закрыт снаружи. Сервер, тесты и скрипты
    # pipeline читают файл С ДИСКА — их это не касается. Служебный ключ
    # пускает и сюда: рутины со старым кодом не должны ослепнуть.
    if path == scrape_guard.STATIC_DATA_PATH and not scrape_guard.service_key_ok(
            request.headers, request.query_params.get("token", "")):
        scrape_guard.bump("static_path_closed")
        return JSONResponse({"error": "not found"}, status_code=404)
    group = scrape_guard.group_of(path, request.method)
    if group and not scrape_guard.service_key_ok(request.headers, request.query_params.get("token", "")):
        ip = scrape_guard.client_ip(request.headers, request.client.host if request.client else None)
        if ip:
            wait = scrape_guard.too_many(group[0], group[1], ip)
            if wait:
                scrape_guard.bump("rate_" + group[0])
                logger.warning("частые запросы: группа %s, адрес %s", group[0], ip)
                return JSONResponse({"error": "Слишком много запросов подряд. Попробуйте через несколько минут."},
                                    status_code=429, headers={"Retry-After": str(int(wait))})
    return await call_next(request)


def _data_access_denied(request: Request) -> JSONResponse | None:
    """Общие проверки для базы и для выдачи токена: робот, чужой сайт."""
    if scrape_guard.is_robot(request.headers.get("user-agent", "")):
        scrape_guard.bump("robot")
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if scrape_guard.foreign_origin(request.headers, request.headers.get("host", "")):
        scrape_guard.bump("foreign_origin")
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return None


@app.api_route("/api/data/session", methods=["GET", "POST"], include_in_schema=False)
def data_session(request: Request):
    """Новый токен для базы — страница зовет это, если ее токен истек
    (вкладка открыта дольше срока, index.html пришел из кэша браузера)."""
    resp = Response(status_code=204)
    if scrape_guard.enabled():
        denied = _data_access_denied(request)
        if denied:
            return denied
        scrape_guard.issue_cookie(resp, request)
    return resp


@app.get(scrape_guard.DATA_PATH, include_in_schema=False)
def data_base_file(request: Request, token: str = ""):
    """База сделок для страницы. Раньше — публичный /static/data/deals_promoted.json."""
    path = os.path.join(STATIC_DIR, "data", "deals_promoted.json")
    if scrape_guard.enabled() and not scrape_guard.service_key_ok(request.headers, token):
        denied = _data_access_denied(request)
        if denied:
            return denied
        ip = scrape_guard.client_ip(request.headers, request.client.host if request.client else None)
        if not scrape_guard.check_token(request.cookies.get(scrape_guard.COOKIE_NAME, ""),
                                        request.headers.get("user-agent", ""), ip):
            scrape_guard.bump("no_token")
            return JSONResponse({"error": "token required"}, status_code=401)
    try:
        st = os.stat(path)
    except OSError:
        return JSONResponse({"error": "not found"}, status_code=404)
    etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
    headers = {"Cache-Control": "private, no-cache", "ETag": etag, "X-Robots-Tag": "noindex"}
    if etag in (request.headers.get("if-none-match") or ""):
        return Response(status_code=304, headers=headers)
    scrape_guard.bump("served")
    return FileResponse(path, media_type="application/json", headers=headers)

# Таблицы аккаунтов (db/models.py) — заготовка лежала не подключенной с 22
# июля, main.py по-прежнему читает static/data/*.json напрямую для сделок и
# компаний. create_all создает только НЕДОСТАЮЩИЕ таблицы и никогда не трогает
# существующие данные — безопасно и на пустой sqlite для разработки, и на
# уже заполненном Postgres на Timeweb.
# Свежая база без пересборки: рутины коммитят данные 4–5 раз в час, и каждый
# такой пуш до 3 сентября 2026 перезапускал сайт (три пуша за минуту дали 502
# на девять минут). Почему так и что качается — docstring data_refresh.py.
def _start_data_refresh():
    data_refresh.ON_CHANGE.append(console._console_after_refresh)
    data_refresh.start()


# ВРЕМЕННО, по прямой просьбе владельца 3 сентября 2026: «разрешить
# авторизованным пользователям скачивать PDF без платной подписки, пока ее
# нет». Карточку сделки в PDF (export_deal) может скачать любой вошедший;
# гостю — по-прежнему 401 (вход нужен, чтобы выгрузка не была анонимной).
# Когда подписка появится — поставить False, и скачивание снова станет
# только для тарифа paid, без другой правки кода и интерфейса.
DEAL_EXPORT_ALL_FREE = True

# 5 сентября 2026, владелец: «разрешим пдф скачивать всем, даже тем, кто не
# платил». Вход для карточки в PDF больше не нужен: гость получает файл так
# же, как вошедший (текст PDF собирается из нашей же базы, ничьих секретов в
# нем нет). Живая отчетность ФНС (bo_file) под это не попадает — каждый ее
# клик тратит платную квоту API-ФНС. Когда появится подписка — поставить
# False, и гостю снова вернется 401 без правки интерфейса (там ветка есть).
DEAL_EXPORT_GUESTS = True

class DealExportIn(BaseModel):
    # Поле оставлено для обратной совместимости с будущим редактором, но сервер
    # формирует PDF из своей базы и не доверяет присланному HTML/тексту.
    title: str | None = None


# ==================== Вебинары ====================

@app.get("/api/webinars")
def list_webinars(db=Depends(get_db)):
    rows = list(db.scalars(select(Webinar).where(Webinar.published.is_(True))
                           .order_by(Webinar.starts_at.desc(), Webinar.id.desc())).all())
    return [{
        "id": row.id, "title": row.title, "summary": row.summary,
        "starts_at": row.starts_at.isoformat() if row.starts_at else None,
        "speaker": row.speaker, "registration_url": row.registration_url,
        "recording_url": row.recording_url, "status": row.status,
    } for row in rows]


# ==================== Экспорт сделки ====================

def _export_finance(deal: dict, db) -> list[dict]:
    """Финансовый контекст сделки для PDF — то же, что блок на карточке.

    Просьба Ксюши (19 сентября 2026): в выгрузке этого раздела не было вовсе,
    а на карточке он есть. Отчет уходит из рук в руки, и «за сколько купили»
    без «сколько эта компания зарабатывает» — половина разговора.

    Берем показатели ЗА ПОСЛЕДНИЙ ГОД ДО СДЕЛКИ (как и на экране): показывать
    в отчете о сделке 2023 года отчетность за 2025-й значило бы отвечать не на
    тот вопрос. Юрлицо и год называются прямо — отчетность сдается по юрлицу,
    а сделка заключается по группе, и подменять одно другим нельзя.
    """
    year_cap = None
    date = str(deal.get("date") or "")
    if len(date) >= 4 and date[:4].isdigit():
        year_cap = int(date[:4])
    rows: list[dict] = []
    for key, role in (("target", "Покупаемая компания"), ("buyer", "Покупатель")):
        company_id = deal.get(key)
        if not company_id:
            continue
        entity = db.scalar(select(LegalEntity).where(
            LegalEntity.company_id == company_id,
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
        ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id))
        if not entity:
            continue
        query = select(FinancialReport).where(FinancialReport.legal_entity_id == entity.id)
        if year_cap:
            query = query.where(FinancialReport.year <= year_cap)
        report = db.scalar(query.order_by(FinancialReport.year.desc()))
        if not report:
            continue
        profile = get_company_profile(company_id) or {}
        rows.append({
            "role": role,
            # Имя из профиля базы, а не из ЕГРЮЛ: «ПУБЛИЧНОЕ АКЦИОНЕРНОЕ
            # ОБЩЕСТВО "ВЫМПЕЛ-КОММУНИКАЦИИ"» капсом — нарушение правила
            # «язык для людей», уже разобранное для экрана мультипликаторов.
            "name": profile.get("name") or entity.short_name or entity.legal_name,
            "legal_name": entity.legal_name,
            "inn": entity.inn,
            "year": report.year,
            "revenue_rub": _plain(report.revenue_rub),
            "net_profit_rub": _plain(report.net_profit_rub),
            "assets_rub": _plain(report.assets_rub),
            "equity_rub": _plain(report.equity_rub),
        })
    return rows


@app.post("/api/deals/{deal_id}/export")
def export_deal(deal_id: str, _payload: DealExportIn | None = None,
                user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user and not DEAL_EXPORT_GUESTS:
        return JSONResponse({"error": "войдите, чтобы скачать карточку"}, status_code=401)
    if user and not DEAL_EXPORT_ALL_FREE and user.tier != UserTier.paid:
        return JSONResponse({"error": "скачивание карточек доступно по подписке"}, status_code=403)
    deal = get_deal(deal_id)
    if not deal:
        return JSONResponse({"error": "сделка не найдена"}, status_code=404)
    enriched = dict(deal)
    for key, out in (("buyer", "buyer_name"), ("target", "target_name"), ("seller_id", "seller_name")):
        company_id = deal.get(key)
        profile = get_company_profile(company_id) if company_id else None
        if profile and not enriched.get(out):
            enriched[out] = profile.get("name")
    enriched["finance"] = _export_finance(deal, db)
    pdf = render_deal_pdf(enriched)
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", deal_id)[:80] + ".pdf"
    return StreamingResponse(iter([pdf]), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


class CompaniesExportIn(BaseModel):
    """Сравнение собрано на экране, оттуда и приходит: сервер не пересобирает
    его заново — иначе в PDF попало бы не то, что человек видел."""
    companies: list[dict] = []


@app.post("/api/companies/export")
def export_companies(payload: CompaniesExportIn,
                      user: User | None = Depends(_current_user)):
    """PDF сравнения компаний. Ксюша 19 сентября 2026: «сделала сравнение
    компаний — могу получить пдф»."""
    if not user and not DEAL_EXPORT_GUESTS:
        return JSONResponse({"error": "войдите, чтобы скачать сравнение"}, status_code=401)
    rows = [r for r in (payload.companies or []) if isinstance(r, dict) and r.get("name")]
    if not rows:
        return JSONResponse({"error": "нечего выгружать: компании не выбраны"}, status_code=400)
    if len(rows) > 3:
        rows = rows[:3]
    pdf = render_companies_pdf(rows)
    return StreamingResponse(iter([pdf]), media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="compass-companies.pdf"'})


# Иконки по корневым адресам, которые браузеры запрашивают САМИ, не читая
# <link> в <head>: Safari на iPhone просит /favicon.ico для значка закладки
# (SVG-фавикон в data: он не понимает вовсе) и /apple-touch-icon.png для
# экрана «Домой». До 5 сентября 2026 эти адреса ловил catch-all ниже и
# отдавал index.html со статусом 200 — Safari получал HTML вместо картинки,
# не считал это ошибкой и рисовал вместо логотипа букву «K» (скриншот
# владельца: окно «Add Bookmark»). Правильный ответ здесь — файл картинки,
# а не «страница не найдена».
ROOT_ICONS = {
    "favicon.ico": ("favicon.ico", "image/x-icon"),
    "apple-touch-icon.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-precomposed.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-180x180.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-180x180-precomposed.png": ("apple-touch-icon.png", "image/png"),
}


@app.get("/{icon_name}.ico")
@app.get("/{icon_name}.png")
def root_icon(icon_name: str, request: Request):
    name = request.url.path.lstrip("/")
    if name not in ROOT_ICONS:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    filename, media_type = ROOT_ICONS[name]
    return FileResponse(os.path.join(STATIC_DIR, "icons", filename), media_type=media_type,
                        headers={"Cache-Control": "public, max-age=86400"})


# Открытые страницы для поисковиков и ИИ-ассистентов (seo_pages.py, 23 октября
# 2026): сделка и компания в объеме поста канала, карта сайта, описание для ИИ.
# Стоят ДО catch-all ниже, иначе их адреса получили бы index.html.
# Это та же страница сайта (index.html), только с заголовком и текстом сделки,
# вписанными для поисковика, — поэтому и токен базы, как у index() ниже.
def _app_page(content: str, request: Request, status_code: int = 200) -> HTMLResponse:
    resp = HTMLResponse(content, status_code=status_code)
    if scrape_guard.enabled():
        resp.headers["Cache-Control"] = "no-cache"
        scrape_guard.issue_cookie(resp, request)
    return resp


@app.api_route("/deal/{deal_id}", methods=["GET", "HEAD"], include_in_schema=False)
def seo_deal(deal_id: str, request: Request):
    state, value = seo_pages.resolve_deal(deal_id)
    if state == "moved":
        return RedirectResponse(f"/deal/{value}", status_code=301)
    if state == "missing":
        return _app_page(seo_pages.missing_html(SITE_URL), request, 404)
    return _app_page(seo_pages.deal_html(value, SITE_URL), request)


@app.api_route("/company/{company_id}", methods=["GET", "HEAD"], include_in_schema=False)
def seo_company(company_id: str, request: Request):
    state, value = seo_pages.resolve_company(company_id)
    if state == "moved":
        return RedirectResponse(f"/company/{value}", status_code=301)
    if state == "missing":
        return _app_page(seo_pages.missing_html(SITE_URL), request, 404)
    return _app_page(seo_pages.company_html(company_id, value, SITE_URL), request)


# Подтверждение прав на сайт в Яндекс Вебмастере (владелец, 23 октября 2026):
# Яндекс скачивает этот файл и сверяет текст дословно. Без маршрута адрес
# ловил catch-all и отдавал index.html — «В HTML-файле неправильное содержимое».
YANDEX_VERIFICATION = "c76538994d1a82ce"


@app.api_route(f"/yandex_{YANDEX_VERIFICATION}.html", methods=["GET", "HEAD"], include_in_schema=False)
def yandex_verification():
    body = ('<html>\n    <head>\n        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
            f'    </head>\n    <body>Verification: {YANDEX_VERIFICATION}</body>\n</html>\n')
    return HTMLResponse(body)


@app.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
def seo_sitemap():
    return Response(seo_pages.sitemap_xml(SITE_URL), media_type="application/xml; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.api_route("/llms.txt", methods=["GET", "HEAD"], include_in_schema=False)
def seo_llms():
    return Response(seo_pages.llms_txt(SITE_URL), media_type="text/plain; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600"})


# Тот же HEAD: этот маршрут ловит «/» и любой адрес одностраничного
# приложения — именно сюда приходит проверка живости хостинга.
# FileResponse на HEAD сам не отправляет тело, только заголовки.
@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
def index(full_path: str, request: Request):
    # Число сделок в описании страницы (meta description, og:description) —
    # живое: «1300+» в файле устарело на четыре сотни, а поисковик и превью
    # ссылки в мессенджере показывают именно его.
    resp = HTMLResponse(seo_pages.index_html(os.path.join(STATIC_DIR, "index.html")))
    # Токен для базы (scrape_guard): страница получает его вместе с собой.
    # no-cache — браузер переспрашивает страницу (304 дешев) и заодно
    # получает свежий токен, а не берет из кэша страницу с истекшим.
    if scrape_guard.enabled():
        resp.headers["Cache-Control"] = "no-cache"
        scrape_guard.issue_cookie(resp, request)
    return resp

# ИМЕНА ДЛЯ ТЕСТОВ И СКРИПТОВ. Все, что раньше жило в main.py, читается через
# `main.<имя>` по-прежнему. Подменять (monkeypatch) нужно в модуле-владельце:
# `app.assistant.call_llm`, а не `main.call_llm` — иначе роутер подмены не
# увидит. Попытка подменить через main падает с подсказкой, где владелец.
_reexport.install(globals(), (core, fns, assistant, accounts, ops, console,))
