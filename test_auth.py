# -*- coding: utf-8 -*-
"""Вход по ссылке на почту: весь цикл на sqlite in-memory, без сети и без SMTP.

Запуск: python3 -m pytest test_auth.py -q
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
from db.models import AuthSession, Base, LoginToken, User


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_request_link_never_sends_without_smtp(session, monkeypatch, caplog):
    """Без SMTP письмо не уходит никуда — ссылка только в лог сервера."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with caplog.at_level("INFO"):
        link = auth.request_login_link(session, "Юрист@Фирма.ру", "http://localhost:8000")
    assert "/api/auth/verify?token=" in link
    assert any("[DEV]" in r.message for r in caplog.records)
    row = session.query(LoginToken).one()
    assert row.email == "юрист@фирма.ру"  # почта приведена к нижнему регистру


def test_token_is_one_time(session):
    """Один и тот же токен нельзя предъявить дважды — это защита от перехвата."""
    link = auth.request_login_link(session, "a@b.ru", "http://localhost")
    token = link.split("token=")[1]
    user, err = auth.verify_login_token(session, token)
    assert user is not None and err is None
    user2, err2 = auth.verify_login_token(session, token)
    assert user2 is None and "уже использована" in err2


def test_expired_token_is_refused(session):
    session.add(LoginToken(email="x@y.ru", token="expired-token",
                            expires_at=datetime.utcnow() - timedelta(minutes=1)))
    session.commit()
    user, err = auth.verify_login_token(session, "expired-token")
    assert user is None and "истекла" in err


def test_unknown_token_is_refused(session):
    user, err = auth.verify_login_token(session, "совершенно-случайная-строка")
    assert user is None and "не найдена" in err


def test_first_login_creates_the_user(session):
    """Пользователя ещё нет на момент запроса ссылки — он появляется при переходе по ней."""
    assert session.query(User).count() == 0
    link = auth.request_login_link(session, "new@user.ru", "http://localhost")
    token = link.split("token=")[1]
    user, err = auth.verify_login_token(session, token)
    assert err is None and user.email == "new@user.ru"
    assert session.query(User).count() == 1


def test_session_cookie_round_trip(session):
    _, err = (None, None)
    link = auth.request_login_link(session, "a@b.ru", "http://localhost")
    user, err = auth.verify_login_token(session, link.split("token=")[1])
    assert err is None
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie).id == user.id
    assert auth.current_user(session, "не-та-кука") is None
    assert auth.current_user(session, None) is None


def test_revoked_session_stops_working(session):
    link = auth.request_login_link(session, "a@b.ru", "http://localhost")
    user, _ = auth.verify_login_token(session, link.split("token=")[1])
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie) is not None
    auth.revoke_session(session, cookie)
    assert auth.current_user(session, cookie) is None


def test_expired_session_stops_working(session):
    link = auth.request_login_link(session, "a@b.ru", "http://localhost")
    user, _ = auth.verify_login_token(session, link.split("token=")[1])
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
