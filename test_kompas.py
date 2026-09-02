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


# ---------- стенд сравнения моделей и честные повторы (2 сентября 2026) ----------
# Партнёр: «40 секунд ту мач». Причины были в call_llm: повтор после таймаута
# (ещё столько же), повтор после ответа без текста (тот же потолок токенов) и
# дедлайн 70 с при 45 с ожидания в браузере. Стенд /api/assistant/bench
# нужен, чтобы выбирать модель и усилие рассуждения по замеру, а не на глаз.

RESPONSES_WITH_USAGE = dict(RESPONSES_OK, status="completed",
                            usage={"output_tokens": 57, "output_tokens_details": {"reasoning_tokens": 7}})


def test_call_llm_passes_model_and_reasoning_effort(monkeypatch):
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    payloads = []

    def handler(request):
        payloads.append(json.loads(request.content))
        return httpx.Response(200, json=RESPONSES_WITH_USAGE)

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
    stats = {}
    text = main.call_llm("sys", "user", max_tokens=700, model="yandexgpt/latest",
                         reasoning_effort="low", stats=stats)
    assert text == "Ответ ассистента"
    assert payloads[-1]["model"] == "gpt://f/yandexgpt/latest"
    assert payloads[-1]["reasoning"] == {"effort": "low"}
    assert stats["attempts"] == 1 and stats["status"] == "completed"
    assert stats["reasoning_tokens"] == 7 and stats["output_tokens"] == 57
    # Пустое усилие — параметр не передаётся вовсе (поведение до 2 сентября).
    main.call_llm("sys", "user", max_tokens=700, reasoning_effort="")
    assert "reasoning" not in payloads[-1]
    assert payloads[-1]["model"] == "gpt://f/" + main.current_model()


def test_call_llm_does_not_retry_a_timeout_or_an_exhausted_budget(monkeypatch):
    """Повтор после таймаута ждёт столько же ещё раз; повтор после ответа без
    текста (модель всё потратила на рассуждение) упрётся в тот же потолок.
    Оба случая — один заход, не три."""
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    calls = {"n": 0}

    def slow(request):
        calls["n"] += 1
        raise httpx.ReadTimeout("read timed out", request=request)

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(slow)))
    with pytest.raises(RuntimeError):
        main.call_llm("sys", "user", max_tokens=700)
    assert calls["n"] == 1

    calls["n"] = 0
    exhausted = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                 "output": [{"type": "reasoning", "content": [{"type": "reasoning_text", "text": "думаю..."}]}],
                 "usage": {"output_tokens": 1500, "output_tokens_details": {"reasoning_tokens": 1500}}}

    def truncated(request):
        calls["n"] += 1
        return httpx.Response(200, json=exhausted)

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(truncated)))
    stats = {}
    with pytest.raises(RuntimeError) as err:
        main.call_llm("sys", "user", max_tokens=700, stats=stats)
    assert calls["n"] == 1
    assert "бюджет" in str(err.value) and stats["reasoning_tokens"] == 1500

    # А быстрый сбой (5xx) по-прежнему повторяется.
    calls["n"] = 0

    def boom(request):
        calls["n"] += 1
        return httpx.Response(500, text="boom")

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(boom)))
    with pytest.raises(RuntimeError):
        main.call_llm("sys", "user", max_tokens=700)
    assert calls["n"] == 1 + main.LLM_RETRIES


def test_server_deadlines_fit_inside_what_the_browser_waits():
    """Браузер ждёт 45 с по базе и 75 с по интернету (aiAnswer в index.html);
    сервер обязан обещать меньше — иначе он дописывает ответ тому, кто уже ушёл."""
    import re
    html = open("static/index.html", encoding="utf-8").read()
    m = re.search(r'mode==="web"\s*\?\s*(\d+)\s*:\s*(\d+)\)', html)
    assert m, "в index.html не найден таймер обрыва запроса к /api/ask"
    web_ms, base_ms = int(m.group(1)), int(m.group(2))
    assert main.LLM_DEADLINE + 5 <= base_ms / 1000
    assert main.LLM_DEADLINE_WEB + 5 <= web_ms / 1000
    assert main.LLM_MIN_ATTEMPT < main.LLM_TIMEOUT <= main.LLM_DEADLINE


def test_bench_requires_the_moderation_token(monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "secret")
    r = TestClient(main.app).post("/api/assistant/bench", json={"token": "wrong", "question": "q"})
    assert r.status_code == 404


def test_bench_without_keys_explains_itself(monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "secret")
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)
    r = TestClient(main.app).post("/api/assistant/bench", json={"token": "secret", "question": ORION_Q})
    assert r.status_code == 503
    assert "YANDEX_API_KEY" in r.json()["error"]


def test_bench_measures_each_model_on_the_same_prompt(client, monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "secret")
    monkeypatch.setenv("YANDEX_MODEL", "deepseek-v4-flash/latest")
    seen = []

    def fake_llm(system, user, max_tokens, deadline=None, model=None, reasoning_effort=None, stats=None):
        seen.append((model, user, reasoning_effort))
        if stats is not None:
            stats.update(attempts=1, status="completed", output_tokens=50, reasoning_tokens=10)
        if model == "broken/latest":
            raise RuntimeError("Responses API HTTP 404: model not found")
        time.sleep(0.05)
        return f"Ответ модели {model}"

    monkeypatch.setattr(main, "call_llm", fake_llm)
    r = client.post("/api/assistant/bench", json={
        "token": "secret", "question": ORION_Q, "models": ["current", "broken/latest"],
        "repeats": 2, "reasoning_effort": "low"})
    assert r.status_code == 200
    body = r.json()
    rows = body["results"]
    assert [x["model"] for x in rows] == ["deepseek-v4-flash/latest"] * 2 + ["broken/latest"] * 2
    ok = [x for x in rows if x["ok"]]
    bad = [x for x in rows if not x["ok"]]
    assert len(ok) == 2 and len(bad) == 2
    assert all(x["seconds"] >= 0.05 and x["chars"] > 0 and x["reasoning_tokens"] == 10 for x in ok)
    assert "404" in bad[0]["error"] and bad[0]["seconds"] is not None
    # Всем моделям — один и тот же промпт, тот же, что у /api/ask (сводка + карточки).
    assert len({u for _, u, _ in seen}) == 1
    assert "СВОДКА" in seen[0][1] and "Orion" in seen[0][1]
    assert all(e == "low" for _, _, e in seen)
    assert body["mode"] == "base" and body["prompt_chars"] == len(seen[0][1])
    assert body["deadline_seconds"] == main.LLM_DEADLINE
    # Без full_answer — только заголовок ответа (240 знаков); с ним — весь
    # текст, чтобы стенд годился для сравнения качества, а не только скорости.
    assert all("answer" not in x for x in rows)
    r2 = client.post("/api/assistant/bench", json={
        "token": "secret", "question": ORION_Q, "models": ["current"], "full_answer": True})
    assert r2.status_code == 200
    row = r2.json()["results"][0]
    assert row["answer"] == "Ответ модели deepseek-v4-flash/latest" and row["answer_head"] == row["answer"][:240]
