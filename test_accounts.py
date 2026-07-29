# -*- coding: utf-8 -*-
"""Аккаунты через HTTP: вход по ссылке, подписки, комментарии.

Своя БД (см. conftest.py — DATABASE_URL выставлен там до импорта main).
Ссылка для входа намеренно не возвращается в теле HTTP-ответа (см. auth.py),
поэтому тесты достают токен прямым запросом к БД — так же, как это в проде
делал бы человек, читающий письмо или лог сервера, а не подглядыванием в
ответ, которого там нет.

Запуск: python3 -m pytest test_accounts.py -q
"""
import pytest
from fastapi.testclient import TestClient

import main
from db.models import Base, LoginToken
from db.session import engine, get_session


@pytest.fixture(scope="module", autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def latest_token(email):
    s = get_session()
    try:
        row = (s.query(LoginToken).filter_by(email=email.lower())
               .order_by(LoginToken.id.desc()).first())
        return row.token if row else None
    finally:
        s.close()


def login(client, email):
    r = client.post("/api/auth/request-link", json={"email": email})
    assert r.status_code == 200 and r.json() == {"ok": True}
    token = latest_token(email)
    assert token
    r2 = client.get("/api/auth/verify", params={"token": token}, follow_redirects=False)
    assert r2.status_code == 302 and "kompas_session" in r2.cookies
    return client


def test_request_link_rejects_bad_email(client):
    r = client.post("/api/auth/request-link", json={"email": "not-an-email"})
    assert r.status_code == 400


def test_request_link_answers_the_same_for_unknown_email(client):
    """Ответ одинаков для существующей и несуществующей почты — иначе по
    ответу можно узнать, зарегистрирован ли чужой адрес (перечисление аккаунтов)."""
    r1 = client.post("/api/auth/request-link", json={"email": "совсем-новый@firm.ru"})
    r2 = client.post("/api/auth/request-link", json={"email": "тоже-новый@firm.ru"})
    assert r1.json() == r2.json() == {"ok": True}


def test_me_without_cookie_is_200_and_anonymous(client):
    """200, а не 401: анонимный визит — самое частое состояние, не ошибка.
    401 здесь заставлял бы браузер писать «Failed to load resource» в
    консоль при каждой загрузке страницы любым не вошедшим посетителем."""
    r = client.get("/api/me")
    assert r.status_code == 200
    assert r.json() == {"logged_in": False}


def test_full_login_flow(client):
    login(client, "юрист@firma.ru")
    r = client.get("/api/me")
    assert r.status_code == 200
    body = r.json()
    assert body["logged_in"] is True
    assert body["email"] == "юрист@firma.ru"
    assert body["role"] == "individual" and body["tier"] == "free"


def test_verify_rejects_unknown_token(client):
    r = client.get("/api/auth/verify", params={"token": "нет-такого"}, follow_redirects=False)
    assert r.status_code == 302 and "kompas_session" not in r.cookies


def test_token_cannot_be_reused(client):
    email = "once@firm.ru"
    client.post("/api/auth/request-link", json={"email": email})
    token = latest_token(email)
    client.get("/api/auth/verify", params={"token": token})
    r2 = client.get("/api/auth/verify", params={"token": token}, follow_redirects=False)
    assert "kompas_session" not in r2.cookies


def test_logout_clears_the_session(client):
    login(client, "выход@firm.ru")
    assert client.get("/api/me").json()["logged_in"] is True
    client.post("/api/auth/logout")
    assert client.get("/api/me").json() == {"logged_in": False}


def test_subscriptions_require_login(client):
    assert client.get("/api/subscriptions").status_code == 401
    assert client.post("/api/subscriptions", json={"industry": "Банки"}).status_code == 401


def test_subscription_needs_industry_or_keyword(client):
    login(client, "подписка1@firm.ru")
    r = client.post("/api/subscriptions", json={})
    assert r.status_code == 400


def test_create_list_delete_subscription(client):
    login(client, "подписка2@firm.ru")
    r = client.post("/api/subscriptions", json={"industry": "Банки", "min_amount_mln_rub": 500})
    assert r.status_code == 200
    sub_id = r.json()["id"]

    listed = client.get("/api/subscriptions").json()
    assert any(s["id"] == sub_id and s["industry"] == "Банки" for s in listed)

    d = client.delete(f"/api/subscriptions/{sub_id}")
    assert d.status_code == 200
    assert not any(s["id"] == sub_id for s in client.get("/api/subscriptions").json())


def test_cannot_delete_someone_elses_subscription(client):
    login(client, "владелец@firm.ru")
    sub_id = client.post("/api/subscriptions", json={"keyword": "Ozon"}).json()["id"]
    other = TestClient(main.app)
    login(other, "чужой@firm.ru")
    r = other.delete(f"/api/subscriptions/{sub_id}")
    assert r.status_code == 404


def test_comments_require_login_to_post(client):
    r = client.post("/api/deals/gtest0001/comments", json={"body": "текст"})
    assert r.status_code == 401


def test_comment_round_trip(client):
    login(client, "коммент@firm.ru")
    r = client.post("/api/deals/gtest0001/comments", json={"body": "Кто консультировал продавца?"})
    assert r.status_code == 200
    assert r.json()["author"] == "коммент"  # часть почты до @, а не сама почта

    listed = client.get("/api/deals/gtest0001/comments").json()
    assert any(c["body"] == "Кто консультировал продавца?" for c in listed)


def test_comment_empty_body_rejected(client):
    login(client, "пустой@firm.ru")
    r = client.post("/api/deals/gtest0001/comments", json={"body": "   "})
    assert r.status_code == 400


def test_comment_too_long_rejected(client):
    login(client, "длинный@firm.ru")
    r = client.post("/api/deals/gtest0001/comments", json={"body": "ф" * 4001})
    assert r.status_code == 400


def test_comments_are_scoped_to_their_own_deal(client):
    login(client, "скоуп@firm.ru")
    client.post("/api/deals/gtestAAAA/comments", json={"body": "про сделку A"})
    client.post("/api/deals/gtestBBBB/comments", json={"body": "про сделку B"})
    only_a = client.get("/api/deals/gtestAAAA/comments").json()
    assert all(c["body"] == "про сделку A" for c in only_a)
