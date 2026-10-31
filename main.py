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


from app import core, fns, assistant, accounts
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
    _start_telegram_polling()
    _start_intake_summary()
    yield


app = FastAPI(title="КОМПАС", lifespan=lifespan)

# Роутеры — в порядке областей; ловилка всех адресов (site) подключается последней.
for _r in (fns.router, assistant.router, accounts.router,):
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
    data_refresh.ON_CHANGE.append(_console_after_refresh)
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


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    # МОДЕЛЬ НАЗВАНА ВСЛУХ. 22 сентября 2026 владелец спросил, не сменить ли
    # deepseek на другую модель, — а прод уже год мог работать на чем угодно:
    # `YANDEX_MODEL` задается переменной окружения хоста, и снаружи узнать ее
    # было нельзя. Догадка вместо факта стоит дороже строки в /health: это
    # идентификатор модели, а не секрет.
    return {"status": "ok", "ai": _yandex_ready(), "model": assistant.current_model(),
            "build": build_fingerprint()}


class TelegramWebhookIn(BaseModel):
    update_id: int | None = None
    message: dict | None = None
    callback_query: dict | None = None
    # У ПРИВАТНОГО КАНАЛА НЕТ @ИМЕНИ. 4 сентября 2026 владелец с партнером
    # закрыли канал, чтобы закрытый тест не привел посторонних, — и
    # публикация встала: `sendMessage` на «@projectcompassru» стал отвечать
    # «chat not found», причем и `getChat` тоже, то есть узнать адрес канала
    # снаружи нечем. Постить в приватный канал можно, но только по ЧИСЛОВОМУ
    # id, а его сообщает лишь сам Telegram — в посте канала, в правке поста
    # или в смене прав бота. Эти три типа обновлений мы и слушаем.
    channel_post: dict | None = None
    edited_channel_post: dict | None = None
    my_chat_member: dict | None = None


class DealExportIn(BaseModel):
    # Поле оставлено для обратной совместимости с будущим редактором, но сервер
    # формирует PDF из своей базы и не доверяет присланному HTML/тексту.
    title: str | None = None


# РАЗМЕТКА ОТВЕТА ВЛАДЕЛЬЦА (8 октября 2026). Telegram присылает текст
# сообщения отдельно от разметки: жирный, ссылки и т. п. лежат в `entities`
# со смещениями в единицах UTF-16. Бот брал только `text`, и поправленный
# владельцем пост ушел в канал без жирных подписей, а «Источник» перестал
# быть ссылкой. Собираем HTML канала из текста и разметки.
_ENTITY_TAGS = {"bold": "b", "italic": "i", "underline": "u", "strikethrough": "s",
                "code": "code", "pre": "pre", "spoiler": "tg-spoiler"}


def _telegram_text_as_html(text: str, entities) -> str:
    import html as _html
    if not entities:
        return text
    units = text.encode("utf-16-le")
    n = len(units) // 2
    opens: dict[int, list[str]] = {}
    closes: dict[int, list[str]] = {}
    for e in sorted(entities, key=lambda e: (e.get("offset", 0), -e.get("length", 0))):
        kind, start = e.get("type"), int(e.get("offset", 0))
        end = start + int(e.get("length", 0))
        if not (0 <= start < end <= n):
            continue
        if kind == "text_link" and str(e.get("url") or "").startswith(("http://", "https://")):
            tag_open, tag_close = '<a href="%s">' % _html.escape(e["url"], quote=True), "</a>"
        elif kind in _ENTITY_TAGS:
            tag = _ENTITY_TAGS[kind]
            tag_open, tag_close = "<%s>" % tag, "</%s>" % tag
        else:
            continue
        opens.setdefault(start, []).append(tag_open)
        closes.setdefault(end, []).insert(0, tag_close)
    out, i = [], 0
    while i <= n:
        out.extend(closes.get(i, []))
        out.extend(opens.get(i, []))
        if i == n:
            break
        cu = int.from_bytes(units[2 * i:2 * i + 2], "little")
        step = 2 if 0xD800 <= cu <= 0xDBFF and i + 1 < n else 1
        out.append(_html.escape(units[2 * i:2 * (i + step)].decode("utf-16-le"), quote=False))
        i += step
    return "".join(out)


@app.post("/api/telegram/webhook/{secret}")
def telegram_webhook(secret: str, payload: TelegramWebhookIn, db=Depends(get_db)):
    """Вход для вебхука. Остается рабочим, но с 7 сентября 2026 по умолчанию
    обновления забираются опросом (см. `_poll_telegram_updates`) — разбор у
    обоих путей общий, чтобы поведение не могло разойтись."""
    expected = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    if not expected or secret != expected:
        return JSONResponse({"error": "not found"}, status_code=404)
    return _handle_telegram_update(payload, db)


def _handle_telegram_update(payload: TelegramWebhookIn, db):
    """Разбор одного обновления Telegram: команды, кнопки, ответы текстом.

    Вынесено из маршрута вебхука, чтобы тем же кодом обрабатывались
    обновления, забранные опросом (`getUpdates`). Единственная разница между
    путями — как обновление к нам попало."""
    # Учится молча на КАЖДОМ апдейте из группы-консоли, ничего не решает и не
    # мешает обработке ниже — id группы мог смениться (см. core._review_chat_ids).
    _learn_review_group(payload, db)
    # Пост в канале или смена прав бота — не команда и не вердикт: у них одна
    # задача, назвать числовой адрес канала (см. TelegramWebhookIn).
    if _announce_channel_id(payload, db):
        return {"ok": True}
    if _learn_console_topics(payload, db):
        return {"ok": True}
    # Кнопка под черновиком карточки: callback_data вида "mod:<id>:ok|hold".
    # Решение пишется в таблицу, а применяет его рутина публикации — у нее нет
    # доступа к этой базе напрямую, поэтому она заберет решение по
    # /api/moderation/decisions (см. модель ModerationDecision).
    callback = payload.callback_query or {}
    if callback:
        from_id = (callback.get("from") or {}).get("id")
        # Кнопки-вопросы под отчетом рутины («что скоро выйдет», «что
        # придержано»). Это НЕ вердикт: ничего не решают, только показывают
        # состав очереди, чтобы не идти искать его руками. Отчет рутины стал
        # человеческим 9 августа (см. pipeline/ops_status.py), и кнопки —
        # его часть: цифра «6 карточек выйдут сами» бесполезна, если нельзя
        # тут же посмотреть, какие именно.
        # Кнопка под ответом на /topic: закрепить номер ЭТОЙ темы за видом
        # сообщений. Номер берется из сообщения самого бота — оно живет внутри
        # темы и несет message_thread_id; нажатие доходит и в режиме
        # приватности, в отличие от напечатанного названия.
        # Список видов берется из САМОГО справочника, а не переписывается здесь
        # руками. 20 сентября 2026 владелец нажал кнопку «Заметки от
        # пользователей» — и ничего не произошло: кнопки строятся по
        # CONSOLE_TOPIC_NAMES (там вид появился 19 сентября), а этот разбор
        # знал только три старых вида и молча ронял нажатие, даже не ответив
        # на него. Тот же класс, что уже записан про прямые кавычки: добавили
        # в одном месте, забыли во втором — чинить надо связь, а не второе
        # место.
        topic = re.match(r"^topic:([a-z_]+)$", str(callback.get("data") or ""))
        if topic and topic.group(1) not in CONSOLE_TOPIC_NAMES:
            notification_service.tg_api(
                "answerCallbackQuery", callback_query_id=callback.get("id"),
                text="Такой темы бот не знает — обновите страницу и дайте /topic снова.")
            return {"ok": True}
        if topic:
            msg = callback.get("message") or {}
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Настраивать темы могут только владелец и партнер.")
                return {"ok": True}
            kind = topic.group(1)
            name = CONSOLE_TOPIC_NAMES[kind]
            thread_id = msg.get("message_thread_id")
            if thread_id:
                _remember_setting(db, "telegram_topic:%s" % _topic_slug(name), str(thread_id))
                done = "Запомнил: это тема «%s». Сюда теперь пойдут %s." % (name, CONSOLE_TOPIC_PURPOSE[kind])
            else:
                done = ("Это главная тема группы — своего номера у нее нет, и закреплять "
                        "ее не нужно: все, для чего не назначена отдельная тема, приходит "
                        "сюда само.")
            if msg.get("message_id"):
                notification_service.tg_api(
                    "editMessageText", chat_id=(msg.get("chat") or {}).get("id"),
                    message_id=msg["message_id"], text=done, disable_web_page_preview=True)
            notification_service.tg_api("answerCallbackQuery",
                                        callback_query_id=callback.get("id"))
            return {"ok": True}

        # «Назначить эту тему» из меню /start — то же, что команда /topic, в
        # той теме, где стоит меню (сообщение бота несет message_thread_id).
        if str(callback.get("data") or "") == "menu:topic":
            msg = callback.get("message") or {}
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Настраивать темы могут только владелец и партнер.")
                return {"ok": True}
            notification_service.tg_api("answerCallbackQuery",
                                        callback_query_id=callback.get("id"))
            chat = (msg.get("chat") or {}).get("id")
            if chat is not None:
                _offer_topic_binding(msg, chat, from_id)
            return {"ok": True}

        # Кнопки меню под /start: очередь и сводка о платформе.
        menu = re.match(r"^menu:(queue|stats)$", str(callback.get("data") or ""))
        if menu:
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Это видят только владелец и партнер.")
                return {"ok": True}
            which = menu.group(1)
            chat = (callback.get("message") or {}).get("chat", {}).get("id")
            thread_kw = _thread_kwargs(callback.get("message"))

            def _send_menu():
                body = _queue_report() if which == "queue" else _stats_report()
                notification_service.tg_api(
                    "sendMessage", chat_id=chat, text=body, parse_mode="HTML",
                    disable_web_page_preview=True, **thread_kw)

            _answer_and_do(callback, _send_menu)
            return {"ok": True}

        # «Показать придержанные / что скоро выйдет» — НЕ список, а рабочие
        # карточки. Первая версия присылала простое перечисление заголовков, и
        # владелец сразу уперся: «я так и не понял, как проверять те, которые
        # придержаны». Список без кнопок — тупик: увидел и ничего не можешь
        # сделать. Теперь каждая карточка приходит своим сообщением с теми же
        # кнопками, что и при первом показе, — решение принимается там же, где
        # увидел.
        show = re.match(r"^show:(soon|held|raw|unread)$", str(callback.get("data") or ""))
        if show:
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Очередь видят только владелец и партнер.")
                return {"ok": True}
            chat = (callback.get("message") or {}).get("chat", {}).get("id")
            kind = show.group(1)
            # КАРТОЧКА С КНОПКАМИ РЕШЕНИЯ ЖИВЕТ В «ПОДТВЕРЖДЕНИИ ПОСТОВ», А НЕ
            # ТАМ, ГДЕ НАЖАЛИ КНОПКУ. Отчет рутины стоит в «Обновлениях», и
            # кнопки «что скоро выйдет» / «что придержано» — часть отчета;
            # раньше ответ на нажатие оставался в той же теме, и очередь
            # карточек с «Опубликовать / Придержать / Изменить / Выкинуть»
            # вываливалась в ленту отчетов. Владелец 22 сентября 2026: «почему
            # посты, которые должны приходить в „подтверждение постов", приходят
            # в „обновления"». Тема выбирается по ВИДУ сообщения, а не по месту
            # нажатия: где нажали — дело случая, а решение всегда ждут в одном
            # месте.
            pressed_in = (callback.get("message") or {}).get("message_thread_id")
            thread = core._console_thread_id(db, "decision") if db is not None else None
            where = ("Открыл очередь в «%s»." % CONSOLE_TOPIC_NAMES["decision"]
                     if thread and thread != pressed_in else None)
            _answer_and_do(callback,
                           lambda: _send_queue_batch(chat, kind,
                                                     thread=thread or pressed_in),
                           text=where)
            return {"ok": True}

        # Заявка на доступ к сайту (core.ACCESS_GATE): «Одобрить»/«Отклонить» под
        # сообщением из _notify_access_request. В отличие от `mod:`, решение
        # применяется ЗДЕСЬ ЖЕ, без таблицы и рутины: аккаунты живут в этой
        # же базе, а не в git-файле. Право решать — по отправителю
        # (from.id), как и у модерации: в общей группе chat.id один на всех.
        acc = re.match(r"^acc:(\d{1,12}):(ok|no)$", str(callback.get("data") or ""))
        if acc:
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Решать могут только владелец и партнер.")
                return {"ok": True}
            applicant = db.get(User, int(acc.group(1)))
            if not applicant:
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Этого аккаунта уже нет — заявку отозвали удалением.")
                return {"ok": True}
            # Отклоненный остается в базе с approved=False: повторная заявка
            # тем же адресом не создаст дубля (почта уникальна), а вход
            # отвечает тем же «доступ не открыт».
            applicant.approved = acc.group(2) == "ok"
            db.commit()
            _mark_decided(callback, "acc_ok" if applicant.approved else "acc_no")
            return {"ok": True}

        # «Это моя компания» (кабинет компании, 14 октября 2026): кнопки
        # «Подтвердить»/«Отклонить» под сообщением из _notify_company_claim.
        # Как у `acc:` — решение применяется здесь же, в базе сайта; право —
        # по from.id.
        claim = re.match(r"^claim:(ok|no):(\d{1,12})$", str(callback.get("data") or ""))
        if claim:
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Решать могут только владелец и партнер.")
                return {"ok": True}
            row = db.get(CompanyClaim, int(claim.group(2)))
            if not row:
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Этой заявки уже нет — аккаунт удален.")
                return {"ok": True}
            accounts._decide_claim(db, row, claim.group(1) == "ok")
            _mark_decided(callback, "claim_ok" if row.status == "approved" else "claim_no")
            return {"ok": True}

        # [\w~-]: `~` — разделитель id сделки и вида этапа у вехи
        # («<id>~<kind>», раздел A, 22 августа) — id сделок сами бывают с
        # дефисами, поэтому обычный `-` для разделителя не годится, а `:`
        # уже занят разбором `mod:<id>:<вердикт>` целиком. Длина увеличена
        # с 40 до 60 — комбинация «id сделки + ~ + вид этапа» бывает длиннее
        # одного голого id.
        match = re.match(r"^mod:([\w~-]{1,60}):(ok|hold|discard|post_ok|post_no|take|drop|edit)$",
                         str(callback.get("data") or ""))
        if match and match.group(2) == "edit" and _is_reviewer(from_id):
            # «Изменить» — не вердикт, а подсказка, как продиктовать правку:
            # окна ввода у кнопок Telegram нет, ввод делается ответом.
            notification_service.tg_api(
                "answerCallbackQuery", callback_query_id=callback.get("id"),
                show_alert=True,
                text="Ответьте на это сообщение своим текстом. Для поста ответ "
                     "заменит текст поста целиком; для карточки и сырья — станет "
                     "заметкой, которую применит рутина через проверки источника.")
            return {"ok": True}
        if match and _is_reviewer(from_id):
            verdict = {"ok": "approve", "hold": "hold", "discard": "discard",
                       "post_ok": "post_yes",
                       "post_no": "post_no", "take": "take", "drop": "drop"}[match.group(2)]
            if verdict in ("approve", "hold", "discard", "post_yes", "post_no") \
                    and _already_on_site(match.group(1)):
                if callback.get("id"):
                    notification_service.tg_api("answerCallbackQuery", callback_query_id=callback["id"],
                                                show_alert=True, text=ALREADY_ON_SITE_TEXT)
                return {"ok": True}
            # Отвечаем Telegram ПЕРВЫМ делом. Пока бот не ответил на нажатие,
            # у человека на кнопке крутится индикатор — и это ровно то, что
            # он описывает словами «кнопка не нажимается». Раньше ответ шел
            # последним, ПОСЛЕ записи в базу и правки сообщения: стоило
            # правке подвиснуть или не пройти (сайт перезапускался,
            # сообщение старше суток), и нажатие выглядело потерянным, хотя
            # решение уже было записано. 7 сентября 2026 партнер из-за этого
            # нажал «не сделка» шесть раз за две секунды.
            if callback.get("id"):
                notification_service.tg_api("answerCallbackQuery",
                                            callback_query_id=callback["id"], text="Принято")
            # Тот же вердикт по той же карточке от того же человека за
            # последнюю минуту — это ПОВТОРНАЯ ДОСТАВКА одного нажатия
            # (Telegram шлет апдейт заново, если вебхук не ответил вовремя)
            # или частые тычки по неотзывчивой кнопке. Человек не решает
            # одно и то же дважды за минуту, а вот шесть одинаковых
            # решений в очереди рутина применит шесть раз — для `take` это
            # шесть карточек, для `post_yes` шесть постов в канал.
            since = datetime.now(timezone.utc) - timedelta(minutes=1)
            twin = db.scalar(select(ModerationDecision).where(
                ModerationDecision.deal_id == match.group(1),
                ModerationDecision.verdict == verdict,
                ModerationDecision.decided_by == str(from_id),
                ModerationDecision.created_at >= since))
            if not twin:
                decision_row = ModerationDecision(deal_id=match.group(1), verdict=verdict,
                                                  decided_by=str(from_id))
                db.add(decision_row)
                db.commit()
                # Этап сделки — в канал сразу, не дожидаясь рутины публикации.
                if (verdict == "post_yes" and "~" in match.group(1)
                        and not match.group(1).startswith("digest~")):
                    threading.Thread(target=_instant_milestone_post,
                                     args=(match.group(1), decision_row.id), daemon=True).start()
            # Правка самого сообщения («— ✅ Одобрено (Борис)») — еще один
            # вызов Bot API, и он не должен задерживать ответ вебхуку:
            # решение уже в базе, а Telegram ждет ответа секунды, не десятки
            # секунд (см. _answer_and_do).
            threading.Thread(target=_mark_decided, args=(callback, verdict),
                             kwargs={"answered": True}, daemon=True).start()
        elif callback.get("id"):
            # Сюда падает нажатие, которого бот не узнал вовсе. Раньше он
            # отвечал «Решать могут только владелец и партнер» — и это была
            # неправда: 20 сентября владелец нажал свою же кнопку и получил
            # отказ по праву доступа, хотя право у него есть, а не узнана была
            # сама кнопка. Ответ теперь говорит, что случилось на самом деле.
            notification_service.tg_api(
                "answerCallbackQuery", callback_query_id=callback["id"],
                text="Эту кнопку бот не узнал — скорее всего, сообщение старое. "
                     "Повторите команду, чтобы получить свежие кнопки.")
        return {"ok": True}

    message = payload.message or {}
    text = str(message.get("text") or "")
    chat_id = (message.get("chat") or {}).get("id")
    # Право решать проверяется по ОТПРАВИТЕЛЮ (message.from.id), а не по чату,
    # в который упало сообщение (message.chat.id). В личном чате с ботом это
    # одно и то же число, и разница была не видна; в ГРУППЕ (владелец и
    # партнер обсуждают черновики вместе) chat.id — это id самой группы, один
    # для всех участников, а не того, кто именно ответил. Проверка по chat_id
    # авторизовала бы либо всех членов группы разом, либо никого.
    sender_id = (message.get("from") or {}).get("id")
    # Тема «Клод» — раньше маркерных ответов ниже: там любой текст владельца
    # (в том числе ответ на сообщение бота) — это сообщение агенту.
    if _claude_topic_message(message, db):
        return {"ok": True}
    # Ответ на сообщение бота. Что означает ответ — решает маркер в первой
    # строке того сообщения, НА КОТОРОЕ ответили:
    #   [пост <id>] / [черновик <id>] — ваш текст заменяет текст поста и
    #       одновременно одобряет карточку (вы поправили пост — вы его ждете);
    #   [карточка <id>] / [сырье <id>] — ваш текст ложится ЗАМЕТКОЙ: ее
    #       читает суточная рутина притока и применяет через review.py с его
    #       проверками цитат — заметка не пишет в базу напрямую.
    #   [инн <id компании>] — очередь «нужен ИНН» (pipeline/
    #       fns_unresolved_queue.py, этап 3 П3'''): ваш текст с номером ИНН
    #       ложится ЗАМЕТКОЙ, которую читает pipeline/fns_notes_to_registry.py
    #       и, если контрольная сумма сходится, пишет в git-реестр
    #       pipeline/fns_registry.py. deal_id хранится с префиксом "инн~" —
    #       голый id компании МОГ БЫ совпасть с id сделки (7 таких совпадений
    #       уже есть в базе, слаги куратора вроде "citibank"), и без префикса
    #       заметка ушла бы неправильному потребителю. Тот же разделитель
    #       `~`, что уже используют вехи в mod:<id>~<kind> (раздел A).
    #   [инн-омоним <id компании>] — этап 9, П8-9: повторный вопрос по
    #       компании, которая УЖЕ в реестре как no_match (pipeline/
    #       fns_homonym_queue.py). Отдельный от "инн" маркер и префикс
    #       "инн-омоним~", потому что ответ должен ПРАВИТЬ существующую
    #       запись на месте, а не дописывать дубль company_id (запрещен
    #       тестом) — pipeline/fns_notes_to_registry.py различает два
    #       сценария по префиксу заметки.
    reply = message.get("reply_to_message") or {}
    marker = re.search(r"\[(пост|черновик|карточка|сырье|инн-омоним|инн) ([\w-]{1,40})\]",
                       str(reply.get("text") or ""))
    # ОТМЕНА ПРАВКИ ПОСТА. «Принято: пост уйдет с вашим текстом» теперь несет
    # метку «(правка поста <id>)», и ответ «отмена» на это сообщение снимает
    # еще не примененное решение. 4 октября 2026 партнер ответил на проект
    # поста вопросом, бот принял вопрос за новый текст поста, а отменить
    # было нечем — владелец спросил «можно его отменить как-то?».
    undo = re.search(r"\(правка поста ([\w~-]{1,46})\)", str(reply.get("text") or ""))
    if undo and _is_reviewer(sender_id) and UNDO_WORDS.match(text.strip()):
        # «<id>~edit» — ответ своей редакцией на предложение правки вышедшего
        # поста (propose_post_edit.py); снимается так же, пока не применен.
        undo_verdict = "post_yes" if undo.group(1).endswith("~edit") else "approve"
        rows = list(db.scalars(select(ModerationDecision).where(
            ModerationDecision.deal_id == undo.group(1), ModerationDecision.verdict == undo_verdict,
            ModerationDecision.edited_text.is_not(None), ModerationDecision.consumed.is_(False))).all())
        for row in rows:
            row.consumed = True
        db.commit()
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id),
            text=("Отменено: текст поста не изменится, карточка ждет решения как раньше."
                  if rows else "Отменять нечего: правку уже применили. Напишите, что сделать, — поправим."),
            disable_web_page_preview=True, **_thread_kwargs(reply))
        return {"ok": True}
    # ОТВЕТ ТЕКСТОМ НА ЭТАП СДЕЛКИ (20 октября 2026). Метка «[веха <id>~<вид>]»
    # не входила в разбор выше, и правка партнера к посту об этапе «Лабинского»
    # (ВТБ продал агрохолдинг) молча пропала: ни решения, ни ответа. Теперь
    # так же, как у проекта поста: полный текст заменяет пост этапа и
    # выпускает его в канал; вопрос или короткая реплика — заметка к сделке.
    # ОТВЕТ СВОЕЙ РЕДАКЦИЕЙ НА ПРЕДЛОЖЕНИЕ ПРАВКИ ВЫШЕДШЕГО ПОСТА (29 октября
    # 2026, «Агропромкредит»). Владелец: «напиши в консоли, что хочешь
    # обновить в посте и как будет выглядеть новый пост… мы нажмем согласие
    # или отказ или направим новую редакцию». Полный текст в ответ на
    # «[правка поста <id>]» — решение `<id>~edit` / post_yes с этим текстом:
    # рутина публикации правит вышедший пост им, а не предложенным
    # (send_telegram.plan_post_edits). Вопрос или реплика — заметка к сделке.
    proposal = re.search(r"\[правка поста ([\w-]{1,40})\]", str(reply.get("text") or ""))
    if proposal and not marker and text.strip() and _is_reviewer(sender_id):
        deal_id = proposal.group(1)
        if _is_question(text) or _not_a_post_text(text, reply.get("text")):
            db.add(ModerationDecision(deal_id=deal_id, verdict="note", edited_text=text.strip(),
                                      decided_by=str(sender_id),
                                      chat_id=str(chat_id) if chat_id is not None else None,
                                      reply_message_id=reply.get("message_id")))
            db.commit()
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Это не похоже на новый текст поста — пост не тронут, замечание записано к "
                      "сделке. Чтобы заменить пост своей редакцией, пришлите ответом полный текст; "
                      "предложенный текст — кнопкой «Пост в канал»."),
                disable_web_page_preview=True, **_thread_kwargs(reply))
            return {"ok": True}
        body = text.strip()
        if message.get("entities"):
            body = _telegram_text_as_html(text, message.get("entities")).strip()
        db.add(ModerationDecision(deal_id=deal_id + "~edit", verdict="post_yes", edited_text=body,
                                  decided_by=str(sender_id),
                                  chat_id=str(chat_id) if chat_id is not None else None,
                                  reply_message_id=reply.get("message_id")))
        db.commit()
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id),
            text=("Принято: пост в канале изменится на ваш текст ближайшим прогоном публикации. "
                  "Передумали — ответьте на это сообщение словом «отмена». (правка поста %s~edit)" % deal_id),
            disable_web_page_preview=True, **_thread_kwargs(reply))
        return {"ok": True}
    milestone = re.search(r"\[веха ([\w-]{1,50}~[\w-]{1,30})\]", str(reply.get("text") or ""))
    if milestone and not marker and text.strip() and _is_reviewer(sender_id):
        combo = milestone.group(1)
        deal_id = combo.split("~", 1)[0]
        if _is_question(text) or _not_a_post_text(text, reply.get("text")):
            db.add(ModerationDecision(deal_id=deal_id, verdict="note", edited_text=text.strip(),
                                      decided_by=str(sender_id),
                                      chat_id=str(chat_id) if chat_id is not None else None,
                                      reply_message_id=reply.get("message_id")))
            db.commit()
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Это не похоже на новый текст поста — пост этапа не тронут, замечание "
                      "записано к сделке. Чтобы заменить пост, пришлите ответом полный текст."),
                disable_web_page_preview=True, **_thread_kwargs(reply))
            return {"ok": True}
        body = text.strip()
        if message.get("entities"):
            body = _telegram_text_as_html(text, message.get("entities")).strip()
        row = db.get(AppSetting, MILESTONE_DRAFT_PREFIX + combo)
        draft = {}
        if row and row.value:
            try:
                draft = json.loads(row.value)
            except ValueError:
                draft = {}
        if not draft:
            # Проекта этапа на сайте нет — выпустит рутина, и своим текстом:
            # честно говорим, а текст кладем заметкой, чтобы его не потерять.
            db.add(ModerationDecision(deal_id=deal_id, verdict="note", edited_text=body,
                                      decided_by=str(sender_id),
                                      chat_id=str(chat_id) if chat_id is not None else None,
                                      reply_message_id=reply.get("message_id")))
            db.commit()
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Текст записан, но сразу выпустить этап не могу — его выпустит рутина "
                      "публикации и подставит ваш текст. (этап %s)" % combo),
                disable_web_page_preview=True, **_thread_kwargs(reply))
            return {"ok": True}
        draft["text"] = body
        draft["edited_by"] = str(sender_id)
        row.value = json.dumps(draft, ensure_ascii=False)
        decision_row = ModerationDecision(deal_id=combo, verdict="post_yes", decided_by=str(sender_id))
        db.add(decision_row)
        db.commit()
        threading.Thread(target=_instant_milestone_post, args=(combo, decision_row.id), daemon=True).start()
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id),
            text="Принято: пост об этапе уйдет в канал с вашим текстом. (этап %s)" % combo,
            disable_web_page_preview=True, **_thread_kwargs(reply))
        return {"ok": True}
    if marker and text.strip() and _is_reviewer(sender_id):
        kind, raw_id = marker.group(1), marker.group(2)
        # Ответ своим текстом на проект поста карточки, которая уже вышла, —
        # не новый пост (см. _already_on_site): говорим об этом, не записывая.
        if kind in ("пост", "черновик") and _already_on_site(raw_id):
            notification_service.tg_api("sendMessage", chat_id=str(chat_id), text=ALREADY_ON_SITE_TEXT,
                                        disable_web_page_preview=True, **_thread_kwargs(reply))
            return {"ok": True}
        verdict = "approve" if kind in ("пост", "черновик") else "note"
        # ВОПРОС — НЕ НОВЫЙ ТЕКСТ ПОСТА (4 октября 2026). Партнер ответил на
        # проект поста OTP Bank «Что такое luminor?», и бот одобрил пост с
        # этим текстом: ближайшая публикация ушла бы в канал тремя словами.
        # Вопрос или короткая реплика ложится заметкой к карточке, пост не
        # трогается; заменить текст можно только полным текстом поста.
        asked = verdict == "approve" and _not_a_post_text(text, reply.get("text"))
        # ВОПРОС — ЭТО НЕ РЕШЕНИЕ, А ПОВОД ОТВЕТИТЬ (владелец, 4 октября 2026:
        # «если спрашивают и вопросительный знак в конце — не отправляй карту
        # в канал, а отвечай на вопрос»). Вопрос к проекту поста или к
        # карточке придерживает карточку — по молчанию она не выйдет, пока
        # кто-то не нажмет «Опубликовать», — и бот сразу отвечает на него.
        question = (kind in ("пост", "черновик", "карточка", "сырье")
                    and _is_question(text))
        if asked or question:
            verdict = "note"
        if question and kind != "сырье":
            db.add(ModerationDecision(deal_id=raw_id, verdict="hold", edited_text=None,
                                      decided_by=str(sender_id)))
        deal_id = (kind + "~" + raw_id) if kind in ("инн", "инн-омоним") else raw_id
        # chat_id/reply_message_id — только у заметок: только их читает и на
        # них отвечает рутина (read_notes.py), решению approve отвечать
        # реплаем не нужно, оно и так подтверждается штампом в сообщении.
        body = text.strip()
        if verdict == "approve" and message.get("entities"):
            body = _telegram_text_as_html(text, message.get("entities")).strip()
        db.add(ModerationDecision(
            deal_id=deal_id, verdict=verdict, edited_text=body,
            decided_by=str(sender_id),
            chat_id=str(chat_id) if verdict == "note" and chat_id is not None else None,
            reply_message_id=reply.get("message_id") if verdict == "note" else None))
        db.commit()
        if verdict == "approve":
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Принято: пост уйдет с вашим текстом. Передумали — ответьте на это "
                      "сообщение словом «отмена». (правка поста %s)" % raw_id),
                disable_web_page_preview=True, **_thread_kwargs(reply))
        elif question:
            # Исходное сообщение не правим: editMessageText снял бы с него
            # кнопки и форматирование. Отвечаем отдельными сообщениями.
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Это вопрос — в канал ничего не уходит. Карточка придержана: по "
                      "молчанию она не выйдет, опубликовать — кнопкой «Опубликовать». "
                      "Ответ пришлю следующим сообщением."
                      if kind != "сырье" else "Это вопрос — ответ пришлю следующим сообщением."),
                disable_web_page_preview=True, **_thread_kwargs(reply))
            thread = _thread_kwargs(reply)
            core._in_background(lambda: _answer_console_question(raw_id, text.strip(), chat_id, thread))
        elif asked:
            notification_service.tg_api(
                "sendMessage", chat_id=str(chat_id),
                text=("Это не похоже на новый текст поста — пост не тронут. Замечание "
                      "записано к карточке. Чтобы заменить текст поста, пришлите ответом "
                      "полный новый текст."),
                disable_web_page_preview=True, **_thread_kwargs(reply))
        else:
            # МГНОВЕННОЕ ПОДТВЕРЖДЕНИЕ — раздел C MILESTONES_BRIEF.md. Раньше
            # заметка уходила в отдельное сообщение и терялась среди прочих;
            # штамп прямо в исходном [сырье …]/[карточка …] — тот же прием,
            # что «— ✅ Одобрено» у _mark_decided, второй человек в группе
            # сразу видит, что заметка не повисла без ответа. Содержательный
            # ответ («что сделала, что нашла») придет позже РЕПЛАЕМ от самой
            # рутины (read_notes.py читает chat_id/reply_message_id).
            who = (message.get("from") or {}).get("first_name") or "участник"
            original = str(reply.get("text") or "")
            stamped = "%s\n\n— 💬 Заметка принята (%s), рутина ответит после чтения" % (original, who)
            if chat_id is not None and reply.get("message_id"):
                notification_service.tg_api(
                    "editMessageText", chat_id=chat_id, message_id=reply["message_id"],
                    text=stamped, disable_web_page_preview=True)
        return {"ok": True}
    # НИ ОДИН ОТВЕТ ЧЕЛОВЕКА В КОНСОЛИ НЕ ПРОПАДАЕТ МОЛЧА (20 октября 2026).
    # Партнер ответил своим текстом на пост этапа «Лабинского», бот этой
    # метки не знал — и не сделал НИЧЕГО: ни решения, ни ответа. Владелец:
    # «у нас все работает через… хотя должно быть все понятно». Ответ, который
    # не разобран ни одним правилом выше, уходит агенту (рутина «тема Клод»)
    # вместе с тем, на что отвечали, а человек сразу видит, что с ним будет.
    chat_type = str((message.get("chat") or {}).get("type") or "")
    if (reply and (reply.get("from") or {}).get("is_bot") and text.strip() and chat_id is not None
            and _is_reviewer(sender_id) and chat_type in ("group", "supergroup") and not text.strip().startswith("/")):
        sender = message.get("from") or {}
        db.add(ClaudeMessage(
            chat_id=str(chat_id), thread_id=int(message.get("message_thread_id") or 0),
            message_id=int(message.get("message_id") or 0), from_id=str(sender_id),
            from_name=" ".join(x for x in (sender.get("first_name"), sender.get("last_name")) if x) or None,
            text=text.strip(), reply_to_text=str(reply.get("text") or reply.get("caption") or "").strip() or None,
            consumed=False, created_at=datetime.now(timezone.utc)))
        db.commit()
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id),
            text=("Бот не понял, что сделать с этим ответом, — передал агенту. Он ответит "
                  "в теме «Клод», обычно в течение часа."),
            disable_web_page_preview=True, **_thread_kwargs(reply))
        return {"ok": True}
    # ЛИЧНЫЙ ЧАТ С БОТОМ — ЭТО ЧИТАТЕЛЬ, А НЕ КОНСОЛЬ (4 октября 2026).
    # Владелец нажал в кабинете «Подключить Telegram», потом «Старт» — и
    # получил инструкцию модерации («какие сделки попадут на сайт и в
    # канал», «Опубликовать / Придержать / Выкинуть»). Ее получал бы любой
    # читатель: /start отвечал всем одной справкой консоли, а привязка по
    # ссылке проходила молча, без единого слова. Консоль живет в группе;
    # в личке бот говорит с подписчиком.
    chat = message.get("chat") or {}
    private = chat.get("type") == "private" or (
        chat_id is not None and sender_id is not None and str(chat_id) == str(sender_id))
    link = re.match(r"^(?:/start\s+)?kompas_([A-Za-z0-9_-]{16,})$", text.strip())
    if link and chat_id is not None and (private or text.strip().startswith("/start")):
        ok = notification_service.bind_telegram(db, link.group(1), str(chat_id))
        if not ok and notification_service.linked_preferences(db, chat_id):
            reply_text = READER_ALREADY_LINKED
        else:
            reply_text = READER_LINKED if ok else READER_LINK_EXPIRED
        notification_service.tg_api("sendMessage", chat_id=str(chat_id), text=reply_text,
                                    parse_mode="HTML", disable_web_page_preview=True,
                                    reply_markup=_reader_menu())
        return {"ok": True}
    # /topic — закрепить за темой форума вид сообщений бота. Именно КОМАНДА и
    # КНОПКИ, а не напечатанное название: у бота включен режим приватности, и
    # в группе он получает только команды, ответы на свои сообщения и нажатия
    # кнопок — обычный текст «Обновления» до него не доходит вовсе (5 сентября
    # 2026 владелец написал названия в трех темах, бот не увидел ни одного).
    if re.match(r"^/topic(?:@\S+)?(?:\s.*)?$", text.strip(), re.I) and chat_id is not None:
        _offer_topic_binding(message, chat_id, sender_id)
        return {"ok": True}
    # Команды бота. Голый «/start» раньше не делал НИЧЕГО и молчал — человек
    # писал боту и получал тишину, неотличимую от поломки. В группе команда
    # приходит с суффиксом («/queue@compass_bot»), его надо отрезать.
    command = re.match(r"^/([a-z_]+)(?:@\S+)?\s*$", text.strip(), re.I)
    if private and chat_id is not None and (
            (command and command.group(1).lower() in ("start", "stop"))
            or (command and command.group(1).lower() == "help" and not _is_reviewer(sender_id))
            or (not command and text.strip() and not _is_reviewer(sender_id))):
        name = command.group(1).lower() if command else ""
        notification_service.tg_api("sendMessage", chat_id=str(chat_id),
                                    text=_reader_reply(db, name, chat_id, sender_id),
                                    parse_mode="HTML", disable_web_page_preview=True,
                                    reply_markup=_reader_menu())
        return {"ok": True}
    if command and chat_id is not None:
        name = command.group(1).lower()
        reply = _bot_command(name, sender_id)
        if reply:
            # У /start и /help — меню кнопками: текстом человек не понимает,
            # что вообще можно нажать, и команду приходится помнить наизусть.
            body = {"chat_id": str(chat_id), "text": reply, "parse_mode": "HTML",
                    "disable_web_page_preview": True, **_thread_kwargs(message)}
            if name in ("start", "help") and _is_reviewer(sender_id):
                body["reply_markup"] = _bot_menu()
            notification_service.tg_api("sendMessage", **body)
    return {"ok": True}


# ---------------------------------------------------------------------------
# ОБНОВЛЕНИЯ TELEGRAM ЗАБИРАЕМ САМИ, А НЕ ЖДЕМ, ПОКА ДО НАС ДОСТУЧАТСЯ.
#
# 7 сентября 2026 владелец полдня не мог нажать ни одну кнопку в консоли:
# «нажимаю, прошло секунд 30, ничего». Замер в те же минуты развел причину и
# следствие окончательно: НАШ POST в тот же самый адрес вебхука отвечал за
# 0,9 секунды кодом 200, вызов Bot API с боевого хоста — за 0,2 секунды, а
# `getWebhookInfo` в ту же секунду показывал `Connection timed out`. То есть
# сайт жив и быстр, а Telegram до него не доходит.
#
# Это обратная сторона уже описанной в CLAUDE.md нестабильности связи
# Timeweb <-> Telegram (в соседнем проекте владельца на том же хостинге
# замерено ~32% отказов на попытку соединения). Для ИСХОДЯЩИХ у нас есть
# лекарство — релей на Cloudflare (telegram_endpoint.py). Для ВХОДЯЩИХ его
# не было, и почини мы вебхук еще десять раз, доступность нас снаружи от
# этого не изменилась бы: чинить надо не обработчик, а направление.
#
# Опрос убирает входящее направление целиком: сайт сам спрашивает «что
# нового» долгим запросом (`getUpdates` с `timeout`), и весь обмен идет
# ИСХОДЯЩИМ путем, где релей уже работает. Ответ на нажатие приходит тем же
# путем, что и раньше.
#
# Выключатели: `TELEGRAM_POLLING=0` возвращает прежнюю схему (вебхук),
# `TELEGRAM_POLL_TIMEOUT` — длина долгого запроса. Вебхук при включенном
# опросе снимается: Telegram не отдает обновления обоими способами сразу и
# на `getUpdates` при живом вебхуке отвечает отказом 409.
TELEGRAM_POLLING = os.environ.get("TELEGRAM_POLLING", "1") != "0"
# 8 секунд, а не 25 (30 октября 2026): после выкладки обрыв SSL шел ровно
# раз в 25 секунд — сеть хостинга рвет соединение, которое висит без данных,
# и долгий запрос не доживал до ответа. Короткий успевает вернуться.
TELEGRAM_POLL_TIMEOUT = int(os.environ.get("TELEGRAM_POLL_TIMEOUT", "8"))
POLL_PAUSE_MAX = float(os.environ.get("TELEGRAM_POLL_PAUSE_MAX", "4"))
_poll_state = {"offset": None, "last_ok": None, "updates": 0, "errors": 0,
               "last_error": None, "running": False}


def _poll_once(token: str) -> int:
    """Один долгий запрос за обновлениями. Возвращает, сколько обработано."""
    params = {"timeout": TELEGRAM_POLL_TIMEOUT,
              "allowed_updates": ["message", "channel_post", "edited_channel_post",
                                  "callback_query", "my_chat_member"]}
    if _poll_state["offset"] is not None:
        params["offset"] = _poll_state["offset"]
    response = httpx.post(telegram_endpoint.method_url(token, "getUpdates"),
                          json=params, timeout=TELEGRAM_POLL_TIMEOUT + 15)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description") or "getUpdates отказал")
    updates = data.get("result") or []
    for raw in updates:
        # Смещение двигаем ДО обработки: обновление, на котором разбор упал,
        # не должно приходить снова и снова — оно уже не станет разбираемым,
        # а очередь встанет намертво (тот же класс, что зацикленный вебхук).
        _poll_state["offset"] = int(raw.get("update_id", 0)) + 1
        db = get_session()
        try:
            _handle_telegram_update(TelegramWebhookIn(**{
                k: raw.get(k) for k in TelegramWebhookIn.model_fields}), db)
        except Exception as exc:      # одно плохое обновление не валит опрос
            logger.error("не удалось разобрать обновление Telegram: %s", exc)
        finally:
            db.close()
    _poll_state["last_ok"] = datetime.now(timezone.utc)
    _poll_state["updates"] += len(updates)
    return len(updates)


def _telegram_reachable(token: str) -> bool:
    """Отвечает ли нам Telegram вообще. Один дешевый вызов `getMe`: если он
    прошел, снимать вебхук безопасно — опрос заработает. Если нет, прежний
    вход трогать нельзя (см. комментарий в `_start_telegram_polling`)."""
    try:
        r = httpx.post(telegram_endpoint.method_url(token, "getMe"), json={}, timeout=20)
        return bool(r.json().get("ok"))
    except Exception:                                        # noqa: BLE001
        return False


def _start_telegram_polling():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not TELEGRAM_POLLING or not token or os.environ.get("PYTEST_CURRENT_TEST"):
        return

    def _run():
        # ВЕБХУК СНИМАЕТСЯ НЕ РАНЬШЕ, ЧЕМ ОПРОС ДОКАЗАЛ, ЧТО РАБОТАЕТ.
        #
        # Первая версия снимала его сразу на старте — и это оказалось
        # необратимым побочным эффектом запуска, который не обязан
        # завершиться успехом. 7 сентября 2026 сборка с опросом упала уже
        # ПОСЛЕ того, как контейнер стартовал и вебхук снял: платформа
        # откатилась на прежний код, где опроса нет, а вебхука уже не было
        # ни у кого. Консоль осталась вообще без входа — не «иногда не
        # доходит», а глухо, и владелец не мог нажать ни одной кнопки.
        #
        # Правило общее: если у запуска есть шаг, ЛОМАЮЩИЙ прежний способ
        # работы, он идет ПОСЛЕ того, как новый способ подтвердил свою
        # работоспособность, а не до. Пока `getUpdates` не ответил ни разу,
        # вебхук остается на месте — Telegram при живом вебхуке отвечает на
        # `getUpdates` отказом 409, и это ожидаемое состояние первых секунд,
        # а не сбой.
        _poll_state["running"] = True
        webhook_dropped = False
        pause = 1.0
        while True:
            try:
                if not webhook_dropped:
                    # Пробный запрос: живы ли мы вообще для Telegram. Отказ
                    # 409 («вебхук активен») здесь ожидаем и означает «связь
                    # есть» — а значит, вебхук можно снимать.
                    reachable = _telegram_reachable(token)
                    if not reachable:
                        raise RuntimeError("Telegram не отвечает — вебхук не снимаю")
                    httpx.post(telegram_endpoint.method_url(token, "deleteWebhook"),
                               json={}, timeout=20)
                    # `drop_pending_updates` не шлем: нажатия, которые Telegram
                    # не смог доставить, придут первым же запросом, и человеку
                    # не придется жать заново.
                    webhook_dropped = True
                    logger.info("вебхук снят, работает опрос getUpdates")
                _poll_once(token)
                pause = 1.0
            except Exception as exc:
                _poll_state["errors"] += 1
                _poll_state["last_error"] = str(exc)[:200]
                logger.warning("опрос Telegram не удался: %s", exc)
                # Нарастающая пауза — чтобы при недоступной сети не молотить
                # запросами. ПОТОЛОК — НЕСКОЛЬКО СЕКУНД (30 октября 2026):
                # связь хостинга с Telegram рвется часто и коротко (186
                # обрывов SSL на 22 успешных ответа за два часа), и при
                # потолке в минуту кнопка в консоли висела до минуты после
                # каждого обрыва («раньше сразу отмечалось, а сейчас хрен
                # знает сколько»). Короткий обрыв лечится сразу следующей
                # попыткой; долгий простой сети стоит лишь лишних запросов.
                time.sleep(pause)
                pause = min(pause * 2, POLL_PAUSE_MAX)

    threading.Thread(target=_run, daemon=True).start()


@app.get("/api/telegram/status")
def telegram_status(token: str = ""):
    """Жив ли опрос и когда последний раз получал ответ — чтобы «кнопки не
    работают» проверялось цифрой, а не пересказом."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    last_ok = _poll_state["last_ok"]
    return {"polling": TELEGRAM_POLLING, "running": _poll_state["running"],
            "poll_timeout": TELEGRAM_POLL_TIMEOUT,
            "offset": _poll_state["offset"], "updates": _poll_state["updates"],
            "errors": _poll_state["errors"], "last_error": _poll_state["last_error"],
            "last_ok": last_ok.isoformat() if last_ok else None,
            "seconds_since_last_ok": (
                (datetime.now(timezone.utc) - last_ok).total_seconds() if last_ok else None)}


BOT_HELP = (
    "👋 <b>Это бот «Компаса»</b>\n"
    "Через него вы решаете, какие сделки попадут на сайт и в канал.\n\n"
    "<b>Как это работает</b>\n"
    "Каждое утро платформа просматривает новости и присылает сюда найденные "
    "сделки — проект поста, черновик карточки и кнопки под ними.\n\n"
    "• <b>✅ Опубликовать</b> — сделка выйдет на сайт и в канал\n"
    "• <b>✋ Придержать</b> — останется ждать, пока вы не решите\n"
    "• <b>🗑 Выкинуть</b> — не наша тема, больше не покажем\n"
    "• Просто <b>ответьте своим текстом</b> — им заменится текст поста\n\n"
    "Если промолчать сутки — сделка выйдет как есть. Сомнительные новости "
    "(⚠️) без вашего слова не публикуются никогда.\n\n"
    "<b>Как поправить текст</b>\n"
    "Ответьте на нужное сообщение своим текстом:\n"
    "• ответ на 📣 <b>проект поста</b> — ваш текст станет текстом поста в канале;\n"
    "• ответ на 🗂 <b>карточку</b> — станет замечанием, платформа проверит его "
    "по источнику и внесет в карточку сама;\n"
    "• <b>вопрос</b> (со знаком «?» в конце) — бот ответит следующим сообщением, а "
    "карточка придержится и по молчанию не выйдет.\n\n"
    "<b>Как вернуться к отложенному</b>\n"
    "Нажмите кнопку ниже — карточки придут заново, каждая со своими кнопками. "
    "Решать можно прямо там, искать ничего не нужно.\n\n"
    "/queue — то же самое одним списком.\n"
    "/topic — внутри темы форума: закрепить за ней сообщения бота (кнопками)."
)


# Тексты для читателя в личке с ботом. Правило «Язык для людей» (CLAUDE.md):
# ни слова о модерации, черновиках и очередях — это консоль, ее видят двое.
READER_WELCOME = (
    "👋 <b>Это бот «Компаса»</b> — базы сделок на российском рынке.\n\n"
    "Сюда приходят уведомления о сделках, компаниях и отраслях, на которые "
    "вы подписались на сайте, и сводка за неделю.\n\n"
    "Чтобы подключить: войдите на сайт, откройте «Уведомления» в личном "
    "кабинете и нажмите «Подключить»."
)
READER_LINKED = (
    "✅ <b>Готово: Telegram подключен к вашему аккаунту «Компаса».</b>\n\n"
    "Сюда будут приходить уведомления о сделках, компаниях и отраслях, на "
    "которые вы подписаны, и сводка за неделю.\n\n"
    "Выключить — командой /stop или в личном кабинете."
)
READER_ALREADY_LINKED = (
    "Telegram подключен к вашему аккаунту «Компаса» — уведомления приходят "
    "сюда.\n\nВыключить — командой /stop или в личном кабинете."
)
READER_LINK_EXPIRED = (
    "Ссылка для подключения устарела. Откройте «Уведомления» в личном "
    "кабинете и нажмите «Подключить» еще раз."
)
READER_STOPPED = (
    "Уведомления в Telegram выключены. Включить снова — в личном кабинете, "
    "раздел «Уведомления»."
)
READER_NOT_LINKED_STOP = "Этот Telegram не подключен к аккаунту «Компаса» — выключать нечего."
READER_ONLY_NOTIFIES = (
    "Бот только присылает уведомления и на сообщения не отвечает. Вопрос или "
    "поправка — через «Написать нам» на сайте."
)
READER_CONSOLE_HINT = "\n\nВы участник консоли «Компаса»: инструкция модерации — /help."


def _reader_menu() -> dict:
    return {"inline_keyboard": [[{"text": "Открыть личный кабинет",
                                  "url": SITE_URL + "/#/account?tab=notifications"}]]}


def _reader_reply(db, name: str, chat_id, sender_id) -> str:
    """Ответ читателю в личке: /start, /stop, /help или просто текст."""
    linked = notification_service.linked_preferences(db, chat_id)
    if name == "stop":
        return READER_STOPPED if notification_service.stop_telegram(db, chat_id) else READER_NOT_LINKED_STOP
    if name in ("start", "help"):
        text = READER_ALREADY_LINKED if linked else READER_WELCOME
        return text + (READER_CONSOLE_HINT if _is_reviewer(sender_id) else "")
    return READER_ONLY_NOTIFIES
BATCH_LIMIT = 6          # Telegram пускает ~20 сообщений в минуту — не частим.


def _card_line(card: dict) -> str:
    """Одна карточка очереди словами: заголовок, стороны, сумма, источник."""
    parts = ["<b>%s</b>" % html_escape(str(card.get("title") or "без заголовка"))]
    who = []
    for label, key in (("Продавец", "seller"), ("Покупатель", "buyer_name"),
                       ("Предмет", "asset")):
        value = card.get(key)
        if value and str(value) not in ("—", "Не раскрыта"):
            who.append("%s: %s" % (label, html_escape(str(value))))
    if who:
        parts.append("\n".join(who))
    facts = []
    if card.get("sum"):
        facts.append("Сумма: %s" % html_escape(str(card["sum"])))
    if card.get("ind"):
        facts.append("Отрасль: %s" % html_escape(str(card["ind"])))
    if facts:
        parts.append(" · ".join(facts))
    # Раньше показывали только src[0] — карточка с 4 источниками выглядела
    # в консоли так же скудно, как с одним, и владелец 19 августа принял
    # хорошо обогащенную карточку («HeadHunter»/Happy Job) за почти пустую
    # именно по этой урезанной строке.
    src = [s for s in (card.get("src") or []) if len(s) > 1]
    if len(src) == 1:
        parts.append("Источник: %s" % html_escape(str(src[0][0])))
    elif src:
        parts.append("Источники (%d): %s" % (
            len(src), html_escape(", ".join(str(s[0]) for s in src))))
    # Ссылка на ПОЛНУЮ карточку до публикации. Без нее видно только выжимку из
    # четырех строк: владелец 10 августа не смог посмотреть карточку «Флит
    # Лизинг» именно потому, что ссылка до него не дошла — сообщение с ней
    # вообще не отправлялось.
    if card.get("id"):
        parts.append('<a href="%s/#/preview/%s">Открыть карточку целиком</a>'
                     % (SITE_URL, html_escape(str(card["id"]))))
    return "\n\n".join(parts)


def _answer_and_do(callback, work, text=None):
    """Ответить Telegram НЕМЕДЛЕННО, а отправку сообщений сделать в фоне.

    НАЙДЕНО ВЛАДЕЛЬЦЕМ 7 сентября 2026: он нажал «Что скоро выйдет», и
    сорок секунд не происходило ничего — «раньше было мгновенно».
    `getWebhookInfo` в ту же минуту показал `last_error_message: Connection
    timed out` и очередь недоставленных обновлений. Причина не в кнопке:
    обработчик делал ВСЮ работу внутри запроса вебхука — ответ на нажатие
    плюс заголовок очереди плюс по сообщению на каждую карточку, и каждый
    вызов Bot API с боевого хоста стоит до 12 секунд таймаута (связь
    Timeweb → api.telegram.org нестабильна, см. telegram_endpoint.py).
    Telegram столько не ждет: он считает вебхук недоступным, отваливается по
    таймауту и присылает то же нажатие снова — очередь растет, а человек
    видит бесконечное вращение.

    Правило: обработчик вебхука обязан вернуть ответ быстро. Все, что
    делает БОЛЬШЕ ОДНОГО вызова Bot API, уходит в фоновый поток; сам
    `answerCallbackQuery` остается в запросе — он один, и именно он гасит
    вращение кнопки.
    """
    if callback.get("id"):
        notification_service.tg_api("answerCallbackQuery",
                                    callback_query_id=callback["id"], text=text)
    threading.Thread(target=work, daemon=True).start()


def _answered_decisions() -> dict:
    """{id: вердикт} решений, которые уже нажаты, но рутиной еще не применены
    (`consumed=False`). Консоль читает очередь из файлов, которые приезжают из
    git, а решение живет в этой базе до ближайшей публикации — в этом окне
    (до часа, а ночью до утра) сырье и карточки выглядели нерешенными:
    владелец 28 октября 2026 ответил на 6 сомнительных, нажал /start — и
    увидел те же 13 снова. Открывается своя сессия: вызов идет из фонового
    потока, где сессии запроса уже нет."""
    session = get_session()
    try:
        rows = session.scalars(select(ModerationDecision)
                               .where(ModerationDecision.consumed.is_(False))
                               .order_by(ModerationDecision.created_at)).all()
        return {str(r.deal_id): r.verdict for r in rows}
    except Exception:                                      # noqa: BLE001 — база недоступна: показываем как есть
        return {}
    finally:
        session.close()


def _card_state(card: dict) -> str:
    """Чего ждет карточка — одно место на весь код: pipeline/ingest/readiness.py
    (held, doubted, unreviewed, accepted_unread, unaccepted, unread2,
    ready_unsent, shown)."""
    from pipeline.ingest import readiness
    return readiness.state(card)


def _send_queue_batch(chat_id, kind: str, thread=None) -> int:
    """Прислать карточки очереди — каждую своим сообщением с кнопками.

    `kind`: held   — придержанные (можно опубликовать или выкинуть);
            soon   — прочитанные, выйдут по молчанию (можно придержать/выкинуть);
            unread — НЕ прочитанные против источника — по молчанию не выйдут
                     никогда, сколько бы часов ни прошло (см. approve.py,
                     `plan_actions`: непрочитанная карточка не публикуется
                     тишиной — это защита от каркасных дефектов черновика,
                     а не забытый таймер). Раньше "soon" считался как «все,
                     что не придержано» — и такая карточка час за часом
                     отчитывалась как «выйдет сама», хотя не могла выйти,
                     пока ее кто-то не прочитает: владелец 18 августа поймал
                     это на «Ленобласти»/«М.видео», зависших без единого
                     движения больше суток при одинаковом каждый час отчете;
            raw    — сомнительные новости, которые ворота не пропустили.
    """
    if kind == "raw":
        state = core._read_json("data/inbox/moderation_state.json", {})
        decided = set(state.get("decided_raw") or {})
        hold_dir = os.path.join(BASE_DIR, "data", "inbox", "hold")
        names = sorted(n for n in os.listdir(hold_dir)
                       if n.endswith(".json")) if os.path.isdir(hold_dir) else []
        drafts = (core._read_json(os.path.join("data", "inbox", "hold", names[-1]), {})
                  .get("drafts") if names else None) or []
        answered = _answered_decisions()
        all_items = [d for d in drafts if str(d.get("draft_id")) not in decided]
        # Нажатое, но еще не примененное решение — не повод показывать то же
        # сырье снова (28 октября 2026: «я вроде на все ответил, почему 13?»).
        items = [d for d in all_items if str(d.get("draft_id")) not in answered]
        already = len(all_items) - len(items)
        # ПРОЧИТАННАЯ И ОТВЕРГНУТАЯ КАРТОЧКА — ТОЖЕ СОМНИТЕЛЬНАЯ (21 сентября
        # 2026, вопрос владельца: «а разве она не должна оказаться в
        # сомнительных тогда?»). Приемка (accept_card.py) читает источник и у
        # части карточек пишет вердикт «это не сделка, рекомендую выкинуть» —
        # такая карточка попадала в блок «ждут прочтения», хотя ждать ей
        # нечего: ее уже прочитали. Показываем ее там, где человек решает
        # судьбу сомнительного, — рядом с сырьем, которое не прошло ворота.
        doubted = [c for c in (core._read_json("static/data/pending.json", {}).get("cards") or [])
                   if _card_state(c) == "doubted"]
        already += sum(1 for c in doubted if str(c.get("id")) in answered)
        items = items + [c for c in doubted if str(c.get("id")) not in answered]
        head = ("⚠️ <b>Сомнительные: %d</b>\n"
                "Новости, которые не прошли ворота, и карточки, которые прочитали "
                "и не приняли. Без вашего слова не публикуются никогда."
                % len(items))
        if already:
            head += ("\n\nЕще %d вы уже решили — решения записаны и применятся при "
                     "ближайшей публикации (в течение часа днем, утром — если ночью)." % already)
    else:
        answered = _answered_decisions()
        pending = core._read_json("static/data/pending.json", {}).get("cards") or []
        not_held = [c for c in pending if not c.get("held")]
        if kind == "held":
            items = [c for c in pending if c.get("held")]
            head = ("✋ <b>Вы придержали: %d</b>\nВыйдут только после «Опубликовать»."
                    % len(items))
        elif kind == "unread":
            # Приемка (11 сентября 2026): прочитанная, но не принятая карточка
            # по молчанию тоже не выходит (approve.plan_actions) — и обещать
            # «выйдет сама» ей нельзя.
            # Карточки с вердиктом приемки «не пропущена» ушли в блок
            # «Сомнительные» — им нужно решение, а не чтение (см. выше).
            # Принятая, но без второго чтения, тоже сюда: до 28 октября 2026
            # такая карточка (ЛСР, g0f479af0) не попадала ни в один блок.
            # Состояние — readiness.state: все, что ждет приток (чтение,
            # приемку, второе чтение); не пропущенные приемкой — в «Сомнительных».
            items = [c for c in not_held
                     if _card_state(c) in ("unreviewed", "accepted_unread", "unaccepted", "stale", "unread2")]
            head = ("📖 <b>Ждут прочтения, второго чтения или приемки: %d</b>\nПока карточку не сверят с "
                    "источником и не примут целиком — молчание ее не публикует, сама не выйдет."
                    % len(items))
        else:  # soon
            # Только показанные в консоли: approve.plan_actions публикует
            # молчанием лишь карточку с `draft_sent`. 19 октября 2026 две
            # принятые, но не отправленные карточки («Экспанта», VEON) пришли
            # владельцу впервые именно отсюда — как «выйдут сами», хотя сами
            # выйти не могли и на подтверждение не приходили.
            items = [c for c in not_held if _card_state(c) == "shown"]
            head = ("⏳ <b>Выйдут сами: %d</b>\nЕсли ничего не нажимать — опубликуются "
                    "в течение суток." % len(items))

    thread_kw = {"message_thread_id": thread} if thread else {}
    notification_service.tg_api("sendMessage", chat_id=chat_id, text=head,
                                parse_mode="HTML", disable_web_page_preview=True, **thread_kw)
    if not items:
        notification_service.tg_api("sendMessage", chat_id=chat_id,
                                    text="Сейчас пусто — решать нечего.", **thread_kw)
        return 0

    shown = items[:BATCH_LIMIT]
    for item in shown:
        # В блоке «Сомнительные» лежат две разные вещи: сырье (у него
        # `draft_id` и кнопки «это сделка / не сделка») и уже собранная
        # карточка, которую приемка не пропустила (у нее `id` и обычные
        # кнопки карточки). Вид сообщения выбирается по самой записи, а не
        # по имени блока.
        is_draft = bool(item.get("draft_id"))
        ident = str(item.get("draft_id") if is_draft else item.get("id"))
        if is_draft:
            text = "⚠️ [сырье %s]\n\n%s" % (ident, _card_line(item))
            why = item.get("hold_reasons") or []
            if why:
                text += "\n\nПочему не пропустили: %s" % html_escape("; ".join(why)[:200])
            keys = [[{"text": "✅ Это сделка", "callback_data": "mod:%s:take" % ident},
                     {"text": "🗑 Не сделка", "callback_data": "mod:%s:drop" % ident}]]
        else:
            # У /queue были СВОИ, урезанные до двух кнопки — набор отличался
            # от исходного сообщения при первом черновике (там всегда четыре:
            # Опубликовать/Придержать/Изменить/Выкинуть). Логика урезания
            # («держим только то, что нужно В ЭТОМ состоянии») выглядела
            # обоснованной для «soon» (зачем публиковать то, что и так выйдет
            # само?), но реально отнимала действие: владелец 10 августа искал
            # кнопку «Опубликовать сейчас» в очереди и не нашел. Теперь везде
            # одинаковый полный набор, как в исходном сообщении, — карточка
            # выглядит и работает одинаково независимо от того, пришла она
            # только что или показана повторно через /queue.
            # ЧЕСТНАЯ ШАПКА У НЕПРОВЕРЕННОЙ КАРТОЧКИ (21 сентября 2026).
            # Владелец открыл /queue и увидел карточку «Корпорация
            # робототехники»: заголовок — обрезанное предложение из новости,
            # покупатель со скобкой «[входит в АФК «Система»]», отрасль
            # «Недвижимость» у складских роботов. Выглядело как «мусор
            # пропустили», хотя ворота как раз сработали: карточка пришла
            # кнопкой «это сделка — в работу», ее еще никто не читал, и сама
            # она выйти не может (approve.plan_actions). Не сработала ТОЛЬКО
            # подпись: сообщение выглядело в точности как готовая карточка.
            # Кнопки при этом НЕ урезаем — ровно за это владелец жаловался
            # 10 августа («искал „Опубликовать сейчас" и не нашел»): право
            # выпустить остается, пропадает лишь ложное впечатление, что
            # поля кто-то проверял. Если приемка прочитала источник и не
            # пропустила карточку, ее вывод идет первой строкой — это он
            # отвечает на вопрос «выкидываем?», а не машинные поля.
            unread_card = False
            if not (item.get("reviewed") and item.get("accepted")):
                why = str(item.get("hold_reason") or "").strip()
                if why:
                    note = ("📖 <b>Прочитали источник — карточку не приняли.</b>\n%s"
                            % html_escape(why[:700]))
                else:
                    unread_card = True
                    note = ("📖 <b>Карточку еще не сверили с источником.</b> Поля ниже "
                            "собрал разбор новости, их никто не проверял глазами. "
                            "Приток прочитает статью и перепишет карточку в ближайший час; "
                            "кнопка «Опубликовать» появится после этого.")
                text = "🗂 [карточка %s]\n\n%s\n\n%s" % (ident, note, _card_line(item))
            elif _card_state(item) == "unread2":
                unread_card = True
                note = ("📖 <b>Карточка прочитана и принята, ждет второго чтения.</b> "
                        "Приток перечитает ее в ближайший час и пришлет на подтверждение.")
                text = "🗂 [карточка %s]\n\n%s\n\n%s" % (ident, note, _card_line(item))
            else:
                text = "🗂 [карточка %s]\n\n%s" % (ident, _card_line(item))
            if unread_card and not item.get("held"):
                # НЕПРОЧИТАННУЮ КАРТОЧКУ НЕЛЬЗЯ ВЫПУСТИТЬ КНОПКОЙ (28 октября
                # 2026): явное «опубликовать» сильнее защиты от каркасных
                # дефектов (approve.plan_actions), и владелец увидел в очереди
                # «Артмузу» с покупателем «Миллиардер Гомон» и кнопкой
                # «Опубликовать» под ней. Нажатие выпустило бы ее как есть.
                # Остаются «Изменить» и «Выкинуть»; «Опубликовать» и
                # «Придержать» приходят с прочитанной карточкой. Придержанную
                # владелец уже держит сам — у нее полный набор (урок 10 августа).
                keys = [[{"text": "✏️ Изменить", "callback_data": "mod:%s:edit" % ident},
                         {"text": "🗑 Выкинуть", "callback_data": "mod:%s:discard" % ident}]]
            else:
                keys = [[{"text": "✅ Опубликовать", "callback_data": "mod:%s:ok" % ident},
                         {"text": "✋ Придержать", "callback_data": "mod:%s:hold" % ident}],
                        [{"text": "✏️ Изменить", "callback_data": "mod:%s:edit" % ident},
                         {"text": "🗑 Выкинуть", "callback_data": "mod:%s:discard" % ident}]]
            if ident in answered:
                # Решение уже нажато и ждет рутину — кнопки второй раз не нужны.
                text += "\n\n%s — ваше решение записано, применится при ближайшей публикации." \
                        % html_escape(_VERDICT_LABEL.get(answered[ident], answered[ident]))
                keys = None
        notification_service.tg_api(
            "sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
            disable_web_page_preview=True,
            **({"reply_markup": {"inline_keyboard": keys}} if keys else {}), **thread_kw)

    if len(items) > len(shown):
        # Умолчавший предел читается как «это все» — называем его вслух.
        notification_service.tg_api(
            "sendMessage", chat_id=chat_id,
            text="Показаны первые %d из %d — нажмите кнопку еще раз после решений."
                 % (len(shown), len(items)))
    return len(shown)


def _bot_menu() -> dict:
    """Меню под /start. Раньше команда отвечала стеной текста, и было
    непонятно, что вообще можно сделать, — кнопки показывают это сразу."""
    return {"inline_keyboard": [
        [{"text": "⏳ Что скоро выйдет", "callback_data": "show:soon"},
         {"text": "✋ Что придержано", "callback_data": "show:held"}],
        [{"text": "📖 Что ждет прочтения", "callback_data": "show:unread"},
         {"text": "⚠️ Сомнительные новости", "callback_data": "show:raw"}],
        [{"text": "📊 Как дела у платформы", "callback_data": "menu:stats"}],
        # То же, что /topic, но без команды наизусть: нажали в теме — бот
        # предложит, какой вид сообщений в нее складывать (17 октября 2026).
        [{"text": "📌 Назначить эту тему", "callback_data": "menu:topic"}],
    ]}


def _stats_report() -> str:
    """Короткая сводка о платформе — человеческим языком, без наших терминов."""
    n = _ops_numbers()
    return (
        "📊 <b>Как дела у платформы</b>\n\n"
        "🗂 Сделок на сайте: <b>%(deals)d</b>\n"
        "🏢 Профилей компаний: <b>%(companies)d</b>\n"
        "🆕 Добавлено за неделю: <b>%(added_week)d</b>\n"
        "📣 Опубликовано в канале: <b>%(published)d</b>\n\n"
        "⏳ Выйдут сами в течение суток: <b>%(queue_soon)d</b>\n"
        "📖 Ждут прочтения или приемки (сами не выйдут): <b>%(queue_unread)d</b>\n"
        "✋ Вы придержали: <b>%(queue_held)d</b>\n\n"
        "🔧 <b>В работе</b>\n"
        "Не дополнены по источнику: <b>%(unread)d</b> из %(from_ingest)d\n"
        "Карточек 2026 года с бедным разбором: <b>%(thin_2026)d</b>"
    ) % n


def _queue_report() -> str:
    """Сводка по трем типам сообщений консоли — теми же значками, что и они.

    🗂/📣 — карточки предпросмотра (pending.json): ждут кнопки, по молчанию
    сутки уходят как есть. ⚠️ — сырье, которое ворота не пропустили: решается
    только кнопкой под своим сообщением, по молчанию не публикуется никогда.
    """
    pending = core._read_json("static/data/pending.json", {}).get("cards") or []
    held = [c for c in pending if c.get("held")]
    active = [c for c in pending if not c.get("held")]
    lines = ["🗂📣 Карточки и посты на проверке: %d" % len(active)]
    for card in active[:8]:
        lines.append("• %s" % str(card.get("title") or "")[:90])
    if len(active) > 8:
        lines.append("… и еще %d" % (len(active) - 8))
    if held:
        lines.append("✋ Придержано вами: %d" % len(held))
        for card in held[:5]:
            lines.append("• %s" % str(card.get("title") or "")[:90])

    state = core._read_json("data/inbox/moderation_state.json", {})
    decided = set((state.get("decided_raw") or {}))
    hold_dir = os.path.join(BASE_DIR, "data", "inbox", "hold")
    names = sorted(n for n in os.listdir(hold_dir) if n.endswith(".json")) \
        if os.path.isdir(hold_dir) else []
    drafts = (core._read_json(os.path.join("data", "inbox", "hold", names[-1]), {}).get("drafts")
              if names else None) or []
    answered = _answered_decisions()
    drafts = [d for d in drafts if str(d.get("draft_id")) not in decided]
    already = sum(1 for d in drafts if str(d.get("draft_id")) in answered)
    drafts = [d for d in drafts if str(d.get("draft_id")) not in answered]
    if already:
        lines.append("\n✅ Вы уже решили: %d — применится при ближайшей публикации." % already)
    if drafts:
        reasons = {}
        for draft in drafts:
            for why in (draft.get("hold_reasons") or ["причина не записана"]):
                reasons[why] = reasons.get(why, 0) + 1
        lines.append("\n⚠️ Сомнительные, ждут вашего слова: %d" % len(drafts))
        for why, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:5]:
            lines.append("• %d — %s" % (count, why[:80]))
        lines.append("Каждая приходит отдельным сообщением с кнопками "
                     "«это сделка» / «не сделка».")
    if not active and not held and not drafts:
        lines = ["Очередь пуста — все решено. Новое приедет с утренним прогоном притока."]
    return "\n".join(lines)


def _bot_command(name: str, sender_id) -> str | None:
    if name in ("start", "help"):
        # Справка консоли — только своим; посторонний, добавивший бота в
        # свою группу, получает читательское приветствие.
        return BOT_HELP if _is_reviewer(sender_id) else READER_WELCOME
    if name in ("queue", "ochered"):
        # Состав очереди — внутренняя кухня платформы, отвечаем только своим.
        if not _is_reviewer(sender_id):
            return "Эта команда доступна только владельцу и партнеру."
        return _queue_report()
    return None


_VERDICT_LABEL = {
    "approve": "✅ Карточка одобрена", "hold": "✋ Придержана",
    "discard": "🗑 Выкинута — не выйдет ни на сайт, ни в канал",
    "post_yes": "📣 Пост одобрен", "post_no": "🔕 Решено: без поста",
    "take": "✅ Признана сделкой — уйдет в работу", "drop": "🗑 Отброшена как не-сделка",
    "acc_ok": "✅ Доступ открыт — человек может войти",
    "acc_no": "🗑 Отклонено — доступ не открыт",
    "claim_ok": "✅ Подтверждено — карточка подключена к кабинету",
    "claim_no": "🗑 Отклонено — карточка не подключена",
}


# Каким каналам уже сказали их числовой адрес — чтобы не повторяться на
# каждом посте. Память живет в процессе: перезапуск сайта бывает только при
# сборке, и повторить сообщение раз в несколько дней не страшно.
_CHANNEL_IDS_TOLD: set[str] = set()


def _is_realty_channel_title(title) -> bool:
    return "недвиж" in str(title or "").lower()


_CHAT_TITLES: dict[str, str] = {}


def _chat_title(chat_id) -> str:
    """Название чата у самого Telegram (один запрос на адрес за жизнь
    процесса); сеть молчит — пустая строка."""
    chat_id = str(chat_id or "").strip()
    if not chat_id or not os.environ.get("TELEGRAM_BOT_TOKEN", "").strip():
        return ""
    if chat_id not in _CHAT_TITLES:
        answer = notification_service.tg_api("getChat", chat_id=chat_id) or {}
        if not answer.get("ok"):
            return ""
        _CHAT_TITLES[chat_id] = str((answer.get("result") or {}).get("title") or "")
    return _CHAT_TITLES[chat_id]


def _sort_channel_slots(db) -> None:
    """Канал недвижимости, попавший в ячейку основного, — в свою ячейку.
    Так 2 октября 2026 и вышло (см. REALTY_CHANNEL_SETTING): ячейка основного
    держала адрес канала недвижимости, пока не исправили."""
    main_row = db.get(AppSetting, CHANNEL_SETTING)
    if not (main_row and main_row.value):
        return
    realty_row = db.get(AppSetting, REALTY_CHANNEL_SETTING)
    if realty_row and realty_row.value and realty_row.value != main_row.value:
        return
    if (realty_row and realty_row.value == main_row.value) \
            or _is_realty_channel_title(_chat_title(main_row.value)):
        value = main_row.value
        db.delete(main_row)
        db.commit()
        _remember_setting(db, REALTY_CHANNEL_SETTING, value)


def _remember_setting(db, key: str, value: str) -> None:
    """Запомнить настройку, которую сайт узнал сам. Сбой записи не должен
    ронять вебхук: сообщение в консоль уже ушло, а адрес Telegram назовет
    снова при следующем посте канала."""
    try:
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value))
        elif row.value != value:
            row.value = value
        else:
            return
        db.commit()
    except SQLAlchemyError as exc:  # noqa: BLE001
        db.rollback()
        logger.error("настройку %s записать не удалось: %s", key, exc)


def _learn_console_topics(payload, db=None) -> bool:
    """Запомнить номер темы форума, если Telegram его показал.

    Возвращает True, если апдейт был целиком служебным про тему (создание,
    переименование) — такой обрабатывать дальше нечего."""
    message = payload.message or {}
    created = message.get("forum_topic_created")
    edited = message.get("forum_topic_edited")
    known = {_topic_slug(v): k for k, v in CONSOLE_TOPIC_NAMES.items()}
    if created or edited:
        name = (created or edited or {}).get("name") or ""
        thread_id = message.get("message_thread_id") or message.get("message_id")
        kind = known.get(_topic_slug(name))
        if db is not None and kind and thread_id:
            _remember_setting(db, "telegram_topic:%s" % _topic_slug(name), str(thread_id))
            _ack_console_topic(message, kind, thread_id)
        return True
    # Бутстрап для тем, заведенных до того, как бот начал слушать служебные
    # сообщения: человек один раз печатает название темы внутри нее. Сверка
    # по слагу (`_topic_slug`), а не строка в строку: первая версия требовала
    # точного совпадения (`text == name`), и лишний пробел от автокоррекции
    # клиента или другой регистр молча не засчитывались — то же слепое пятно,
    # что и с падежами/окончаниями в других частях кода. И бот ОТВЕЧАЕТ в ту
    # же тему, что запомнил: молчание при успехе неотличимо от молчания при
    # неудаче — 5 сентября 2026 владелец напечатал названия, не увидел ничего
    # и решил, что темы не работают и нужны две отдельные группы.
    text = (message.get("text") or "").strip()
    kind = known.get(_topic_slug(text)) if text else None
    if db is None or not kind:
        return False
    # Право настраивать консоль — у тех же, у кого право решать (по
    # отправителю, не по чату — см. _is_reviewer).
    if not _is_reviewer((message.get("from") or {}).get("id")):
        return False
    thread_id = message.get("message_thread_id")
    if thread_id:
        _remember_setting(db, "telegram_topic:%s" % _topic_slug(text), str(thread_id))
    _ack_console_topic(message, kind, thread_id)
    return True


CONSOLE_TOPIC_PURPOSE = {
    "decision": "посты, карточки и сомнительные новости — все, где вы решаете, выйдет это или нет",
    "update": "отчеты о каждом прогоне рутин",
    "info": "заметки, отзывы и служебные сообщения",
    "user_notes": "уточнения и поправки, которые посетители сайта оставляют с карточек сделок и из футера",
    "admin": "служебные очереди: заявки на вход, вопросы про ИНН и однофамильцев, пары возможных дублей",
    "claude": ("ваши сообщения агенту Claude — задачи, правки, вопросы; ответы приходят "
               "сюда же"),
}


def _ack_console_topic(message: dict, kind: str, thread_id) -> None:
    """Ответить в ту же тему, что ее номер запомнили, — или объяснить, почему
    нет. Общая лента форума (General) номера темы не несет вовсе: сообщение
    без `message_thread_id` и так уходит туда, запоминать нечего — но человеку
    об этом надо сказать, иначе он повторяет попытку и ждет."""
    chat_id = (message.get("chat") or {}).get("id")
    if not chat_id:
        return
    name = CONSOLE_TOPIC_NAMES[kind]
    if thread_id:
        text = "Запомнил: это тема «%s». Сюда теперь пойдут %s." % (name, CONSOLE_TOPIC_PURPOSE[kind])
    elif kind == "info":
        text = ("Понял: «%s» — это общая лента группы, без своей темы. Сюда и так идут %s — "
                "запоминать ничего не нужно." % (name, CONSOLE_TOPIC_PURPOSE[kind]))
    else:
        text = ("«%s» написано в общей ленте, а не внутри темы — так номер темы не узнать. "
                "Откройте саму тему и напишите ее название там." % name)
    notification_service.tg_api("sendMessage", chat_id=str(chat_id), text=text,
                                disable_web_page_preview=True,
                                **({"message_thread_id": thread_id} if thread_id else {}))


def _offer_topic_binding(message: dict, chat_id, sender_id) -> None:
    """Ответ на /topic: кнопки с названиями тем внутри той темы, где команду
    дали. Нажатие (см. ветку `topic:` в вебхуке) закрепляет номер темы за
    видом сообщений. В общей ленте форума номера темы нет — так и говорим."""
    if not _is_reviewer(sender_id):
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id),
            text="Настраивать темы могут только владелец и партнер.",
            disable_web_page_preview=True, **_thread_kwargs(message))
        return
    thread_id = message.get("message_thread_id")
    if not thread_id:
        # Главная тема форума (в Telegram она всегда со значком #, ее можно
        # переименовать — у владельца это «Общая информация») номера НЕ имеет:
        # сообщение без темы приходит именно в нее. Прежний ответ говорил
        # «это общая лента группы», и человек, стоя ВНУТРИ темы, читал его
        # как «вы не в теме» и давал команду снова (6 сентября 2026, дважды).
        forum = bool((message.get("chat") or {}).get("is_forum"))
        notification_service.tg_api(
            "sendMessage", chat_id=str(chat_id), disable_web_page_preview=True,
            text=("Это главная тема группы — у нее в Telegram нет своего номера, и "
                  "закреплять ее не нужно: все, для чего не назначена отдельная тема, "
                  "приходит сюда само. Заметки и служебные сообщения уже идут именно "
                  "в нее."
                  if forum else
                  "Это обычная группа без тем: сюда и так идет все. Темы включаются "
                  "в настройках группы, после этого дайте /topic внутри нужной темы."))
        return
    keyboard = {"inline_keyboard": [[{"text": name, "callback_data": "topic:%s" % kind}]
                                    for kind, name in CONSOLE_TOPIC_NAMES.items()]}
    notification_service.tg_api(
        "sendMessage", chat_id=str(chat_id), message_thread_id=thread_id,
        text="Что должно приходить в эту тему? Нажмите название — бот запомнит ее номер.",
        reply_markup=keyboard, disable_web_page_preview=True)



# ТЕМА «КЛОД» (17 октября 2026). Владелец и партнер пишут в эту тему
# сообщения агенту Claude; сайт складывает их в таблицу claude_messages, рутина
# «тема Клод» забирает их по токену (/api/claude/inbox), делает работу и
# отвечает в ту же тему (pipeline/claude_topic.py). Бот без прав админа в
# режиме приватности видит здесь только упоминания @бота и ответы на свои
# сообщения; админом — все. Код ничего сверх пришедшего не требует.
CLAUDE_ACK_TEXT = "Принял. Отвечу здесь, обычно в течение часа."
CLAUDE_ACK_QUIET_SECONDS = 60
_BOT_MENTION = re.compile(r"^\s*@\w+bot\b[\s,:]*", re.I)


def _claude_topic_message(message: dict, db) -> bool:
    """Сохранить сообщение из темы «Клод» и коротко подтвердить прием.

    True — сообщение принято (дальше его разбирать не нужно). Берем только:
    группу-консоль, тему, закрепленную как «claude», отправителя с правом
    (_is_reviewer), не команду. Подтверждение — реплаем, и только первому из
    серии: если за последнюю минуту в теме уже было принятое сообщение, молчим."""
    if db is None or not message:
        return False
    chat = message.get("chat") or {}
    if str(chat.get("type") or "") not in ("group", "supergroup"):
        return False
    thread = message.get("message_thread_id")
    if not thread:
        return False
    bound = db.get(AppSetting, "telegram_topic:%s" % _topic_slug(CONSOLE_TOPIC_NAMES["claude"]))
    if not (bound and str(bound.value) == str(thread)):
        return False
    group = db.get(AppSetting, REVIEW_GROUP_SETTING)
    chat_id = chat.get("id")
    if group and group.value and str(group.value) != str(chat_id):
        return False
    sender = message.get("from") or {}
    if not _is_reviewer(sender.get("id")):
        return False
    raw = str(message.get("text") or message.get("caption") or "")
    if raw.strip().startswith("/"):
        return False
    body = _BOT_MENTION.sub("", raw).strip()
    photos = message.get("photo") or []
    photo_id = None
    if photos:
        best = max(photos, key=lambda p: (p.get("file_size") or 0,
                                          (p.get("width") or 0) * (p.get("height") or 0)))
        photo_id = best.get("file_id")
    document = message.get("document") or {}
    if not (body or photo_id or document.get("file_id")):
        return False
    reply = message.get("reply_to_message") or {}
    reply_text = str(reply.get("text") or reply.get("caption") or "").strip() or None
    name = " ".join(x for x in (sender.get("first_name"), sender.get("last_name")) if x) \
        or sender.get("username") or None
    now = datetime.now(timezone.utc)
    recent = db.scalars(select(ClaudeMessage).where(
        ClaudeMessage.chat_id == str(chat_id), ClaudeMessage.thread_id == int(thread))
        .order_by(ClaudeMessage.id.desc()).limit(1)).first()
    quiet = False
    if recent is not None and recent.created_at is not None:
        last = recent.created_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        quiet = (now - last).total_seconds() < CLAUDE_ACK_QUIET_SECONDS
    db.add(ClaudeMessage(
        chat_id=str(chat_id), thread_id=int(thread), message_id=int(message.get("message_id") or 0),
        from_id=str(sender.get("id")), from_name=name, text=body or None,
        photo_file_id=photo_id, document_file_id=document.get("file_id"),
        document_name=document.get("file_name"), reply_to_text=reply_text,
        consumed=False, created_at=now))
    db.commit()
    if not quiet:
        kw = {"message_thread_id": thread}
        if message.get("message_id"):
            kw["reply_to_message_id"] = message["message_id"]
        notification_service.tg_api("sendMessage", chat_id=str(chat_id), text=CLAUDE_ACK_TEXT,
                                    disable_web_page_preview=True, **kw)
    return True


UNDO_WORDS = re.compile(r"^(?:отмена|отменить|отмени|отменяю|отбой|стоп|cancel)[.!]*$", re.I)
QUESTION_START = re.compile(
    r"^(?:что|как|почему|зачем|кто|где|когда|сколько|какой|какая|какое|какие|каков\w*|чем|откуда"
    r"|куда|разве|неужели|а\s|можно|нужно\s+ли|это\s|ты\s|вы\s)", re.I)



def _is_question(text: str) -> bool:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return bool(t) and (t.endswith("?") or bool(QUESTION_START.match(t) and len(t) < 200 and "?" in t))


CONSOLE_QA_SYSTEM = (
    "Ты помогаешь владельцу «Компаса» проверить карточку сделки перед публикацией в "
    "Telegram-канале. Отвечай по-русски, коротко — два-пять предложений, как коллега в "
    "переписке. Опирайся на карточку и на выдачу поиска ниже; факт из поиска — с "
    "названием источника в скобках. Если ответа нет ни в карточке, ни в выдаче, так и "
    "скажи. Числа и имена не выдумывай. Без разметки markdown.")


def _console_card(deal_id: str) -> dict:
    """Карточка из очереди консоли или из базы — то, о чем спросили."""
    for card in (core._read_json("static/data/pending.json", {}).get("cards") or []):
        if card.get("id") == deal_id:
            return card
    return get_deal(deal_id) or {}


def _console_answer(deal_id: str, question: str) -> str | None:
    """Ответ на вопрос из консоли по карточке и свежей выдаче поиска."""
    if not _yandex_ready():
        return None
    card = _console_card(deal_id)
    keep = {k: card.get(k) for k in ("title", "date", "status", "type", "buyer_name", "seller",
                                      "asset", "sum", "eco", "law", "src") if card.get(k)}
    block = ""
    try:
        query = ("%s %s" % (question, str(card.get("title") or "")[:90])).strip()
        block = build_search_block(yandex_search(query, config=SearchConfig.from_env(), client=core._http))
    except Exception as exc:                                  # noqa: BLE001
        logger.info("консоль: поиск для ответа не удался (%s)", exc)
    user_msg = "Вопрос: %s\n\nКарточка:\n%s\n\n%s" % (
        question, json.dumps(keep, ensure_ascii=False)[:6000], block)
    try:
        text = assistant.call_llm(CONSOLE_QA_SYSTEM, user_msg, max_tokens=700, deadline=time.monotonic() + 45)
    except Exception as exc:                                  # noqa: BLE001
        logger.warning("консоль: модель не ответила (%s)", exc)
        return None
    text = re.sub(r"\*\*|__|^#+\s*", "", str(text or ""), flags=re.M).strip()
    return text[:3500] or None


def _answer_console_question(deal_id: str, question: str, chat_id, thread: dict) -> None:
    answer = _console_answer(deal_id, question)
    notification_service.tg_api(
        "sendMessage", chat_id=str(chat_id),
        text=(("Ответ: " + answer) if answer else
              "Сразу ответить не получилось — ответ подготовит рутина притока в ближайший прогон."),
        disable_web_page_preview=True, **thread)

def _not_a_post_text(text: str, original) -> bool:
    """Ответ на проект поста — вопрос или реплика, а не новый текст поста.
    Вопросительный знак в конце, вопросительное слово в начале короткой
    фразы или ответ в разы короче самого проекта поста."""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if not t:
        return True
    if t.endswith("?") or (QUESTION_START.match(t) and len(t) < 200):
        return True
    orig = re.sub(r"\s+", " ", str(original or "")).strip()
    return len(t) < 80 and len(orig) > 3 * len(t)

def _thread_kwargs(source: dict | None) -> dict:
    """kwargs с message_thread_id, если сообщение стоит внутри темы форума —
    иначе пустой dict. Ответ обязан оставаться там же, где его ждут: Telegram
    НЕ выводит тему сам по `reply_to_message_id`, это нужно указать явно."""
    tid = (source or {}).get("message_thread_id")
    return {"message_thread_id": tid} if tid else {}


def _learn_review_group(payload, db=None) -> None:
    """Запомнить актуальный id группы-консоли — той же болезни, что у адреса
    канала, только источник другой: не смена имени, а то, что Telegram САМ
    меняет id при переходе группы в супергруппу (см. `core._review_chat_ids`).
    Источник истины — любое сообщение от владельца/партнера ИЗ группы: его
    `chat.id` — единственно верный, актуальный номер прямо сейчас. Ничего не
    возвращает и не мешает дальнейшей обработке того же апдейта.

    ВТОРОЙ ИСТОЧНИК — добавление бота в группу (`my_chat_member`), и он
    важнее первого. У бота включен режим приватности
    (`can_read_all_group_messages: false`), поэтому обычный текст в группе
    до него НЕ доходит — только команды, ответы на его собственные
    сообщения и нажатия кнопок. А своих сообщений в новой группе у него нет
    и быть не может, пока он не знает ее номера: круг замкнут, и «ждать,
    пока владелец что-нибудь напишет» — тупик. 6 сентября 2026 консоль
    молчала ровно так: бот вообще не состоял в новом чате
    (`getChatMember` → status: left), а рутина час за часом отчитывалась,
    что ждет сообщения. Смена прав бота приходит ВСЕГДА, независимо от
    приватности, — значит, достаточно добавить бота в группу, и адрес
    запомнится сам."""
    if db is None:
        return
    # Канал публикации адресом консоли стать не может НИКОГДА — даже если бота
    # добавят туда администратором и Telegram пришлет про это `my_chat_member`
    # (см. _channel_chat_ids: 7 сентября 2026 отчет рутины ушел подписчикам).
    forbidden = _channel_chat_ids(db)
    member = payload.my_chat_member or {}
    if member:
        chat = member.get("chat") or {}
        status = str((member.get("new_chat_member") or {}).get("status") or "")
        chat_id = str(chat.get("id") or "")
        # Учимся только на ВХОДЕ бота в чат: «left»/«kicked» — это выход, и
        # запоминать по нему адрес значило бы записать чат, где бот уже никто.
        if chat_id and str(chat.get("type") or "") in ("group", "supergroup") \
                and status in ("member", "administrator", "creator") \
                and _is_reviewer((member.get("from") or {}).get("id")):
            known = db.get(AppSetting, REVIEW_GROUP_SETTING)
            if not (known and known.value == chat_id):
                if chat_id not in forbidden:
                    _remember_setting(db, REVIEW_GROUP_SETTING, chat_id)
                _greet_console_group(db, chat_id, chat.get("title"))
        return
    message = payload.message or (payload.callback_query or {}).get("message") or {}
    chat = message.get("chat") or {}
    if str(chat.get("type") or "") not in ("group", "supergroup"):
        return
    sender_id = ((payload.message or {}).get("from") or {}).get("id") \
        or ((payload.callback_query or {}).get("from") or {}).get("id")
    if not _is_reviewer(sender_id):
        return
    chat_id = str(chat.get("id") or "")
    if chat_id and chat_id not in forbidden:
        _remember_setting(db, REVIEW_GROUP_SETTING, chat_id)


def _greet_console_group(db, chat_id: str, title: str | None) -> None:
    """Сказать в группе, что консоль подключена. Человек, добавивший бота,
    иначе не отличит «работает» от «молчит»: тот же урок, что у настройки
    тем 5 сентября 2026 — у действия, которое человек делает руками, обязан
    быть видимый ответ."""
    try:
        notification_service.tg_api(
            "sendMessage", chat_id=chat_id, disable_web_page_preview=True,
            text=("\U0001F4CC Консоль «%s» подключена — отчеты и карточки на решение "
                  "будут приходить сюда.\n\nЕсли в группе включены темы, откройте "
                  "нужную и отправьте там /topic — бот покажет кнопки, какой вид "
                  "сообщений в нее складывать." ) % (title or "без названия"))
    except Exception as exc:  # noqa: BLE001 — адрес уже сохранен, приветствие не главное
        logger.warning("приветствие в группу-консоль не ушло: %s", exc)


CHANNEL_EDIT_PREFIX = "channel_manual_edit:"


def _remember_manual_channel_edit(post: dict, db) -> None:
    """Пост в канале поправили руками — запомнить, чтобы рутина его больше не
    переписывала. 21 октября 2026 владелец поправил пост Swordfish Security в
    канале сам, а агент следом «вернул» его к прежнему тексту из базы: правка
    в Telegram в git не видна, и о ней никто не знал («Я уже поправил пост!!!»)."""
    chat = str((post.get("chat") or {}).get("id") or "")
    mid = post.get("message_id")
    if not chat or not mid:
        return
    key = "%s%s:%s" % (CHANNEL_EDIT_PREFIX, chat, mid)
    # Текст после правки — тоже (31 октября 2026): владелец просит показывать
    # закономерности своих правок, а без текста сравнивать было не с чем.
    text = post.get("text") or post.get("caption") or ""
    entities = post.get("entities") or post.get("caption_entities")
    try:
        html_text = _telegram_text_as_html(text, entities) if text else ""
    except Exception:  # noqa: BLE001 — разметка не важнее факта правки
        html_text = text
    value = json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "edit_date": post.get("edit_date"),
                        "text": text[:4096], "html": html_text[:8192]}, ensure_ascii=False)
    try:
        row = db.get(AppSetting, key)
        if row:
            row.value = value
        else:
            db.add(AppSetting(key=key, value=value))
        db.commit()
    except Exception as exc:  # noqa: BLE001 — не мешаем остальному разбору обновления
        db.rollback()
        logger.warning("ручная правка поста %s не запомнена: %s", key, exc)


@app.get("/api/ops/channel-edits")
def ops_channel_edits(token: str = "", db=Depends(get_db)):
    """Посты каналов, поправленные руками: {"<chat>:<message_id>": {at, edit_date}}."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    out = {}
    for row in db.scalars(select(AppSetting).where(AppSetting.key.like(CHANNEL_EDIT_PREFIX + "%"))).all():
        try:
            out[row.key[len(CHANNEL_EDIT_PREFIX):]] = json.loads(row.value or "{}")
        except ValueError:
            continue
    return {"edits": out}


def _announce_channel_id(payload, db=None) -> bool:
    """Сказать в консоль числовой адрес канала, если Telegram его показал.

    Единственный способ узнать адрес приватного канала — услышать его от
    самого Telegram (см. комментарий у TelegramWebhookIn). Возвращает True,
    если обновление было целиком «про канал» и обрабатывать его дальше
    нечего.
    """
    post = payload.channel_post or payload.edited_channel_post or {}
    if payload.edited_channel_post and db is not None:
        _remember_manual_channel_edit(payload.edited_channel_post, db)
    member = payload.my_chat_member or {}
    forwarded = ((payload.message or {}).get("forward_from_chat") or {})
    chat = post.get("chat") or member.get("chat") or forwarded or {}
    channel_update = bool(post or member)
    if str(chat.get("type") or "") != "channel":
        return channel_update
    chat_id = str(chat.get("id") or "")
    if not chat_id or chat_id == os.environ.get("TELEGRAM_CHANNEL_ID", "").strip():
        return channel_update
    realty = _is_realty_channel_title(chat.get("title"))
    if db is not None:
        if realty:
            _remember_setting(db, REALTY_CHANNEL_SETTING, chat_id)
            _sort_channel_slots(db)
        else:
            _remember_setting(db, CHANNEL_SETTING, chat_id)
    if chat_id not in _CHANNEL_IDS_TOLD:
        _CHANNEL_IDS_TOLD.add(chat_id)
        title = chat.get("title") or "без названия"
        role = ("Посты о недвижимости пойдут туда; о крупных сделках "
                "(от 1 млрд ₽) — и туда, и в основной канал, со ссылкой "
                "друг на друга.\n\n" if realty else "")
        thread = core._console_thread_id(db, "info") if db is not None else None
        for target in core._review_chat_ids(db):
            notification_service.tg_api(
                "sendMessage", chat_id=target, disable_web_page_preview=True,
                text=("\U0001F4E1 Канал «%s» отозвался — адрес запомнили.\n\n%s"
                      "У закрытого канала нет короткого имени, и постить в него "
                      "можно только по внутреннему номеру. Телеграм назвал его "
                      "сам, сайт его сохранил, публикация подхватит в ближайший "
                      "прогон — делать ничего не нужно." ) % (title, role),
                **({"message_thread_id": thread} if thread else {}))
    return channel_update


def _already_on_site(deal_id: str) -> bool:
    """Карточка уже вышла на сайт и ушла из очереди — решения по ее старому
    черновику ничего не меняют. 13 октября 2026 «Медси» (g4d7b2e19) была
    опубликована, а в консоли выше висели два ее черновика с живыми кнопками
    («Он нам эту хуйню второй раз не опубликует?»). Повторно она не выйдет —
    `approve.py` смотрит только на очередь, а `send_telegram.py` не шлет
    второй первый пост, — но нажатие отвечало «Принято» и ставило «✅
    Одобрено», будто что-то решило. Теперь бот говорит, как есть."""
    did = str(deal_id or "")
    if not did or "~" in did:
        return False
    pending = {str(c.get("id")) for c in (core._read_json("static/data/pending.json", {}).get("cards") or [])}
    if did in pending:
        return False
    base = base_data.promoted() or {}
    # Карточка в базе, а пост еще не вышел (29 октября 2026, Velle: решение
    # применено, публикация ждет pytest) — текст владельца еще успеет стать
    # текстом поста (send_telegram.late_owner_texts), ответ записывается.
    if not (base.get("telegram_posts") or {}).get(did):
        return False
    return any(str(d.get("id")) == did for d in base.get("deals") or [])


ALREADY_ON_SITE_TEXT = ("Эта карточка уже на сайте, пост — в канале. Кнопки и ответы на этот "
                        "черновик больше ничего не меняют. Поправить вышедшее — напишите, что "
                        "изменить, ответом на карточку.")


def _mark_decided(callback: dict, verdict: str, answered: bool = False) -> None:
    """Показать решение В САМОМ сообщении — иначе в общей группе второй
    человек не видит, что первый уже нажал, и жмет еще раз. Кнопки снимаются,
    под текстом появляется строка «решил такой-то». Оба вызова best-effort:
    решение уже в таблице, и сбой отрисовки его не отменяет.

    `answered=True` — на нажатие уже ответили раньше (вердикты модерации
    отвечают первым делом, чтобы кнопка не крутилась); второй
    answerCallbackQuery по тому же id Telegram отвергает."""
    if callback.get("id") and not answered:
        notification_service.tg_api("answerCallbackQuery",
                                    callback_query_id=callback["id"], text="Принято")
    message = callback.get("message") or {}
    chat = (message.get("chat") or {}).get("id")
    if chat is None or not message.get("message_id"):
        return
    who = (callback.get("from") or {}).get("first_name") or "участник"
    stamped = "%s\n\n— %s (%s)" % (str(message.get("text") or ""),
                                   _VERDICT_LABEL.get(verdict, verdict), who)
    # Отрисовка — best-effort не только по смыслу, но и по коду: любая ошибка
    # здесь не должна доходить до вебхука. Иначе Telegram получит 500, сочтет
    # доставку неудачной и пришлет то же нажатие заново — одно нажатие
    # превратится в несколько решений в очереди.
    # Разметку возвращаем той же, что пришла: Telegram отдает жирный и ссылки
    # отдельно от текста (`entities`), и правка одним текстом их стирала —
    # 8 октября 2026 владелец нажал кнопку под проектом поста «Дом.РФ»/ЦНТИ
    # и увидел его без жирного. Решение дописано в конце, отступы прежние.
    extra = {"entities": message["entities"]} if message.get("entities") else {}
    try:
        notification_service.tg_api("editMessageText", chat_id=chat,
                                    message_id=message["message_id"], text=stamped,
                                    disable_web_page_preview=True, **extra)
    except Exception as exc:  # noqa: BLE001
        logger.warning("не удалось дописать решение в сообщение: %s", exc)


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


@app.get("/ops")
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


@app.get("/api/ops/summary")
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


@app.get("/api/ops/activity")
def ops_activity(token: str = "", db=Depends(get_db)):
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return _activity_numbers(db)


@app.get("/ops/activity")
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


@app.post("/api/t")
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


@app.get("/api/ops/traffic")
def ops_traffic(token: str = "", days: int = 7, db=Depends(get_db)):
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    return _traffic_stats(db, days)


@app.get("/ops/traffic")
def ops_traffic_page(token: str = "", days: int = 7, metrika: int = 1, db=Depends(get_db)):
    """Посещаемость для владельца: наш счетчик и, если отвечает, Метрика."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    import traffic
    lines = _metrika_lines() if metrika else None
    lines = [re.sub(r"</?b>", "", x) for x in lines] if lines else lines
    return HTMLResponse(traffic.page_html(_traffic_stats(db, days), token, lines))


@app.post("/api/ops/traffic-report")
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


@app.get("/api/data/status")
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


@app.get("/api/moderation/decisions")
def moderation_decisions(token: str = "", db=Depends(get_db)):
    """Мост к рутине публикации: она в другом облаке и до базы не достает."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    rows = list(db.scalars(select(ModerationDecision)
                           .where(ModerationDecision.consumed.is_(False))
                           .order_by(ModerationDecision.created_at)).all())
    return {"decisions": [{"id": r.id, "deal_id": r.deal_id, "verdict": r.verdict,
                           "edited_text": r.edited_text, "decided_by": r.decided_by,
                           "chat_id": r.chat_id, "reply_message_id": r.reply_message_id,
                           "created_at": r.created_at.isoformat()} for r in rows]}


@app.get("/api/moderation/channel")
def moderation_channel(token: str = "", db=Depends(get_db)):
    """Адрес телеграм-канала для рутины публикации.

    Тот же мост, что и у решений модерации, и по той же причине: адрес знает
    САЙТ (Telegram называет его в посте канала, вебхук здесь), а нужен он
    РУТИНЕ, у которой доступа к этой базе нет. С 4 сентября 2026 канал
    закрытый: короткого имени у него не существует, и другого способа узнать
    адрес, кроме как услышать от Telegram, нет.
    """
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    _sort_channel_slots(db)
    row = db.get(AppSetting, CHANNEL_SETTING)
    realty = db.get(AppSetting, REALTY_CHANNEL_SETTING)
    return {"chat_id": row.value if row else None,
            "updated_at": row.updated_at.isoformat() if row else None,
            "realty_chat_id": realty.value if realty else None}


@app.get("/api/moderation/group")
def moderation_group(token: str = "", db=Depends(get_db)):
    """Актуальный id группы-консоли для рутин: тот же мост, что у канала и
    тем — рутина работает в другом процессе и не видит эту базу напрямую."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    row = db.get(AppSetting, REVIEW_GROUP_SETTING)
    return {"chat_id": row.value if row else None,
            "updated_at": row.updated_at.isoformat() if row else None}


@app.get("/api/moderation/topics")
def moderation_topics(token: str = "", db=Depends(get_db)):
    """Номера тем группы-консоли для рутин: та же логика, что у
    /api/moderation/channel — рутина работает в другом процессе, у нее нет
    доступа к этой базе, и адреса приходится спрашивать по токену."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    rows = db.scalars(select(AppSetting).where(
        AppSetting.key.like("telegram_topic:%"))).all()
    return {"topics": {r.key.split(":", 1)[1]: r.value for r in rows}}


def _access_row(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "company": u.company,
            "position": u.position, "created_at": u.created_at.isoformat()}


@app.get("/api/access/requests")
def access_requests(token: str = "", db=Depends(get_db)):
    """Заявки на доступ (core.ACCESS_GATE) для владельца, который смотрит не в
    Telegram, а через сессию Claude: аккаунты живут в базе сайта (приватная
    сеть Timeweb), и единственный путь до нее снаружи — сам сервер, тем же
    токеном, что у /api/moderation/decisions. Отдаем ожидающих (approved=False)
    и полный список уже одобренных — чтобы «никого нет» отличалось от «все
    одобрены», и чтобы можно было увидеть, кто вообще зарегистрирован."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    pending = list(db.scalars(select(User).where(User.approved.is_(False))
                              .order_by(User.created_at)).all())
    approved = list(db.scalars(select(User).where(User.approved.is_(True))
                               .order_by(User.created_at)).all())
    return {"pending": [_access_row(u) for u in pending],
            "approved": [_access_row(u) for u in approved],
            "approved_count": len(approved), "gate": core.ACCESS_GATE}


class AccessDecideIn(BaseModel):
    token: str = ""
    user_id: int = 0
    approve: bool = True


@app.post("/api/access/decide")
def access_decide(req: AccessDecideIn, db=Depends(get_db)):
    """То же решение, что кнопка «Одобрить»/«Отклонить» в Telegram, но по
    токену: для случая, когда владелец дает команду в чате сессии, а не в
    группе. Право — тот же токен, что у моста модерации."""
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    applicant = db.get(User, int(req.user_id))
    if not applicant:
        return JSONResponse({"error": "аккаунта с таким id нет"}, status_code=404)
    applicant.approved = bool(req.approve)
    db.commit()
    return {"ok": True, "user_id": applicant.id, "email": applicant.email, "approved": applicant.approved}


class ModerationConsumeIn(BaseModel):
    token: str = ""
    ids: list[int] = []


# ---------------------------------------------------------------------------
# Показ готовых карточек с сервера (28 октября 2026)
#
# Владелец: «почему нельзя по нахождении новости… сделать черновик карты,
# пост и сразу отправить создателям?» Показ карточки в консоль был шагом
# прогона притока, который агент четыре раза подряд не сделал («Ломбард 888»
# ждал сутки, KNOWN_ISSUES 28 октября 2026). Сайт подтягивает pending.json
# каждые несколько минут и видит каждую принятую карточку раньше любого
# прогона — поэтому показывает ее сам: те же ворота (reviewed, accepted,
# second_read), те же тексты и кнопки (send_drafts.card_message/
# post_message_text), та же тема консоли. Что показано — помнит в AppSetting
# (`console_shown:<id>`, снимок поста — `console_post_preview:<id>`), и
# отдает рутинам по /api/moderation/shown, чтобы send_drafts не показал
# карточку второй раз, а send_telegram отправил в канал ровно тот текст,
# который видел владелец. Сырье (⚠️) сервер не показывает — его помнит тот же
# мост (`console_raw_shown:<ключ заголовка>`), чтобы два контейнера притока
# не показали одно и то же дважды.
# ---------------------------------------------------------------------------
CONSOLE_SHOWN_PREFIX = "console_shown:"
CONSOLE_PREVIEW_PREFIX = "console_post_preview:"
CONSOLE_RAW_PREFIX = "console_raw_shown:"


def _send_drafts_module():
    import sys
    for sub in (("pipeline", "ingest"), ("pipeline", "publish"), ("pipeline",)):
        path = os.path.join(BASE_DIR, *sub)
        if path not in sys.path:
            sys.path.insert(0, path)
    import send_drafts  # noqa: WPS433 — тяжелый модуль, грузится только здесь
    return send_drafts


def _console_ready_cards(db, cards: list) -> list:
    """Принятые карточки, которых владелец еще не видел: три отметки чтения,
    нет отметки показа в очереди и на сервере, нет неприменного решения."""
    out = []
    for card in cards:
        cid = str(card.get("id") or "")
        if not cid or not (card.get("reviewed") and card.get("accepted") and card.get("second_read")):
            continue
        if card.get("draft_sent") or db.get(AppSetting, CONSOLE_SHOWN_PREFIX + cid):
            continue
        waiting = db.scalars(select(ModerationDecision)
                             .where(ModerationDecision.deal_id == cid, ModerationDecision.consumed.is_(False))).first()
        if waiting:
            continue
        out.append(card)
    return out


def console_show_ready_cards() -> dict:
    """Показать в консоли готовые карточки из pending.json. Возвращает счет."""
    pending = (core._read_json("static/data/pending.json", {}) or {}).get("cards") or []
    db = get_session()
    try:
        ready = _console_ready_cards(db, pending)
        if not ready:
            return {"shown": 0}
        chats = core._review_chat_ids(db)
        if not chats:
            logger.error("готовых карточек %d, а консоли нет — показывать некому", len(ready))
            return {"shown": 0, "error": "консоли нет"}
        sd = _send_drafts_module()
        comps = (base_data.promoted() or {}).get("companies") or {}
        thread = core._console_thread_id(db, "decision")
        shown = 0
        for card in ready:
            common = {"chat_id": chats[0], "disable_web_page_preview": True}
            if thread:
                common["message_thread_id"] = thread
            r = notification_service.tg_api("sendMessage", text=sd.card_message(card, comps),
                                            reply_markup=sd.card_keyboard(card), **common)
            if not (r and r.get("ok")):
                logger.error("карточка %s в консоль не ушла: %s", card["id"], r)
                continue
            preview = None
            if sd.goes_to_channel(card):
                preview = sd.post_message_text(card, comps)
                rp = notification_service.tg_api("sendMessage", text=preview, parse_mode="HTML",
                                                 reply_markup=sd.post_keyboard(card), **common)
                if not (rp and rp.get("ok")):
                    rp = notification_service.tg_api("sendMessage", text=re.sub(r"<[^>]+>", "", preview),
                                                     reply_markup=sd.post_keyboard(card), **common)
                if not (rp and rp.get("ok")):
                    preview = None
            _remember_setting(db, CONSOLE_SHOWN_PREFIX + card["id"], datetime.utcnow().isoformat(timespec="seconds"))
            if preview:
                _remember_setting(db, CONSOLE_PREVIEW_PREFIX + card["id"], preview)
            shown += 1
        logger.info("показано готовых карточек в консоли: %d", shown)
        return {"shown": shown}
    finally:
        db.close()


def _console_after_refresh(changed: list) -> None:
    if "static/data/pending.json" in changed and not os.environ.get("PYTEST_CURRENT_TEST"):
        console_show_ready_cards()


class ModerationShownIn(BaseModel):
    token: str = ""
    cards: list[dict] = []     # [{"id": ..., "post_preview": ...}]
    raw: list[str] = []        # ключи заголовков сырья (promote.raw_key)


@app.get("/api/moderation/shown")
def moderation_shown(token: str = "", db=Depends(get_db)):
    """Что консоль уже видела: карточки (с текстом показанного поста) и сырье."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    cards, raw = {}, []
    for row in db.scalars(select(AppSetting).where(AppSetting.key.like("console_%"))).all():
        if row.key.startswith(CONSOLE_SHOWN_PREFIX):
            cards.setdefault(row.key[len(CONSOLE_SHOWN_PREFIX):], {})["shown_at"] = row.value
        elif row.key.startswith(CONSOLE_PREVIEW_PREFIX):
            cards.setdefault(row.key[len(CONSOLE_PREVIEW_PREFIX):], {})["post_preview"] = row.value
        elif row.key.startswith(CONSOLE_RAW_PREFIX):
            raw.append(row.key[len(CONSOLE_RAW_PREFIX):])
    return {"cards": cards, "raw": raw}


@app.post("/api/moderation/shown")
def moderation_shown_record(req: ModerationShownIn, db=Depends(get_db)):
    """Рутина показала карточку или сырье сама — пусть сервер это помнит."""
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    now = datetime.utcnow().isoformat(timespec="seconds")
    n = 0
    for item in req.cards:
        cid = str(item.get("id") or "").strip()
        if not cid:
            continue
        _remember_setting(db, CONSOLE_SHOWN_PREFIX + cid, now)
        if item.get("post_preview"):
            _remember_setting(db, CONSOLE_PREVIEW_PREFIX + cid, str(item["post_preview"]))
        n += 1
    for key in req.raw:
        if key:
            _remember_setting(db, CONSOLE_RAW_PREFIX + str(key)[:200], now)
            n += 1
    return {"recorded": n}


@app.post("/api/moderation/decisions/consume")
def moderation_consume(req: ModerationConsumeIn, db=Depends(get_db)):
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    n = 0
    for row in db.scalars(select(ModerationDecision).where(ModerationDecision.id.in_(req.ids or []))).all():
        row.consumed = True
        n += 1
    db.commit()
    return {"consumed": n}


def _claude_row(r: ClaudeMessage) -> dict:
    return {"id": r.id, "chat_id": r.chat_id, "thread_id": r.thread_id,
            "message_id": r.message_id, "from_id": r.from_id, "from_name": r.from_name,
            "text": r.text, "photo_file_id": r.photo_file_id,
            "document_file_id": r.document_file_id, "document_name": r.document_name,
            "reply_to_text": r.reply_to_text,
            "created_at": r.created_at.isoformat() if r.created_at else None}


@app.get("/api/claude/inbox")
def claude_inbox(token: str = "", db=Depends(get_db)):
    """Непрочитанные сообщения из темы «Клод» для рутины «тема Клод» — тот же
    мост по токену, что у /api/moderation/decisions."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    rows = list(db.scalars(select(ClaudeMessage).where(ClaudeMessage.consumed.is_(False))
                           .order_by(ClaudeMessage.created_at, ClaudeMessage.id)).all())
    return {"messages": [_claude_row(r) for r in rows]}


@app.post("/api/claude/inbox/consume")
def claude_inbox_consume(req: ModerationConsumeIn, db=Depends(get_db)):
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    n = 0
    for row in db.scalars(select(ClaudeMessage).where(ClaudeMessage.id.in_(req.ids or []))).all():
        row.consumed = True
        n += 1
    db.commit()
    return {"consumed": n}


# СВОДКА ДНЯ В КОНСОЛЬ (5 октября 2026). Владелец: «давай сделаем 1 раз в день
# в 18:00 и отправляй статистику из Яндекс Метрики». Раньше приток писал в
# консоль после каждого прогона, где были карточки, — до шести сообщений в
# день. Рутина идет в новом контейнере каждый час и помнить день не может,
# поэтому она отдает цифры прогона сюда (`POST /api/ops/intake-run`), а в
# 18:00 МСК сайт складывает их в одно сообщение и добавляет посещаемость из
# Метрики (`metrika.py`, ключ `METRIKA_TOKEN`). Сбой рутины по-прежнему
# приходит сразу (`ops_status.py --broken`), а не ждет вечера. Если до 18:00
# от притока не пришло ни одного прогона, сводка так и говорит — молчание
# рутины не должно выглядеть как тихий день. `INTAKE_SUMMARY=0` — выключить.
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


@app.post("/api/ops/intake-run")
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


@app.post("/api/ops/intake-summary")
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
MILESTONE_DRAFT_PREFIX = "milestone_draft:"
MILESTONE_POSTED_PREFIX = "milestone_posted:"


class MilestoneDraftIn(BaseModel):
    token: str = ""
    combo: str
    event_id: str
    text: str
    buttons: dict | None = None
    route: list[str] = []


@app.post("/api/ops/milestone-draft")
def ops_milestone_draft(req: MilestoneDraftIn, db=Depends(get_db)):
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    if not re.fullmatch(r"[\w-]{1,50}~[\w-]{1,30}", req.combo or ""):
        return JSONResponse({"error": "bad combo"}, status_code=400)
    value = json.dumps({"event_id": req.event_id, "text": req.text, "buttons": req.buttons,
                        "route": list(req.route or []),
                        "stored_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                       ensure_ascii=False)
    row = db.get(AppSetting, MILESTONE_DRAFT_PREFIX + req.combo)
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=MILESTONE_DRAFT_PREFIX + req.combo, value=value))
    db.commit()
    return {"ok": True}


def _main_channel_id(db) -> str:
    """Адрес основного канала — тем же порядком, что у рутины публикации
    (`send_telegram.channel_address`): числовой адрес из окружения, иначе тот,
    что сайт услышал от Telegram, но никогда не адрес канала недвижимости."""
    from_env = (os.environ.get("TELEGRAM_CHANNEL_ID") or "").strip()
    if from_env and not from_env.startswith("@"):
        return from_env
    _sort_channel_slots(db)
    row = db.get(AppSetting, CHANNEL_SETTING)
    realty = db.get(AppSetting, REALTY_CHANNEL_SETTING)
    chat = str(row.value or "").strip() if row else ""
    if chat and chat != (str(realty.value or "").strip() if realty else ""):
        return chat
    return ""


def _milestone_already_out(event_id: str) -> bool:
    """Этап уже вышел (рутиной — например, по суткам молчания)."""
    base = core._read_json("static/data/deals_promoted.json", {})
    return event_id in (base.get("telegram_milestones") or {})


def _instant_milestone_post(combo: str, decision_id: int, db=None) -> int | None:
    """Опубликовать этап сразу. Номер поста или None (тогда опубликует рутина)."""
    own = db is None
    db = db or get_session()
    try:
        row = db.get(AppSetting, MILESTONE_DRAFT_PREFIX + combo)
        if not row or not row.value:
            return None
        draft = json.loads(row.value)
        if list(draft.get("route") or []) != ["main"] or not draft.get("text"):
            return None
        if _milestone_already_out(str(draft.get("event_id") or "")):
            return None
        channel = _main_channel_id(db)
        if not channel or channel in core._review_chat_ids(db):
            return None
        # Ключ «уже публикуем» пишется ДО отправки: второе нажатие (партнер
        # в ту же минуту) не выпустит пост дважды. Та же отметка — в самом
        # решении: рутина публикации, прочитав его в эти секунды, этап не
        # шлет (`send_telegram.site_posted_milestones`).
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.add(AppSetting(key=MILESTONE_POSTED_PREFIX + combo, value=started))
        decision = db.get(ModerationDecision, decision_id)
        if decision is not None:
            decision.edited_text = json.dumps({"posting_since": started})
        try:
            db.commit()
        except Exception:                                    # noqa: BLE001
            db.rollback()
            return None
        payload = {"chat_id": channel, "text": draft["text"], "parse_mode": "HTML",
                   "disable_web_page_preview": True}
        if draft.get("buttons"):
            payload["reply_markup"] = draft["buttons"]
        res = notification_service.tg_api("sendMessage", **payload) or {}
        if not res.get("ok"):
            logger.error("этап %s не опубликован сайтом: %s", combo, res.get("description"))
            guard = db.get(AppSetting, MILESTONE_POSTED_PREFIX + combo)
            if guard:
                db.delete(guard)
            if decision is not None:
                decision.edited_text = None
            db.commit()
            return None
        mid = (res.get("result") or {}).get("message_id")
        if decision is not None:
            decision.edited_text = json.dumps({"posted_message_id": mid,
                                               "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        db.commit()
        return mid
    finally:
        if own:
            db.close()


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
_reexport.install(globals(), (core, fns, assistant, accounts,))
