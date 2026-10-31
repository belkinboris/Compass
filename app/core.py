# -*- coding: utf-8 -*-
"""Общее для всех роутеров: журнал, пути, сессия БД, настройки входа, адреса
консоли, HTTP-клиент, проверка токена моста. Ничего из app/ сюда не
импортируется — это нижний слой (docs/server_layout.md)."""
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


_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("kompas")


# Корень репозитория (на уровень выше app/): отсюда читаются static/, data/ и отпечаток сборки.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

# ВХОД ПО ЗАЯВКЕ — этап закрытого тестирования (просьба владельца 2 сентября
# 2026: «как в Автопосте»). Пока включено, посетитель без входа видит вместо
# любого экрана сайта блок «Войти / Запросить доступ»; регистрация создает
# аккаунт с approved=False и шлет заявку в Telegram-консоль, где владелец или
# партнер нажимает «Одобрить» — только после этого вход по этим данным
# работает. По умолчанию ВКЛЮЧЕНО (на боевом хосте переменной нет), выключить
# — `ACCESS_GATE=0` в окружении или одна правка здесь. Гейт визуальный: API
# сделок и компаний не закрываются, закрыт только вход в аккаунт.
# 3 октября 2026 — запуск для всех: дверь «Войти / Запросить доступ» снята,
# умолчание «0». Включить обратно на время — ACCESS_GATE=1 в окружении.
ACCESS_GATE = os.environ.get("ACCESS_GATE", "0") == "1"


# Общий keep-alive клиент (урок TruePost: не создавать новый на каждый вызов).
_http = httpx.Client(
    timeout=float(os.environ.get("LLM_TIMEOUT", "30")),  # то же LLM_TIMEOUT, что у ассистента
    transport=httpx.HTTPTransport(retries=2),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)


def _yandex_ready() -> bool:
    return bool(os.environ.get("YANDEX_API_KEY")) and bool(os.environ.get("YANDEX_FOLDER_ID"))


def _review_chat_ids(db=None) -> list[str]:
    """Куда слать в консоль. Группа — id из `TELEGRAM_REVIEW_GROUP_ID`, но
    4 сентября 2026 выяснилось, что этот номер может устареть НЕЗАМЕТНО и БЕЗ
    участия человека: как только владелец включил в группе темы (форум),
    Telegram сам превратил ее в супергруппу — а у супергруппы ВСЕГДА другой
    chat_id, старый отвечает 400 «group chat was upgraded to a supergroup
    chat». Переменная окружения при этом продолжает выглядеть настроенной.
    Поэтому здесь та же иерархия, что у адреса канала, только источники
    поменялись местами: САЙТ уже знает свежий id (учит его из любого
    сообщения владельца/партнера в группе, см. `_learn_review_group`) —
    спрашиваем БД первой, а переменная окружения остается запасным путем для
    вызовов без доступа к базе (фоновые потоки без своей сессии)."""
    forbidden = _channel_chat_ids(db)

    def usable(chat_id: str) -> bool:
        return bool(chat_id) and chat_id not in forbidden and not _chat_is_channel(chat_id)

    if db is not None:
        row = db.get(AppSetting, REVIEW_GROUP_SETTING)
        if row and row.value and usable(row.value):
            return [row.value]
    group = os.environ.get("TELEGRAM_REVIEW_GROUP_ID", "").strip()
    if usable(group):
        return [group]
    return [x.strip() for x in os.environ.get("TELEGRAM_REVIEW_CHAT_IDS", "").split(",")
            if x.strip() and x.strip() not in forbidden]


def _channel_chat_ids(db=None) -> set[str]:
    """Адреса канала публикации — все, что о нем известно сайту.

    КОНСОЛЬ И КАНАЛ НЕЛЬЗЯ ПЕРЕПУТАТЬ НИ ПРИ КАКОМ СБОЕ. 7 сентября 2026
    отчет рутины ушел в публичный канал, к подписчикам: в контейнере рутин
    `TELEGRAM_REVIEW_GROUP_ID` содержал номер КАНАЛА, сайт в ту минуту
    перезапускался после сборки, и запасной путь честно отработал по
    неверному адресу. Цена ошибки несимметрична: сообщение консоли, не
    дошедшее до владельца, — неудобство; ушедшее подписчикам — публичный
    ущерб. Поэтому адрес канала вычеркивается из кандидатов в консоль
    всегда, откуда бы он ни пришел; если после этого ничего не осталось,
    пишем лично владельцу и партнеру."""
    ids = set()
    env = (os.environ.get("TELEGRAM_CHANNEL_ID") or "").strip()
    if env:
        ids.add(env)
    if db is not None:
        for key in (CHANNEL_SETTING, REALTY_CHANNEL_SETTING):
            row = db.get(AppSetting, key)
            if row and row.value:
                ids.add(str(row.value))
    return ids


_CHAT_IS_CHANNEL: dict[str, bool] = {}


def _chat_is_channel(chat_id) -> bool:
    """Правда ли, что этот адрес — КАНАЛ. Спрашиваем сам Telegram.

    Сравнения с известным номером канала мало, и это выяснилось в тот же
    вечер, что и утечка: владелец, поправляя переменные, записал в
    `TELEGRAM_CHANNEL_ID` старое @имя канала — а оно перестало существовать,
    когда канал сделали приватным. Номера канала мы после этого не знали
    вообще, и защита, построенная только на сравнении номеров, стала пустой.
    Тип чата — свойство самого чата: он не может «не быть» из-за того, что
    кто-то не так заполнил переменную. Один запрос на адрес за жизнь
    процесса; сеть молчит — не блокируем (сравнение по номерам остается
    вторым рубежом)."""
    chat_id = str(chat_id or "").strip()
    if not chat_id:
        return False
    if chat_id in _CHAT_IS_CHANNEL:
        return _CHAT_IS_CHANNEL[chat_id]
    if not os.environ.get("TELEGRAM_BOT_TOKEN", "").strip():
        return False
    answer = notification_service.tg_api("getChat", chat_id=chat_id) or {}
    if answer.get("ok"):
        verdict = str((answer.get("result") or {}).get("type") or "") == "channel"
        _CHAT_IS_CHANNEL[chat_id] = verdict
        return verdict
    return False


def _current_user(request: Request, db=Depends(get_db)) -> User | None:
    return auth.current_user(db, request.cookies.get(auth.SESSION_COOKIE))


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


SITE_URL = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")


def _read_json(path, default):
    try:
        with open(os.path.join(BASE_DIR, path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


REVIEW_GROUP_SETTING = "telegram_review_group_id"
CHANNEL_SETTING = "telegram_channel_id"
# Второй канал — «Компас - Недвижимость» (2 октября 2026). Пока канал был один,
# любой канал, кроме записанного в окружении, считался ОСНОВНЫМ: владелец
# добавил бота в новый канал, и сайт записал его адрес в ячейку основного.
# Публикацию спасла только переменная окружения рутин. Теперь канал узнается
# по названию: «недвижимость» в нем — своя ячейка.
REALTY_CHANNEL_SETTING = "telegram_channel_id:realty"


# ТОПИКИ КОНСОЛИ. 4 сентября 2026 владелец превратил группу-консоль в форум
# и завел темы («Подтверждение постов», «Обновления», «Общая информация»),
# чтобы решения, отчеты рутин и разное не лежали одной кучей. Bot API не
# дает список тем группы (нет метода вроде getForumTopics) — номер темы
# (`message_thread_id`) узнается так же, как адрес приватного канала выше:
# из служебного сообщения о создании/переименовании темы (несет имя и id
# напрямую), а для уже существующих тем, чье служебное сообщение прошло ДО
# того, как бот начал их слушать, — разовым бутстрапом: человек печатает
# точное название темы внутри нее самой.
CONSOLE_TOPIC_NAMES = {
    "decision": "Подтверждение постов",   # чего-то ждет ваше решение
    "update": "Обновления",               # отчет рутины о прогоне
    "info": "Общая информация",           # служебное: канал отозвался, адрес запомнили
    # Все, что написал ПОСЕТИТЕЛЬ: уточнение с карточки сделки, заметка из
    # футера и обе половины отзыва об ассистенте («Ответ помог?» и «Чем не
    # помог?»). Отзывы жили в «Общей информации» и тонули среди отчетов о
    # прогонах — переехали 22 сентября 2026.
    "user_notes": "Заметки от пользователей",
    # Служебные очереди, где вы отвечаете на ТЕХНИЧЕСКИЙ вопрос, а не решаете
    # судьбу поста. Заведена 22 сентября 2026, чтобы в «Подтверждении постов»
    # остались только посты и карточки.
    "admin": "Админ",
    # Сообщения владельца и партнера агенту Claude: задачи, правки, вопросы.
    # Ловит их _claude_topic_message, читает рутина «тема Клод»
    # (routines/claude_topic.md), ответ приходит в ту же тему. 17 октября 2026.
    "claude": "Клод",
}

# Запасная тема, пока номер не закреплен: пропасть очереди заявок на вход
# хуже, чем полежать не в той теме. Дублирует pipeline/console_topics.FALLBACK.
CONSOLE_TOPIC_FALLBACK = {"admin": "decision"}


def _topic_slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s)


def _console_thread_id(db, kind: str) -> int | None:
    """Номер темы для сообщений вида `kind`, запущенных из этого же процесса
    (сайт уже держит базу — незачем ходить за собой по HTTP, как это делают
    рутины через /api/moderation/topics)."""
    name = CONSOLE_TOPIC_NAMES.get(kind)
    if not name:
        return None
    row = db.get(AppSetting, "telegram_topic:%s" % _topic_slug(name))
    if row and row.value.lstrip("-").isdigit():
        return int(row.value)
    spare = CONSOLE_TOPIC_FALLBACK.get(kind)
    return _console_thread_id(db, spare) if spare else None


def _in_background(fn) -> None:
    """Долгая работа (ответ модели) — не в потоке опроса Telegram: пока он
    ждет модель, бот не слышит ни одной кнопки. Тесты подменяют на вызов."""
    threading.Thread(target=fn, daemon=True).start()


def _is_reviewer(chat_id) -> bool:
    """Право решать есть только у чатов из TELEGRAM_REVIEW_CHAT_IDS (владелец и
    партнер). Любой другой человек, нашедший бота, решений не оставит."""
    allowed = {x.strip() for x in os.environ.get("TELEGRAM_REVIEW_CHAT_IDS", "").split(",") if x.strip()}
    return chat_id is not None and str(chat_id) in allowed


def _moderation_token_ok(token: str) -> bool:
    expected = os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or ""
    return bool(expected) and token == expected


