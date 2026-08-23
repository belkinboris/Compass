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
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from html import escape as html_escape

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

import auth
import notification_service
import subscription_feed
from company_catalog import get_company_profile
from deal_catalog import get_deal
from deal_export import render_deal_pdf
from db.models import Base as DBBase
from db.models import (
    AssistantMessage, AssistantThread, AuthSession, Comment, CorrectionRequest,
    DealWatch, FinancialReport, FnsSyncRun, LegalEntity, LegalEntityMatchStatus,
    ModerationDecision, Notification,
    NotificationPreference, OwnershipSnapshot, OwnershipStake, RegistryEvent,
    SavedFilter, User, UserRole, UserTier, Webinar,
)
from db.session import engine, get_session
from fns_client import ApiFnsClient, ApiFnsError
from pipeline.fns_registry import by_company_id as fns_registry_by_company_id
from sqlalchemy import inspect, select, text
from yandex_search import SearchConfig, SearchError, SearchResult, build_search_block, yandex_search

_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("kompas")

app = FastAPI(title="КОМПАС")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Сжатие ответов. База сделок — 4,6 МБ текста, и до этого она уезжала в браузер
# как есть: 4695 КБ по сети на каждый первый заход. JSON сжимается в шесть раз,
# так что это самая дешёвая правка из возможных — одна строка вместо дробления
# файла на части и переписывания загрузчика.
# minimum_size: мелочь сжимать дороже, чем отдать как есть.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Таблицы аккаунтов (db/models.py) — заготовка лежала не подключённой с 22
# июля, main.py по-прежнему читает static/data/*.json напрямую для сделок и
# компаний. create_all создаёт только НЕДОСТАЮЩИЕ таблицы и никогда не трогает
# существующие данные — безопасно и на пустой sqlite для разработки, и на
# уже заполненном Postgres на Timeweb.
@app.on_event("startup")
def _create_account_tables():
    try:
        DBBase.metadata.create_all(engine)
        # password_hash добавлен в User 2 августа — create_all его на уже
        # СУЩЕСТВОВАВШЕЙ (до этой даты) таблице users не создаст: он создаёт
        # только недостающие ТАБЛИЦЫ целиком, а не недостающие колонки в уже
        # существующих. `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — синтаксис
        # только Postgres, на SQLite это просто синтаксическая ошибка (проверено
        # здесь же: колонка молча не добавлялась). Проверяем через инспектор
        # SQLAlchemy — он одинаково работает на обоих диалектах — и добавляем
        # обычным ADD COLUMN без IF NOT EXISTS, который тоже понимают оба.
        try:
            with engine.begin() as conn:
                cols = {c["name"] for c in inspect(conn).get_columns("users")}
                if "password_hash" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(200)"))
                # full_name/company/position добавлены 2 августа тем же способом —
                # см. комментарий выше про password_hash, тот же диалект-независимый приём.
                for col in ("full_name", "company", "position"):
                    if col not in cols:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(200)"))
        except Exception as e:
            logger.error("не удалось добавить password_hash в users: %s", e)
        # chat_id/reply_message_id добавлены в moderation_decisions 22 августа
        # для ответа рутины реплаем на заметку (раздел C MILESTONES_BRIEF.md) —
        # тот же диалект-независимый приём инспектора, что и выше для users.
        try:
            with engine.begin() as conn:
                cols = {c["name"] for c in inspect(conn).get_columns("moderation_decisions")}
                if "chat_id" not in cols:
                    conn.execute(text("ALTER TABLE moderation_decisions ADD COLUMN chat_id VARCHAR(40)"))
                if "reply_message_id" not in cols:
                    conn.execute(text("ALTER TABLE moderation_decisions ADD COLUMN reply_message_id INTEGER"))
        except Exception as e:
            logger.error("не удалось добавить chat_id/reply_message_id в moderation_decisions: %s", e)
        # deal_id расширен с 40 до 80 знаков 22 августа: у вехи это
        # "<id сделки>~<вид этапа>", длиннее одного голого id. SQLite VARCHAR
        # не проверяется движком вообще (хранится как TEXT) — расширять там
        # нечего; Postgres проверяет строго, и без ALTER запись веха-решения
        # там упала бы с ошибкой длины, которую на SQLite никто бы не увидел.
        # ALTER COLUMN TYPE — тоже синтаксис только Postgres, SQLite его не
        # поддерживает вовсе — тот же диалект-независимый приём: действие
        # только там, где оно применимо и нужно.
        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    conn.execute(text(
                        "ALTER TABLE moderation_decisions ALTER COLUMN deal_id TYPE VARCHAR(80)"))
        except Exception as e:
            logger.error("не удалось расширить deal_id в moderation_decisions: %s", e)
    except Exception as e:  # БД недоступна — сайт и без аккаунтов должен жить
        logger.error("не удалось создать таблицы аккаунтов: %s", e)


# Подписки сверяются здесь, а не в притоке: приток работает в другом облаке, а
# база пользователей стоит во внутренней сети хостинга и оттуда недостижима.
# Отдельного расписания у сверки нет и не нужно — новые карточки попадают на
# сайт ровно одним способом, деплоем нового deals_promoted.json, и старт
# процесса после деплоя и есть единственный момент, когда есть что сверять.
# Первый прогон никого не будит: он только запоминает состав базы.
@app.on_event("startup")
def _match_subscriptions_against_new_deals():
    subscription_feed.scan_on_startup()


# Докачка ФНС по git-реестру (pipeline/fns_registry.py) — механика,
# COMPANY_FINANCE_BRIEF.md, раздел «Суждение — в git-реестре, механика — на
# боевом хосте»: суждение «какой ИНН чей» уже принято чтением и лежит в
# реестре, здесь только подтверждается и докачивается отчётность. В отдельном
# потоке — это живые запросы к api-fns.ru (до 25 с таймаута на каждый по
# fns_client.py), и сайт не должен ждать их, чтобы начать отвечать на
# обычные запросы. Ключа нет — тихо пропускаем: это НЕ сбой (ключ на боевом
# хосте может быть ещё не добавлен, локальная разработка — тем более).
@app.on_event("startup")
def _sync_fns_from_registry():
    if not os.environ.get("API_FNS_KEY"):
        return
    # PYTEST_CURRENT_TEST — переменная, которую сам pytest выставляет на
    # время каждого теста: без этой защиты КАЖДЫЙ TestClient(main.app) в
    # тестах бил бы по живому api-fns.ru и тратил платную квоту прогоном
    # тестов — а этот ключ в среде разработки реально задан (см. П0).
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    def _run():
        db = get_session()
        try:
            _fns_sync_once(db)
        except Exception as e:  # сеть/квота/что угодно — сайт не должен упасть из-за этого
            logger.error("не удалось докачать ФНС из реестра при старте: %s", e)
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()


def _fns_sync_once(db) -> dict | None:
    """Одна попытка докачки ФНС по реестру — вынесена из `_run()` отдельной
    функцией, чтобы её можно было проверить тестом напрямую, без потока и
    без обхода env-гварда `_sync_fns_from_registry()`. Возвращает `stats`
    при реальной попытке синка, `None` при пропуске (потолок достигнут)."""
    from pipeline.sync_fns import sync_from_registry
    from fns_client import ApiFnsClient

    used_today = _fns_requests_today(db)
    if used_today >= FNS_DAILY_REQUEST_CAP:
        logger.warning(
            "ФНС: дневной потолок запросов достигнут (%d/%d) — старт "
            "пропускает докачку, до завтра", used_today, FNS_DAILY_REQUEST_CAP)
        return None
    with ApiFnsClient() as client:
        stats = sync_from_registry(db, client, limit=FNS_STARTUP_SYNC_LIMIT)
    logger.info("ФНС из реестра при старте: %s", stats)
    db.add(FnsSyncRun(
        mode="startup",
        companies_total=stats.get("confirmed_now", 0) + stats.get("synced", 0)
        + stats.get("skipped_fresh", 0),
        matched=stats.get("confirmed_now", 0) + stats.get("synced", 0),
        errors=stats.get("errors", 0),
        details_json=json.dumps(stats),
    ))
    db.commit()
    return stats


def _fns_requests_today(db) -> int:
    """Сумма `requests` из FnsSyncRun за текущие календарные сутки (UTC).

    П5''' (COMPANY_FINANCE_BRIEF.md, этап 3): защита не от нехватки квоты
    (её достаточно — см. «Открытие, которое меняет бюджет» в CLAUDE.md), а
    от петли или бага, который перезапускал бы процесс много раз подряд и
    каждый раз бил по api-fns.ru заново. Счётчик обязан пережить сам
    перезапуск, из-за которого его завели, — поэтому он не переменная
    процесса (умирает вместе с ним), а строка в БД, которая переживает
    рестарт (тот же принцип, что уже применён к `fns_asked` на профиле
    компании — штамп в постоянном хранилище, а не в памяти одного запуска).
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    rows = db.scalars(select(FnsSyncRun).where(FnsSyncRun.started_at >= today_start)).all()
    total = 0
    for row in rows:
        try:
            total += json.loads(row.details_json or "{}").get("requests", 0)
        except (ValueError, TypeError):
            continue
    return total


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

# «Компания сегодня» не показывает отчётность старше этого числа лет от
# текущего года — правило владельца от 18 августа 2026 после жалобы на
# видимые на сайте показатели банков за 2020-2021 год.
FNS_REPORT_MAX_AGE_YEARS = 2

# ВРЕМЕННО, по прямой просьбе владельца 22 августа 2026: «давай сначала всё
# сделаем бесплатно, чтобы я видел как работает». Финансовый блок компании
# показывает полную историю (все отчётные годы, все события ЕГРЮЛ, полный
# состав участников) всем посетителям, не только платным. Когда владелец
# увидит витрину целиком и решит границу бесплатного (см.
# pipeline/COMPANY_FINANCE_BRIEF.md, раздел П6) — выключить флагом здесь,
# без другой правки кода. Скачивание живой БФО (bo_file) остаётся только для
# вошедших: это не про платность, а про то, что каждый клик — платный запрос
# к API-ФНС (бюджет 3000/год), и открывать его анонимно нельзя ни в каком
# режиме бесплатности.
FNS_ALL_FREE = True

# Сколько подтверждённых профилей (pipeline/fns_registry.py) докачивать за
# ОДИН старт процесса. COMPANY_FINANCE_BRIEF.md, раздел П2: расписания нет —
# новые решения реестра появляются деплоем, и старт после деплоя уже и есть
# то самое естественное событие (тот же приём, что и у сверки подписок ниже).
# Потолок — на РЕАЛЬНУЮ работу (sync_from_registry считает limit после
# проверки свежести с 23 августа, не как срез списка), а не на просмотр
# строк реестра: уже свежие профили лимит не тратят вовсе. 23 августа
# 2026 обнаружено, что квота на самом деле по-методная (3000/год на каждый
# метод отдельно, а bo/egr/changes — «по организациям», повторный запрос
# той же организации в год бесплатен) — прежняя осторожность в 30 была
# рассчитана на неверную модель «3000 на всё». Поднято до 60, чтобы реестр
# (растёт партиями по 50-60) догонял прод за один-два деплоя, а не тянулся
# неделями за счёт частоты рестартов процесса.
FNS_STARTUP_SYNC_LIMIT = 60

# Дневной потолок живых запросов к api-fns.ru (П5''', этап 3). НЕ от нехватки
# квоты — её достаточно (см. «Открытие, которое меняет бюджет» в CLAUDE.md),
# а от петли или бага: если что-то заставит процесс перезапускаться много раз
# подряд (сбойный деплой, крэш-луп), каждый старт без этой защиты бил бы по
# api-fns.ru заново. _fns_requests_today() считает по FnsSyncRun за текущие
# сутки UTC — строка в БД переживает сам рестарт, из-за которого счётчик
# понадобился. 200 — с большим запасом над одним нормальным стартом
# (FNS_STARTUP_SYNC_LIMIT=60 работ ~ до 180 запросов в худшем случае), но
# далеко от годовой квоты (3000/год на метод) — цель поймать петлю, а не
# экономить бюджет по запросу.
FNS_DAILY_REQUEST_CAP = 200

RESPONSES_URL = "https://ai.api.cloud.yandex.net/v1/responses"
# СКОЛЬКО ЖДЁТ ПОЛЬЗОВАТЕЛЬ. Раньше здесь стояли только «таймаут одной попытки
# 60 с» и «повторов 2» — и это молча означало худший случай 180 с ожидания с
# ПУСТЫМ ответом в конце: замер 7 августа на бою поймал ровно такой запрос
# (вопрос про сделки в фарме, 180,0 с, ноль знаков ответа). Три независимых
# таймаута не складывались ни в какое обещание пользователю. Теперь обещание
# одно — общий дедлайн; попытки укладываются в него, а не наоборот.
LLM_TIMEOUT = 30.0  # одна попытка
LLM_DEADLINE = float(os.environ.get("LLM_DEADLINE", "70"))  # весь ответ, включая повторы
LLM_RETRIES = 2  # повторов сверх первой попытки
# СКОЛЬКО МОДЕЛИ ПОЗВОЛЕНО «ДУМАТЬ» ДО ОТВЕТА. DeepSeek через Yandex рассуждает
# всегда, и эти токены генерируются ПОСЛЕДОВАТЕЛЬНО перед первым словом ответа —
# то есть прямо превращаются в ожидание пользователя. Замер 7 августа на бою:
# вопрос по базе с настоящим контекстом — 20,8 с, веб-режим — 25,8 с; владелец
# видел и больше 30. Бюджет в 8000 токенов брался с запасом «чтобы точно
# хватило», но задача ассистента — не олимпиадная математика, а выборка фактов
# из переданного JSON: столько рассуждений ей не нужно. Значение вынесено в
# переменную окружения, чтобы подбирать его без выкладки кода.
THINKING_BUDGET = int(os.environ.get("LLM_THINKING_BUDGET", "2000"))

# Общий keep-alive клиент (урок TruePost: не создавать новый на каждый вызов).
_http = httpx.Client(
    timeout=LLM_TIMEOUT,
    transport=httpx.HTTPTransport(retries=2),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)

SYSTEM_BASE = """Ты — ассистент платформы «КОМПАС» о сделках и компаниях российского рынка.
Отвечай ТОЛЬКО на основе базы данных, переданной в сообщении (JSON).
Правила:
- По-русски, кратко, как аналитик для юристов и банкиров.
- Ссылки на сделки платформы: [название](#/deal/ID).
- Разрешённое форматирование: ссылки [текст](адрес) и выделение **жирным**. Запрещены: заголовки #, списки с - или *, таблицы, код в ```.
- Никаких вступительных фраз («Отличный вопрос», «Конечно») — сразу ответ по существу.
- Не выдумывай факты, суммы, консультантов. Нет данных — так и скажи.
- Данные из публичных источников и могут быть неполными; упоминай это, когда уместно.
- Никаких рейтингов качества фирм — только факты."""

SYSTEM_WEB = """Ты — аналитик платформы «КОМПАС» о сделках и компаниях российского рынка.
У тебя два источника: база платформы (JSON в сообщении) и блок «СВЕЖАЯ ВЫДАЧА ПОИСКА (Яндекс)».

ГЛАВНОЕ: от тебя ждут ВЫВОД, а не пересказ выдачи со ссылками. Пользователь и сам
видит ссылки — ценность в том, что ты их сопоставил.
Структура ответа:
1. Первым абзацем — прямой ответ на вопрос одной-двумя фразами. Что произошло, кто
   участники, какая сумма. Без предисловий.
2. Дальше — существенные детали и, если они есть, связи: как это соотносится со
   сделками из базы «Компаса», продолжение ли это уже известной истории, сходятся ли
   цифры разных источников. Расхождение источников — само по себе важный факт, назови его.
3. Если из фактов следует осторожность (сумма только по оценке, сделка не закрыта,
   сторона не раскрыта) — скажи об этом прямо.

Правила достоверности:
- Факты бери ТОЛЬКО из базы и из блока выдачи. Ничего сверх этих двух источников не добавляй.
- Каждый факт из выдачи сопровождай ссылкой [название источника](URL) — URL из строки «Источник:».
- Чётко различай, что из базы «Компаса», а что найдено в сети.
- Нет данных ни в базе, ни в выдаче — так и скажи, коротко.

Форма: по-русски, как аналитик для юристов и банкиров, 3–6 предложений плюс детали.
Разрешено: ссылки [текст](адрес) и **жирный**. Запрещены: заголовки #, списки с - или *,
таблицы, код в ```. Никаких вступительных фраз вроде «Отличный вопрос»."""


class AskRequest(BaseModel):
    question: str
    context: str
    mode: str = "base"  # base | web
    thread_id: int | None = None
    context_type: str = "general"
    context_id: str | None = None
    save_thread: bool = True


def _yandex_ready() -> bool:
    return bool(os.environ.get("YANDEX_API_KEY")) and bool(os.environ.get("YANDEX_FOLDER_ID"))


@app.get("/health")
def health():
    return {"status": "ok", "ai": _yandex_ready()}


def _extract_text(data: dict) -> str:
    """Достаём текст из Responses API, отбрасывая reasoning-блоки DeepSeek."""
    parts: list[str] = []
    for item in data.get("output", []):
        if item.get("type") == "reasoning":
            continue
        if item.get("type") == "message":
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    parts.append(block.get("text", ""))
    if not parts and isinstance(data.get("output_text"), str):
        parts.append(data["output_text"])
    return "".join(parts).strip()


def call_llm(system: str, user: str, max_tokens: int, deadline: float | None = None) -> str:
    """Вызов Yandex AI Studio Responses API с ретраями. Пустой ответ/сбой -> RuntimeError.

    `deadline` — момент (time.monotonic), после которого попыток больше не будет.
    Повтор запускается, только если до дедлайна осталось хотя бы 8 секунд: иначе
    он гарантированно не успеет, а пользователь всё это время ждёт.
    """
    api_key = os.environ.get("YANDEX_API_KEY", "")
    folder_id = os.environ.get("YANDEX_FOLDER_ID", "")
    model = os.environ.get("YANDEX_MODEL", "deepseek-v4-flash/latest")
    payload = {
        "model": f"gpt://{folder_id}/{model}",
        "instructions": system,
        "input": user,
        "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
        "max_output_tokens": max_tokens + THINKING_BUDGET,
    }
    headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}

    last_err: Exception | None = None
    for attempt in range(1 + LLM_RETRIES):
        left = None if deadline is None else deadline - time.monotonic()
        if left is not None and left < 8:
            logger.warning("LLM: до дедлайна осталось %.1f с, попытку %d не начинаю", left, attempt + 1)
            break
        try:
            timeout = LLM_TIMEOUT if left is None else min(LLM_TIMEOUT, left)
            resp = _http.post(RESPONSES_URL, json=payload, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                raise RuntimeError(f"Responses API HTTP {resp.status_code}: {resp.text[:300]}")
            text = _extract_text(resp.json())
            if text:
                return text
            raise RuntimeError("Responses API вернул пустой текст")
        except (httpx.HTTPError, RuntimeError, ValueError) as e:
            last_err = e
            logger.warning("LLM attempt %d/%d failed: %s", attempt + 1, 1 + LLM_RETRIES, e)
    raise RuntimeError(f"LLM недоступен после {1 + LLM_RETRIES} попыток: {last_err}")


def _sources_footer(results: list[SearchResult]) -> str:
    """Список источников как markdown-ссылки — гарантия цитирования, даже если модель
    проигнорировала инструкцию про ссылки в тексте (DeepSeek это делает не всегда)."""
    lines = "\n".join(f"[{r.title}]({r.url})" for r in results[:5])
    return f"\n\nИсточники:\n{lines}"


@app.post("/api/ask")
def ask(req: AskRequest, request: Request, db=Depends(get_db)):
    if not _yandex_ready():
        return JSONResponse({"fallback": True})

    deadline = time.monotonic() + LLM_DEADLINE
    web = req.mode == "web"
    system = SYSTEM_BASE
    search_block = ""
    results: list = []

    if web:
        try:
            results = yandex_search(req.question, config=SearchConfig.from_env(), client=_http)
            if results:
                search_block = build_search_block(results)
                system = SYSTEM_WEB
            else:
                logger.info("web-режим: пустая выдача, деградация в base")
        except SearchError as e:
            logger.warning("web-режим: поиск упал (%s), деградация в base", e)

    user_msg = f"База данных платформы (JSON):\n{req.context}\n\n"
    if search_block:
        user_msg += f"{search_block}\n\n"
    user_msg += f"Вопрос пользователя: {req.question}"

    try:
        text = call_llm(system, user_msg, max_tokens=1400 if search_block else 700, deadline=deadline)
        if search_block and not _MD_LINK_RE.search(text):
            logger.info("web-режим: модель не дала ссылки сама, подставляю источники")
            text += _sources_footer(results)
        user = auth.current_user(db, request.cookies.get(auth.SESSION_COOKIE))
        thread_id = None
        if user and req.save_thread:
            thread = None
            if req.thread_id:
                thread = db.scalar(select(AssistantThread).where(
                    AssistantThread.id == req.thread_id,
                    AssistantThread.user_id == user.id,
                ))
            if not thread:
                title = " ".join(req.question.strip().split())[:120] or "Новый диалог"
                thread = AssistantThread(
                    user_id=user.id,
                    title=title,
                    context_type=(req.context_type or "general")[:30],
                    context_id=(req.context_id or None),
                )
                db.add(thread)
                db.flush()
            db.add(AssistantMessage(thread_id=thread.id, role="user", body=req.question, mode=req.mode))
            db.add(AssistantMessage(thread_id=thread.id, role="assistant", body=text, mode=req.mode))
            thread.updated_at = datetime.utcnow()
            db.commit()
            thread_id = thread.id
        payload = {"answer": text}
        if thread_id is not None:
            payload["thread_id"] = thread_id
        return payload
    except RuntimeError as e:
        logger.error("ask() failed: %s", e)
        # Поиск уже отработал, а модель не ответила — отдать найденное честнее,
        # чем общий отказ: ссылки на источники добыты и они по делу. Пустой
        # экран после минуты ожидания читается как «ассистент не работает».
        if results:
            return {"answer": "Не удалось собрать ответ — модель не ответила вовремя. "
                              "Вот что нашлось по вопросу в сети:" + _sources_footer(results)}
        return JSONResponse({"fallback": True})


# ==================== АККАУНТЫ: email + пароль, подписки, комментарии ====================
# Вход по email и паролю (auth.py), решение владельца от 2 августа 2026 —
# см. docstring auth.py. Раньше был вход по ссылке на почту без пароля, но он
# требовал SMTP (которого не было) и рисковал попасть в спам на каждый визит.

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: str | None = None
    position: str | None = None
    role: str = "individual"


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateIn(BaseModel):
    full_name: str | None = None
    company: str | None = None
    position: str | None = None
    role: str | None = None


class AccountDeleteIn(BaseModel):
    password: str


class SubscriptionIn(BaseModel):
    industry: str | None = None
    keyword: str | None = None
    min_amount_mln_rub: float | None = None


class CommentIn(BaseModel):
    body: str


class CorrectionIn(BaseModel):
    body: str
    contact: str | None = None


class NotificationPreferencesIn(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    telegram_enabled: bool | None = None
    weekly_digest: bool | None = None


class NotificationReadIn(BaseModel):
    ids: list[int] | None = None
    all: bool = False


class TelegramWebhookIn(BaseModel):
    update_id: int | None = None
    message: dict | None = None
    callback_query: dict | None = None


class DealExportIn(BaseModel):
    # Поле оставлено для обратной совместимости с будущим редактором, но сервер
    # формирует PDF из своей базы и не доверяет присланному HTML/тексту.
    title: str | None = None


def _current_user(request: Request, db=Depends(get_db)) -> User | None:
    return auth.current_user(db, request.cookies.get(auth.SESSION_COOKIE))


@app.post("/api/auth/register")
def register(req: RegisterRequest, response: Response, db=Depends(get_db)):
    user, err = auth.register_user(db, req.email, req.password, req.full_name,
                                    company=req.company, position=req.position, role=req.role)
    if not user:
        return JSONResponse({"error": err}, status_code=400)
    cookie = auth.create_session(db, user)
    response.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                         httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"ok": True}


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response, db=Depends(get_db)):
    user, err = auth.authenticate(db, req.email, req.password)
    if not user:
        return JSONResponse({"error": err}, status_code=400)
    cookie = auth.create_session(db, user)
    response.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                         httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db=Depends(get_db)):
    token = request.cookies.get(auth.SESSION_COOKIE)
    if token:
        auth.revoke_session(db, token)
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/me")
def me(user: User | None = Depends(_current_user)):
    # 200 всегда: анонимный визит — самое частое и совершенно нормальное
    # состояние, а не ошибка. Раньше отвечали 401, и браузер писал «Failed to
    # load resource: 401» в консоль при КАЖДОЙ загрузке страницы — что прямо
    # нарушает правило «в консоли нет ошибок» (test_ui.py) для анонимного
    # визитора, то есть почти всегда.
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, "email": user.email, "role": user.role.value,
            "tier": user.tier.value, "is_verified": user.is_verified,
            "full_name": user.full_name, "company": user.company, "position": user.position}


@app.patch("/api/me")
def update_profile(payload: ProfileUpdateIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    if payload.full_name is not None:
        full_name = payload.full_name.strip()
        if not (2 <= len(full_name) <= 200):
            return JSONResponse({"error": "укажите имя и фамилию"}, status_code=400)
        user.full_name = full_name
    if payload.company is not None:
        user.company = payload.company.strip() or None
    if payload.position is not None:
        user.position = payload.position.strip() or None
    if payload.role is not None:
        if not auth.valid_role(payload.role):
            return JSONResponse({"error": "неизвестный тип аккаунта"}, status_code=400)
        user.role = UserRole(payload.role)
    db.commit()
    return {"ok": True}


@app.delete("/api/account")
def delete_account(payload: AccountDeleteIn, request: Request, response: Response,
                    user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    if not user.password_hash or not auth.verify_password(payload.password, user.password_hash):
        return JSONResponse({"error": "неверный пароль"}, status_code=400)
    thread_ids = [t.id for t in db.query(AssistantThread).filter(AssistantThread.user_id == user.id).all()]
    if thread_ids:
        db.query(AssistantMessage).filter(AssistantMessage.thread_id.in_(thread_ids)) \
            .delete(synchronize_session=False)
    db.query(AssistantThread).filter(AssistantThread.user_id == user.id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == user.id).delete(synchronize_session=False)
    db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id) \
        .delete(synchronize_session=False)
    db.query(DealWatch).filter(DealWatch.user_id == user.id).delete(synchronize_session=False)
    db.query(SavedFilter).filter(SavedFilter.user_id == user.id).delete(synchronize_session=False)
    db.query(Comment).filter(Comment.user_id == user.id).delete(synchronize_session=False)
    db.query(CorrectionRequest).filter(CorrectionRequest.user_id == user.id).delete(synchronize_session=False)
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


# ==================== ФНС: ЕГРЮЛ, БФО, история изменений ====================

def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _entity_payload(entity: LegalEntity) -> dict:
    fields = (
        "id", "company_id", "legal_name", "short_name", "inn", "ogrn", "kpp",
        "legal_form", "status", "registration_date", "termination_date", "address",
        "region_code", "okved_code", "okved_name", "charter_capital_rub",
        "director_name", "director_title", "director_since", "source_provider",
        "source_updated_at", "fetched_at", "match_confidence", "manually_verified",
        "is_primary",
    )
    return {field: _plain(getattr(entity, field)) for field in fields}


def _report_payload(row: FinancialReport) -> dict:
    fields = (
        "year", "reporting_standard", "revenue_rub", "gross_profit_rub",
        "operating_profit_rub", "profit_before_tax_rub", "net_profit_rub",
        "assets_rub", "non_current_assets_rub", "current_assets_rub", "cash_rub",
        "receivables_rub", "inventory_rub", "equity_rub",
        "long_term_liabilities_rub", "short_term_liabilities_rub", "borrowings_rub",
        "payables_rub", "fetched_at",
    )
    return {field: _plain(getattr(row, field)) for field in fields}


def _owner_payload(row: OwnershipStake) -> dict:
    return {
        "key": row.owner_key,
        "name": row.owner_name,
        "type": row.owner_type,
        "inn": row.inn,
        "ogrn": row.ogrn,
        "country": row.country,
        "share_percent": _plain(row.share_percent),
        "nominal_value_rub": _plain(row.nominal_value_rub),
    }


def _is_ao_entity(entity: LegalEntity) -> bool:
    """ЕГРЮЛ хранит для акционерных обществ не текущих владельцев, а список
    УЧРЕДИТЕЛЕЙ на момент регистрации (реестр акционеров ведёт не ФНС, а
    сам регистратор/депозитарий) — в отличие от ООО, где участники в ЕГРЮЛ
    действительно актуальны. Определяем форму по `legal_form`/`short_name`:
    один и тот же regex для обеих веток `_ownership_payload` (раньше
    работал только когда снапшотов не было вовсе — П1''''', этап 5)."""
    form = f"{entity.legal_form or ''} {entity.short_name or ''}".lower()
    return bool(re.search(r"(?:^|\s)(?:пао|ао|оао|зао)(?:\s|$)|акционерн", form))


def _dedupe_owners(owners: list[dict]) -> list[dict]:
    """Одно лицо в ЕГРЮЛ иногда встречается в снапшоте дважды — записью с
    ИНН и записью без (два разных блока исходной выписки слиты в один
    снапшот при разборе). Схлопываем по нормализованному имени, предпочитая
    запись с ИНН — иначе на экране одно и то же лицо дублируется (П1''''',
    этап 5: «Горбатовский Александр Иванович» ×2, «Зубов Дмитрий Львович» ×2)."""
    by_key: dict[str, dict] = {}
    order: list[str] = []
    for owner in owners:
        key = re.sub(r"\s+", " ", str(owner.get("name") or "").strip().lower())
        if key not in by_key:
            by_key[key] = owner
            order.append(key)
        elif owner.get("inn") and not by_key[key].get("inn"):
            by_key[key] = owner
    return [by_key[k] for k in order]


def _ownership_payload(db, entity: LegalEntity, paid: bool) -> dict:
    is_ao = _is_ao_entity(entity)
    snapshots = list(db.scalars(select(OwnershipSnapshot).where(
        OwnershipSnapshot.legal_entity_id == entity.id
    ).order_by(OwnershipSnapshot.snapshot_date, OwnershipSnapshot.id)).all())
    if not snapshots:
        return {
            "available": False,
            "current": [],
            "history": [],
            "has_more_history": False,
            "is_ao": is_ao,
            "notice": ("ЕГРЮЛ не раскрывает состав акционеров акционерного общества. "
                       "Если акционеры названы в сообщениях эмитента или источниках сделки, "
                       "они показываются в карточках соответствующих сделок.") if is_ao else
                      "Сведения об участниках в полученных данных ЕГРЮЛ не найдены.",
        }

    enriched = []
    for snap in snapshots:
        stakes = list(db.scalars(select(OwnershipStake).where(
            OwnershipStake.snapshot_id == snap.id
        ).order_by(OwnershipStake.share_percent.desc(), OwnershipStake.owner_name)).all())
        enriched.append((snap, stakes))
    current_pair = next(((snap, stakes) for snap, stakes in reversed(enriched)
                         if snap.source_kind == "current"), enriched[-1])
    current = _dedupe_owners([_owner_payload(x) for x in current_pair[1]])

    def comparable(pair):
        snap, stakes = pair
        if snap.is_complete:
            return True
        return len(stakes) == 1 and float(stakes[0].share_percent or 0) == 100.0

    history = []
    previous = None
    for pair in enriched:
        snap, stakes = pair
        if snap.id == current_pair[0].id and previous is None:
            previous = pair
            continue
        if previous is None:
            previous = pair
            if snap.source_kind != "current":
                for stake in stakes:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "recorded",
                        "owner": _owner_payload(stake), "before_share": None,
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
            continue
        before_snap, before_stakes = previous
        before = {x.owner_key: x for x in before_stakes}
        after = {x.owner_key: x for x in stakes}
        if comparable(previous) and comparable(pair):
            for key, stake in after.items():
                old = before.get(key)
                if old is None:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "joined",
                        "owner": _owner_payload(stake), "before_share": None,
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
                elif _plain(old.share_percent) != _plain(stake.share_percent):
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "share_changed",
                        "owner": _owner_payload(stake), "before_share": _plain(old.share_percent),
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
            for key, stake in before.items():
                if key not in after:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "left",
                        "owner": _owner_payload(stake), "before_share": _plain(stake.share_percent),
                        "after_share": None, "source_text": snap.source_text,
                        "is_complete": snap.is_complete,
                    })
        elif snap.source_kind != "current":
            for stake in stakes:
                history.append({
                    "date": _plain(snap.snapshot_date), "kind": "recorded",
                    "owner": _owner_payload(stake), "before_share": None,
                    "after_share": _plain(stake.share_percent),
                    "source_text": snap.source_text, "is_complete": snap.is_complete,
                })
        previous = pair

    history.sort(key=lambda x: (x.get("date") or "", x.get("kind") or ""), reverse=True)
    shown = history if paid else history[:3]
    # П1''''', этап 5: для АО/ПАО этот снапшот — не «текущий состав», а
    # УЧРЕДИТЕЛИ на момент регистрации (см. _is_ao_entity) — ЕГРЮЛ реестр
    # акционеров вообще не ведёт, и показывать список 2002 года под
    # заголовком «Текущий» — не старость данных, а неверная подпись.
    heading = "Учредители при регистрации" if is_ao else "Текущий состав"
    notice = ("Показываем изменения, которые зафиксированы в ЕГРЮЛ. "
              "Для неполных исторических записей не восстанавливаем состав участников догадками.")
    if is_ao:
        notice = ("ЕГРЮЛ не отслеживает акционеров акционерного общества — здесь список "
                  "учредителей на момент регистрации, а не текущие владельцы. Актуальные "
                  "собственники, если раскрыты, — в блоке «Собственники» на странице компании.")
    return {
        "available": bool(current or history),
        "current": current,
        "as_of": _plain(current_pair[0].snapshot_date),
        "heading": heading,
        "is_ao": is_ao,
        "history": shown,
        "has_more_history": len(history) > len(shown),
        "notice": notice,
    }


@app.get("/api/fns/status")
def fns_status(db=Depends(get_db)):
    confirmed = db.query(LegalEntity).filter_by(match_status=LegalEntityMatchStatus.confirmed).count()
    synced = db.query(LegalEntity).filter(LegalEntity.fetched_at.is_not(None)).count()
    return {
        "configured": bool(os.environ.get("API_FNS_KEY")),
        "confirmed_entities": confirmed,
        "synced_entities": synced,
        "provider": "API-ФНС",
    }


@app.get("/api/companies/{company_id}/fns")
def company_fns(company_id: str, as_of_year: int | None = None, user: User | None = Depends(_current_user), db=Depends(get_db)):
    profile = get_company_profile(company_id)
    entities = list(db.scalars(select(LegalEntity).where(
        LegalEntity.company_id == company_id,
        LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
    ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id)).all())
    # Этап 6: `category` нужна фронтенду в ОБОИХ исходах — не только когда
    # юрлицо не сопоставлено вовсе (ветка ниже), но и когда LegalEntity УЖЕ
    # есть (часть банков когда-то была сопоставлена с ИНН до того, как для
    # них завели решение "bank" — коммерческие поля БФО у них пустые, а
    # категория раньше терялась). Без неё фронтенд не мог отличить банк от
    # обычной компании с пустой отчётностью и не мог решить, показывать ли
    # вместо ФНС-грида блок Банка России.
    registry_entry = fns_registry_by_company_id().get(company_id)
    registry_category = registry_entry["decision"] if registry_entry else None
    if not entities:
        # П5 (COMPANY_FINANCE_BRIEF.md): «нашли/не нашли» — не одно честное
        # состояние, а минимум шесть разных судеб (реестр pipeline/
        # fns_registry.py). Профиль без записи в реестре — тот же старый
        # «ещё не сопоставлено», ничего не меняется для большинства базы.
        decision = registry_category
        category_reasons = {
            "bank": "Кредитная организация — бухгалтерскую отчётность в общем "
                    "порядке банки не сдают, только по отдельной форме перед "
                    "Банком России.",
            "foreign": "Иностранное юридическое лицо — российской отчётности "
                       "ЕГРЮЛ/ФНС для него не существует.",
            "state_org": "Государственный орган или государственная корпорация — "
                         "бухгалтерскую отчётность в общем порядке не сдаёт.",
            "person": "Сторона сделки — физическое лицо, а не юридическое.",
            "lot": "Сторона сделки — несколько юридических лиц под одним "
                   "названием, а не одна компания.",
        }
        # person/lot — блок не рендерится вовсе (родня правилу «вкладка без
        # данных не показывается», CLAUDE.md), не пустое состояние с текстом.
        hidden = decision in ("person", "lot")
        return {
            "available": False,
            "hidden": hidden,
            "company_id": company_id,
            "company_name": profile.get("name") if profile else None,
            "configured": bool(os.environ.get("API_FNS_KEY")),
            "category": decision,
            "reason": category_reasons.get(decision, "Юридическое лицо ещё не сопоставлено с ЕГРЮЛ"),
        }
    paid = FNS_ALL_FREE or bool(user and user.tier == UserTier.paid)
    result = []
    for entity in entities:
        all_reports = list(db.scalars(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id
        ).order_by(FinancialReport.year.desc())).all())
        # Для карточки сделки показываем последний отчётный год ДО года сделки,
        # а не текущие показатели, появившиеся спустя несколько лет.
        stale_latest_year = None
        if as_of_year is not None:
            reports = [row for row in all_reports if row.year < as_of_year]
        else:
            # «Компания сегодня» не должна выглядеть моложе своей последней
            # отчётности на много лет: старше двух лет от текущего года —
            # честнее не показывать вовсе, чем выдавать за актуальное (владелец,
            # 18 августа — устаревшие 2020-2021 годы у банков/АФК «Система»
            # читались как обман). На историю сделки (as_of_year задан) это
            # правило не распространяется — там старый год того же периода,
            # что и сама сделка, и есть ровно то, что нужно показать.
            cutoff_year = datetime.now(timezone.utc).year - FNS_REPORT_MAX_AGE_YEARS
            reports = [row for row in all_reports if row.year >= cutoff_year]
            # Отличаем «отчётности нет вовсе» от «есть, но старше порога» —
            # это разные честные состояния и разный текст на экране.
            if not reports and all_reports:
                stale_latest_year = all_reports[0].year
        events = list(db.scalars(select(RegistryEvent).where(
            RegistryEvent.legal_entity_id == entity.id
        ).order_by(RegistryEvent.event_date.desc(), RegistryEvent.id.desc())).all())
        shown_reports = reports if paid else reports[:1]
        shown_events = events if paid else events[:3]
        result.append({
            "entity": _entity_payload(entity),
            "reports": [_report_payload(row) for row in shown_reports],
            "report_years": [row.year for row in reports],
            "stale_latest_year": stale_latest_year,
            "events": [{
                "id": row.id,
                "date": _plain(row.event_date),
                "type": row.event_type,
                "text": row.text,
            } for row in shown_events],
            "ownership": _ownership_payload(db, entity, paid),
            "has_more_reports": len(reports) > len(shown_reports),
            "has_more_events": len(events) > len(shown_events),
        })
    return {
        "available": True,
        "company_id": company_id,
        "company_name": profile.get("name") if profile else None,
        "category": registry_category,
        "entities": result,
        "access": {"paid": paid, "full_history": paid, "downloads": paid},
        "as_of_year": as_of_year,
        "disclaimer": "Показатели относятся к указанному юридическому лицу по РСБУ и могут не отражать консолидированные показатели всей группы.",
    }


def _confirmed_entity(db, company_id: str, entity_id: int | None = None) -> LegalEntity | None:
    query = select(LegalEntity).where(
        LegalEntity.company_id == company_id,
        LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
    )
    if entity_id is not None:
        query = query.where(LegalEntity.id == entity_id)
    return db.scalar(query.order_by(LegalEntity.is_primary.desc(), LegalEntity.id))


@app.get("/api/companies/{company_id}/fns/extract")
def company_fns_extract(company_id: str, entity_id: int | None = None,
                        user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы скачать выписку"}, status_code=401)
    entity = _confirmed_entity(db, company_id, entity_id)
    if not entity or not (entity.inn or entity.ogrn):
        return JSONResponse({"error": "юридическое лицо не сопоставлено"}, status_code=404)
    try:
        with ApiFnsClient() as client:
            response = client.extract_pdf(entity.inn or entity.ogrn)
    except ApiFnsError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    filename = f"egrul-{entity.inn or entity.ogrn}.pdf"
    return StreamingResponse(iter([response.content]), media_type=response.headers.get("content-type", "application/pdf"),
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/api/companies/{company_id}/fns/bo/{year}")
def company_fns_bo_file(company_id: str, year: int, entity_id: int | None = None, xls: bool = False,
                        user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы скачать отчётность"}, status_code=401)
    if not FNS_ALL_FREE and user.tier != UserTier.paid:
        return JSONResponse({"error": "скачивание полной отчётности доступно по подписке"}, status_code=403)
    entity = _confirmed_entity(db, company_id, entity_id)
    if not entity or not (entity.inn or entity.ogrn):
        return JSONResponse({"error": "юридическое лицо не сопоставлено"}, status_code=404)
    try:
        with ApiFnsClient() as client:
            response = client.bo_file(entity.inn or entity.ogrn, year, xls=xls)
    except ApiFnsError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    ext = "xlsx" if xls else "pdf"
    filename = f"bfo-{entity.inn or entity.ogrn}-{year}.{ext}"
    media = response.headers.get("content-type", "application/octet-stream")
    return StreamingResponse(iter([response.content]), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ==================== Уведомления и подписка на конкретную сделку ====================

@app.get("/api/deals/{deal_id}/watch")
def deal_watch_status(deal_id: str, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return {"logged_in": False, "watching": False}
    row = db.scalar(select(DealWatch).where(DealWatch.user_id == user.id, DealWatch.deal_id == deal_id))
    return {"logged_in": True, "watching": bool(row and row.active)}


@app.post("/api/deals/{deal_id}/watch")
def create_deal_watch(deal_id: str, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы подписаться на обновления"}, status_code=401)
    row = db.scalar(select(DealWatch).where(DealWatch.user_id == user.id, DealWatch.deal_id == deal_id))
    if not row:
        row = DealWatch(user_id=user.id, deal_id=deal_id)
        db.add(row)
    row.active = True
    notification_service.get_preferences(db, user.id)
    db.commit()
    return {"watching": True}


@app.delete("/api/deals/{deal_id}/watch")
def delete_deal_watch(deal_id: str, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = db.scalar(select(DealWatch).where(DealWatch.user_id == user.id, DealWatch.deal_id == deal_id))
    if row:
        row.active = False
        db.commit()
    return {"watching": False}


@app.get("/api/deal-watches")
def list_deal_watches(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    rows = list(db.scalars(select(DealWatch).where(
        DealWatch.user_id == user.id, DealWatch.active.is_(True)
    ).order_by(DealWatch.created_at.desc())).all())
    result = []
    for row in rows:
        deal = get_deal(row.deal_id) or {}
        result.append({"deal_id": row.deal_id, "title": deal.get("title") or row.deal_id,
                       "created_at": row.created_at.isoformat()})
    return result


@app.get("/api/notifications")
def list_notifications(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    prefs = notification_service.get_preferences(db, user.id)
    if not prefs.in_app_enabled:
        return []
    rows = list(db.scalars(select(Notification).where(Notification.user_id == user.id)
                           .order_by(Notification.created_at.desc()).limit(100)).all())
    return [{
        "id": row.id, "kind": row.kind, "title": row.title, "body": row.body,
        "link": row.link, "deal_id": row.deal_id, "is_read": row.is_read,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@app.post("/api/notifications/read")
def read_notifications(payload: NotificationReadIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if not payload.all:
        ids = payload.ids or []
        query = query.filter(Notification.id.in_(ids))
    query.update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"ok": True}


@app.get("/api/notification-preferences")
def get_notification_preferences(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = notification_service.get_preferences(db, user.id)
    return {
        "in_app_enabled": row.in_app_enabled,
        "email_enabled": row.email_enabled,
        "telegram_enabled": row.telegram_enabled,
        "weekly_digest": row.weekly_digest,
        "telegram_connected": bool(row.telegram_chat_id),
        "telegram_available": bool(os.environ.get("TELEGRAM_BOT_USERNAME")),
        "email_available": notification_service.email_configured(),
    }


@app.patch("/api/notification-preferences")
def update_notification_preferences(payload: NotificationPreferencesIn,
                                    user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = notification_service.get_preferences(db, user.id)
    for field in ("in_app_enabled", "email_enabled", "telegram_enabled", "weekly_digest"):
        value = getattr(payload, field)
        if value is not None:
            if field == "telegram_enabled" and value and not row.telegram_chat_id:
                return JSONResponse({"error": "сначала подключите Telegram"}, status_code=400)
            if field in ("email_enabled", "weekly_digest") and value and not notification_service.email_configured():
                return JSONResponse({"error": "почтовая рассылка ещё не подключена"}, status_code=400)
            setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.post("/api/notification-preferences/telegram-link")
def notification_telegram_link(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    url = notification_service.telegram_connect_url(db, user.id)
    if not url:
        return JSONResponse({"error": "Telegram-бот ещё не настроен"}, status_code=503)
    return {"url": url}


@app.post("/api/telegram/webhook/{secret}")
def telegram_webhook(secret: str, payload: TelegramWebhookIn, db=Depends(get_db)):
    expected = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    if not expected or secret != expected:
        return JSONResponse({"error": "not found"}, status_code=404)
    # Кнопка под черновиком карточки: callback_data вида "mod:<id>:ok|hold".
    # Решение пишется в таблицу, а применяет его рутина публикации — у неё нет
    # доступа к этой базе напрямую, поэтому она заберёт решение по
    # /api/moderation/decisions (см. модель ModerationDecision).
    callback = payload.callback_query or {}
    if callback:
        from_id = (callback.get("from") or {}).get("id")
        # Кнопки-вопросы под отчётом рутины («что скоро выйдет», «что
        # придержано»). Это НЕ вердикт: ничего не решают, только показывают
        # состав очереди, чтобы не идти искать его руками. Отчёт рутины стал
        # человеческим 9 августа (см. pipeline/ops_status.py), и кнопки —
        # его часть: цифра «6 карточек выйдут сами» бесполезна, если нельзя
        # тут же посмотреть, какие именно.
        # Кнопки меню под /start: очередь и сводка о платформе.
        menu = re.match(r"^menu:(queue|stats)$", str(callback.get("data") or ""))
        if menu:
            if not _is_reviewer(from_id):
                notification_service.tg_api(
                    "answerCallbackQuery", callback_query_id=callback.get("id"),
                    text="Это видят только владелец и партнёр.")
                return {"ok": True}
            body = _queue_report() if menu.group(1) == "queue" else _stats_report()
            notification_service.tg_api(
                "sendMessage",
                chat_id=(callback.get("message") or {}).get("chat", {}).get("id"),
                text=body, parse_mode="HTML", disable_web_page_preview=True)
            notification_service.tg_api("answerCallbackQuery",
                                        callback_query_id=callback.get("id"))
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
                    text="Очередь видят только владелец и партнёр.")
                return {"ok": True}
            chat = (callback.get("message") or {}).get("chat", {}).get("id")
            kind = show.group(1)
            notification_service.tg_api("answerCallbackQuery",
                                        callback_query_id=callback.get("id"))
            _send_queue_batch(chat, kind)
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
            db.add(ModerationDecision(deal_id=match.group(1), verdict=verdict,
                                      decided_by=str(from_id)))
            db.commit()
            _mark_decided(callback, verdict)
        elif callback.get("id"):
            notification_service.tg_api("answerCallbackQuery",
                                        callback_query_id=callback["id"],
                                        text="Решать могут только владелец и партнёр.")
        return {"ok": True}

    message = payload.message or {}
    text = str(message.get("text") or "")
    chat_id = (message.get("chat") or {}).get("id")
    # Право решать проверяется по ОТПРАВИТЕЛЮ (message.from.id), а не по чату,
    # в который упало сообщение (message.chat.id). В личном чате с ботом это
    # одно и то же число, и разница была не видна; в ГРУППЕ (владелец и
    # партнёр обсуждают черновики вместе) chat.id — это id самой группы, один
    # для всех участников, а не того, кто именно ответил. Проверка по chat_id
    # авторизовала бы либо всех членов группы разом, либо никого.
    sender_id = (message.get("from") or {}).get("id")
    # Ответ на сообщение бота. Что означает ответ — решает маркер в первой
    # строке того сообщения, НА КОТОРОЕ ответили:
    #   [пост <id>] / [черновик <id>] — ваш текст заменяет текст поста и
    #       одновременно одобряет карточку (вы поправили пост — вы его ждёте);
    #   [карточка <id>] / [сырьё <id>] — ваш текст ложится ЗАМЕТКОЙ: её
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
    reply = message.get("reply_to_message") or {}
    marker = re.search(r"\[(пост|черновик|карточка|сырьё|инн) ([\w-]{1,40})\]",
                       str(reply.get("text") or ""))
    if marker and text.strip() and _is_reviewer(sender_id):
        kind, raw_id = marker.group(1), marker.group(2)
        verdict = "approve" if kind in ("пост", "черновик") else "note"
        deal_id = ("инн~" + raw_id) if kind == "инн" else raw_id
        # chat_id/reply_message_id — только у заметок: только их читает и на
        # них отвечает рутина (read_notes.py), решению approve отвечать
        # реплаем не нужно, оно и так подтверждается штампом в сообщении.
        db.add(ModerationDecision(
            deal_id=deal_id, verdict=verdict, edited_text=text.strip(),
            decided_by=str(sender_id),
            chat_id=str(chat_id) if verdict == "note" and chat_id is not None else None,
            reply_message_id=reply.get("message_id") if verdict == "note" else None))
        db.commit()
        if verdict == "approve":
            notification_service._send_telegram(str(chat_id), "Принято: пост уйдёт с вашим текстом.")
        else:
            # МГНОВЕННОЕ ПОДТВЕРЖДЕНИЕ — раздел C MILESTONES_BRIEF.md. Раньше
            # заметка уходила в отдельное сообщение и терялась среди прочих;
            # штамп прямо в исходном [сырьё …]/[карточка …] — тот же приём,
            # что «— ✅ Одобрено» у _mark_decided, второй человек в группе
            # сразу видит, что заметка не повисла без ответа. Содержательный
            # ответ («что сделала, что нашла») придёт позже РЕПЛАЕМ от самой
            # рутины (read_notes.py читает chat_id/reply_message_id).
            who = (message.get("from") or {}).get("first_name") or "участник"
            original = str(reply.get("text") or "")
            stamped = "%s\n\n— 💬 Заметка принята (%s), рутина ответит после чтения" % (original, who)
            if chat_id is not None and reply.get("message_id"):
                notification_service.tg_api(
                    "editMessageText", chat_id=chat_id, message_id=reply["message_id"],
                    text=stamped, disable_web_page_preview=True)
        return {"ok": True}
    match = re.match(r"^/start\s+kompas_([A-Za-z0-9_-]+)$", text.strip())
    if match and chat_id is not None:
        notification_service.bind_telegram(db, match.group(1), str(chat_id))
        return {"ok": True}
    # Команды бота. Голый «/start» раньше не делал НИЧЕГО и молчал — человек
    # писал боту и получал тишину, неотличимую от поломки. В группе команда
    # приходит с суффиксом («/queue@compass_bot»), его надо отрезать.
    command = re.match(r"^/([a-z_]+)(?:@\S+)?\s*$", text.strip(), re.I)
    if command and chat_id is not None:
        name = command.group(1).lower()
        reply = _bot_command(name, sender_id)
        if reply:
            # У /start и /help — меню кнопками: текстом человек не понимает,
            # что вообще можно нажать, и команду приходится помнить наизусть.
            body = {"chat_id": str(chat_id), "text": reply, "parse_mode": "HTML",
                    "disable_web_page_preview": True}
            if name in ("start", "help") and _is_reviewer(sender_id):
                body["reply_markup"] = _bot_menu()
            notification_service.tg_api("sendMessage", **body)
    return {"ok": True}


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
    "по источнику и внесёт в карточку сама.\n\n"
    "<b>Как вернуться к отложенному</b>\n"
    "Нажмите кнопку ниже — карточки придут заново, каждая со своими кнопками. "
    "Решать можно прямо там, искать ничего не нужно.\n\n"
    "/queue — то же самое одним списком."
)


SITE_URL = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")
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
    # хорошо обогащённую карточку («HeadHunter»/Happy Job) за почти пустую
    # именно по этой урезанной строке.
    src = [s for s in (card.get("src") or []) if len(s) > 1]
    if len(src) == 1:
        parts.append("Источник: %s" % html_escape(str(src[0][0])))
    elif src:
        parts.append("Источники (%d): %s" % (
            len(src), html_escape(", ".join(str(s[0]) for s in src))))
    # Ссылка на ПОЛНУЮ карточку до публикации. Без неё видно только выжимку из
    # четырёх строк: владелец 10 августа не смог посмотреть карточку «Флит
    # Лизинг» именно потому, что ссылка до него не дошла — сообщение с ней
    # вообще не отправлялось.
    if card.get("id"):
        parts.append('<a href="%s/#/preview/%s">Открыть карточку целиком</a>'
                     % (SITE_URL, html_escape(str(card["id"]))))
    return "\n\n".join(parts)


def _send_queue_batch(chat_id, kind: str) -> int:
    """Прислать карточки очереди — каждую своим сообщением с кнопками.

    `kind`: held   — придержанные (можно опубликовать или выкинуть);
            soon   — прочитанные, выйдут по молчанию (можно придержать/выкинуть);
            unread — НЕ прочитанные против источника — по молчанию не выйдут
                     никогда, сколько бы часов ни прошло (см. approve.py,
                     `plan_actions`: непрочитанная карточка не публикуется
                     тишиной — это защита от каркасных дефектов черновика,
                     а не забытый таймер). Раньше "soon" считался как «всё,
                     что не придержано» — и такая карточка час за часом
                     отчитывалась как «выйдет сама», хотя не могла выйти,
                     пока её кто-то не прочитает: владелец 18 августа поймал
                     это на «Ленобласти»/«М.видео», зависших без единого
                     движения больше суток при одинаковом каждый час отчёте;
            raw    — сомнительные новости, которые ворота не пропустили.
    """
    if kind == "raw":
        state = _read_json("data/inbox/moderation_state.json", {})
        decided = set(state.get("decided_raw") or {})
        hold_dir = os.path.join(BASE_DIR, "data", "inbox", "hold")
        names = sorted(n for n in os.listdir(hold_dir)
                       if n.endswith(".json")) if os.path.isdir(hold_dir) else []
        drafts = (_read_json(os.path.join("data", "inbox", "hold", names[-1]), {})
                  .get("drafts") if names else None) or []
        items = [d for d in drafts if str(d.get("draft_id")) not in decided]
        head = ("⚠️ <b>Сомнительные новости: %d</b>\n"
                "Ворота их не пропустили. Без вашего слова не публикуются никогда."
                % len(items))
    else:
        pending = _read_json("static/data/pending.json", {}).get("cards") or []
        not_held = [c for c in pending if not c.get("held")]
        if kind == "held":
            items = [c for c in pending if c.get("held")]
            head = ("✋ <b>Вы придержали: %d</b>\nВыйдут только после «Опубликовать»."
                    % len(items))
        elif kind == "unread":
            items = [c for c in not_held if not c.get("reviewed")]
            head = ("📖 <b>Ждут прочтения: %d</b>\nПока карточку не сверят с "
                    "источником — молчание её не публикует, сама не выйдет."
                    % len(items))
        else:  # soon
            items = [c for c in not_held if c.get("reviewed")]
            head = ("⏳ <b>Выйдут сами: %d</b>\nЕсли ничего не нажимать — опубликуются "
                    "в течение суток." % len(items))

    notification_service.tg_api("sendMessage", chat_id=chat_id, text=head,
                                parse_mode="HTML", disable_web_page_preview=True)
    if not items:
        notification_service.tg_api("sendMessage", chat_id=chat_id,
                                    text="Сейчас пусто — решать нечего.")
        return 0

    shown = items[:BATCH_LIMIT]
    for item in shown:
        ident = str(item.get("draft_id") if kind == "raw" else item.get("id"))
        if kind == "raw":
            text = "⚠️ [сырьё %s]\n\n%s" % (ident, _card_line(item))
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
            # кнопку «Опубликовать сейчас» в очереди и не нашёл. Теперь везде
            # одинаковый полный набор, как в исходном сообщении, — карточка
            # выглядит и работает одинаково независимо от того, пришла она
            # только что или показана повторно через /queue.
            text = "🗂 [карточка %s]\n\n%s" % (ident, _card_line(item))
            keys = [[{"text": "✅ Опубликовать", "callback_data": "mod:%s:ok" % ident},
                     {"text": "✋ Придержать", "callback_data": "mod:%s:hold" % ident}],
                    [{"text": "✏️ Изменить", "callback_data": "mod:%s:edit" % ident},
                     {"text": "🗑 Выкинуть", "callback_data": "mod:%s:discard" % ident}]]
        notification_service.tg_api(
            "sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
            disable_web_page_preview=True, reply_markup={"inline_keyboard": keys})

    if len(items) > len(shown):
        # Умолчавший предел читается как «это всё» — называем его вслух.
        notification_service.tg_api(
            "sendMessage", chat_id=chat_id,
            text="Показаны первые %d из %d — нажмите кнопку ещё раз после решений."
                 % (len(shown), len(items)))
    return len(shown)


def _bot_menu() -> dict:
    """Меню под /start. Раньше команда отвечала стеной текста, и было
    непонятно, что вообще можно сделать, — кнопки показывают это сразу."""
    return {"inline_keyboard": [
        [{"text": "⏳ Что скоро выйдет", "callback_data": "show:soon"},
         {"text": "✋ Что придержано", "callback_data": "show:held"}],
        [{"text": "📖 Что ждёт прочтения", "callback_data": "show:unread"},
         {"text": "⚠️ Сомнительные новости", "callback_data": "show:raw"}],
        [{"text": "📊 Как дела у платформы", "callback_data": "menu:stats"}],
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
        "📖 Ждут прочтения (сами не выйдут): <b>%(queue_unread)d</b>\n"
        "✋ Вы придержали: <b>%(queue_held)d</b>\n\n"
        "🔧 <b>В работе</b>\n"
        "Не дополнены по источнику: <b>%(unread)d</b> из %(from_ingest)d\n"
        "Карточек 2026 года с бедным разбором: <b>%(thin_2026)d</b>"
    ) % n


def _read_json(path, default):
    try:
        with open(os.path.join(BASE_DIR, path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _queue_report() -> str:
    """Сводка по трём типам сообщений консоли — теми же значками, что и они.

    🗂/📣 — карточки предпросмотра (pending.json): ждут кнопки, по молчанию
    сутки уходят как есть. ⚠️ — сырьё, которое ворота не пропустили: решается
    только кнопкой под своим сообщением, по молчанию не публикуется никогда.
    """
    pending = _read_json("static/data/pending.json", {}).get("cards") or []
    held = [c for c in pending if c.get("held")]
    active = [c for c in pending if not c.get("held")]
    lines = ["🗂📣 Карточки и посты на проверке: %d" % len(active)]
    for card in active[:8]:
        lines.append("• %s" % str(card.get("title") or "")[:90])
    if len(active) > 8:
        lines.append("… и ещё %d" % (len(active) - 8))
    if held:
        lines.append("✋ Придержано вами: %d" % len(held))
        for card in held[:5]:
            lines.append("• %s" % str(card.get("title") or "")[:90])

    state = _read_json("data/inbox/moderation_state.json", {})
    decided = set((state.get("decided_raw") or {}))
    hold_dir = os.path.join(BASE_DIR, "data", "inbox", "hold")
    names = sorted(n for n in os.listdir(hold_dir) if n.endswith(".json")) \
        if os.path.isdir(hold_dir) else []
    drafts = (_read_json(os.path.join("data", "inbox", "hold", names[-1]), {}).get("drafts")
              if names else None) or []
    drafts = [d for d in drafts if str(d.get("draft_id")) not in decided]
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
        lines = ["Очередь пуста — всё решено. Новое приедет с утренним прогоном притока."]
    return "\n".join(lines)


def _bot_command(name: str, sender_id) -> str | None:
    if name in ("start", "help"):
        return BOT_HELP
    if name in ("queue", "ochered"):
        # Состав очереди — внутренняя кухня платформы, отвечаем только своим.
        if not _is_reviewer(sender_id):
            return "Эта команда доступна только владельцу и партнёру."
        return _queue_report()
    return None


_VERDICT_LABEL = {
    "approve": "✅ Карточка одобрена", "hold": "✋ Придержана",
    "discard": "🗑 Выкинута — не выйдет ни на сайт, ни в канал",
    "post_yes": "📣 Пост одобрен", "post_no": "🔕 Решено: без поста",
    "take": "✅ Признана сделкой — уйдёт в работу", "drop": "🗑 Отброшена как не-сделка",
}


def _mark_decided(callback: dict, verdict: str) -> None:
    """Показать решение В САМОМ сообщении — иначе в общей группе второй
    человек не видит, что первый уже нажал, и жмёт ещё раз. Кнопки снимаются,
    под текстом появляется строка «решил такой-то». Оба вызова best-effort:
    решение уже в таблице, и сбой отрисовки его не отменяет."""
    if callback.get("id"):
        notification_service.tg_api("answerCallbackQuery",
                                    callback_query_id=callback["id"], text="Принято")
    message = callback.get("message") or {}
    chat = (message.get("chat") or {}).get("id")
    if chat is None or not message.get("message_id"):
        return
    who = (callback.get("from") or {}).get("first_name") or "участник"
    stamped = "%s\n\n— %s (%s)" % (str(message.get("text") or ""),
                                   _VERDICT_LABEL.get(verdict, verdict), who)
    notification_service.tg_api("editMessageText", chat_id=chat,
                                message_id=message["message_id"], text=stamped,
                                disable_web_page_preview=True)


def _is_reviewer(chat_id) -> bool:
    """Право решать есть только у чатов из TELEGRAM_REVIEW_CHAT_IDS (владелец и
    партнёр). Любой другой человек, нашедший бота, решений не оставит."""
    allowed = {x.strip() for x in os.environ.get("TELEGRAM_REVIEW_CHAT_IDS", "").split(",") if x.strip()}
    return chat_id is not None and str(chat_id) in allowed


def _moderation_token_ok(token: str) -> bool:
    expected = os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or ""
    return bool(expected) and token == expected


def _ops_numbers() -> dict:
    """Цифры для дашборда основателей — считаются из тех же файлов, что и сайт.

    Ни одной величины «на глаз»: каждая берётся из данных, и рядом с ней в
    интерфейсе стоит подпись, ИЗ КАКОГО множества она получена (урок CLAUDE.md
    про то, что у числа на экране два свойства — величина и множество).
    """
    base = _read_json("static/data/deals_promoted.json", {})
    deals = base.get("deals") or []
    pending = (_read_json("static/data/pending.json", {}).get("cards") or [])

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
    published = sum(1 for v in posts.values() if v)

    return {
        "deals": len(deals),
        "companies": len(base.get("companies") or {}),
        "added_week": len(week),
        # «Скоро выйдет» — ТОЛЬКО прочитанные против источника: непрочитанная
        # карточка не публикуется по молчанию никогда (approve.py,
        # `plan_actions`), и раньше это число молча включало её тоже —
        # владелец 18 августа поймал два таких «зависших» примера.
        "queue_soon": sum(1 for c in pending if not c.get("held") and c.get("reviewed")),
        "queue_unread": sum(1 for c in pending if not c.get("held") and not c.get("reviewed")),
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
<p class="sub">Обновляется при каждом открытии. Все цифры считаются из тех же файлов, что отдаёт сайт.</p>
<div class="grid">
<div class="c"><div class="n">%(deals)d</div><div class="l">сделок на сайте</div></div>
<div class="c"><div class="n">%(companies)d</div><div class="l">профилей компаний</div></div>
<div class="c"><div class="n">%(added_week)d</div><div class="l">добавлено за 7 дней</div></div>
<div class="c"><div class="n">%(published)d</div><div class="l">постов в канале</div></div>
</div>
<h2>Ждёт вашего решения</h2>
<div class="grid">
<div class="c"><div class="n">%(queue_soon)d</div><div class="l">выйдут сами в течение суток</div></div>
<div class="c"><div class="n">%(queue_unread)d</div><div class="l">ждут прочтения — сами не выйдут</div></div>
<div class="c"><div class="n">%(queue_held)d</div><div class="l">вы придержали</div></div>
</div>
%(queue_list)s
<h2>Все карточки, которые ещё не опубликованы</h2>
<p class="hint">Их видно только здесь и в боте: на сайте они появятся после публикации.
Нажмите заголовок, чтобы открыть карточку целиком — ровно в том виде, в каком она выйдет.</p>
%(preview_list)s
<h2>Что ещё не доделано</h2>
<div class="grid">
<div class="c warn"><div class="n">%(unread)d</div><div class="l">из %(from_ingest)d карточек притока не дополнены по источнику</div></div>
<div class="c warn"><div class="n">%(thin_2026)d</div><div class="l">карточек 2026 года с почти пустыми разборами</div></div>
</div>
%(thin_list)s
</div></body></html>"""


@app.get("/ops")
def ops_dashboard(token: str = ""):
    """Панель основателей: то же, что рутина шлёт в Telegram, но целиком и
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
            return '<p class="empty">Сейчас в очереди пусто — всё опубликовано или выкинуто.</p>'
        rows = []
        for c in cards:
            tag = ' <span class="tag">придержана</span>' if c["held"] else ""
            rows.append('<li><a href="/#/preview/%s">%s</a>%s</li>'
                        % (html_escape(c["id"]), html_escape(c["title"]), tag))
        return '<ol class="prev">%s</ol>' % "".join(rows)

    page = OPS_PAGE % {
        **{k: v for k, v in n.items() if isinstance(v, int)},
        "queue_list": as_list(n["queue_titles"], "Очередь пуста — всё решено."),
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


@app.get("/api/moderation/decisions")
def moderation_decisions(token: str = "", db=Depends(get_db)):
    """Мост к рутине публикации: она в другом облаке и до базы не достаёт."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    rows = list(db.scalars(select(ModerationDecision)
                           .where(ModerationDecision.consumed.is_(False))
                           .order_by(ModerationDecision.created_at)).all())
    return {"decisions": [{"id": r.id, "deal_id": r.deal_id, "verdict": r.verdict,
                           "edited_text": r.edited_text, "decided_by": r.decided_by,
                           "chat_id": r.chat_id, "reply_message_id": r.reply_message_id,
                           "created_at": r.created_at.isoformat()} for r in rows]}


class ModerationConsumeIn(BaseModel):
    token: str = ""
    ids: list[int] = []


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


# ==================== История диалогов ассистента ====================

@app.get("/api/assistant/threads")
def list_assistant_threads(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    rows = list(db.scalars(select(AssistantThread).where(AssistantThread.user_id == user.id)
                           .order_by(AssistantThread.updated_at.desc()).limit(100)).all())
    return [{"id": row.id, "title": row.title, "context_type": row.context_type,
             "context_id": row.context_id, "updated_at": row.updated_at.isoformat()} for row in rows]


@app.get("/api/assistant/threads/{thread_id}")
def get_assistant_thread(thread_id: int, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    thread = db.scalar(select(AssistantThread).where(
        AssistantThread.id == thread_id, AssistantThread.user_id == user.id
    ))
    if not thread:
        return JSONResponse({"error": "диалог не найден"}, status_code=404)
    messages = list(db.scalars(select(AssistantMessage).where(AssistantMessage.thread_id == thread.id)
                               .order_by(AssistantMessage.created_at, AssistantMessage.id)).all())
    return {"id": thread.id, "title": thread.title, "context_type": thread.context_type,
            "context_id": thread.context_id,
            "messages": [{"role": row.role, "body": row.body, "mode": row.mode,
                           "created_at": row.created_at.isoformat()} for row in messages]}


@app.delete("/api/assistant/threads/{thread_id}")
def delete_assistant_thread(thread_id: int, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    thread = db.scalar(select(AssistantThread).where(
        AssistantThread.id == thread_id, AssistantThread.user_id == user.id
    ))
    if not thread:
        return JSONResponse({"error": "диалог не найден"}, status_code=404)
    db.delete(thread); db.commit()
    return {"ok": True}


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

@app.post("/api/deals/{deal_id}/export")
def export_deal(deal_id: str, _payload: DealExportIn | None = None,
                user: User | None = Depends(_current_user)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы скачать карточку"}, status_code=401)
    if user.tier != UserTier.paid:
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
    pdf = render_deal_pdf(enriched)
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", deal_id)[:80] + ".pdf"
    return StreamingResponse(iter([pdf]), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/api/subscriptions")
def list_subscriptions(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    rows = db.query(SavedFilter).filter_by(user_id=user.id, active=True).order_by(SavedFilter.created_at.desc()).all()
    return [{"id": r.id, "industry": r.industry, "keyword": r.keyword,
             "min_amount_mln_rub": float(r.min_amount_mln_rub) if r.min_amount_mln_rub is not None else None}
            for r in rows]


@app.post("/api/subscriptions")
def create_subscription(sub: SubscriptionIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    if not sub.industry and not sub.keyword:
        return JSONResponse({"error": "укажите отрасль или ключевое слово"}, status_code=400)
    row = SavedFilter(user_id=user.id, industry=sub.industry or None, keyword=sub.keyword or None,
                       min_amount_mln_rub=sub.min_amount_mln_rub)
    db.add(row)
    db.commit()
    return {"id": row.id}


@app.delete("/api/subscriptions/{sub_id}")
def delete_subscription(sub_id: int, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = db.get(SavedFilter, sub_id)
    if not row or row.user_id != user.id:
        return JSONResponse({"error": "не найдено"}, status_code=404)
    row.active = False
    db.commit()
    return {"ok": True}


# Комментарии видны сразу: писать может только вошедший по почте пользователь,
# и это уже проверенный e-mail — планка выше, чем у анонимного интернета.
# Модерация (жалоба/скрытие) — следующий шаг, не блокирующий первую версию;
# поле status у Comment для неё уже есть.
def _comment_author(user: User) -> str:
    # Регистрация с 2 августа 2026 требует «Имя и фамилию» (RegisterRequest.full_name
    # обязательное поле) — но подпись под комментарием строилась не из него, а из
    # локальной части e-mail (`email.split("@")[0]`): анонимный посетитель видел
    # кусок чужого адреса почты на каждом комментарии, а введённое при регистрации
    # имя нигде не показывалось. У аккаунтов старой схемы (до 2 августа) full_name
    # может быть пуст — для них оставлен прежний вид, единственный, что у них есть.
    name = (user.full_name or "").strip()
    return name if name else user.email.split("@")[0]


@app.get("/api/deals/{deal_id}/comments")
def list_comments(deal_id: str, db=Depends(get_db)):
    rows = (db.query(Comment)
            .filter_by(deal_id=deal_id, status="approved")
            .order_by(Comment.created_at.asc()).all())
    return [{"id": c.id, "body": c.body, "created_at": c.created_at.isoformat(),
             "author": _comment_author(c.user)} for c in rows]


@app.post("/api/deals/{deal_id}/comments")
def post_comment(deal_id: str, comment: CommentIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите по почте, чтобы комментировать"}, status_code=401)
    body = comment.body.strip()
    if not body:
        return JSONResponse({"error": "пустой комментарий"}, status_code=400)
    if len(body) > 4000:
        return JSONResponse({"error": "слишком длинный комментарий"}, status_code=400)
    row = Comment(deal_id=deal_id, user_id=user.id, body=body, status="approved")
    db.add(row)
    db.commit()
    return {"id": row.id, "created_at": row.created_at.isoformat(), "author": _comment_author(user)}


# «Уточнить или дополнить» отправляет сообщение прямо в продукт, а не открывает
# почтовый клиент. Вход намеренно не обязателен: для исправления ошибки в базе
# нельзя ставить барьер выше, чем сама форма. Публично эти сообщения не
# показываются — в отличие от Comment, это редакционная очередь.
def _save_correction(deal_id: str | None, correction: CorrectionIn, user: User | None, db):
    body = correction.body.strip()
    contact = (correction.contact or "").strip() or (user.email if user else None)
    if not body:
        return JSONResponse({"error": "напишите, что нужно уточнить"}, status_code=400)
    if len(body) > 4000:
        return JSONResponse({"error": "сообщение слишком длинное"}, status_code=400)
    if contact and len(contact) > 300:
        return JSONResponse({"error": "контакт слишком длинный"}, status_code=400)
    row = CorrectionRequest(deal_id=deal_id, user_id=user.id if user else None,
                            contact=contact, body=body, status="new")
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id}


@app.post("/api/deals/{deal_id}/corrections")
def post_correction(deal_id: str, correction: CorrectionIn,
                    user: User | None = Depends(_current_user), db=Depends(get_db)):
    return _save_correction(deal_id, correction, user, db)


@app.post("/api/corrections")
def post_general_correction(correction: CorrectionIn,
                            user: User | None = Depends(_current_user), db=Depends(get_db)):
    """Общее сообщение редакции из футера, без привязки к карточке."""
    return _save_correction(None, correction, user, db)


@app.get("/{full_path:path}")
def index(full_path: str):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
