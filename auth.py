# -*- coding: utf-8 -*-
"""Вход по ссылке на почту — без пароля и без стороннего сервиса аутентификации.

ПОЧЕМУ ССЫЛКА, А НЕ ПАРОЛЬ. Решение владельца (28 июля 2026): аудитория —
юристы, экономисты и консультанты, а не массовый B2C, и у каждого уже есть
рабочая почта. Не нужно хранить и защищать хэши паролей вовсе. Схема БД
(`db/models.py`) ничего не привязывает к этому способу жёстко — заменить на
пароль или SSO позже можно, не трогая `User`.

ЧТО ЕСТЬ И ЧЕГО ПОКА НЕТ. Есть: одноразовый токен на 15 минут (`LoginToken`),
серверная сессия на 30 дней поверх обычной httponly-куки (`AuthSession`,
opaque-токен — без стороннего подписывающего пакета, проверяется прямым
запросом к таблице, как и `LoginToken`). Нет: отправки письма по-настоящему —
нужен SMTP, а его пока не задали (`SMTP_HOST` пуст). Пока его нет, ссылка не
теряется — она пишется в лог сервера строкой `[DEV] ссылка для входа` — и
NIKOGDA не возвращается в теле HTTP-ответа: иначе введя чужую почту в форму,
можно было бы получить чужую ссылку для входа прямо в браузере. Тот же
принцип, что уже применён к токену телеграм-бота: механизм готов и
тестируется, включается одной переменной окружения, без промежуточных
полумер.

Запуск теста от начала до конца — без сети и без SMTP:
    python3 -m pytest test_auth.py -q
"""
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import select

from db.models import AuthSession, LoginToken, User, UserRole, UserTier

logger = logging.getLogger("kompas.auth")

LOGIN_TOKEN_TTL = timedelta(minutes=15)
SESSION_TTL = timedelta(days=30)
SESSION_COOKIE = "kompas_session"


def valid_email(email):
    e = str(email or "").strip()
    return 5 <= len(e) <= 300 and "@" in e and "." in e.split("@")[-1] and " " not in e


def smtp_configured():
    return bool(os.environ.get("SMTP_HOST"))


def _send_email(to_addr, link):
    msg = EmailMessage()
    msg["Subject"] = "Вход в «Компас»"
    msg["From"] = os.environ.get("SMTP_FROM", "noreply@kompas.deals")
    msg["To"] = to_addr
    msg.set_content("Ссылка для входа (действует 15 минут): %s\n\nЕсли вы не запрашивали вход — просто игнорируйте это письмо." % link)
    host, port = os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.starttls()
        user = os.environ.get("SMTP_USER")
        if user:
            smtp.login(user, os.environ.get("SMTP_PASSWORD", ""))
        smtp.send_message(msg)


def request_login_link(session, email, base_url):
    """Создаёт одноразовый токен; отправляет письмо, если задан SMTP, иначе
    пишет ссылку в лог. Возвращает саму ссылку — вызывающий код (main.py)
    обязан НЕ класть её в тело HTTP-ответа, только использовать для теста/лога."""
    email = str(email).strip().lower()
    token = secrets.token_urlsafe(32)
    session.add(LoginToken(email=email, token=token,
                            expires_at=datetime.utcnow() + LOGIN_TOKEN_TTL))
    session.commit()
    link = "%s/api/auth/verify?token=%s" % (base_url.rstrip("/"), token)
    if smtp_configured():
        _send_email(email, link)
    else:
        logger.info("[DEV] ссылка для входа (%s): %s", email, link)
    return link


def verify_login_token(session, token):
    """Токен -> (User, причина отказа). Одноразовый: used_at ставится сразу,
    повторное предъявление того же токена больше не проходит."""
    row = session.scalar(select(LoginToken).where(LoginToken.token == token))
    if not row:
        return None, "ссылка не найдена"
    if row.used_at is not None:
        return None, "ссылка уже использована"
    if row.expires_at < datetime.utcnow():
        return None, "ссылка истекла — запросите новую"
    row.used_at = datetime.utcnow()
    user = session.scalar(select(User).where(User.email == row.email))
    if not user:
        user = User(email=row.email, role=UserRole.individual, tier=UserTier.free)
        session.add(user)
        session.flush()
    session.commit()
    return user, None


def create_session(session, user):
    token = secrets.token_urlsafe(32)
    session.add(AuthSession(user_id=user.id, token=token,
                             expires_at=datetime.utcnow() + SESSION_TTL))
    session.commit()
    return token


def revoke_session(session, token):
    row = session.scalar(select(AuthSession).where(AuthSession.token == token))
    if row and row.revoked_at is None:
        row.revoked_at = datetime.utcnow()
        session.commit()


def current_user(session, cookie_token):
    if not cookie_token:
        return None
    row = session.scalar(select(AuthSession).where(AuthSession.token == cookie_token))
    if not row or row.revoked_at is not None or row.expires_at < datetime.utcnow():
        return None
    return session.get(User, row.user_id)
