# -*- coding: utf-8 -*-
"""Доставка уведомлений «Компаса»: приложение, почта и Telegram.

Внутреннее уведомление работает сразу. Почта и Telegram включаются переменными
окружения; отсутствие внешних ключей не мешает сайту и не теряет уведомление.
"""
from __future__ import annotations

import logging
import os
import secrets
import smtplib
from datetime import datetime
from email.message import EmailMessage

import httpx
from sqlalchemy import select

import telegram_endpoint
from db.models import DealWatch, Notification, NotificationPreference, User

logger = logging.getLogger("kompas.notifications")


def get_preferences(db, user_id: int) -> NotificationPreference:
    row = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    if not row:
        row = NotificationPreference(user_id=user_id)
        db.add(row)
        db.commit()
    return row


def email_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST"))


def _send_email(to_addr: str, subject: str, body: str) -> bool:
    if not email_configured():
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM", "noreply@projectcompass.ru")
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=12) as smtp:
            if os.environ.get("SMTP_STARTTLS", "true").lower() != "false":
                smtp.starttls()
            if os.environ.get("SMTP_USER"):
                smtp.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return True
    except Exception as exc:
        logger.warning("email delivery failed: %s", exc)
        return False


def tg_api(method: str, **payload) -> dict | None:
    """Любой метод Bot API с боевого хоста — через релей (telegram_endpoint).

    Нужен модерации: ответить на нажатие кнопки (answerCallbackQuery) и
    дописать решение в само сообщение (editMessageText), чтобы владелец и
    партнёр видели в группе, что уже решено и кем. Сбой не критичен ни для
    одного вызова — решение уже в таблице; поэтому None, а не исключение.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return None
    try:
        response = httpx.post(telegram_endpoint.method_url(token, method),
                              json=payload, timeout=12)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # ValueError — не-JSON в ответе (например, страница ошибки релея):
        # без него исключение пролетало бы сквозь вебхук и роняло его в 500.
        logger.warning("telegram %s failed: %s", method, exc)
        return None


def _send_telegram(chat_id: str, text: str, *, html: bool = False,
                   button: tuple[str, str] | None = None) -> bool:
    """Сообщение читателю в личку от бота. `button` — (подпись, адрес):
    ссылка кнопкой читается лучше голого адреса в конце текста."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or not chat_id:
        return False
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if html:
        payload["parse_mode"] = "HTML"
    if button and button[1]:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": button[0], "url": button[1]}]]}
    try:
        response = httpx.post(
            telegram_endpoint.method_url(token, "sendMessage"),
            json=payload,
            timeout=12,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        logger.warning("telegram delivery failed: %s", exc)
        return False


def telegram_text(title: str, body: str | None = None) -> str:
    """Уведомление в Telegram: заголовок жирным, под ним пояснение. Адрес
    уходит кнопкой «Открыть на сайте», а не строкой в конце (4 октября 2026)."""
    from html import escape
    parts = ["<b>%s</b>" % escape(str(title or "").strip())]
    if body and str(body).strip():
        parts.append(escape(str(body).strip()))
    return "\n\n".join(parts)


def create_notification(db, user: User, *, title: str, body: str | None = None,
                        link: str | None = None, deal_id: str | None = None,
                        kind: str = "deal_update") -> Notification:
    prefs = get_preferences(db, user.id)
    row = Notification(user_id=user.id, kind=kind, title=title, body=body, link=link, deal_id=deal_id)
    db.add(row)
    db.commit()
    if prefs.email_enabled and _send_email(user.email, title, f"{body or ''}\n\n{link or ''}".strip()):
        row.email_sent_at = datetime.utcnow()
    if prefs.telegram_enabled and prefs.telegram_chat_id:
        if _send_telegram(prefs.telegram_chat_id, telegram_text(title, body), html=True,
                          button=("Открыть на сайте", link) if link else None):
            row.telegram_sent_at = datetime.utcnow()
    db.commit()
    return row


def notify_deal_watchers(db, deal_id: str, title: str, body: str | None = None,
                         link: str | None = None) -> int:
    watches = list(db.scalars(select(DealWatch).where(
        DealWatch.deal_id == deal_id, DealWatch.active.is_(True)
    )).all())
    count = 0
    for watch in watches:
        user = db.get(User, watch.user_id)
        if user:
            create_notification(db, user, title=title, body=body, link=link, deal_id=deal_id)
            count += 1
    return count


def telegram_connect_url(db, user_id: int) -> str | None:
    username = os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
    if not username:
        return None
    prefs = get_preferences(db, user_id)
    # Ссылка одна, пока ею не воспользовались: раньше каждое нажатие
    # «Подключить» выдавало новую, и ссылка из первой вкладки или первого
    # нажатия молча переставала работать.
    if not prefs.telegram_connect_token:
        prefs.telegram_connect_token = secrets.token_urlsafe(24)
        prefs.updated_at = datetime.utcnow()
        db.commit()
    return f"https://t.me/{username}?start=kompas_{prefs.telegram_connect_token}"


def telegram_connect_code(db, user_id: int) -> str | None:
    """Тот же ключ текстом — его можно просто отправить боту, если Telegram
    открыл чат без кнопки «Старт» (так бывает, когда чат с ботом уже есть)."""
    prefs = get_preferences(db, user_id)
    return f"kompas_{prefs.telegram_connect_token}" if prefs.telegram_connect_token else None


def bind_telegram(db, connect_token: str, chat_id: str) -> bool:
    prefs = db.scalar(select(NotificationPreference).where(
        NotificationPreference.telegram_connect_token == connect_token
    ))
    if not prefs:
        return False
    prefs.telegram_chat_id = str(chat_id)
    prefs.telegram_enabled = True
    prefs.telegram_connect_token = None
    prefs.updated_at = datetime.utcnow()
    db.commit()
    return True


def linked_preferences(db, chat_id) -> NotificationPreference | None:
    """Аккаунт, к которому привязан этот чат Telegram, — или None."""
    if chat_id is None:
        return None
    return db.scalar(select(NotificationPreference).where(
        NotificationPreference.telegram_chat_id == str(chat_id)))


def stop_telegram(db, chat_id) -> bool:
    """Команда /stop в боте: уведомления в Telegram выключаются, привязка
    остаётся — включить снова можно одним переключателем в кабинете."""
    prefs = linked_preferences(db, chat_id)
    if not prefs:
        return False
    prefs.telegram_enabled = False
    prefs.updated_at = datetime.utcnow()
    db.commit()
    return True


def unlink_telegram(db, user_id: int) -> None:
    """Кнопка «Отвязать» в кабинете: чат забывается целиком."""
    prefs = get_preferences(db, user_id)
    prefs.telegram_chat_id = None
    prefs.telegram_enabled = False
    prefs.telegram_connect_token = None
    prefs.updated_at = datetime.utcnow()
    db.commit()
