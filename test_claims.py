# -*- coding: utf-8 -*-
"""Кабинет компании: «Это моя компания» (14 октября 2026).

Заявка вошедшего на карточку компании или фирмы-консультанта, решение
кнопкой в Telegram-консоли или по токену, правки от подтверждённого
представителя — обычной заметкой для рутины, просмотры карточки за 30 дней.
Устройство — docs/company_cabinet.md.

Запуск: python3 -m pytest test_claims.py -q
"""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import base_data
import main
from db.models import CompanyClaim, CorrectionRequest, Notification, PageView, User
from db.session import get_session

PASSWORD = "надёжный-тестовый-пароль"
GROUP = "-1001234567890"


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def console(monkeypatch):
    """Консоль с двумя участниками (111 и 222); всё, что ушло в Telegram, — в список."""
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    monkeypatch.setenv("TELEGRAM_REVIEW_CHAT_IDS", "111, 222")
    monkeypatch.setenv("TELEGRAM_REVIEW_GROUP_ID", GROUP)
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    return sent


def _user(client, name="Софья Тестова"):
    email = "cab-%s@firm.ru" % uuid.uuid4().hex[:8]
    r = client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "full_name": name,
                                                "company": "Тест", "position": "Основатель"})
    assert r.status_code == 200
    return email


def _company_id():
    companies = (base_data.promoted() or {}).get("companies") or {}
    cid = next(k for k, v in companies.items() if v.get("name"))
    return cid, companies[cid]["name"]


def _press(client, data, from_id=111):
    return client.post("/api/telegram/webhook/тайна", json={"callback_query": {
        "id": "cb1", "data": data, "from": {"id": from_id, "first_name": "Борис"},
        "message": {"chat": {"id": int(GROUP)}, "message_id": 7, "text": "Просят подключить"}}})


def _claim(cid):
    s = get_session()
    try:
        row = s.get(CompanyClaim, cid)
        s.expunge(row)
        return row
    finally:
        s.close()


def test_claim_needs_login_and_a_card_that_exists(client, console):
    assert client.post("/api/claims", json={"kind": "firm", "target_id": "execburo"}).status_code == 401
    assert client.get("/api/me/claims").status_code == 401
    _user(client)
    for kind, target in (("firm", "нет-такой"), ("company", "g00000000"), ("person", "execburo")):
        r = client.post("/api/claims", json={"kind": kind, "target_id": target})
        assert r.status_code == 400, (kind, target)
    assert not console


def test_claim_goes_to_the_console_with_two_buttons_and_a_repeat_adds_nothing(client, console):
    email = _user(client)
    r = client.post("/api/claims", json={"kind": "firm", "target_id": "execburo",
                                         "position": "Основатель", "note": "Пишите в Telegram"})
    assert r.status_code == 200 and r.json()["existing"] is False
    claim = r.json()["claim"]
    assert claim["status"] == "pending" and claim["target_name"] == "Execburo"
    assert claim["link"] == "#/advisors/execburo" and "views_30d" not in claim
    assert [m for m, _ in console] == ["sendMessage"]
    msg = console[0][1]
    assert msg["chat_id"] == GROUP
    for word in ("Execburo", "консультант", email, "Основатель", "Пишите в Telegram", "/#/advisors/execburo"):
        assert word in msg["text"], word
    buttons = [b["callback_data"] for row in msg["reply_markup"]["inline_keyboard"] for b in row]
    assert buttons == ["claim:ok:%d" % claim["id"], "claim:no:%d" % claim["id"]]

    console.clear()
    again = client.post("/api/claims", json={"kind": "firm", "target_id": "execburo"})
    assert again.status_code == 200 and again.json()["existing"] is True
    assert again.json()["claim"]["id"] == claim["id"] and not console
    mine = client.get("/api/me/claims").json()
    assert [c["id"] for c in mine["claims"]] == [claim["id"]]
    assert ["look", "Логотип и оформление"] in mine["change_kinds"]


def test_change_request_only_after_approval_and_only_by_the_owner_of_the_claim(client, console):
    cid, name = _company_id()
    email = _user(client)
    claim_id = client.post("/api/claims", json={"kind": "company", "target_id": cid}).json()["claim"]["id"]
    r = client.post("/api/claims/%d/change" % claim_id, json={"kind": "about", "body": "Новое описание"})
    assert r.status_code == 403

    console.clear()
    _press(client, "claim:ok:%d" % claim_id, from_id=999)          # чужой в группе
    assert _claim(claim_id).status == "pending"
    assert console[0][0] == "answerCallbackQuery" and "только владелец" in console[0][1]["text"]

    console.clear()
    _press(client, "claim:ok:%d" % claim_id)
    row = _claim(claim_id)
    assert row.status == "approved" and row.decided_at is not None
    stamps = {m: kw for m, kw in console}
    assert "подключена к кабинету" in stamps["editMessageText"]["text"]
    s = get_session()
    try:
        user = s.query(User).filter_by(email=email).one()
        note = s.query(Notification).filter_by(user_id=user.id, kind="company_claim").one()
        assert name in note.title and note.link.endswith("#/account?tab=company")
    finally:
        s.close()

    r = client.post("/api/claims/%d/change" % claim_id,
                    json={"kind": "contacts", "body": "Сайт теперь example.ru"})
    assert r.status_code == 200
    s = get_session()
    try:
        row = s.get(CorrectionRequest, r.json()["id"])
        assert row.status == "new" and row.deal_id is None and row.contact == email
        assert row.body.startswith("Представитель «%s» (подтверждён), %s: Сайт и контакты" % (name, email))
        assert "Сайт теперь example.ru" in row.body and "/#/companies/%s" % cid in row.body
    finally:
        s.close()
    assert client.post("/api/claims/%d/change" % claim_id, json={"body": "  "}).status_code == 400

    client.cookies.clear()
    _user(client, name="Чужой Человек")
    r = client.post("/api/claims/%d/change" % claim_id, json={"kind": "other", "body": "Подмена"})
    assert r.status_code == 404


def test_claim_is_decided_by_the_moderation_token_without_buttons(client, console, monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "секрет")
    _user(client)
    claim_id = client.post("/api/claims", json={"kind": "firm", "target_id": "execburo"}).json()["claim"]["id"]
    assert client.get("/api/ops/claims", params={"token": "чужой"}).status_code == 404
    listed = client.get("/api/ops/claims", params={"token": "секрет"}).json()["claims"]
    assert claim_id in [c["id"] for c in listed]
    assert client.post("/api/ops/claims/%d" % claim_id, json={"token": "чужой"}).status_code == 404
    assert client.post("/api/ops/claims/999999999", json={"token": "секрет"}).status_code == 404
    r = client.post("/api/ops/claims/%d" % claim_id, json={"token": "секрет", "approve": False})
    assert r.status_code == 200 and r.json()["claim"]["status"] == "rejected"
    assert client.post("/api/claims/%d/change" % claim_id, json={"body": "x"}).status_code == 403
    r = client.post("/api/ops/claims/%d" % claim_id, json={"token": "секрет", "approve": True})
    assert r.json()["claim"]["status"] == "approved"


def test_my_claims_count_card_views_for_the_last_30_days(client, console, monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "секрет")
    _user(client)
    claim_id = client.post("/api/claims", json={"kind": "firm", "target_id": "execburo"}).json()["claim"]["id"]
    s = get_session()
    try:
        before = s.query(PageView).filter(PageView.path == "/advisors/execburo",
                                          PageView.created_at >= datetime.utcnow() - timedelta(days=29)).count()
        old = datetime.utcnow() - timedelta(days=40)
        for when in (None, None, old):
            s.add(PageView(visitor="v" * 24, session="s" * 24, path="/advisors/execburo", section="advisor",
                           **({"created_at": when} if when else {})))
        s.add(PageView(visitor="v" * 24, session="s" * 24, path="/advisors/kept", section="advisor"))
        s.commit()
    finally:
        s.close()
    client.post("/api/ops/claims/%d" % claim_id, json={"token": "секрет"})
    mine = [c for c in client.get("/api/me/claims").json()["claims"] if c["id"] == claim_id][0]
    assert mine["status"] == "approved" and mine["views_30d"] == before + 2


def test_deleting_the_account_removes_its_claims(client, console):
    _user(client)
    claim_id = client.post("/api/claims", json={"kind": "firm", "target_id": "execburo"}).json()["claim"]["id"]
    assert client.request("DELETE", "/api/account", json={"password": PASSWORD}).status_code == 200
    s = get_session()
    try:
        assert s.get(CompanyClaim, claim_id) is None
    finally:
        s.close()
