# -*- coding: utf-8 -*-
"""Вход по email и паролю: весь цикл на sqlite in-memory, без сети.

Запуск: python3 -m pytest test_auth.py -q
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
from db.models import AuthSession, Base, User


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_password_hash_round_trip():
    h = auth.hash_password("верный-конь-скрепка")
    assert auth.verify_password("верный-конь-скрепка", h)
    assert not auth.verify_password("другой-пароль", h)


def test_password_hash_is_salted():
    """Один и тот же пароль дважды — разные хэши: соль своя на каждый вызов."""
    assert auth.hash_password("одинаковый") != auth.hash_password("одинаковый")


def test_verify_password_rejects_malformed_hash():
    assert not auth.verify_password("что угодно", "не-похоже-на-хэш")
    assert not auth.verify_password("что угодно", None)


def test_register_creates_user_with_lowercase_email(session):
    user, err = auth.register_user(session, "Юрист@Фирма.ру", "надёжный-пароль", "Юрист Юристов")
    assert err is None and user is not None
    assert user.email == "юрист@фирма.ру"
    assert session.query(User).count() == 1


def test_register_rejects_bad_email(session):
    user, err = auth.register_user(session, "not-an-email", "надёжный-пароль", "Тест Тестов")
    assert user is None and "почта" in err


def test_register_rejects_short_password(session):
    user, err = auth.register_user(session, "a@b.ru", "коротк", "Тест Тестов")
    assert user is None and "пароль" in err


def test_register_rejects_duplicate_email(session):
    auth.register_user(session, "a@b.ru", "первый-пароль-123", "Тест Тестов")
    user, err = auth.register_user(session, "a@b.ru", "второй-пароль-456", "Тест Тестов")
    assert user is None and "уже зарегистрирована" in err


def test_register_rejects_missing_full_name(session):
    """До 2 августа роль записывалась всем подряд как individual без выбора —
    теперь ФИО и тип аккаунта обязательны, а не тихая заглушка."""
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "")
    assert user is None and "имя" in err


def test_register_rejects_unknown_role(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Тест Тестов", role="начальник")
    assert user is None and "тип аккаунта" in err


def test_register_stores_full_name_company_position_and_role(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Иван Иванов",
                                    company="ООО Ромашка", position="Партнёр", role="firm")
    assert err is None
    assert user.full_name == "Иван Иванов"
    assert user.company == "ООО Ромашка"
    assert user.position == "Партнёр"
    assert user.role.value == "firm"


def test_register_defaults_role_to_individual_and_allows_empty_company(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Иван Иванов")
    assert err is None
    assert user.role.value == "individual"
    assert user.company is None and user.position is None


def test_authenticate_accepts_correct_password(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "a@b.ru", "правильный-пароль")
    assert err is None and user is not None and user.email == "a@b.ru"


def test_authenticate_is_case_insensitive_on_email(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "A@B.RU", "правильный-пароль")
    assert err is None and user is not None


def test_authenticate_rejects_wrong_password(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "a@b.ru", "неверный-пароль")
    assert user is None and err is not None


def test_authenticate_unknown_email_gives_same_error_as_wrong_password(session):
    """Один и тот же отказ на обе причины — иначе по разнице ответов можно
    перечислять зарегистрированные адреса."""
    auth.register_user(session, "known@firm.ru", "правильный-пароль", "Тест Тестов")
    _, err_unknown = auth.authenticate(session, "unknown@firm.ru", "что-угодно")
    _, err_wrong = auth.authenticate(session, "known@firm.ru", "неверный-пароль")
    assert err_unknown == err_wrong


def test_session_cookie_round_trip(session):
    user, err = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    assert err is None
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie).id == user.id
    assert auth.current_user(session, "не-та-кука") is None
    assert auth.current_user(session, None) is None


def test_revoked_session_stops_working(session):
    user, _ = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie) is not None
    auth.revoke_session(session, cookie)
    assert auth.current_user(session, cookie) is None


def test_expired_session_stops_working(session):
    user, _ = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    session.add(AuthSession(user_id=user.id, token="stale-session",
                             expires_at=datetime.utcnow() - timedelta(days=1)))
    session.commit()
    assert auth.current_user(session, "stale-session") is None


@pytest.mark.parametrize("bad", ["", "not-an-email", "a@b", "a b@c.ru", "a" * 301])
def test_invalid_emails_are_rejected(bad):
    assert not auth.valid_email(bad)


@pytest.mark.parametrize("ok", ["a@b.ru", "Юрист.Консультант@firma.legal"])
def test_valid_emails_pass(ok):
    assert auth.valid_email(ok)


@pytest.mark.parametrize("bad", ["", "коротк", "1234567"])
def test_invalid_passwords_are_rejected(bad):
    assert not auth.valid_password(bad)


def test_valid_password_passes():
    assert auth.valid_password("восемь-символов-и-больше")
