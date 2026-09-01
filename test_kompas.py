"""Тесты «КОМПАС»: yandex_search + /api/ask. Запуск: pytest test_kompas.py -v"""
import base64
import json
import time
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

import main
import yandex_search as ys

# ---------- yandex_search ----------

XML_OK = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch><response><results><grouping>
<group><doc>
  <url>https://old.example.ru/a</url><title>Старая новость</title>
  <modtime>20260101T000000</modtime>
  <passage>Старый сниппет</passage>
</doc></group>
<group><doc>
  <url>https://fresh.example.ru/b</url><title>Свежая сделка</title>
  <modtime>20260718T120000</modtime>
  <passage>Компания А купила компанию Б</passage>
</doc></group>
<group><doc>
  <url>https://nodate.example.ru/c</url><title>Без даты</title>
  <passage>Сниппет без modtime</passage>
</doc></group>
</grouping></results></response></yandexsearch>"""

XML_EMPTY = """<?xml version="1.0"?><yandexsearch><response><results/></response></yandexsearch>"""
XML_ERROR = """<?xml version="1.0"?><yandexsearch><response><error code="15">Nothing found for query</error></response></yandexsearch>"""

CFG = ys.SearchConfig(api_key="k", folder_id="f")


def _transport(status=200, xml=XML_OK):
    def handler(request):
        return httpx.Response(status, json={"rawData": base64.b64encode(xml.encode()).decode()})
    return httpx.MockTransport(handler)


def test_parse_ok_sorted_by_freshness():
    r = ys.parse_search_xml(XML_OK.encode())
    assert [x.title for x in r] == ["Свежая сделка", "Старая новость", "Без даты"]
    assert r[0].url == "https://fresh.example.ru/b"
    assert r[0].modtime == datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    assert "Источник: https://fresh.example.ru/b" in r[0].as_prompt_line()


def test_parse_empty_is_empty_list_not_error():
    assert ys.parse_search_xml(XML_EMPTY.encode()) == []


def test_parse_service_error_raises():
    with pytest.raises(ys.SearchError):
        ys.parse_search_xml(XML_ERROR.encode())


def test_search_http_error_raises():
    with httpx.Client(transport=_transport(status=403)) as c:
        with pytest.raises(ys.SearchError):
            ys.yandex_search("q", config=CFG, client=c)


def test_search_disabled_raises():
    cfg = ys.SearchConfig(api_key="k", folder_id="f", enabled=False)
    with pytest.raises(ys.SearchError):
        ys.yandex_search("q", config=cfg)


def test_search_bad_base64_raises():
    def handler(request):
        return httpx.Response(200, json={"rawData": "%%%not-base64%%%"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(ys.SearchError):
            ys.yandex_search("q", config=CFG, client=c)


def test_build_search_block():
    block = ys.build_search_block(ys.parse_search_xml(XML_OK.encode()))
    assert block.startswith("СВЕЖАЯ ВЫДАЧА ПОИСКА (Яндекс)")
    assert "не выдумывай" in block
    assert block.count("Источник:") == 3
    assert ys.build_search_block([]) == ""


# ---------- /api/ask ----------

RESPONSES_OK = {
    "output": [
        {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "думаю..."}]},
        {"type": "message", "content": [{"type": "output_text", "text": "Ответ ассистента"}]},
    ]
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    return TestClient(main.app)


def test_health_ai_flag(monkeypatch):
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)
    assert TestClient(main.app).get("/health").json() == {"status": "ok", "ai": False}


def test_ask_no_keys_fallback(monkeypatch):
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)
    r = TestClient(main.app).post("/api/ask", json={"question": "q", "context": "{}"})
    assert r.json() == {"fallback": True}


def test_ask_base_mode(client, monkeypatch):
    captured = {}

    def fake_llm(system, user, max_tokens, deadline=None):
        captured.update(system=system, user=user, max_tokens=max_tokens)
        return "Ответ ассистента"

    monkeypatch.setattr(main, "call_llm", fake_llm)
    r = client.post("/api/ask", json={"question": "Кто купил X?", "context": "{}", "mode": "base"})
    assert r.json()["answer"] == "Ответ ассистента"
    assert captured["system"] == main.SYSTEM_BASE
    assert "СВЕЖАЯ ВЫДАЧА" not in captured["user"]
    assert captured["max_tokens"] == 700


def test_ask_web_mode_with_results(client, monkeypatch):
    # Модель не дала ссылку сама -> ask() обязан подставить источники
    # (см. main._sources_footer): это гарантия цитирования, а не опция.
    captured = {}
    results = ys.parse_search_xml(XML_OK.encode())
    monkeypatch.setattr(main, "yandex_search", lambda q, config=None, client=None: results)

    def fake_llm(system, user, max_tokens, deadline=None):
        captured.update(system=system, user=user, max_tokens=max_tokens)
        return "Ответ с фактами"

    monkeypatch.setattr(main, "call_llm", fake_llm)
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "web"})
    assert r.json()["answer"] == "Ответ с фактами" + main._sources_footer(results)
    assert captured["system"] == main.SYSTEM_WEB
    assert "СВЕЖАЯ ВЫДАЧА ПОИСКА (Яндекс)" in captured["user"]
    assert captured["max_tokens"] == 1400


def test_ask_web_mode_model_already_cited_no_footer(client, monkeypatch):
    # Модель сама вставила markdown-ссылку -> источники повторно не приписываем.
    monkeypatch.setattr(
        main, "yandex_search",
        lambda q, config=None, client=None: ys.parse_search_xml(XML_OK.encode()),
    )
    cited = "Ответ с фактами и [ссылкой на источник](https://fresh.example.ru/b)."
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None: cited)
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "web"})
    assert r.json()["answer"] == cited


def test_ask_web_mode_search_fails_degrades_to_base(client, monkeypatch):
    captured = {}

    def broken_search(q, config=None, client=None):
        raise ys.SearchError("403")

    monkeypatch.setattr(main, "yandex_search", broken_search)
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None: captured.update(system=s) or "Ответ по базе")
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "web"})
    assert r.json()["answer"] == "Ответ по базе"  # пользователь не видит ошибку
    assert captured["system"] == main.SYSTEM_BASE


def test_ask_web_mode_empty_results_degrades_to_base(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "yandex_search", lambda q, config=None, client=None: [])
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None: captured.update(system=s) or "Ответ по базе")
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "web"})
    assert r.json()["answer"] == "Ответ по базе"
    assert captured["system"] == main.SYSTEM_BASE


def test_ask_llm_dead_returns_fallback(client, monkeypatch):
    def dead(s, u, max_tokens, deadline=None):
        raise RuntimeError("LLM недоступен")
    monkeypatch.setattr(main, "call_llm", dead)
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "base"})
    assert r.json() == {"fallback": True}


# ---------- call_llm / _extract_text ----------

def test_extract_text_filters_reasoning():
    assert main._extract_text(RESPONSES_OK) == "Ответ ассистента"


def test_call_llm_thinking_budget_and_retry(monkeypatch):
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    calls = {"n": 0, "payload": None}

    def handler(request):
        calls["n"] += 1
        calls["payload"] = json.loads(request.content)
        if calls["n"] == 1:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json=RESPONSES_OK)

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
    text = main.call_llm("sys", "user", max_tokens=700)
    assert text == "Ответ ассистента"
    assert calls["n"] == 2  # первый упал, второй прошёл
    p = calls["payload"]
    assert p["model"] == "gpt://f/deepseek-v4-flash/latest"
    assert p["max_output_tokens"] == 700 + main.THINKING_BUDGET
    assert p["instructions"] == "sys"


def test_call_llm_stops_when_the_deadline_has_passed(monkeypatch):
    """Три попытки по 30 с складывались в 180 с ожидания и ПУСТОЙ ответ (замер
    на бою 7 августа поймал ровно такой запрос). Дедлайн обязан обрывать
    повторы: пользователю обещано время ответа, а не число попыток."""
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500, text="boom")

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
    # Дедлайн уже в прошлом — ни одной попытки быть не должно.
    with pytest.raises(RuntimeError):
        main.call_llm("sys", "user", max_tokens=700, deadline=time.monotonic() - 1)
    assert calls["n"] == 0
    # Запаса меньше восьми секунд не хватит и на одну попытку — тоже не начинаем.
    with pytest.raises(RuntimeError):
        main.call_llm("sys", "user", max_tokens=700, deadline=time.monotonic() + 3)
    assert calls["n"] == 0
    # Запаса достаточно — попытки идут, но их число ограничено LLM_RETRIES.
    with pytest.raises(RuntimeError):
        main.call_llm("sys", "user", max_tokens=700, deadline=time.monotonic() + 60)
    assert calls["n"] == 1 + main.LLM_RETRIES


def test_web_mode_returns_found_sources_when_the_model_is_silent(client, monkeypatch):
    """Поиск отработал, модель — нет. Пустой экран после минуты ожидания читается
    как «ассистент сломан»; найденные ссылки по делу и их надо отдать."""
    results = ys.parse_search_xml(XML_OK.encode())
    monkeypatch.setattr(main, "yandex_search", lambda q, config=None, client=None: results)

    def dead(s, u, max_tokens, deadline=None):
        raise RuntimeError("LLM недоступен")

    monkeypatch.setattr(main, "call_llm", dead)
    r = client.post("/api/ask", json={"question": "q", "context": "{}", "mode": "web"})
    body = r.json()
    assert "fallback" not in body
    assert results[0].url in body["answer"]


# ---------- поиск по базе на сервере (1 сентября 2026) ----------
# Партнёр 31 августа получил от ассистента «у Orion сделок нет» при 15
# карточках в базе, служебные id в скобках и 30–40 секунд ожидания. Теперь
# факты ищет сервер (assistant_retrieval.py) ДО модели, и ниже — контракт.

ORION_Q = "Какие сделки сопровождала Orion?"


def test_ask_gives_the_model_a_verified_summary_and_cards(client, monkeypatch):
    captured = {}

    def fake_llm(system, user, max_tokens, deadline=None):
        captured.update(user=user)
        return "Ответ"

    monkeypatch.setattr(main, "call_llm", fake_llm)
    body = client.post("/api/ask", json={"question": ORION_Q}).json()
    assert "СВОДКА" in captured["user"] and "КАРТОЧКИ" in captured["user"]
    assert "#/advisors/orion" in captured["user"]
    assert captured["user"].rstrip().endswith("Вопрос посетителя: " + ORION_Q)
    assert body["intent"] == "advisor" and len(body["deals"]) >= 5
    assert all({"id", "title"} <= set(d) for d in body["deals"])


def test_ask_without_keys_still_answers_from_the_base(monkeypatch):
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)
    body = TestClient(main.app).post("/api/ask", json={"question": ORION_Q}).json()
    assert "fallback" not in body
    assert body["model"] is False and "#/advisors/orion" in body["answer"]


def test_ask_llm_dead_but_the_base_knows_returns_facts(client, monkeypatch):
    def dead(s, u, max_tokens, deadline=None):
        raise RuntimeError("LLM недоступен")

    monkeypatch.setattr(main, "call_llm", dead)
    body = client.post("/api/ask", json={"question": ORION_Q}).json()
    assert "fallback" not in body
    assert body["model"] is False and "#/advisors/orion" in body["answer"]
    assert body["answer"].startswith("Модель не ответила вовремя")


def test_ask_passes_guest_history_to_the_model(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None: captured.update(user=u) or "Ответ")
    client.post("/api/ask", json={
        "question": "А кто консультировал?",
        "history": [{"role": "user", "body": "Кто купил Ситибанк?"},
                    {"role": "assistant", "body": "Ренессанс Капитал, в феврале 2026 года."}],
    })
    assert "Посетитель: Кто купил Ситибанк?" in captured["user"]
    assert "Ассистент: Ренессанс Капитал" in captured["user"]


def test_ask_strips_the_context_prefix_of_old_clients(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None: captured.update(user=u) or "Ответ")
    client.post("/api/ask", json={
        "question": "Контекст: пользователь смотрит «Магнит». Вопрос: какие сделки были у Магнита?",
        "context_type": "company", "context_id": "gd19e26bf",
    })
    assert captured["user"].rstrip().endswith("Вопрос посетителя: какие сделки были у Магнита?")
    assert "пользователь смотрит" not in captured["user"]


def test_polish_removes_bare_ids_and_links_to_unknown_deals():
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    did = "citibank"
    assert did in idx.by_id
    text = (f"Сделка [Ситибанк](#/deal/{did}) и она же ({did}), "
            f"чужая [ссылка](#/deal/nope-123) и голый адрес #/deal/{did}.")
    out = main._polish_answer(text, idx)
    assert f"({did})" not in out
    assert "#/deal/nope-123" not in out and "ссылка" in out
    assert out.count(f"(#/deal/{did})") == 2  # ссылка осталась, голый адрес стал ссылкой с названием


def test_lookup_returns_facts_without_the_model(client):
    body = client.post("/api/assistant/lookup", json={"question": ORION_Q}).json()
    assert body["intent"] == "advisor" and body["deals"] and "#/advisors/orion" in body["answer"]
    assert client.post("/api/assistant/lookup", json={"question": "q"}).json()["answer"] is None


def test_suggestions_come_from_the_base_and_not_the_silly_list(client):
    s = client.get("/api/assistant/suggestions").json()["suggestions"]
    assert len(s) >= 3
    assert "Кто сопровождал сделки в базе?" not in s
    assert all("база" not in q.lower() for q in s)


def test_feedback_is_stored_and_a_down_vote_reaches_the_console(monkeypatch):
    from db.models import AssistantFeedback
    from db.session import get_session
    from sqlalchemy import select as sa_select

    sent = []
    monkeypatch.setenv("TELEGRAM_REVIEW_GROUP_ID", "-100500")
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **p: sent.append((method, p)) or {"ok": True})

    class SyncThread:  # отправка идёт в фоне; в тесте — сразу
        def __init__(self, target=None, args=(), daemon=None):
            self.target, self.args = target, args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(main.threading, "Thread", SyncThread)
    with TestClient(main.app) as c:
        bad = c.post("/api/assistant/feedback", json={"question": "q", "answer": "a", "verdict": "maybe"})
        assert bad.status_code == 400
        r = c.post("/api/assistant/feedback", json={
            "question": ORION_Q, "answer": "У Orion сделок нет.", "verdict": "down",
            "mode": "base", "intent": "advisor"})
        assert r.json()["ok"] is True
        fid = r.json()["id"]
        assert sent and sent[0][0] == "sendMessage" and sent[0][1]["chat_id"] == "-100500"
        assert "не помог" in sent[0][1]["text"] and ORION_Q in sent[0][1]["text"]
        # Комментарий — вторым запросом к той же записи, не новой строкой.
        r2 = c.post("/api/assistant/feedback", json={
            "question": ORION_Q, "answer": "У Orion сделок нет.", "verdict": "down",
            "note": "В базе 15 сделок Orion", "feedback_id": fid})
        assert r2.json() == {"ok": True, "id": fid}
        assert "В базе 15 сделок Orion" in sent[-1][1]["text"]
        up = c.post("/api/assistant/feedback", json={"question": "x", "answer": "y", "verdict": "up"})
        assert up.json()["ok"] is True
    db = get_session()
    try:
        row = db.get(AssistantFeedback, fid)  # тестовая БД живёт между прогонами — ищем свою строку
        assert row.verdict == "down"
        assert row.note == "В базе 15 сделок Orion" and row.intent == "advisor"
        assert db.scalar(sa_select(AssistantFeedback).where(AssistantFeedback.question == "x")).verdict == "up"
    finally:
        db.close()
