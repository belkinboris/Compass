# -*- coding: utf-8 -*-
"""Вход по почте и паролю — без магической ссылки и без стороннего сервиса.

ПОЧЕМУ НЕ ССЫЛКА НА ПОЧТУ. Первая версия (28 июля 2026) сознательно избегала
паролей: аудитория — юристы и консультанты, доверенная почта уже есть,
хранить хэши не хотелось. Но ссылка требует реальной отправки писем (SMTP),
а это добавляет отдельную точку отказа, которой не было у автопостинга в
Telegram: письмо может попасть в спам, SMTP может быть не настроен (как и
было все эти дни) — и тогда войти нельзя вообще, каким бы ни был пароль.
Решение владельца (2 августа 2026): просто email + пароль, как в
Telegram-боте (там тоже логин через токен, а не переписка). Без SMTP —
можно совсем не заводить его для входа (понадобится только на будущее,
если появится восстановление пароля, а не как сейчас — на каждый визит).

ХЭШИРОВАНИЕ БЕЗ НОВОЙ ЗАВИСИМОСТИ. PBKDF2-HMAC-SHA256 из стандартного
`hashlib` — то же семейство алгоритма, что Django берёт по умолчанию;
260 000 итераций (актуальный ориентир OWASP на 2026 год), соль на каждого
пользователя своя (`secrets.token_hex`), сравнение хэшей — временем,
независимым от совпадения (`secrets.compare_digest`), чтобы не утечь через
тайминг-атаку. Отдельный pip-пакет (bcrypt/passlib) не нужен.

ЧТО ЕСТЬ. Хэш пароля в `User.password_hash`; серверная сессия на 30 дней
поверх обычной httponly-куки (`AuthSession`, opaque-токен — без стороннего
подписывающего пакета, проверяется прямым запросом к таблице).

ЧЕГО ПОКА НЕТ (честно, а не полумерой). Восстановления забытого пароля —
для него всё равно нужен канал связи (почта или Telegram), которого
сегодня нет. Пока это так, ответ на «забыл пароль» — новый аккаунт с той же
почтой невозможен (email уникален), но и починить старый нечем; когда
появится SMTP или бот с привязкой аккаунта, это первое, что стоит достроить.

Запуск теста от начала до конца — без сети:
    python3 -m pytest test_auth.py -q
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select

from db.models import AuthSession, User, UserRole, UserTier

logger = logging.getLogger("kompas.auth")

SESSION_TTL = timedelta(days=30)
SESSION_COOKIE = "kompas_session"

PBKDF2_ITERATIONS = 260_000
MIN_PASSWORD_LEN = 8


def valid_email(email):
    e = str(email or "").strip()
    return 5 <= len(e) <= 300 and "@" in e and "." in e.split("@")[-1] and " " not in e


def valid_password(password):
    return isinstance(password, str) and MIN_PASSWORD_LEN <= len(password) <= 200


def hash_password(password):
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return "pbkdf2_sha256$%s$%s" % (salt, dk.hex())


def verify_password(password, stored):
    """Сравнение временем, не зависящим от того, где хэши разошлись — иначе
    ранний выход на первом несовпавшем байте выдаёт длину общей части."""
    try:
        algo, salt, hex_digest = str(stored or "").split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return secrets.compare_digest(dk.hex(), hex_digest)


def valid_role(role):
    try:
        UserRole(role)
        return True
    except ValueError:
        return False


def register_user(session, email, password, full_name, company=None, position=None, role="individual"):
    """(User, None) при успехе, (None, причина отказа) иначе. Email уникален —
    вторая регистрация тем же адресом отклоняется явно, а не тихо перезаписывает
    чужой пароль. ФИО и тип аккаунта обязательны — это то, что раньше молча
    записывалось как role=individual всем подряд без выбора при регистрации."""
    if not valid_email(email):
        return None, "некорректная почта"
    if not valid_password(password):
        return None, "пароль — от %d символов" % MIN_PASSWORD_LEN
    full_name = str(full_name or "").strip()
    if not (2 <= len(full_name) <= 200):
        return None, "укажите имя и фамилию"
    if not valid_role(role):
        return None, "неизвестный тип аккаунта"
    email = str(email).strip().lower()
    if session.scalar(select(User).where(User.email == email)):
        return None, "эта почта уже зарегистрирована — войдите"
    user = User(email=email, role=UserRole(role), tier=UserTier.free,
                password_hash=hash_password(password), full_name=full_name,
                company=(str(company).strip() or None) if company else None,
                position=(str(position).strip() or None) if position else None)
    session.add(user)
    session.commit()
    return user, None


def authenticate(session, email, password):
    """Один и тот же отказ и на неизвестную почту, и на неверный пароль —
    иначе по разнице ответов можно перечислять зарегистрированные адреса."""
    email = str(email or "").strip().lower()
    user = session.scalar(select(User).where(User.email == email))
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return None, "неверная почта или пароль"
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
