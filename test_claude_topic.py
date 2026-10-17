# -*- coding: utf-8 -*-
"""Тема «Клод» в группе-консоли: приём сообщений агенту, мост для рутины и
кнопка «Назначить эту тему» в меню /start (17 октября 2026)."""
import os
import sys

import pytest
from fastapi.testclient import TestClient

import main

CHAT = {"id": -100111, "type": "supergroup", "is_forum": True}
THREAD = 4242
HOOK = "/api/telegram/webhook/тайна"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    monkeypatch.setenv("MODERATION_TOKEN", "тайна")
    monkeypatch.setenv("TELEGRAM_REVIEW_CHAT_IDS", "111, 222")
    calls = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: calls.append((method, kw)) or {"ok": True})
    # Вебхук учит номер группы-консоли и темы в ОБЩЕЙ тестовой базе — а
    # test_kompas позже ждёт адрес группы из окружения. Возвращаем как было.
    from db.session import get_session
    keys = (main.REVIEW_GROUP_SETTING, "telegram_topic:клод")
    with TestClient(main.app) as c:
        with get_session() as s:
            before = {k: (s.get(main.AppSetting, k).value if s.get(main.AppSetting, k) else None)
                      for k in keys}
        # Закрепить тему «Клод» кнопкой, как это сделает владелец.
        c.post(HOOK, json={"callback_query": {
            "id": "bind", "data": "topic:claude", "from": {"id": 111},
            "message": {"message_id": 1, "message_thread_id": THREAD, "chat": CHAT}}})
        # Прочитать всё, что осталось от прошлых тестов: база у модуля общая.
        old = c.get("/api/claude/inbox", params={"token": "тайна"}).json()["messages"]
        c.post("/api/claude/inbox/consume", json={"token": "тайна", "ids": [m["id"] for m in old]})
        main_quiet = main.CLAUDE_ACK_QUIET_SECONDS
        calls.clear()
        yield c, calls
        main.CLAUDE_ACK_QUIET_SECONDS = main_quiet
    with get_session() as s:
        for k, v in before.items():
            row = s.get(main.AppSetting, k)
            if v is None and row is not None:
                s.delete(row)
            elif v is not None:
                if row is None:
                    s.add(main.AppSetting(key=k, value=v))
                else:
                    row.value = v
        s.commit()


def _msg(text=None, sender=111, thread=THREAD, mid=10, **extra):
    m = {"message_id": mid, "chat": CHAT, "from": {"id": sender, "first_name": "Борис"}}
    if thread is not None:
        m["message_thread_id"] = thread
    if text is not None:
        m["text"] = text
    m.update(extra)
    return {"message": m}


def _inbox(c):
    return c.get("/api/claude/inbox", params={"token": "тайна"}).json()["messages"]


def test_topic_lists_agree_and_name_claude():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))
    import console_topics
    assert main.CONSOLE_TOPIC_NAMES["claude"] == "Клод"
    assert console_topics.TOPIC_NAMES == main.CONSOLE_TOPIC_NAMES
    assert set(main.CONSOLE_TOPIC_PURPOSE) == set(main.CONSOLE_TOPIC_NAMES)


def test_reviewer_message_in_claude_topic_is_saved_and_acknowledged(env):
    c, calls = env
    assert c.post(HOOK, json=_msg("@projectcompassru_bot поправь подпись на главной",
                                  mid=10)).status_code == 200
    rows = _inbox(c)
    assert len(rows) == 1
    assert rows[0]["text"] == "поправь подпись на главной"
    assert rows[0]["message_id"] == 10 and rows[0]["thread_id"] == THREAD
    assert rows[0]["from_name"] == "Борис"
    sent = [kw for m, kw in calls if m == "sendMessage"]
    assert len(sent) == 1
    assert sent[0]["text"] == main.CLAUDE_ACK_TEXT
    assert sent[0]["message_thread_id"] == THREAD and sent[0]["reply_to_message_id"] == 10

    # Второе сообщение подряд — сохраняется, но подтверждения не получает.
    calls.clear()
    c.post(HOOK, json=_msg("и ещё одно", mid=11))
    assert len(_inbox(c)) == 2
    assert [m for m, _kw in calls if m == "sendMessage"] == []

    # Через минуту тишины — снова подтверждаем.
    main.CLAUDE_ACK_QUIET_SECONDS = 0
    calls.clear()
    c.post(HOOK, json=_msg("третье", mid=12))
    assert len([m for m, _kw in calls if m == "sendMessage"]) == 1


def test_photo_document_and_reply_context_are_kept(env):
    c, _calls = env
    c.post(HOOK, json=_msg(None, mid=20, caption="вот скрин",
                           photo=[{"file_id": "small", "file_size": 10, "width": 90, "height": 90},
                                  {"file_id": "big", "file_size": 900, "width": 1280, "height": 720}],
                           reply_to_message={"message_id": 5, "text": "Сделано: кнопка на месте"}))
    c.post(HOOK, json=_msg(None, mid=21, document={"file_id": "doc1", "file_name": "отчёт.pdf"}))
    rows = _inbox(c)
    assert rows[0]["text"] == "вот скрин" and rows[0]["photo_file_id"] == "big"
    assert rows[0]["reply_to_text"] == "Сделано: кнопка на месте"
    assert rows[1]["document_file_id"] == "doc1" and rows[1]["document_name"] == "отчёт.pdf"


def test_reply_to_a_marked_bot_message_in_claude_topic_goes_to_claude(env):
    """Маркерная ветка ([пост …]) не перехватывает тему «Клод»."""
    c, _calls = env
    c.post(HOOK, json=_msg("а это что?", mid=30,
                           reply_to_message={"message_id": 6, "text": "[пост g12345678]\nтекст"}))
    rows = _inbox(c)
    assert len(rows) == 1 and rows[0]["text"] == "а это что?"
    decisions = c.get("/api/moderation/decisions", params={"token": "тайна"}).json()["decisions"]
    assert not any(d["deal_id"] == "g12345678" for d in decisions)


def test_stranger_other_topic_and_commands_are_not_saved(env):
    c, calls = env
    c.post(HOOK, json=_msg("я посторонний", sender=999, mid=40))
    c.post(HOOK, json=_msg("это другая тема", thread=77, mid=41))
    c.post(HOOK, json=_msg("это общая лента", thread=None, mid=42))
    c.post(HOOK, json=_msg("/queue@projectcompassru_bot", mid=43))
    assert _inbox(c) == []
    assert not any(kw.get("text") == main.CLAUDE_ACK_TEXT for _m, kw in calls)


def test_inbox_and_consume_need_the_token(env):
    c, _calls = env
    c.post(HOOK, json=_msg("задача", mid=50))
    assert c.get("/api/claude/inbox", params={"token": "чужой"}).status_code == 404
    assert c.post("/api/claude/inbox/consume",
                  json={"token": "чужой", "ids": [1]}).status_code == 404
    rows = _inbox(c)
    assert len(rows) == 1
    r = c.post("/api/claude/inbox/consume", json={"token": "тайна", "ids": [rows[0]["id"]]})
    assert r.json() == {"consumed": 1}
    assert _inbox(c) == []


def test_menu_button_offers_topic_kinds_including_claude(env):
    c, calls = env
    data = [b["callback_data"] for row in main._bot_menu()["inline_keyboard"] for b in row]
    assert "menu:topic" in data
    c.post(HOOK, json={"callback_query": {
        "id": "m1", "data": "menu:topic", "from": {"id": 111},
        "message": {"message_id": 70, "message_thread_id": 555, "chat": CHAT}}})
    sent = [kw for m, kw in calls if m == "sendMessage"]
    assert len(sent) == 1 and sent[0]["message_thread_id"] == 555
    buttons = [b for row in sent[0]["reply_markup"]["inline_keyboard"] for b in row]
    assert {"text": "Клод", "callback_data": "topic:claude"} in buttons
    assert any(m == "answerCallbackQuery" for m, _kw in calls)

    # Посторонний — отказ, без кнопок.
    calls.clear()
    c.post(HOOK, json={"callback_query": {
        "id": "m2", "data": "menu:topic", "from": {"id": 999},
        "message": {"message_id": 71, "message_thread_id": 555, "chat": CHAT}}})
    assert [m for m, _kw in calls] == ["answerCallbackQuery"]


def test_script_prints_instead_of_sending_without_bot_token(monkeypatch, capsys):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))
    import claude_topic
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert claude_topic.main(["--reply", "10", "--text", "x" * 9000]) == 0
    out = capsys.readouterr().out
    assert "ничего не отправлено" in out and out.count("---") == 3
    parts = claude_topic.split_text("слово " * 1000)
    assert all(len(p) <= claude_topic.CHUNK for p in parts) and len(parts) == 2
    assert " ".join(parts).split() == ["слово"] * 1000
