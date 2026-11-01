# -*- coding: utf-8 -*-
"""Аккаунты: регистрация и вход, кабинет, подписки, уведомления, комментарии,
правки от посетителей, кабинет компании, таблицы на старте, сводка за неделю
(docs/server_layout.md)."""
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import auth
import base_data
import deal_catalog
import notification_service
import subscription_feed
from deal_catalog import get_deal
from db.models import Base as DBBase
from db.models import (
    AppSetting,
    AssistantFeedback,
    AssistantMessage,
    AssistantThread,
    AuthSession,
    Comment,
    CompanyClaim,
    CorrectionRequest,
    DealWatch,
    Notification,
    NotificationPreference,
    PageView,
    SavedFilter,
    User,
    UserRole,
)
from db.session import engine, get_session
from sqlalchemy import func, inspect, select, text

from app import core
from app.core import STATIC_DIR, get_db, logger, _current_user, _moderation_token_ok, COOKIE_SECURE, SITE_URL

router = APIRouter()


def _ensure_user_columns(db_engine) -> None:
    """Колонки users, которых нет в таблице, созданной до их появления в модели.

    password_hash добавлен в User 2 августа — create_all его на уже
    СУЩЕСТВОВАВШЕЙ (до этой даты) таблице users не создаст: он создает
    только недостающие ТАБЛИЦЫ целиком, а не недостающие колонки в уже
    существующих. `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — синтаксис
    только Postgres, на SQLite это просто синтаксическая ошибка (проверено
    здесь же: колонка молча не добавлялась). Проверяем через инспектор
    SQLAlchemy — он одинаково работает на обоих диалектах — и добавляем
    обычным ADD COLUMN без IF NOT EXISTS, который тоже понимают оба.
    Вынесено в функцию с параметром-движком, чтобы миграцию можно было
    проверить тестом на отдельной базе со «старой» таблицей.
    """
    with db_engine.begin() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("users")}
        if "password_hash" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(200)"))
        # full_name/company/position добавлены 2 августа тем же способом —
        # см. комментарий выше про password_hash, тот же диалект-независимый прием.
        for col in ("full_name", "company", "position"):
            if col not in cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(200)"))
        # approved добавлен 2 сентября (вход по заявке, core.ACCESS_GATE). Всем
        # УЖЕ существующим аккаунтам ставим True — иначе владелец и партнер,
        # зарегистрировавшиеся до гейта, оказались бы за дверью, которую
        # сами же и держат. Значение задаем отдельным UPDATE с параметром, а
        # не `DEFAULT TRUE` в ALTER: литерал TRUE понимают не все версии
        # SQLite, а `DEFAULT 1` не примет Postgres для BOOLEAN — параметр
        # SQLAlchemy привязывает верно для обоих диалектов.
        if "approved" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN approved BOOLEAN"))
            conn.execute(text("UPDATE users SET approved = :yes WHERE approved IS NULL"), {"yes": True})
        # comment_name_consent_at — 16 октября 2026, отдельное согласие на
        # показ имени у комментариев. TIMESTAMP понимают и SQLite, и Postgres;
        # у существующих аккаунтов остается пустым: согласие спросим при
        # первом комментарии.
        if "comment_name_consent_at" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN comment_name_consent_at TIMESTAMP"))


def _create_account_tables():
    try:
        DBBase.metadata.create_all(engine)
        try:
            _ensure_user_columns(engine)
        except Exception as e:
            logger.error("не удалось добавить колонки в users: %s", e)
        # chat_id/reply_message_id добавлены в moderation_decisions 22 августа
        # для ответа рутины реплаем на заметку (раздел C MILESTONES_BRIEF.md) —
        # тот же диалект-независимый прием инспектора, что и выше для users.
        try:
            with engine.begin() as conn:
                cols = {c["name"] for c in inspect(conn).get_columns("moderation_decisions")}
                if "chat_id" not in cols:
                    conn.execute(text("ALTER TABLE moderation_decisions ADD COLUMN chat_id VARCHAR(40)"))
                if "reply_message_id" not in cols:
                    conn.execute(text("ALTER TABLE moderation_decisions ADD COLUMN reply_message_id INTEGER"))
        except Exception as e:
            logger.error("не удалось добавить chat_id/reply_message_id в moderation_decisions: %s", e)
        # company_id добавлен в saved_filters 19 сентября 2026 (подписка на
        # компанию). Тот же диалект-независимый прием инспектора: колонка
        # nullable, поэтому ничего не досчитываем — у старых подписок
        # компании и не было.
        try:
            with engine.begin() as conn:
                cols = {c["name"] for c in inspect(conn).get_columns("saved_filters")}
                if "company_id" not in cols:
                    conn.execute(text("ALTER TABLE saved_filters ADD COLUMN company_id VARCHAR(40)"))
        except Exception as e:
            logger.error("не удалось добавить company_id в saved_filters: %s", e)
        # deal_id расширен с 40 до 80 знаков 22 августа: у вехи это
        # "<id сделки>~<вид этапа>", длиннее одного голого id. SQLite VARCHAR
        # не проверяется движком вообще (хранится как TEXT) — расширять там
        # нечего; Postgres проверяет строго, и без ALTER запись веха-решения
        # там упала бы с ошибкой длины, которую на SQLite никто бы не увидел.
        # ALTER COLUMN TYPE — тоже синтаксис только Postgres, SQLite его не
        # поддерживает вовсе — тот же диалект-независимый прием: действие
        # только там, где оно применимо и нужно.
        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    conn.execute(text(
                        "ALTER TABLE moderation_decisions ALTER COLUMN deal_id TYPE VARCHAR(80)"))
        except Exception as e:
            logger.error("не удалось расширить deal_id в moderation_decisions: %s", e)
        # event_type в registry_events расширен со 160 до 400 знаков 7 сентября
        # 2026 — тот же класс, что и deal_id выше, и найден он так же: на
        # проде, не тестами. ЕГРЮЛ пишет в «тип события» целое предложение
        # («Регистрирующим органом принято решение о предстоящем исключении
        # юридического лица из ЕГРЮЛ…» — 189 знаков), Postgres отверг вставку
        # (StringDataRightTruncation), и докачка ФНС по этой компании
        # откатилась целиком. SQLite длину VARCHAR не проверяет вовсе, поэтому
        # ни один локальный прогон этого увидеть не мог.
        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    conn.execute(text(
                        "ALTER TABLE registry_events ALTER COLUMN event_type TYPE VARCHAR(400)"))
        except Exception as e:
            logger.error("не удалось расширить event_type в registry_events: %s", e)
        # app_settings.value — с 255 знаков до TEXT, 5 октября 2026. Тот же
        # класс, что deal_id и event_type выше: туда теперь пишутся прогоны
        # притока за день (сводка в 18:00) и готовый текст поста об этапе
        # сделки (публикация по кнопке), оба длиннее 255 знаков. Postgres
        # отверг бы запись, SQLite в тестах длину не проверяет. Тип меняем,
        # только пока у колонки есть предел длины, — без лишней блокировки
        # таблицы на каждом старте.
        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    cols = {c["name"]: c for c in inspect(conn).get_columns("app_settings")}
                    if getattr(cols.get("value", {}).get("type"), "length", None):
                        conn.execute(text("ALTER TABLE app_settings ALTER COLUMN value TYPE TEXT"))
        except Exception as e:
            logger.error("не удалось расширить value в app_settings: %s", e)
    except Exception as e:  # БД недоступна — сайт и без аккаунтов должен жить
        logger.error("не удалось создать таблицы аккаунтов: %s", e)


# Подписки сверяются здесь, а не в притоке: приток работает в другом облаке, а
# база пользователей стоит во внутренней сети хостинга и оттуда недостижима.
# Первый прогон никого не будит: он только запоминает состав базы.
# ВАЖНО с 3 сентября 2026: старт процесса больше НЕ единственный момент, когда
# есть что сверять, — новые карточки теперь приезжают подтягиванием данных без
# перезапуска (data_refresh.py), и после каждой такой замены сверка зовется
# оттуда же. Здесь она осталась ради первого прогона после деплоя.
def _match_subscriptions_against_new_deals():
    subscription_feed.scan_on_startup()


# СВОДКА ЗА НЕДЕЛЮ (4 октября 2026). Переключатель в кабинете был, скрипт
# pipeline/send_weekly_digest.py был, а запускать его было некому: рутины не
# видят базу пользователей, а cron на хостинге не заведен. Сайт видит и базу,
# и Telegram — значит, рассылает он: по понедельникам с 10:00 МСК, один раз
# за неделю. Ключ недели пишется в app_settings ДО рассылки: перезапуск
# посреди понедельника не повторит ее. `WEEKLY_DIGEST=0` — выключить.
WEEKLY_DIGEST = os.environ.get("WEEKLY_DIGEST", "1") != "0"
WEEKLY_DIGEST_HOUR_MSK = 10


def _weekly_digest_key(now_utc: datetime) -> str | None:
    msk = now_utc.astimezone(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)
    if msk.weekday() != 0 or msk.hour < WEEKLY_DIGEST_HOUR_MSK:
        return None
    year, week, _ = msk.isocalendar()
    return "weekly_digest:%d-W%02d" % (year, week)


def _weekly_digest_once(db, now_utc: datetime | None = None) -> int | None:
    """Разослать сводку, если пора и на этой неделе ее еще не было.
    None — не пора или уже разослана; число — сколько адресатов."""
    now_utc = now_utc or datetime.now(timezone.utc)
    key = _weekly_digest_key(now_utc)
    if not key or db.get(AppSetting, key):
        return None
    db.add(AppSetting(key=key, value=now_utc.isoformat(timespec="seconds")))
    try:
        db.commit()
    except Exception:                                        # noqa: BLE001
        db.rollback()          # другой процесс успел первым
        return None
    from pipeline.send_weekly_digest import send_digest
    msk_today = (now_utc.astimezone(timezone.utc) + timedelta(hours=3)).date()
    return send_digest(db, list(deal_catalog.load_deals().values()), msk_today, SITE_URL)


def _start_weekly_digest():
    if not WEEKLY_DIGEST or os.environ.get("PYTEST_CURRENT_TEST"):
        return

    def _run():
        while True:
            time.sleep(600)
            db = get_session()
            try:
                sent = _weekly_digest_once(db)
                if sent is not None:
                    logger.info("сводка за неделю разослана: %d адресатов", sent)
            except Exception as exc:                             # noqa: BLE001
                logger.error("сводка за неделю не разослана: %s", exc)
            finally:
                db.close()

    threading.Thread(target=_run, daemon=True).start()


def _notify_access_request(user: User, db=None) -> None:
    """Заявка на доступ — в Telegram-консоль основателей, с кнопками
    «Одобрить»/«Отклонить» (callback_data `acc:<id>:ok|no`, разбирается в
    telegram_webhook рядом с `mod:`). Тот же путь, что у обратной связи
    ассистента: `core._review_chat_ids()` + `notification_service.tg_api`. Сбой
    отправки регистрацию не роняет — заявка уже в таблице, а без токена
    (локальная разработка, тесты) вызов молча ничего не делает."""
    try:
        chats = core._review_chat_ids(db)
        if not chats:
            logger.warning("заявка на доступ #%s: консоль не настроена, в Telegram не ушла", user.id)
            return
        when = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m.%Y %H:%M МСК")
        text = "\n".join([
            f"🔑 Заявка на доступ: {user.full_name or '—'}, "
            f"{user.company or 'компания не указана'}, {user.position or 'должность не указана'}",
            f"Почта: {user.email}",
            f"Отправлена: {when}",
        ])
        keys = [[{"text": "✅ Одобрить", "callback_data": "acc:%d:ok" % user.id},
                 {"text": "🗑 Отклонить", "callback_data": "acc:%d:no" % user.id}]]
        thread = core._console_thread_id(db, "admin") if db is not None else None
        for chat in chats:
            notification_service.tg_api("sendMessage", chat_id=chat, text=text,
                                        reply_markup={"inline_keyboard": keys},
                                        disable_web_page_preview=True,
                                        **({"message_thread_id": thread} if thread else {}))
    except Exception as exc:  # noqa: BLE001 — регистрация важнее уведомления
        logger.error("заявка на доступ #%s: не удалось отправить в Telegram: %s", user.id, exc)


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


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


class EmailChangeIn(BaseModel):
    password: str
    new_email: str


class SubscriptionIn(BaseModel):
    industry: str | None = None
    company_id: str | None = None
    keyword: str | None = None
    min_amount_mln_rub: float | None = None


class CommentIn(BaseModel):
    body: str
    # Галочка «Согласен, чтобы рядом с моим комментарием показывались мои имя
    # и фамилия» — нужна только под первым комментарием (см. post_comment).
    name_consent: bool = False


class CorrectionIn(BaseModel):
    body: str
    contact: str | None = None
    kind: str | None = None          # "consultant" — кнопка «Вы консультант?» в каталоге


class NotificationPreferencesIn(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    telegram_enabled: bool | None = None
    weekly_digest: bool | None = None


class NotificationReadIn(BaseModel):
    ids: list[int] | None = None
    all: bool = False


GATE_PENDING_TEXT = "Заявка получена, доступ откроем после проверки. Попробуйте войти позже."


@router.post("/api/auth/register")
def register(req: RegisterRequest, response: Response, db=Depends(get_db)):
    user, err = auth.register_user(db, req.email, req.password, req.full_name,
                                    company=req.company, position=req.position, role=req.role,
                                    approved=not core.ACCESS_GATE)
    if not user:
        return JSONResponse({"error": err}, status_code=400)
    if core.ACCESS_GATE:
        # Заявка, а не вход: сессию не ставим, владельцу уходит сообщение с
        # кнопками. Войти человек сможет после «Одобрить» (см. telegram_webhook).
        _notify_access_request(user, db)
        return {"ok": True, "pending": True}
    cookie = auth.create_session(db, user)
    response.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                         httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"ok": True}


@router.post("/api/auth/login")
def login(req: LoginRequest, response: Response, db=Depends(get_db)):
    user, err = auth.authenticate(db, req.email, req.password)
    if not user:
        return JSONResponse({"error": err}, status_code=400)
    if core.ACCESS_GATE and not user.approved:
        # Пароль верный, но заявка еще не одобрена (или отклонена — снаружи это
        # одно и то же «доступ не открыт», отклоненных не удаляем и не выдаем).
        return JSONResponse({"error": GATE_PENDING_TEXT, "pending": True}, status_code=403)
    cookie = auth.create_session(db, user)
    response.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                         httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"ok": True}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response, db=Depends(get_db)):
    token = request.cookies.get(auth.SESSION_COOKIE)
    if token:
        auth.revoke_session(db, token)
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


@router.get("/api/me")
def me(user: User | None = Depends(_current_user)):
    # 200 всегда: анонимный визит — самое частое и совершенно нормальное
    # состояние, а не ошибка. Раньше отвечали 401, и браузер писал «Failed to
    # load resource: 401» в консоль при КАЖДОЙ загрузке страницы — что прямо
    # нарушает правило «в консоли нет ошибок» (test_ui.py) для анонимного
    # визитора, то есть почти всегда.
    # gate — включен ли вход по заявке: по нему интерфейс решает, показывать
    # сайт или экран «Войти / Запросить доступ» (см. core.ACCESS_GATE).
    if not user:
        return {"logged_in": False, "gate": core.ACCESS_GATE}
    return {"logged_in": True, "email": user.email, "role": user.role.value,
            "tier": user.tier.value, "is_verified": user.is_verified,
            "full_name": user.full_name, "company": user.company, "position": user.position,
            "gate": core.ACCESS_GATE, "approved": bool(user.approved),
            "comment_name_consent": user.comment_name_consent_at is not None}


@router.patch("/api/me")
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


@router.post("/api/auth/password")
def change_password(payload: PasswordChangeIn, response: Response,
                     user: User | None = Depends(_current_user), db=Depends(get_db)):
    """Смена пароля. Просьба Артема 19 сентября 2026: на вкладке «Аккаунт»
    ее не было вовсе — сменить пароль было нельзя никак."""
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    ok, err = auth.change_password(db, user, payload.current_password, payload.new_password)
    if not ok:
        return JSONResponse({"error": err}, status_code=400)
    # Все входы погашены, включая этот: выдаем новый, иначе человек вылетит
    # из собственного браузера ровно в тот момент, когда сменил пароль.
    cookie = auth.create_session(db, user)
    response.set_cookie(auth.SESSION_COOKIE, cookie, max_age=int(auth.SESSION_TTL.total_seconds()),
                         httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return {"ok": True}


@router.post("/api/auth/email")
def change_email(payload: EmailChangeIn, user: User | None = Depends(_current_user),
                  db=Depends(get_db)):
    """Смена почты. Ксюша, тот же день: «И в идеале почту»."""
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    ok, err = auth.change_email(db, user, payload.password, payload.new_email)
    if not ok:
        return JSONResponse({"error": err}, status_code=400)
    return {"ok": True, "email": user.email}


@router.delete("/api/account")
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
    # Оценки ответов ассистента уходят вместе с аккаунтом (16 октября 2026):
    # в них вопрос, ответ и комментарий человека. Удаляются до диалогов — на
    # диалог оценка ссылается (thread_id), и Postgres не дал бы удалить диалог
    # раньше нее. Оценки по диалогам этого человека — тоже, даже если оставлены
    # без входа: диалог его, и после удаления ссылаться им не на что.
    feedback = db.query(AssistantFeedback).filter(AssistantFeedback.user_id == user.id)
    feedback.delete(synchronize_session=False)
    if thread_ids:
        db.query(AssistantFeedback).filter(AssistantFeedback.thread_id.in_(thread_ids)) \
            .delete(synchronize_session=False)
    db.query(AssistantThread).filter(AssistantThread.user_id == user.id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == user.id).delete(synchronize_session=False)
    db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id) \
        .delete(synchronize_session=False)
    db.query(DealWatch).filter(DealWatch.user_id == user.id).delete(synchronize_session=False)
    db.query(SavedFilter).filter(SavedFilter.user_id == user.id).delete(synchronize_session=False)
    db.query(Comment).filter(Comment.user_id == user.id).delete(synchronize_session=False)
    db.query(CorrectionRequest).filter(CorrectionRequest.user_id == user.id).delete(synchronize_session=False)
    db.query(CompanyClaim).filter(CompanyClaim.user_id == user.id).delete(synchronize_session=False)
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


# ==================== Уведомления и подписка на конкретную сделку ====================

@router.get("/api/deals/{deal_id}/watch")
def deal_watch_status(deal_id: str, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return {"logged_in": False, "watching": False}
    row = db.scalar(select(DealWatch).where(DealWatch.user_id == user.id, DealWatch.deal_id == deal_id))
    return {"logged_in": True, "watching": bool(row and row.active)}


@router.post("/api/deals/{deal_id}/watch")
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


@router.delete("/api/deals/{deal_id}/watch")
def delete_deal_watch(deal_id: str, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = db.scalar(select(DealWatch).where(DealWatch.user_id == user.id, DealWatch.deal_id == deal_id))
    if row:
        row.active = False
        db.commit()
    return {"watching": False}


@router.get("/api/deal-watches")
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


@router.get("/api/notifications")
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


@router.post("/api/notifications/read")
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


@router.get("/api/notification-preferences")
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
        "telegram_bot": os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@") or None,
        "email_available": notification_service.email_configured(),
    }


@router.patch("/api/notification-preferences")
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
            # Сводка за неделю приходит на сайт и в Telegram — почта ей не
            # обязательна (до 4 октября 2026 переключатель был заперт до
            # подключения почты и висел с подписью «Скоро»).
            if field == "email_enabled" and value and not notification_service.email_configured():
                return JSONResponse({"error": "почтовая рассылка еще не подключена"}, status_code=400)
            setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.post("/api/notification-preferences/telegram-link")
def notification_telegram_link(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    url = notification_service.telegram_connect_url(db, user.id)
    if not url:
        return JSONResponse({"error": "Telegram-бот еще не настроен"}, status_code=503)
    return {"url": url, "code": notification_service.telegram_connect_code(db, user.id)}


@router.delete("/api/notification-preferences/telegram-link")
def notification_telegram_unlink(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    notification_service.unlink_telegram(db, user.id)
    return {"ok": True}


@router.get("/api/subscriptions")
def list_subscriptions(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    rows = db.query(SavedFilter).filter_by(user_id=user.id, active=True).order_by(SavedFilter.created_at.desc()).all()
    # Имя компании отдаем вместе с id: подписка на экране должна называться
    # «Магнит», а не «g1a2b3c4» — id внутренний, человеку он ничего не говорит.
    companies = (base_data.promoted() or {}).get("companies") or {}
    return [{"id": r.id, "industry": r.industry, "keyword": r.keyword,
             "company_id": r.company_id,
             "company_name": ((companies.get(r.company_id) or {}).get("name") if r.company_id else None),
             "min_amount_mln_rub": float(r.min_amount_mln_rub) if r.min_amount_mln_rub is not None else None}
            for r in rows]


@router.post("/api/subscriptions")
def create_subscription(sub: SubscriptionIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    if not sub.industry and not sub.keyword and not sub.company_id:
        return JSONResponse({"error": "укажите компанию, отрасль или ключевое слово"}, status_code=400)
    company_id = (sub.company_id or "").strip() or None
    if company_id and company_id not in ((base_data.promoted() or {}).get("companies") or {}):
        # Подписка на несуществующий профиль молча никогда не сработает —
        # человек будет ждать писем, которых не бывает. Родня уже записанному
        # уроку «не придержано — не то же самое, что выйдет по молчанию».
        return JSONResponse({"error": "такой компании нет в базе"}, status_code=400)
    if company_id:
        # Второй раз на ту же компанию — не вторая подписка, а тот же самый
        # ответ «вы подписаны»: сердечко на карточке нажимают повторно легко.
        same = db.query(SavedFilter).filter_by(user_id=user.id, active=True,
                                               company_id=company_id).first()
        if same and not sub.industry and not sub.keyword and sub.min_amount_mln_rub is None:
            return {"id": same.id, "existing": True}
    # Та же подписка второй раз — не вторая строка, а ответ «уже есть»: на
    # форму, которая не отвечала (4 октября 2026), жали по нескольку раз.
    for same in db.query(SavedFilter).filter_by(user_id=user.id, active=True,
                                                industry=sub.industry or None,
                                                keyword=sub.keyword or None,
                                                company_id=company_id).all():
        was = float(same.min_amount_mln_rub) if same.min_amount_mln_rub is not None else None
        if was == sub.min_amount_mln_rub:
            return {"id": same.id, "existing": True}
    row = SavedFilter(user_id=user.id, industry=sub.industry or None, keyword=sub.keyword or None,
                       company_id=company_id, min_amount_mln_rub=sub.min_amount_mln_rub)
    db.add(row)
    db.commit()
    return {"id": row.id}


@router.delete("/api/subscriptions/{sub_id}")
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
# поле status у Comment для нее уже есть.
def _comment_author(user: User) -> str:
    # Регистрация с 2 августа 2026 требует «Имя и фамилию» (RegisterRequest.full_name
    # обязательное поле) — но подпись под комментарием строилась не из него, а из
    # локальной части e-mail (`email.split("@")[0]`): анонимный посетитель видел
    # кусок чужого адреса почты на каждом комментарии, а введенное при регистрации
    # имя нигде не показывалось. У аккаунтов старой схемы (до 2 августа) full_name
    # может быть пуст — для них оставлен прежний вид, единственный, что у них есть.
    name = (user.full_name or "").strip()
    return name if name else user.email.split("@")[0]


@router.get("/api/deals/{deal_id}/comments")
def list_comments(deal_id: str, db=Depends(get_db)):
    rows = (db.query(Comment)
            .filter_by(deal_id=deal_id, status="approved")
            .order_by(Comment.created_at.asc()).all())
    return [{"id": c.id, "body": c.body, "created_at": c.created_at.isoformat(),
             "author": _comment_author(c.user)} for c in rows]


@router.post("/api/deals/{deal_id}/comments")
def post_comment(deal_id: str, comment: CommentIn, user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите по почте, чтобы комментировать"}, status_code=401)
    body = comment.body.strip()
    if not body:
        return JSONResponse({"error": "пустой комментарий"}, status_code=400)
    if len(body) > 4000:
        return JSONResponse({"error": "слишком длинный комментарий"}, status_code=400)
    # Имя автора публикуется рядом с комментарием — это распространение
    # персональных данных, и согласие на него отдельное (ст. 10.1 152-ФЗ,
    # 16 октября 2026). Спрашиваем один раз, момент согласия храним у аккаунта.
    if user.comment_name_consent_at is None:
        if not comment.name_consent:
            return JSONResponse({"error": "отметьте согласие на показ имени рядом с комментарием",
                                 "need_name_consent": True}, status_code=400)
        user.comment_name_consent_at = datetime.now(timezone.utc).replace(tzinfo=None)
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
    if correction.kind == "consultant":
        # Письмо от фирмы-консультанта уходит основателям в Telegram сразу
        # (владелец, 8 октября 2026), а не через рутину заметок раз в три часа.
        # Дошло — строка помечается «sent», и рутина ее не повторит; не дошло
        # — остается «new», и рутина донесет.
        if _forward_consultant_to_console(db, row):
            row.status = "sent"
            db.commit()
    return {"ok": True, "id": row.id}


def _forward_consultant_to_console(db, row: CorrectionRequest) -> bool:
    chats = core._review_chat_ids(db)
    if not chats:
        return False
    thread = core._console_thread_id(db, "user_notes")
    text = ("🤝 Консультант хочет связаться\n%s\nКонтакт: %s"
            % (row.body, row.contact or "не указан"))
    ok = False
    for chat in chats:
        res = notification_service.tg_api("sendMessage", chat_id=chat, text=text, disable_web_page_preview=True,
                                          **({"message_thread_id": thread} if thread else {}))
        ok = ok or bool(res and res.get("ok"))
    return ok


@router.post("/api/deals/{deal_id}/corrections")
def post_correction(deal_id: str, correction: CorrectionIn,
                    user: User | None = Depends(_current_user), db=Depends(get_db)):
    return _save_correction(deal_id, correction, user, db)


@router.post("/api/corrections")
def post_general_correction(correction: CorrectionIn,
                            user: User | None = Depends(_current_user), db=Depends(get_db)):
    """Общее сообщение редакции из футера, без привязки к карточке."""
    return _save_correction(None, correction, user, db)


@router.get("/api/corrections/pending")
def corrections_pending(token: str = "", db=Depends(get_db)):
    """Мост к рутине публикации: `CorrectionRequest` живет в базе сайта
    (приватная сеть), рутина работает в другом процессе — тот же токен, что
    у /api/moderation/decisions. 19 сентября 2026: до этого канал был
    write-only — сообщения писались в таблицу, и ни один экран или скрипт
    их не читал (см. KNOWN_ISSUES.md)."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    rows = list(db.scalars(select(CorrectionRequest).where(CorrectionRequest.status == "new")
                           .order_by(CorrectionRequest.created_at)).all())
    return {"corrections": [{"id": r.id, "deal_id": r.deal_id, "contact": r.contact,
                             "body": r.body, "created_at": r.created_at.isoformat()}
                            for r in rows]}


class CorrectionsConsumeIn(BaseModel):
    token: str = ""
    ids: list[int] = []


@router.post("/api/corrections/consume")
def corrections_consume(req: CorrectionsConsumeIn, db=Depends(get_db)):
    """Удалить показанные заявки — их постоянное место теперь в Telegram-
    консоли (тема «Заметки от пользователей»), а не в этой таблице; держать
    прочитанное здесь незачем и только копит мусор в базе (владелец 19
    сентября 2026: «если они засоряют базу данных, то нужно их оттуда
    убирать»)."""
    if not _moderation_token_ok(req.token):
        return JSONResponse({"error": "not found"}, status_code=404)
    n = 0
    for row in db.scalars(select(CorrectionRequest).where(CorrectionRequest.id.in_(req.ids or []))).all():
        db.delete(row)
        n += 1
    db.commit()
    return {"deleted": n}


# ==================== Кабинет компании: «Это моя компания» ====================
# Владелец, 14 октября 2026: представитель компании (первой — партнер
# Execburo) просит в личном кабинете подключить его к карточке, мы в консоли
# подтверждаем, и дальше он видит «свою» карточку и шлет нам заявки на
# правки. Править карточку сам он не может: содержимое остается за редакцией,
# правка приходит обычной заметкой в консоль. Устройство — docs/company_cabinet.md.

CLAIM_KINDS = ("company", "firm")
CLAIM_STATUSES = ("pending", "approved", "rejected")
CLAIMS_PER_USER = 10            # больше карточек одному человеку не нужно — это уже спам
CLAIM_VIEWS_DAYS = 30
# Что представитель может попросить поменять. Ключ — для формы, подпись —
# и в форме, и в тексте заметки для консоли.
CLAIM_CHANGE_KINDS = {
    "about": "Описание компании",
    "contacts": "Сайт и контакты",
    "deals": "Сделки компании",
    "look": "Логотип и оформление",
    "other": "Другое",
}
_FIRM_ID_RE = re.compile(r'\{id:"([a-z0-9_-]{1,40})",n:"([^"]{1,200})"')
_firm_cache: dict = {"mtime": None, "firms": {}}


def _firm_catalog() -> dict[str, str]:
    """id → название фирм-консультантов. Справочник фирм живет в коде
    страницы (FIRMS, INV_FIRMS, EXEC_FIRMS в static/index.html), а не в базе:
    читаем его оттуда же, чтобы заявка не могла сослаться на фирму, которой
    на сайте нет, и название в консоли было нашим, а не присланным."""
    path = os.path.join(STATIC_DIR, "index.html")
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    if _firm_cache["mtime"] != mtime:
        with open(path, encoding="utf-8") as fh:
            _firm_cache["firms"] = dict(_FIRM_ID_RE.findall(fh.read()))
        _firm_cache["mtime"] = mtime
    return _firm_cache["firms"]


def _claim_target_name(kind: str, target_id: str) -> str | None:
    if kind == "company":
        profile = ((base_data.promoted() or {}).get("companies") or {}).get(target_id)
        return (profile or {}).get("name") or None
    if kind == "firm":
        return _firm_catalog().get(target_id)
    return None


def _claim_page_path(row: CompanyClaim) -> str:
    """Адрес карточки внутри сайта — тот же, что пишет счетчик посещений
    (`trackView` → traffic.normalize: /companies/<id>, /advisors/<id>)."""
    return ("/companies/%s" if row.kind == "company" else "/advisors/%s") % row.target_id


def _claim_views(db, row: CompanyClaim) -> int:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=CLAIM_VIEWS_DAYS)
    return int(db.scalar(select(func.count(PageView.id)).where(
        PageView.path == _claim_page_path(row), PageView.created_at >= since)) or 0)


def _claim_json(db, row: CompanyClaim) -> dict:
    out = {"id": row.id, "kind": row.kind, "target_id": row.target_id,
           "target_name": row.target_name, "status": row.status,
           "position": row.position, "note": row.note,
           "link": "#" + _claim_page_path(row),
           "created_at": row.created_at.isoformat() if row.created_at else None,
           "decided_at": row.decided_at.isoformat() if row.decided_at else None}
    if row.status == "approved":
        out["views_30d"] = _claim_views(db, row)
    return out


def _notify_company_claim(db, row: CompanyClaim, user: User) -> bool:
    """Заявка — в консоль, тема «Заметки от пользователей», с кнопками
    «Подтвердить»/«Отклонить» (`claim:ok|no:<id>`, разбор — в
    _handle_telegram_update рядом с `acc:`). Сбой отправки заявку не роняет:
    она в базе, и ее видно по `GET /api/ops/claims?token=…`."""
    try:
        chats = core._review_chat_ids(db)
        if not chats:
            logger.warning("заявка на карточку #%s: консоль не настроена", row.id)
            return False
        when = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m.%Y %H:%M МСК")
        what = "компания" if row.kind == "company" else "консультант"
        lines = [
            "🏢 Просят подключить карточку к личному кабинету",
            "Карточка: %s (%s)" % (row.target_name, what),
            "%s/#%s" % (SITE_URL, _claim_page_path(row)),
            "",
            "Кто: %s, %s" % (user.full_name or "имя не указано",
                             row.position or user.position or "должность не указана"),
            "Почта: %s" % user.email,
        ]
        if user.company:
            lines.append("Компания в профиле: %s" % user.company)
        if row.note:
            lines.append("Комментарий: %s" % row.note)
        lines += ["Отправлена: %s" % when, "",
                  "Подтвердите, только если уверены, что человек работает в этой компании."]
        keys = [[{"text": "✅ Подтвердить", "callback_data": "claim:ok:%d" % row.id},
                 {"text": "🗑 Отклонить", "callback_data": "claim:no:%d" % row.id}]]
        thread = core._console_thread_id(db, "user_notes")
        ok = False
        for chat in chats:
            res = notification_service.tg_api("sendMessage", chat_id=chat, text="\n".join(lines),
                                              reply_markup={"inline_keyboard": keys},
                                              disable_web_page_preview=True,
                                              **({"message_thread_id": thread} if thread else {}))
            ok = ok or bool(res and res.get("ok"))
        return ok
    except Exception as exc:  # noqa: BLE001 — заявка важнее уведомления
        logger.error("заявка на карточку #%s: не ушла в Telegram: %s", row.id, exc)
        return False


def _decide_claim(db, row: CompanyClaim, approve: bool) -> None:
    """Одно решение для кнопки в консоли и для запроса по токену. О
    подтверждении человеку приходит уведомление (в кабинет, а если он
    подключил Telegram — и туда); об отказе — нет: экран кабинета сам
    показывает статус, а письма «вам отказано» никто не просил."""
    status = "approved" if approve else "rejected"
    changed = row.status != status
    row.status = status
    row.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    if approve and changed and row.user:
        try:
            notification_service.create_notification(
                db, row.user, kind="company_claim",
                title="Карточка «%s» подключена к вашему кабинету" % row.target_name,
                body="Теперь в разделе «Моя компания» видно, сколько раз ее открывали, "
                     "и можно предложить нам правку.",
                link="%s/#/account?tab=company" % SITE_URL)
        except Exception as exc:  # noqa: BLE001
            logger.warning("заявка на карточку #%s: уведомление не создано: %s", row.id, exc)


class CompanyClaimIn(BaseModel):
    kind: str
    target_id: str
    position: str | None = None
    note: str | None = None


class ClaimChangeIn(BaseModel):
    kind: str = "other"
    body: str


class ClaimDecideIn(BaseModel):
    token: str = ""
    approve: bool = True


@router.post("/api/claims")
def create_company_claim(payload: CompanyClaimIn, user: User | None = Depends(_current_user),
                         db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы подключить компанию"}, status_code=401)
    kind = (payload.kind or "").strip()
    target_id = (payload.target_id or "").strip()
    name = _claim_target_name(kind, target_id) if kind in CLAIM_KINDS else None
    if not name:
        return JSONResponse({"error": "такой карточки на сайте нет"}, status_code=400)
    position = (payload.position or "").strip()[:200] or None
    note = (payload.note or "").strip()
    if len(note) > 2000:
        return JSONResponse({"error": "комментарий слишком длинный"}, status_code=400)
    row = db.scalar(select(CompanyClaim).where(CompanyClaim.user_id == user.id,
                                               CompanyClaim.kind == kind,
                                               CompanyClaim.target_id == target_id))
    if row:
        # Повтор той же пары записи не плодит и консоль не дергает: заявка
        # уже ждет решения или решена.
        return {"ok": True, "existing": True, "claim": _claim_json(db, row)}
    if db.scalar(select(func.count(CompanyClaim.id)).where(CompanyClaim.user_id == user.id)) >= CLAIMS_PER_USER:
        return JSONResponse({"error": "заявок слишком много — напишите нам, разберемся"}, status_code=400)
    row = CompanyClaim(user_id=user.id, kind=kind, target_id=target_id, target_name=name,
                       position=position, note=note or None, status="pending")
    db.add(row)
    db.commit()
    _notify_company_claim(db, row, user)
    return {"ok": True, "existing": False, "claim": _claim_json(db, row)}


@router.get("/api/me/claims")
def my_company_claims(user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    rows = db.scalars(select(CompanyClaim).where(CompanyClaim.user_id == user.id)
                      .order_by(CompanyClaim.created_at.desc())).all()
    return {"claims": [_claim_json(db, r) for r in rows],
            "change_kinds": [[k, v] for k, v in CLAIM_CHANGE_KINDS.items()]}


@router.post("/api/claims/{claim_id}/change")
def propose_claim_change(claim_id: int, payload: ClaimChangeIn,
                         user: User | None = Depends(_current_user), db=Depends(get_db)):
    """Заявка на правку карточки от подтвержденного представителя. Пишется
    обычной заметкой (CorrectionRequest) — ее донесет до консоли та же
    рутина, что и остальные заметки посетителей (docs/user_notes.md)."""
    if not user:
        return JSONResponse({"error": "не авторизован"}, status_code=401)
    row = db.get(CompanyClaim, claim_id)
    if not row or row.user_id != user.id:
        return JSONResponse({"error": "заявка не найдена"}, status_code=404)
    if row.status != "approved":
        return JSONResponse({"error": "правки можно предлагать после того, как мы подтвердим связь с компанией"},
                            status_code=403)
    text_ = (payload.body or "").strip()
    if not text_:
        return JSONResponse({"error": "напишите, что поменять"}, status_code=400)
    if len(text_) > 4000:
        return JSONResponse({"error": "сообщение слишком длинное"}, status_code=400)
    label = CLAIM_CHANGE_KINDS.get(payload.kind, CLAIM_CHANGE_KINDS["other"])
    body = ("Представитель «%s» (подтвержден), %s: %s\n\n%s\n\nКарточка: %s/#%s"
            % (row.target_name, user.email, label, text_, SITE_URL, _claim_page_path(row)))
    note = CorrectionRequest(deal_id=None, user_id=user.id, contact=user.email, body=body, status="new")
    db.add(note)
    db.commit()
    return {"ok": True, "id": note.id}


@router.get("/api/ops/claims")
def ops_claims(token: str = "", status: str = "pending", db=Depends(get_db)):
    """Запасной путь без кнопок консоли: список заявок по токену модерации."""
    if not _moderation_token_ok(token):
        return JSONResponse({"error": "not found"}, status_code=404)
    q = select(CompanyClaim).order_by(CompanyClaim.created_at)
    if status in CLAIM_STATUSES:
        q = q.where(CompanyClaim.status == status)
    out = []
    for row in db.scalars(q).all():
        item = _claim_json(db, row)
        item["email"] = row.user.email if row.user else None
        item["full_name"] = row.user.full_name if row.user else None
        out.append(item)
    return {"claims": out}


@router.post("/api/ops/claims/{claim_id}")
def ops_decide_claim(claim_id: int, payload: ClaimDecideIn, token: str = "", db=Depends(get_db)):
    """То же решение, что кнопки «Подтвердить»/«Отклонить» в консоли, — по
    токену модерации (в теле или в адресе)."""
    if not _moderation_token_ok(payload.token or token):
        return JSONResponse({"error": "not found"}, status_code=404)
    row = db.get(CompanyClaim, claim_id)
    if not row:
        return JSONResponse({"error": "заявки с таким id нет"}, status_code=404)
    _decide_claim(db, row, bool(payload.approve))
    return {"ok": True, "claim": _claim_json(db, row)}


