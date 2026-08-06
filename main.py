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
from datetime import datetime
from decimal import Decimal

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
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
    DealWatch, FinancialReport, LegalEntity, LegalEntityMatchStatus, ModerationDecision,
    Notification,
    NotificationPreference, OwnershipSnapshot, OwnershipStake, RegistryEvent,
    SavedFilter, User, UserRole, UserTier, Webinar,
)
from db.session import engine, get_session
from fns_client import ApiFnsClient, ApiFnsError
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


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

RESPONSES_URL = "https://ai.api.cloud.yandex.net/v1/responses"
LLM_TIMEOUT = 60.0
LLM_RETRIES = 2  # повторов сверх первой попытки
THINKING_BUDGET = 8000  # DeepSeek: thinking включён всегда, отключить через Yandex нельзя

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

SYSTEM_WEB = """Ты — ассистент платформы «КОМПАС» о сделках и компаниях российского рынка.
У тебя два источника: база платформы (JSON в сообщении) и блок «СВЕЖАЯ ВЫДАЧА ПОИСКА (Яндекс)».
Правила:
- Сначала проверь базу; факты из интернета бери ТОЛЬКО из блока выдачи поиска. Не выдумывай ничего сверх этих двух источников.
- По-русски, кратко, как аналитик для юристов и банкиров.
- Ссылки на сделки платформы: [название](#/deal/ID). Для фактов из выдачи ОБЯЗАТЕЛЬНО указывай источник ссылкой [название источника](URL) — URL бери из строки «Источник:».
- Формат обязателен для КАЖДОГО факта из выдачи, без исключений. Пример: «Роснефть выкупила «Саянскхимпласт» за 30,3 млрд ₽ [Интерфакс](https://www.interfax.ru/...).» Факт из выдачи без ссылки сразу после него — ошибка, так делать нельзя.
- Чётко различай, что из базы «Компаса», а что найдено в сети.
- Разрешённое форматирование: ссылки [текст](адрес) и выделение **жирным**. Запрещены: заголовки #, списки с - или *, таблицы, код в ```.
- Никаких вступительных фраз — сразу ответ по существу.
- Нет данных ни в базе, ни в выдаче — так и скажи."""


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


def call_llm(system: str, user: str, max_tokens: int) -> str:
    """Вызов Yandex AI Studio Responses API с ретраями. Пустой ответ/сбой -> RuntimeError."""
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
        try:
            resp = _http.post(RESPONSES_URL, json=payload, headers=headers)
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
        text = call_llm(system, user_msg, max_tokens=1400 if search_block else 700)
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


def _ownership_payload(db, entity: LegalEntity, paid: bool) -> dict:
    snapshots = list(db.scalars(select(OwnershipSnapshot).where(
        OwnershipSnapshot.legal_entity_id == entity.id
    ).order_by(OwnershipSnapshot.snapshot_date, OwnershipSnapshot.id)).all())
    if not snapshots:
        form = f"{entity.legal_form or ''} {entity.short_name or ''}".lower()
        is_ao = bool(re.search(r"(?:^|\s)(?:пао|ао|оао|зао)(?:\s|$)|акционерн", form))
        return {
            "available": False,
            "current": [],
            "history": [],
            "has_more_history": False,
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
    current = [_owner_payload(x) for x in current_pair[1]]

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
    return {
        "available": bool(current or history),
        "current": current,
        "as_of": _plain(current_pair[0].snapshot_date),
        "history": shown,
        "has_more_history": len(history) > len(shown),
        "notice": ("Показываем изменения, которые зафиксированы в ЕГРЮЛ. "
                   "Для неполных исторических записей не восстанавливаем состав участников догадками."),
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
    if not entities:
        return {
            "available": False,
            "company_id": company_id,
            "company_name": profile.get("name") if profile else None,
            "configured": bool(os.environ.get("API_FNS_KEY")),
            "reason": "Юридическое лицо ещё не сопоставлено с ЕГРЮЛ",
        }
    paid = bool(user and user.tier == UserTier.paid)
    result = []
    for entity in entities:
        reports = list(db.scalars(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id
        ).order_by(FinancialReport.year.desc())).all())
        # Для карточки сделки показываем последний отчётный год ДО года сделки,
        # а не текущие показатели, появившиеся спустя несколько лет.
        if as_of_year is not None:
            reports = [row for row in reports if row.year < as_of_year]
        events = list(db.scalars(select(RegistryEvent).where(
            RegistryEvent.legal_entity_id == entity.id
        ).order_by(RegistryEvent.event_date.desc(), RegistryEvent.id.desc())).all())
        shown_reports = reports if paid else reports[:1]
        shown_events = events if paid else events[:3]
        result.append({
            "entity": _entity_payload(entity),
            "reports": [_report_payload(row) for row in shown_reports],
            "report_years": [row.year for row in reports],
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
    if not user or user.tier != UserTier.paid:
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
        match = re.match(r"^mod:([\w-]{1,40}):(ok|hold|discard|post_ok|post_no|take|drop|edit)$",
                         str(callback.get("data") or ""))
        from_id = (callback.get("from") or {}).get("id")
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
    reply = message.get("reply_to_message") or {}
    marker = re.search(r"\[(пост|черновик|карточка|сырьё) ([\w-]{1,40})\]",
                       str(reply.get("text") or ""))
    if marker and text.strip() and _is_reviewer(sender_id):
        kind, deal_id = marker.group(1), marker.group(2)
        verdict = "approve" if kind in ("пост", "черновик") else "note"
        db.add(ModerationDecision(deal_id=deal_id, verdict=verdict,
                                  edited_text=text.strip(), decided_by=str(sender_id)))
        db.commit()
        confirm = ("Принято: пост уйдёт с вашим текстом." if verdict == "approve"
                   else "Заметка записана — рутина притока применит её при следующем "
                        "прогоне через проверки review.py.")
        notification_service._send_telegram(str(chat_id), confirm)
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
        reply = _bot_command(command.group(1).lower(), sender_id)
        if reply:
            notification_service._send_telegram(str(chat_id), reply)
    return {"ok": True}


BOT_HELP = (
    "Бот «Компаса» — модерация новых карточек.\n\n"
    "/queue — что сейчас ждёт решения\n"
    "/help — эта справка\n\n"
    "Когда приток находит сделку, бот присылает сюда проект поста, ссылку на "
    "карточку (её ещё нет на сайте) и две кнопки. Ответ на сообщение с вашим "
    "текстом заменит текст поста. Молчание сутки — публикуем как есть."
)


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
@app.get("/api/deals/{deal_id}/comments")
def list_comments(deal_id: str, db=Depends(get_db)):
    rows = (db.query(Comment)
            .filter_by(deal_id=deal_id, status="approved")
            .order_by(Comment.created_at.asc()).all())
    return [{"id": c.id, "body": c.body, "created_at": c.created_at.isoformat(),
             "author": c.user.email.split("@")[0]} for c in rows]


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
    return {"id": row.id, "created_at": row.created_at.isoformat(), "author": user.email.split("@")[0]}


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
