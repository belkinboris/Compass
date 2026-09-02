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
    assert r.json() == {"logged_in": False, "gate": False}


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
    assert client.get("/api/me").json() == {"logged_in": False, "gate": False}


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
    assert client.get("/api/me").json() == {"logged_in": False, "gate": False}

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


# ==================== Вход по заявке (ACCESS_GATE, 2 сентября 2026) ====================
# Гейт для тестов выключен в conftest.py (ACCESS_GATE=0); здесь он включается
# явно через main.ACCESS_GATE — эндпоинты читают модульную константу при
# каждом вызове, monkeypatch её видит.

def _gate_on(monkeypatch):
    monkeypatch.setattr(main, "ACCESS_GATE", True)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    monkeypatch.setenv("TELEGRAM_REVIEW_CHAT_IDS", "111, 222")
    monkeypatch.setenv("TELEGRAM_REVIEW_GROUP_ID", "-1001234567890")
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    return sent


def _request_access(client, email, **extra):
    payload = {"email": email, "password": TEST_PASSWORD, "full_name": "Заявка Заявкина",
               "company": "ООО Ромашка", "position": "Партнёр"}
    payload.update(extra)
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 200 and r.json() == {"ok": True, "pending": True}
    assert "kompas_session" not in r.cookies, "заявка не должна ставить сессию"
    s = get_session()
    try:
        return s.query(User).filter_by(email=email).one().id
    finally:
        s.close()


def test_me_reports_whether_the_gate_is_on(client, monkeypatch):
    """Интерфейс решает, показывать ли экран входа вместо сайта, по полю gate."""
    assert client.get("/api/me").json() == {"logged_in": False, "gate": False}
    monkeypatch.setattr(main, "ACCESS_GATE", True)
    assert client.get("/api/me").json() == {"logged_in": False, "gate": True}


def test_registration_under_gate_is_a_pending_request_with_a_telegram_notice(client, monkeypatch):
    """Заявка: аккаунт с approved=False, без сессии, владельцам уходит сообщение
    с кнопками «Одобрить»/«Отклонить» (callback_data acc:<id>:ok|no)."""
    sent = _gate_on(monkeypatch)
    uid = _request_access(client, "заявка@firm.ru")
    s = get_session()
    try:
        assert s.get(User, uid).approved is False
    finally:
        s.close()
    assert [m for m, _ in sent] == ["sendMessage"]
    body = sent[0][1]
    assert body["chat_id"] == "-1001234567890"
    for word in ("Заявка на доступ", "Заявка Заявкина", "ООО Ромашка", "Партнёр", "заявка@firm.ru"):
        assert word in body["text"], word
    buttons = [b["callback_data"] for row in body["reply_markup"]["inline_keyboard"] for b in row]
    assert buttons == [f"acc:{uid}:ok", f"acc:{uid}:no"]


def test_login_under_gate_is_403_until_the_owner_approves(client, monkeypatch):
    _gate_on(monkeypatch)
    uid = _request_access(client, "ждёт@firm.ru")
    r = client.post("/api/auth/login", json={"email": "ждёт@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 403 and r.json()["pending"] is True
    assert "доступ откроем после проверки" in r.json()["error"]
    assert "kompas_session" not in r.cookies

    ok = client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"id": "1", "data": f"acc:{uid}:ok", "from": {"id": 111, "first_name": "Борис"},
                            "message": {"chat": {"id": -1001234567890}, "message_id": 7, "text": "Заявка"}}})
    assert ok.status_code == 200
    r = client.post("/api/auth/login", json={"email": "ждёт@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 200 and "kompas_session" in r.cookies
    me = client.get("/api/me").json()
    assert me["logged_in"] is True and me["gate"] is True and me["approved"] is True


def test_access_requests_are_listed_and_decided_by_token(client, monkeypatch):
    """Владелец, который смотрит заявки не из Telegram: список ожидающих и
    решение по токену моста модерации; чужой токен — 404, как у моста."""
    _gate_on(monkeypatch)
    monkeypatch.setenv("MODERATION_TOKEN", "секрет")
    uid = _request_access(client, "список@firm.ru")
    assert client.get("/api/access/requests", params={"token": "чужой"}).status_code == 404
    r = client.get("/api/access/requests", params={"token": "секрет"})
    assert r.status_code == 200
    body = r.json()
    mine = [p for p in body["pending"] if p["id"] == uid]
    assert mine and mine[0]["email"] == "список@firm.ru" and mine[0]["company"] == "ООО Ромашка"
    assert body["gate"] is True and isinstance(body["approved_count"], int)
    d = client.post("/api/access/decide", json={"token": "секрет", "user_id": uid, "approve": True})
    assert d.status_code == 200 and d.json()["approved"] is True
    assert uid not in [p["id"] for p in client.get("/api/access/requests", params={"token": "секрет"}).json()["pending"]]
    r = client.post("/api/auth/login", json={"email": "список@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 200
    assert client.post("/api/access/decide", json={"token": "секрет", "user_id": 10**9}).status_code == 404


def test_approval_is_stamped_into_the_telegram_message(client, monkeypatch):
    """Как у модерации: решение дописывается в само сообщение группы, чтобы
    второй человек видел, что первый уже нажал."""
    sent = _gate_on(monkeypatch)
    uid = _request_access(client, "штамп@firm.ru")
    sent.clear()
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"id": "9", "data": f"acc:{uid}:ok", "from": {"id": 222, "first_name": "Партнёр"},
                            "message": {"chat": {"id": -1001234567890}, "message_id": 7, "text": "Заявка на доступ"}}})
    methods = {m: kw for m, kw in sent}
    assert methods["answerCallbackQuery"]["callback_query_id"] == "9"
    assert methods["editMessageText"]["message_id"] == 7
    assert "Доступ открыт" in methods["editMessageText"]["text"] and "(Партнёр)" in methods["editMessageText"]["text"]


def test_stranger_cannot_approve_an_access_request(client, monkeypatch):
    """Право решать — по from.id, как у mod: (в общей группе chat.id один на всех)."""
    sent = _gate_on(monkeypatch)
    uid = _request_access(client, "чужой-судья@firm.ru")
    sent.clear()
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"id": "2", "data": f"acc:{uid}:ok", "from": {"id": 999}}})
    s = get_session()
    try:
        assert s.get(User, uid).approved is False
    finally:
        s.close()
    assert sent and sent[0][0] == "answerCallbackQuery" and "только владелец" in sent[0][1]["text"]
    r = client.post("/api/auth/login", json={"email": "чужой-судья@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 403


def test_rejected_request_stays_closed_and_does_not_duplicate(client, monkeypatch):
    """Отклонённый не удаляется: вход отвечает тем же «доступ не открыт», а
    повторная заявка тем же адресом — отказ «уже зарегистрирована», не дубль."""
    _gate_on(monkeypatch)
    uid = _request_access(client, "отказ@firm.ru")
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"id": "3", "data": f"acc:{uid}:no", "from": {"id": 111}}})
    r = client.post("/api/auth/login", json={"email": "отказ@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 403 and "доступ откроем после проверки" in r.json()["error"]
    again = client.post("/api/auth/register", json={"email": "отказ@firm.ru", "password": TEST_PASSWORD,
                                                     "full_name": "Заявка Заявкина"})
    assert again.status_code == 400 and "уже зарегистрирована" in again.json()["error"]
    s = get_session()
    try:
        assert s.query(User).filter_by(email="отказ@firm.ru").count() == 1
        assert s.get(User, uid).approved is False
    finally:
        s.close()


def test_telegram_failure_does_not_break_the_registration(client, monkeypatch):
    """Сеть до Telegram упала — заявка всё равно сохранена и отвечает pending."""
    _gate_on(monkeypatch)

    def boom(method, **kw):
        raise RuntimeError("telegram недоступен")
    monkeypatch.setattr(main.notification_service, "tg_api", boom)
    uid = _request_access(client, "без-сети@firm.ru")
    s = get_session()
    try:
        assert s.get(User, uid).approved is False
    finally:
        s.close()


def test_gate_off_registers_approved_users_and_logs_them_in(client, monkeypatch):
    """Выключенный гейт (ACCESS_GATE=0) — прежнее поведение: сессия сразу,
    approved=True, чтобы при последующем включении гейта эти люди вошли."""
    monkeypatch.setattr(main, "ACCESS_GATE", False)
    login(client, "до-гейта@firm.ru")
    s = get_session()
    try:
        assert s.query(User).filter_by(email="до-гейта@firm.ru").one().approved is True
    finally:
        s.close()
    monkeypatch.setattr(main, "ACCESS_GATE", True)
    other = TestClient(main.app)
    r = other.post("/api/auth/login", json={"email": "до-гейта@firm.ru", "password": TEST_PASSWORD})
    assert r.status_code == 200


def test_users_table_created_before_the_gate_gets_approved_column_set_to_true(tmp_path):
    """Миграция для уже существующей таблицы users (create_all колонку не
    добавит): approved появляется диалект-независимым ADD COLUMN, и всем
    существующим аккаунтам ставится True — владелец и партнёр не оказываются
    за дверью. Повторный запуск ничего не ломает."""
    from sqlalchemy import create_engine, inspect, text
    engine = create_engine(f"sqlite:///{tmp_path}/old.db")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(300))"))
        conn.execute(text("INSERT INTO users (email) VALUES ('старый@firm.ru')"))
    main._ensure_user_columns(engine)
    main._ensure_user_columns(engine)
    cols = {c["name"] for c in inspect(engine).get_columns("users")}
    assert {"password_hash", "full_name", "company", "position", "approved"} <= cols
    with engine.connect() as conn:
        assert conn.execute(text("SELECT approved FROM users")).scalar() == 1
