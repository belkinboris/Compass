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
import logging
import os
import re

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

import auth
from db.models import Base as DBBase
from db.models import Comment, CorrectionRequest, SavedFilter, User
from db.session import engine, get_session
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
    except Exception as e:  # БД недоступна — сайт и без аккаунтов должен жить
        logger.error("не удалось создать таблицы аккаунтов: %s", e)


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
def ask(req: AskRequest):
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
        return {"answer": text}
    except RuntimeError as e:
        logger.error("ask() failed: %s", e)
        return JSONResponse({"fallback": True})


# ==================== АККАУНТЫ: вход по ссылке, подписки, комментарии ====================
# Вход по ссылке на почту (auth.py), решение владельца от 28 июля 2026 — см.
# docstring auth.py. Отправка письма пока не подключена: SMTP не задан, ссылка
# уходит в лог сервера строкой "[DEV]", а не в теле ответа (иначе введённая
# чужая почта отдавала бы чужую ссылку для входа прямо в браузере).

class LoginRequest(BaseModel):
    email: str


class SubscriptionIn(BaseModel):
    industry: str | None = None
    keyword: str | None = None
    min_amount_mln_rub: float | None = None


class CommentIn(BaseModel):
    body: str


class CorrectionIn(BaseModel):
    body: str
    contact: str | None = None


def _current_user(request: Request, db=Depends(get_db)) -> User | None:
    return auth.current_user(db, request.cookies.get(auth.SESSION_COOKIE))


@app.post("/api/auth/request-link")
def request_link(req: LoginRequest, request: Request, db=Depends(get_db)):
    if not auth.valid_email(req.email):
        return JSONResponse({"error": "некорректная почта"}, status_code=400)
    base_url = str(request.base_url).rstrip("/")
    auth.request_login_link(db, req.email, base_url)
    # Один и тот же ответ независимо от того, существовал пользователь раньше
    # или нет: иначе по ответу можно узнавать, зарегистрирован ли чужой адрес.
    return {"ok": True}


@app.get("/api/auth/verify")
def verify_link(token: str, db=Depends(get_db)):
    user, err = auth.verify_login_token(db, token)
    if not user:
        return RedirectResponse(url="/#/account?error=" + err.replace(" ", "+"), status_code=302)
    cookie = auth.create_session(db, user)
    resp = RedirectResponse(url="/#/account", status_code=302)
    resp.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                     httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return resp


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
            "tier": user.tier.value, "is_verified": user.is_verified}


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
