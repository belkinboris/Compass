# -*- coding: utf-8 -*-
"""Аккаунты через HTTP: email + пароль, подписки, комментарии.

Своя БД (см. conftest.py — DATABASE_URL выставлен там до импорта main).

Запуск: python3 -m pytest test_accounts.py -q
"""
import pytest
from fastapi.testclient import TestClient

import main
from db.models import Base, CorrectionRequest, User
from db.session import engine, get_session

TEST_PASSWORD = "надёжный-тестовый-пароль"


@pytest.fixture(scope="module", autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def login(client, email):
    """Регистрирует и сразу логинит — куки ставятся уже на /register, но
    некоторые тесты хотят явно проверить и повторный /login тем же паролем."""
    r = client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    assert r.status_code == 200 and r.json() == {"ok": True} and "kompas_session" in r.cookies
    return client


def test_register_rejects_bad_email(client):
    r = client.post("/api/auth/register",
                     json={"email": "not-an-email", "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    assert r.status_code == 400


def test_register_rejects_short_password(client):
    r = client.post("/api/auth/register",
                     json={"email": "короткий@firm.ru", "password": "1234567", "full_name": "Тест Тестов"})
    assert r.status_code == 400


def test_register_rejects_missing_full_name(client):
    """До 2 августа регистрация вообще не спрашивала ФИО и тип аккаунта —
    поле role молча писалось individual всем подряд. Теперь ФИО обязательно."""
    r = client.post("/api/auth/register", json={"email": "без-имени@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 422  # Pydantic: full_name — обязательное поле


def test_register_rejects_duplicate_email(client):
    email = "дубль@firm.ru"
    client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    r2 = client.post("/api/auth/register",
                      json={"email": email, "password": "другой-пароль-123", "full_name": "Тест Тестов"})
    assert r2.status_code == 400


def test_login_accepts_correct_password(client):
    email = "повторный-вход@firm.ru"
    client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    other = TestClient(main.app)
    r = other.post("/api/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert r.status_code == 200 and "kompas_session" in r.cookies


def test_login_rejects_wrong_password(client):
    email = "неверный-пароль@firm.ru"
    client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    other = TestClient(main.app)
    r = other.post("/api/auth/login", json={"email": email, "password": "не-тот-пароль"})
    assert r.status_code == 400 and "kompas_session" not in r.cookies


def test_login_unknown_email_and_wrong_password_give_the_same_error(client):
    """Одинаковый отказ на обе причины — иначе по разнице ответов можно
    перечислять зарегистрированные адреса."""
    email = "известная-почта@firm.ru"
    client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    other = TestClient(main.app)
    r1 = other.post("/api/auth/login", json={"email": "неизвестная-почта@firm.ru", "password": "что-угодно"})
    r2 = other.post("/api/auth/login", json={"email": email, "password": "не-тот-пароль"})
    assert r1.json() == r2.json()


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
    assert body["full_name"] == "Тест Тестов"


def test_logout_clears_the_session(client):
    login(client, "выход@firm.ru")
    assert client.get("/api/me").json()["logged_in"] is True
    client.post("/api/auth/logout")
    assert client.get("/api/me").json() == {"logged_in": False}


def test_profile_update_round_trip(client):
    """Профиль раньше нельзя было поправить после регистрации — role навсегда
    оставался individual. PATCH /api/me — способ уже зарегистрированного
    аккаунта сменить тип, не создавая новый."""
    login(client, "профиль@firm.ru")
    r = client.patch("/api/me", json={"company": "ООО Ромашка", "position": "Партнёр", "role": "firm"})
    assert r.status_code == 200
    me = client.get("/api/me").json()
    assert me["company"] == "ООО Ромашка" and me["position"] == "Партнёр" and me["role"] == "firm"


def test_profile_update_rejects_unknown_role(client):
    login(client, "плохая-роль@firm.ru")
    r = client.patch("/api/me", json={"role": "начальник"})
    assert r.status_code == 400


def test_profile_update_rejects_empty_full_name(client):
    login(client, "пустое-имя@firm.ru")
    r = client.patch("/api/me", json={"full_name": " "})
    assert r.status_code == 400


def test_profile_update_requires_login(client):
    assert client.patch("/api/me", json={"company": "X"}).status_code == 401


def test_delete_account_requires_correct_password(client):
    login(client, "удаление-пароль@firm.ru")
    r = client.request("DELETE", "/api/account", json={"password": "не-тот-пароль"})
    assert r.status_code == 400
    assert client.get("/api/me").json()["logged_in"] is True


def test_delete_account_round_trip(client):
    """Удаление стирает аккаунт и всё, что на него ссылалось (подписка,
    отслеживаемая сделка) — и снова можно зарегистрироваться той же почтой."""
    email = "удаление@firm.ru"
    login(client, email)
    client.post("/api/subscriptions", json={"industry": "Банки"})
    client.post("/api/deals/gtest0001/watch")

    r = client.request("DELETE", "/api/account", json={"password": TEST_PASSWORD})
    assert r.status_code == 200
    assert client.get("/api/me").json() == {"logged_in": False}

    again = client.post("/api/auth/register",
                         json={"email": email, "password": TEST_PASSWORD, "full_name": "Тест Тестов"})
    assert again.status_code == 200


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
    # Регистрация просит «Имя и фамилию» — под комментарием показываем их, а
    # не часть e-mail до @ (прежнее поведение молча раскрывало кусок чужого
    # адреса почты каждому посетителю, хотя имя для показа уже было введено).
    assert r.json()["author"] == "Тест Тестов"

    listed = client.get("/api/deals/gtest0001/comments").json()
    assert any(c["body"] == "Кто консультировал продавца?" for c in listed)


def test_comment_author_falls_back_to_email_prefix_without_full_name(client):
    # Аккаунты до 2 августа 2026 (`full_name` добавлено этой датой) могут не
    # нести имени — для них подпись остаётся прежней, единственной, что есть.
    user = User(email="легаси@firm.ru", password_hash="x", full_name=None)
    assert main._comment_author(user) == "легаси"
    user_blank = User(email="пусто@firm.ru", password_hash="x", full_name="   ")
    assert main._comment_author(user_blank) == "пусто"


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


def test_anonymous_correction_goes_to_editorial_queue(client):
    r = client.post("/api/deals/gtest0001/corrections", json={
        "body": "Покупателем был российский девелопер.",
        "contact": "@source_person",
    })
    assert r.status_code == 200 and r.json()["ok"] is True
    s = get_session()
    try:
        row = s.get(CorrectionRequest, r.json()["id"])
        assert row.body == "Покупателем был российский девелопер."
        assert row.contact == "@source_person" and row.user_id is None
    finally:
        s.close()


def test_correction_uses_logged_in_email_when_contact_is_empty(client):
    login(client, "источник@firm.ru")
    r = client.post("/api/deals/gtest0002/corrections", json={"body": "Есть уточнение по дате."})
    assert r.status_code == 200
    s = get_session()
    try:
        row = s.get(CorrectionRequest, r.json()["id"])
        assert row.contact == "источник@firm.ru" and row.user_id is not None
    finally:
        s.close()



def test_general_editorial_message_is_stored_without_a_deal(client):
    r = client.post("/api/corrections", json={
        "body": "Предлагаю добавить новый источник.",
        "contact": "@source_editor",
    })
    assert r.status_code == 200
    s = get_session()
    try:
        row = s.get(CorrectionRequest, r.json()["id"])
        assert row.deal_id is None
        assert row.contact == "@source_editor"
        assert row.status == "new"
    finally:
        s.close()

def test_empty_correction_is_rejected(client):
    r = client.post("/api/deals/gtest0001/corrections", json={"body": "   "})
    assert r.status_code == 400
