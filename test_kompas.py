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
    body = TestClient(main.app).get("/health").json()
    assert body["status"] == "ok" and body["ai"] is False
    # С 19 сентября 2026 в ответе есть ещё отпечаток выложенной сборки —
    # см. test_launch_features::test_health_carries_a_build_fingerprint,
    # а с 22 сентября — имя модели, на которой прод отвечает на самом деле
    # (владелец спросил, не сменить ли модель, и выяснилось, что узнать
    # текущую снаружи было нельзя).
    # Проверяем НАЛИЧИЕ нужных полей, а не равенство набора: иначе каждая
    # новая строка в /health ломает тест, который про флаг поиска. Прежняя
    # версия именно это и обещала в комментарии, а сравнивала набор целиком.
    assert {"status", "ai", "build", "model"} <= set(body)
    assert body["model"] == main.current_model()


def test_brand_font_is_served_as_a_font():
    """Шрифт фирменной карточки каталога (static/fonts/*.woff2) хостинг
    отдавал как text/plain: Python там не знал расширения .woff2 (6 октября
    2026). Тип прописан в main.py явно и не зависит от машины."""
    r = TestClient(main.app).get("/static/fonts/commissioner-latin.woff2")
    assert r.status_code == 200 and r.headers["content-type"] == "font/woff2"


@pytest.mark.parametrize("path", ["/", "/health", "/#/analytics"])
def test_head_request_is_answered_not_rejected(path):
    """Проверка живости у хостинга ходит методом HEAD, и 405 в ответ означает
    для платформы «приложение мертво»: 6 сентября 2026 контейнер из-за этого
    перезапускался по кругу, живого процесса за прокси не было, и сайт не
    открывался всю ночь. FastAPI, в отличие от «голого» Starlette, сам HEAD к
    GET-маршруту не добавляет — поэтому его надо объявлять явно, и поэтому
    здесь стоит тест, а не надежда на фреймворк."""
    r = TestClient(main.app).head(path)
    assert r.status_code == 200, (path, r.status_code)


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
    assert captured["max_tokens"] == 1000


def test_question_about_the_service_gets_a_ready_answer_without_the_model(client, monkeypatch):
    """Вопрос посетителя 7 октября 2026 (опечатки — его): модель ответила
    отказом «могу помочь только информацией о сделках…», посетитель пояснил
    «Пытаюсь понять пользу от сервиса». Теперь на такой вопрос — готовый
    короткий рассказ о сервисе, сразу и без модели, в обоих режимах и в
    быстром поиске."""
    def no_llm(*a, **k):
        raise AssertionError("модель не должна вызываться на вопрос о сервисе")
    monkeypatch.setattr(main, "call_llm", no_llm)
    monkeypatch.setattr(main, "yandex_search", no_llm)
    q = "Чем мы можете ьыть полезны для меня"
    for mode in ("base", "web"):
        body = client.post("/api/ask", json={"question": q, "context": "{}", "mode": mode}).json()
        assert body["intent"] == "about" and body["model"] is False and not body.get("refused")
        assert "сделок с 2022 года" in body["answer"] and "(#/analytics)" in body["answer"]
    quick = client.post("/api/assistant/lookup", json={"question": q, "context": ""}).json()
    assert quick["intent"] == "about" and quick["answer"] == body["answer"]


def test_about_service_does_not_catch_questions_about_deals():
    """Готовый рассказ о сервисе не должен перехватывать вопрос о рынке:
    признак требует, чтобы речь шла о «вас / сервисе / Компасе». Замер — по
    тем же 500+ вопросам из живой базы, что и у гейта политики."""
    import assistant_retrieval as ar
    import test_assistant_policy
    for q in ("Чем полезен Компас?", "Чем может быть полезен Компас?", "Чем вы можете быть полезны?", "Что ты умеешь?", "Что это за сервис?",
              "Пытаюсь понять пользу от сервиса", "Как пользоваться?", "Привет"):
        assert ar.about_service(q), q
    for q in ("Чем полезна сделка для Сбербанка?", "Что вы можете сказать о сделке Магнита?",
              "Привет, кто купил Boxberry?", "Какая польза от сделки для акционеров?",
              "Чем полезен проект Восток Ойл?", "Чем может быть полезна покупка Boxberry для Яндекса?",
              "Что может помешать сделке?"):
        assert not ar.about_service(q), q
    caught = [q for q in test_assistant_policy._live_questions() if ar.about_service(q)]
    assert not caught, caught[:5]


def test_owner_reply_keeps_bold_and_links_from_telegram_entities():
    """8 октября 2026 владелец поправил пост ответом в консоли, и пост ушёл
    без жирных подписей, а «ПРАЙМ» перестал быть ссылкой: Telegram присылает
    разметку отдельно от текста (`entities`, смещения в UTF-16), а бот брал
    только текст. Эмодзи в начале (две единицы UTF-16) не сбивает смещения."""
    text = "📌 Сделка закрыта\n\nПокупатель: «А & Б»\nИсточник: ПРАЙМ"
    def ent(sub, kind, **kw):
        off = len(text[:text.index(sub)].encode("utf-16-le")) // 2
        return dict(type=kind, offset=off, length=len(sub.encode("utf-16-le")) // 2, **kw)
    out = main._telegram_text_as_html(text, [ent("Сделка закрыта", "bold"), ent("Покупатель:", "bold"),
                                             ent("Источник:", "bold"),
                                             ent("ПРАЙМ", "text_link", url="https://1prime.ru/a?b=1&c=2")])
    assert out == ('📌 <b>Сделка закрыта</b>\n\n<b>Покупатель:</b> «А &amp; Б»\n'
                   '<b>Источник:</b> <a href="https://1prime.ru/a?b=1&amp;c=2">ПРАЙМ</a>')
    assert main._telegram_text_as_html("без разметки <", None) == "без разметки <"


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
    assert p["model"] == "gpt://f/gpt-oss-120b/latest"
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



def test_polish_joins_links_with_a_space_and_drops_orphan_addresses():
    """Владелец 5 октября 2026: «надо убрать референсы в скобках». Модель
    писала «[покупка ТРЦ] (#/deal/…)» — с пробелом между скобками, и
    читатель видел квадратные скобки и адрес вместо ссылки."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    did = "citibank"
    text = (f"• Недвижимость — [покупка ТРЦ «Триумф Молл»] (#/deal/{did})\n"
            f"• Фармацевтика — продажа сети «Апрель» (#/deal/{did})")
    out = main._polish_answer(text, idx)
    assert f"[покупка ТРЦ «Триумф Молл»](#/deal/{did})" in out
    assert "«Апрель» (#/deal/" not in out and "продажа сети «Апрель»" in out
    assert "] (" not in out


def test_polish_collapses_a_doubled_list_marker():
    """Ответ на подготовку к встрече (5 октября 2026) пришёл пунктами
    «- - **[сделка]**»: на экране перед каждой сделкой стояла лишняя
    чёрточка. Жирный текст в начале пункта маркером не считается."""
    text = "- - **[Покупка «Элемента»](#/deal/citibank)** — покупатель\n  * - вложенный\n- **Важно**: одна черта"
    import assistant_retrieval
    out = main._polish_answer(text, assistant_retrieval.get_index())
    assert out.splitlines() == ["- **[Покупка «Элемента»](#/deal/citibank)** — покупатель",
                                "  - вложенный", "- **Важно**: одна черта"]

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

    asked = []
    real_thread_id = main._console_thread_id
    monkeypatch.setattr(main, "_console_thread_id",
                        lambda db, kind: asked.append(kind) or real_thread_id(db, kind))
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
        # ТЕМА — «Заметки от пользователей», не «Общая информация». Обе
        # половины отзыва пишет ПОСЕТИТЕЛЬ о том, что у нас не так, — то же
        # самое, что уточнение с карточки сделки. В «Общей информации» они
        # тонули среди отчётов о прогонах (владелец нашёл их там 22 сентября
        # 2026). Тема ещё не заведена в тестовой базе, поэтому проверяем не
        # номер, а то, какой вид темы спрашивают.
        assert asked == ["user_notes", "user_notes"], asked
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


def test_lookup_follow_up_keeps_the_deal_from_the_previous_question():
    """Аудит, раунд 2 (6 сентября 2026): на «перепроверь» ассистент отвечал
    «в Компасе нет сделки Яндекс — Boxberry», сославшись на неё репликой
    раньше. Быстрый ответ по базе получает историю и ищет уточнение вместе
    с предыдущим вопросом."""
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app)
    history = [{"role": "user", "body": "Когда Яндекс приобрёл Boxberry?"},
               {"role": "assistant", "body": "Сделка закрыта 24 апреля 2025."}]
    r = client.post("/api/assistant/lookup", json={"question": "Перепроверь, пожалуйста", "context": "",
                                                    "context_type": "general", "context_id": None,
                                                    "history": history})
    body = r.json()
    assert body["deals"] and body["deals"][0]["id"] == "g46c6e23f", body
    assert "16 апреля 2025" in (body["answer"] or ""), body["answer"]
    alone = client.post("/api/assistant/lookup", json={"question": "Перепроверь, пожалуйста", "context": "",
                                                        "context_type": "general", "context_id": None}).json()
    assert not alone["deals"]


# ---------- сводка дня в консоль: раз в день в 18:00 с Метрикой (5 октября 2026) ----------

def _fresh_runs(db):
    from db.models import AppSetting
    for key in (main.INTAKE_RUNS_SETTING, main.INTAKE_SUMMARY_LAST):
        row = db.get(AppSetting, key)
        if row:
            db.delete(row)
    for row in db.query(AppSetting).filter(AppSetting.key.like("intake_summary:%")).all():
        db.delete(row)
    db.commit()


def test_intake_runs_are_collected_and_the_day_summary_goes_once_after_18(monkeypatch):
    """Владелец 5 октября 2026: сводку притока — «1 раз в день в 18:00» и со
    статистикой Яндекс Метрики. Прогоны копятся на сайте, сводка уходит одна."""
    from datetime import datetime, timezone
    from db.session import get_session
    import metrika
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "s3cret")
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **p: sent.append((method, p)) or {"ok": True})
    monkeypatch.setattr(main, "_review_chat_ids", lambda db=None: ["-100500"])
    monkeypatch.setattr(metrika, "day_stats", lambda day="today", token=None, client=None: {
        "users": 812, "visits": 1034, "pageviews": 3210, "avg_seconds": 135, "new_pct": 64.2,
        "sources": [("Переходы из поисковых систем", 38), ("Прямые заходы", 20)],
        "yesterday": {"users": 790, "visits": 1001}})
    db = get_session()
    try:
        _fresh_runs(db)
        with TestClient(main.app) as c:
            assert c.post("/api/ops/intake-run", json={"token": "нет", "looked": 1}).status_code == 404
            for looked, found, cards, screened in ((2816, 29, 6, 22), (2790, 3, 0, 4)):
                r = c.post("/api/ops/intake-run", json={"token": "s3cret", "looked": looked, "found": found,
                                                        "cards": cards, "screened": screened})
                assert r.json()["ok"] is True
        before = datetime(2026, 10, 6, 14, 30, tzinfo=timezone.utc)      # 17:30 МСК
        assert main._intake_summary_once(db, now_utc=before) is False and not sent
        at18 = datetime(2026, 10, 6, 15, 5, tzinfo=timezone.utc)          # 18:05 МСК
        assert main._intake_summary_once(db, now_utc=at18) is True
        assert len(sent) == 1
        text = sent[0][1]["text"]
        assert "6 октября" in text and "2 раза" in text and "Похожих на сделки — 32" in text
        assert "мусор ещё до консоли — 26" in text and "6 карточек" in text
        assert "Посетителей — 812" in text and "переходы из поисковых систем — 38%" in text
        assert "2 мин 15 с" in text and "Вчера: посетителей — 790" in text
        # Второй раз за день — нет, даже после перезапуска сайта.
        assert main._intake_summary_once(db, now_utc=at18) is False and len(sent) == 1
    finally:
        _fresh_runs(db)
        db.close()


def test_day_summary_says_so_when_intake_was_silent(monkeypatch):
    """Молчание рутины не должно выглядеть тихим днём (урок 9 августа)."""
    from datetime import datetime, timezone
    from db.session import get_session
    import metrika
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **p: sent.append((method, p)) or {"ok": True})
    monkeypatch.setattr(main, "_review_chat_ids", lambda db=None: ["-100500"])
    monkeypatch.setattr(metrika, "day_stats", lambda *a, **k: None)
    db = get_session()
    try:
        _fresh_runs(db)
        assert main._intake_summary_once(db, now_utc=datetime(2026, 10, 7, 15, 1, tzinfo=timezone.utc)) is True
        text = sent[0][1]["text"]
        assert "ни разу не отчитался" in text
        assert "подключим доступ к Метрике" in text
    finally:
        _fresh_runs(db)
        db.close()


def test_summary_asked_for_after_18_counts_as_the_days_summary(monkeypatch):
    """Сводка, отправленная по просьбе после 18:00, — это и есть сводка дня:
    вечерняя вторым сообщением не приходит. Отправленная днём — не мешает
    вечерней (в 18:00 приходит обычная)."""
    from datetime import datetime, timezone
    from db.models import AppSetting
    from db.session import get_session
    import metrika
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **p: sent.append((method, p)) or {"ok": True})
    monkeypatch.setattr(main, "_review_chat_ids", lambda db=None: ["-100500"])
    monkeypatch.setattr(metrika, "day_stats", lambda *a, **k: None)
    db = get_session()
    try:
        _fresh_runs(db)
        noon = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)            # 12:00 МСК
        assert main._intake_summary_once(db, now_utc=noon, force=True) is True
        assert db.get(AppSetting, "intake_summary:2026-10-08") is None
        evening = datetime(2026, 10, 8, 17, 30, tzinfo=timezone.utc)       # 20:30 МСК
        assert main._intake_summary_once(db, now_utc=evening) is True and len(sent) == 2
        _fresh_runs(db)
        sent.clear()
        late = datetime(2026, 10, 9, 17, 30, tzinfo=timezone.utc)
        assert main._intake_summary_once(db, now_utc=late, force=True) is True
        assert main._intake_summary_once(db, now_utc=late) is False and len(sent) == 1
    finally:
        _fresh_runs(db)
        db.close()


def test_site_settings_hold_texts_longer_than_255(monkeypatch):
    """Прогоны притока за день и готовый текст поста об этапе сделки лежат в
    `app_settings.value`. На Postgres колонка была VARCHAR(255) и такую запись
    отвергла бы, а SQLite в тестах длину не проверяет вовсе, — поэтому здесь
    проверяется сам тип колонки и то, что старт сайта расширяет старую."""
    import inspect as _inspect
    from db.models import AppSetting
    assert getattr(AppSetting.__table__.c.value.type, "length", None) is None
    assert "ALTER TABLE app_settings ALTER COLUMN value TYPE TEXT" in _inspect.getsource(main._create_account_tables)


def test_metrika_reads_totals_and_sources_without_inventing_numbers():
    import httpx
    import metrika
    assert metrika.day_stats(token="") is None
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["Authorization"] == "OAuth T"
        q = dict(request.url.params)
        if q.get("dimensions"):
            return httpx.Response(200, json={"totals": [100], "data": [
                {"dimensions": [{"name": "Переходы из социальных сетей"}], "metrics": [55]},
                {"dimensions": [{"name": "Прямые заходы"}], "metrics": [45]}]})
        if q.get("date1") == "yesterday":
            return httpx.Response(200, json={"totals": [70, 90]})
        return httpx.Response(200, json={"totals": [80, 100, 300, 61, 50.0]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        st = metrika.day_stats(token="T", client=c)
    assert len(calls) == 3 and all(dict(r.url.params)["ids"] == metrika.COUNTER for r in calls)
    assert st["users"] == 80 and st["visits"] == 100 and st["pageviews"] == 300
    assert st["sources"] == [("Переходы из социальных сетей", 55), ("Прямые заходы", 45)]
    lines = metrika.render(st)
    assert "Посетителей — 80" in lines[1] and "1 мин 1 с" in lines[2]


def test_intake_routine_hands_its_numbers_to_the_site(monkeypatch):
    import httpx
    import sys as _sys
    _sys.path.insert(0, "pipeline")
    import ops_status
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "s3cret")
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True, "runs_today": 3})

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        ok, why = ops_status.send_intake_run(2816, 29, 6, 22, client=c)
    assert ok and "3" in why
    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/api/ops/intake-run" and body["cards"] == 6 and body["token"] == "s3cret"


# ---------- проверка ассистента 14 октября 2026: ответ ----------

def test_prompts_forbid_claiming_completeness_counting_and_foreign_currency_as_rubles():
    """В 35 ответах из 100 были неверные факты, почти все — «других нет»,
    «это все», «список полон» при неполной выборке. Правило — в обоих
    режимах; «отвечай только о сделках» ослаблено до короткого объяснения
    термина; список — до десяти строк, а не шести."""
    for prompt in (main.SYSTEM_BASE, main.SYSTEM_WEB):
        for phrase in ("«других нет»", "«это все»", "«список полон»", "среди найденных сделок",
                       "Сам не считай", "обычно закрываются за год", "не переводи в рубли",
                       "объяснить термин", "нужно ли согласие ФАС"):
            assert phrase in prompt, phrase
        # Прежний совет «скажи прямо: в Компасе такой сделки нет» убран.
        assert "или «в Компасе такой сделки нет»" not in prompt
    assert "Не больше десяти строк" in main.SYSTEM_BASE and "шести" not in main.SYSTEM_BASE
    assert "«топ-N»" in main.SYSTEM_BASE


PRODUCT_QUESTIONS = {
    # Вопросы №84–87, 55, 62 проверки — дословно: все получали отказ
    # «я помогаю только со сделками».
    "Как подписаться на новые сделки в отрасли?": ("subscribe", "#/account"),
    "Сколько стоит подписка на Компас?": ("price", "бесплатн"),
    "Можно ли выгрузить список сделок в Excel?": ("export", "Выгрузить в таблицу"),
    "Чем вы отличаетесь от Cbonds и Интерфакса?": ("rivals", "сделок с 2022 года"),
    "Что такое M&A простыми словами?": ("what_is_ma", "#/deal/"),
    "Чем сделка M&A отличается от инвестиции?": ("ma_vs_investment", "#/deal/"),
    "Как следить за сделками Сбербанка?": ("subscribe", "Следить за сделками компании"),
    "Это платно?": ("price", "бесплатн"),
    # №90 третьей проверки (18 октября 2026): модель отказывала «я только о сделках».
    "Как вырастить свой бизнес через покупки?": ("grow_by_ma", "#/companies/"),
}


@pytest.mark.parametrize("question", list(PRODUCT_QUESTIONS))
def test_product_questions_get_a_ready_answer_without_the_model(client, monkeypatch, question):
    kind, must = PRODUCT_QUESTIONS[question]
    def no_llm(*a, **k):
        raise AssertionError("модель не должна вызываться на вопрос о продукте")
    monkeypatch.setattr(main, "call_llm", no_llm)
    monkeypatch.setattr(main, "yandex_search", no_llm)
    for mode in ("base", "web"):
        body = client.post("/api/ask", json={"question": question, "mode": mode}).json()
        assert body["intent"] == "about" and body["product"] == kind and body["model"] is False
        assert must in body["answer"], (question, body["answer"])
        assert not any(w in body["answer"].lower() for w in ("только со сделками", "не могу помочь"))
    quick = client.post("/api/assistant/lookup", json={"question": question}).json()
    assert quick["answer"] == body["answer"]


def test_product_answers_name_no_price_and_link_only_to_existing_deals():
    """Цены на сайте нет: пользовательское соглашение говорит «сейчас все
    функции Сервиса предоставляются бесплатно». Ответ не выдумывает тарифов,
    а примеры из базы — настоящие сделки."""
    import re as _re
    import assistant_product as ap
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    html = (main.pathlib.Path(main.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    assert "Сейчас все функции Сервиса предоставляются бесплатно" in html
    for button in ("Выгрузить в таблицу", "Следить за сделками компании", "Следить за сделками отрасли",
                   "Подписаться на обновления", "Новая подписка"):
        assert button in html, button
    for k in (ap.SUBSCRIBE, ap.EXPORT, ap.PRICE, ap.RIVALS, ap.WHAT_IS_MA, ap.MA_VS_INVESTMENT, ap.GROW_BY_MA):
        text = ap.answer(k, idx)
        assert not _re.search(r"\d[\d\s]*(?:₽|руб)\w*\s*(?:в|/)\s*мес", text), k
        for did in _re.findall(r"#/deal/([A-Za-z0-9_-]+)", text):
            assert did in idx.by_id, (k, did)
        assert ap.answer(k, None)  # без индекса — тоже ответ, просто без примеров


def test_product_answers_do_not_catch_questions_about_deals():
    """Готовый ответ о продукте не должен перехватывать вопрос о рынке: замер
    по тем же 500+ вопросам из живой базы, что и у гейта политики."""
    import assistant_product as ap
    import test_assistant_policy
    for q in ("Сколько стоила Азбука вкуса?", "Кто конкуренты Магнита?", "Когда было подписание сделки?",
              "Какая стоимость сделки CyberOK?", "Цена раскрыта или это оценка?", "Что такое earn-out?",
              "Чем отличается сделка Магнита от сделки Ленты?", "Интерфакс писал о сделке Сбербанка?",
              "Сделки с инвестициями в ИИ", "Что такое правкомиссия?"):
        assert ap.kind(q) is None, q
    caught = [q for q in test_assistant_policy._live_questions() if ap.kind(q)]
    assert not caught, caught[:5]


def test_polish_fixes_links_codes_footnotes_and_latin_letters():
    """Оформление из проверки 14 октября 2026: ссылки без «#» (№35), вложенные
    ссылки (№37), служебные коды вместо названий (№80), сноски «【…】» (№34,
    59), латинская «l» в «ленте» (№45, 46), «2 март 2026» (№35)."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    did, other = "citibank", next(d.id for d in idx.docs if d.id != "citibank")
    title = idx.by_id[other].title
    code = next(d.id for d in idx.docs if main.re.fullmatch(main._DEAL_CODE, d.id))
    text = (f"Всё в [lенте сделок](#/deals).\n"
            f"- [Ситибанк](/deal/{did}) — 2 март 2026\n"
            f"- [Сделка]('[Полное название](#/deal/{did}))\n"
            f"- ВТБ выкупил долю — [{code}](#/deal/{code})\n"
            f"- Ещё [{other}](#/deal/{other}) и [ссылка](deal/{did})\n"
            f"Оценки 【A‑Invest](https://a-invest.pro/x)», см. 【https://e.law.ru/1210219】 и 【4†L1-L3】.\n"
            f"iPhone, K2‑9b и Tинькофф.")
    out = main._polish_answer(text, idx)
    assert "[ленте сделок](#/deals)" in out and "lенте" not in out
    assert f"[Ситибанк](#/deal/{did}) — 2 марта 2026" in out
    assert f"- [Сделка](#/deal/{did})" in out and "'[" not in out
    assert f"- [ВТБ выкупил долю](#/deal/{code})" in out and f"[{code}]" not in out
    assert f"[{title}](#/deal/{other})" in out
    assert f"[ссылка](#/deal/{did})" in out and "](deal/" not in out and "](/deal/" not in out
    assert "【" not in out and "】" not in out
    assert "[A‑Invest](https://a-invest.pro/x)" in out and "[e.law.ru](https://e.law.ru/1210219)" in out
    assert "iPhone" in out and "K2‑9b" in out and "Тинькофф" in out


def test_a_cut_off_answer_is_replaced_by_the_summary(client, monkeypatch):
    """№13 проверки: «Топ-10 крупнейших сделок 2025 года» → одна строка
    «- **300 млрд ₽** –». Обрубок не показываем — показываем сводку."""
    monkeypatch.setattr(main, "call_llm", lambda s, u, max_tokens, deadline=None:
                        "**Топ-6 крупнейших сделок 2025 года:**\n\n- **300 млрд ₽** –")
    body = client.post("/api/ask", json={"question": ORION_Q}).json()
    assert body["model"] is False and "#/advisors/orion" in body["answer"]
    # Служебной фразы «Подробный ответ не уместился» посетитель не видит
    # (№66 проверки 18 октября 2026) — только короткую сводку.
    assert body["answer"].startswith("Коротко, по данным «Компаса»:") and "300 млрд" not in body["answer"]
    assert "не уместился" not in body["answer"]
    for cut in ("Вот список:", "- **300 млрд ₽** –", "сделки: **Магнит"):
        assert main._looks_cut(cut), cut
    for whole in ("Сделок три.", "- [Сделка](#/deal/x) — 5 млрд ₽", "Подробнее — на [странице](#/deals)"):
        assert not main._looks_cut(whole), whole


def test_call_llm_treats_an_incomplete_answer_with_text_as_cut_off(monkeypatch):
    """Модель начала ответ и упёрлась в потолок вывода (status=incomplete):
    это обрубок, а не ответ, и повтор упрётся в тот же потолок."""
    monkeypatch.setenv("YANDEX_API_KEY", "k")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "f")
    calls = {"n": 0}
    partial = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
               "output": [{"type": "message", "content": [{"type": "output_text", "text": "- **300 млрд ₽** –"}]}],
               "usage": {"output_tokens": 1500, "output_tokens_details": {"reasoning_tokens": 1450}}}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json=partial)

    monkeypatch.setattr(main, "_http", httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(main.LLMCutOff) as err:
        main.call_llm("sys", "user", max_tokens=1000)
    assert calls["n"] == 1 and err.value.partial == "- **300 млрд ₽** –"


# ── Проверка 18 октября 2026: страховка после модели и подготовка к встрече ──

def _doc(did, title, added="", **kw):
    from types import SimpleNamespace
    return SimpleNamespace(id=did, title=title, buyer=kw.get("buyer", ""), seller=kw.get("seller", ""),
                           target=kw.get("target", ""), asset="", raw={"added": added})


def _ret(intent="company", answer="", docs=(), pool=()):
    from types import SimpleNamespace
    return SimpleNamespace(intent=intent, answer=answer, docs=list(docs), pool=list(pool))


def _idx(docs):
    from types import SimpleNamespace
    return SimpleNamespace(by_id={d.id: d for d in docs})


# Ответ «Подготовка к встрече» по ВТБ со скриншотов партнёра (18 октября 2026).
VTB_PREP_ANSWER = """**Что важно знать о ВТБ**
- Второй по величине банк России, контролируется государством.

**Ключевые сделки (до 5 штук)**
- [ВТБ продал отель](#/deal/g1) — 2026, продавец

**Как подготовиться**
- Подготовьте документацию для правкомиссии ФАС по прошлым сделкам.
- Изучите сделки 、、、 компании.

**Что лучше не говорить**
- Не упоминайте имена юридических фирм, кроме VERBA LEGAL.
- Не делайте предположения о конкретных контрагентах, которых в данных нет (например, банки-партнёры в сделке с RVB).

Данные собраны из открытых источников и могут быть неполными."""


def test_meeting_prep_prompt_carries_no_service_notes_and_no_dont_say_section():
    """«Ключевые сделки (до 5 штук)»: пометка о количестве из задания модель
    переносила в заголовок. В задании со страницы её больше нет — сколько
    сделок, решают правила сервера, и о «чём лучше не говорить» не просим."""
    html = open(main.os.path.join(main.STATIC_DIR, "index.html"), encoding="utf-8").read()
    start = html.index("function meetingPrepQuestion(")
    body = html[start:html.index("\n}\n", start)]
    for bad in ("до 5", "до пяти", "штук", "лучше не говорить"):
        assert bad not in body, bad
    for prompt in (html[html.index("Готовлюсь к собеседованию в компанию"):][:400],
                   html[html.index("Готовлюсь к собеседованию в ${isLegal"):][:400]):
        assert "(до пяти" not in prompt
    rules = main.MEETING_PREP_RULES
    assert "до 5 штук" in rules and "без пометок в скобках" in rules  # называется как запрет
    assert "ФАС — разные органы" in rules and "выдуманных примеров" in rules
    assert "основную" in rules  # не выделять одного консультанта


def test_meeting_prep_question_gets_its_own_rules():
    import assistant_retrieval
    ret = assistant_retrieval.Retrieval("company", "Сводка.", [], "ВТБ")
    prep = main._prepare_ask("Готовлюсь к встрече с компанией «ВТБ». Коротко, по пунктам.", ret, "base", "")
    assert prep.meeting and main.MEETING_PREP_RULES in prep.system and prep.max_tokens >= 1400
    plain = main._prepare_ask("Какие сделки были у ВТБ?", ret, "base", "")
    assert not plain.meeting and main.MEETING_PREP_RULES not in plain.system


def test_polish_cleans_the_meeting_prep_answer_from_the_screenshot():
    source = "СВОДКА: ВТБ продал отель. Wildberries — ООО «РВБ». Согласование правкомиссии."
    out = main._polish_answer(VTB_PREP_ANSWER, _idx([_doc("g1", "ВТБ продал отель")]), source=source, meeting=True)
    assert "(до 5 штук)" not in out and "**Ключевые сделки**" in out
    assert "лучше не говорить" not in out and "VERBA LEGAL" not in out and "RVB" not in out
    assert "Не упоминайте" not in out and "Не делайте предположения" not in out
    assert "правкомиссии ФАС" not in out and "для правкомиссии по прошлым" in out
    assert "、" not in out and "Изучите сделки компании." in out
    assert out.endswith("Данные собраны из открытых источников и могут быть неполными.")
    assert "[ВТБ продал отель](#/deal/g1)" in out


def test_glued_approval_bodies_are_split_as_in_the_deals():
    fix = main._unglue_approval_bodies
    assert fix("Нужно согласие правкомиссии ФАС.", "одобрила ФАС") == "Нужно согласие ФАС."
    assert fix("Нужно согласие правкомиссии ФАС.", "одобрила правкомиссия") == "Нужно согласие правкомиссии."
    assert fix("Правкомиссия ФАС одобрила.", "") == "Правкомиссия и ФАС одобрила."
    assert fix("Для Правительственной комиссии при ФАС России", "") == "Для Правительственной комиссии и ФАС"
    for ok in ("Сделку одобрили ФАС и правкомиссия.", "решение комиссии ФАС", "согласие ФАС; правкомиссия — нет"):
        assert fix(ok, "") == ok


def test_service_notes_and_junk_are_removed_but_numbers_stay():
    out = main._polish_answer("**Сделки (до 5 штук)**\n**Итоги (не больше пяти)**\n**Кратко (по пунктам)**\n"
                              "Скидка (до 30%) и сделки (до 2025 года).\nА、、、Б，В。​Г", None)
    assert "(до 5 штук)" not in out and "(не больше пяти)" not in out and "(по пунктам)" not in out
    assert "**Сделки**" in out and "(до 30%)" in out and "(до 2025 года)" in out
    assert "、" not in out and "，" not in out and "。" not in out and "​" not in out


def test_completeness_claims_are_dropped_only_when_search_found_more():
    docs = [_doc(f"g{i}", f"Сделка номер {i}") for i in range(3)]
    text = ("У компании три сделки. Это все сделки в «Компасе». Других сделок нет.\n"
            "- [Сделка номер 0](#/deal/g0)\n\nИтого: 3 сделки. Сумму не раскрывали, данных о цене ещё нет.")
    part = _ret(answer="Всего 20 сделок, [список](#/companies/x).", docs=docs, pool=docs * 7)
    out = main._polish_answer(text, _idx(docs), ret=part)
    assert "Это все" not in out and "Других сделок нет" not in out and "Итого" not in out
    assert "У компании три сделки." in out and "данных о цене ещё нет" in out
    assert out.endswith("Здесь показана часть найденных сделок, полный список — [список](#/companies/x).")
    whole = _ret(answer="Всего 3 сделки.", docs=docs, pool=docs)
    assert main._polish_answer(text, _idx(docs), ret=whole) == text
    # «Ещё N — в ленте» в сводке — тоже часть списка.
    assert main._shows_part(_ret(answer="- a\nЕщё 12 — в [ленте](#/deals).", docs=docs))


def test_a_multiple_absent_from_the_deals_is_dropped():
    """№70: модель «оценила» сделку в мультипликатор, которого нет в карточках."""
    text = "Сумма — 10 млрд ₽. Это примерно 7x EBITDA. Покупатель — «Альфа»."
    assert main._polish_answer(text, None, source="цена 10 млрд ₽") == "Сумма — 10 млрд ₽. Покупатель — «Альфа»."
    kept = "Сделка прошла по 6,5x EBITDA."
    assert main._polish_answer(kept, None, source="мультипликатор 6.5x EBITDA") == kept


def test_generalizations_from_the_model_are_dropped():
    text = ("Нашлось три сделки. Как правило, такие сделки закрываются за год. "
            "Это говорит о том, что рынок растёт.\n- [А](#/deal/a)")
    assert main._polish_answer(text, _idx([_doc("a", "А")])) == "Нашлось три сделки.\n- [А](#/deal/a)"


def test_list_items_without_links_get_the_deal_link():
    """№5, 37, 39, 73, 79: список сделок без единой ссылки на карточку."""
    docs = [_doc("g1", "«Карат» купил Павловский молочный завод", buyer="Карат", target="Павловский молочный завод"),
            _doc("g2", "Альфа-Банк купил долю в «Медси»", buyer="Альфа-Банк", target="Медси"),
            _doc("g3", "Visiology привлекла 200 млн рублей", target="Visiology")]
    text = ("Среди найденных:\n- **Павловский молочный завод** — купил «Карат», 2026\n"
            "- Альфа-Банк купил долю в «Медси» — 2026\n- Visiology — 200 млн ₽\n- Покупка доли — 2026\n"
            "- Возьмите с собой список сделок\n- [Уже ссылка](#/deal/g9) — 2025")
    out = main._polish_answer(text, _idx(docs + [_doc("g9", "Уже ссылка")]), ret=_ret(docs=docs))
    assert "- **[Павловский молочный завод](#/deal/g1)** — купил «Карат», 2026" in out
    assert "- [Альфа-Банк купил долю в «Медси»](#/deal/g2) — 2026" in out
    assert "- [Visiology](#/deal/g3) — 200 млн ₽" in out
    assert "- Покупка доли — 2026" in out  # общих слов мало — ссылку не ставим
    assert "- Возьмите с собой список сделок" in out and "[Уже ссылка](#/deal/g9)" in out


def test_same_day_events_of_one_kind_collapse_into_one_line():
    """№45, 46: пять строк «Активы X переданы во временное управление»."""
    names = ["Tarkett в России", "«Каппа Рус»", "«Менсен Пакаджинг СНГ»"]
    docs = [_doc(f"g{i}", f"Активы {n} переданы во временное управление «Центр Капиталу»", "2026-10-17")
            for i, n in enumerate(names)]
    docs.append(_doc("g9", "Visiology привлекла 200 млн рублей", "2026-10-17"))
    lines = [f"- [{d.title}](#/deal/{d.id}) — 17 октября 2026" for d in docs]
    out = main._polish_answer("За неделю:\n" + "\n".join(lines), _idx(docs), ret=_ret(intent="recent", docs=docs))
    assert out.splitlines() == [
        "За неделю:",
        "- Активы переданы во временное управление «Центр Капиталу»: [Tarkett в России](#/deal/g0), "
        "[«Каппа Рус»](#/deal/g1), [«Менсен Пакаджинг СНГ»](#/deal/g2) — 17 октября 2026",
        "- [Visiology привлекла 200 млн рублей](#/deal/g9) — 17 октября 2026"]
    # Разные дни не сворачиваются.
    docs[1].raw["added"], docs[2].raw["added"] = "2026-10-16", "2026-10-15"
    out = main._polish_answer("\n".join(lines), _idx(docs), ret=_ret(intent="recent", docs=docs))
    assert len(out.splitlines()) == 4


def test_polish_leaves_an_ordinary_answer_alone():
    """Страховка не должна портить нормальный ответ."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    d = idx.docs[0]
    text = (f"Среди найденных сделок самая крупная — [{d.title}](#/deal/{d.id}).\n\n"
            f"- [{d.title}](#/deal/{d.id}) — 2025, 10 млрд ₽\n\n"
            "Сумму раскрывают не всегда: в наших данных об этом не сказано. Согласие ФАС получено.")
    ret = _ret(answer="Всего 1 сделка.", docs=[d], pool=[d])
    assert main._polish_answer(text, idx, ret=ret, source="сводка ФАС 10 млрд", meeting=True) == text



# ── Третья проверка на 100 вопросах (18 октября 2026): ответ ─────────────────

def test_own_count_of_deals_is_dropped_and_the_more_line_is_written_by_code():
    """№4: «зафиксировано 12 сделок» при 34 найденных и «ещё 2» при 22
    оставшихся. Своё число снимается вместе с фразой, «Ещё N» — по сводке."""
    docs = [_doc(f"g{i}", f"Сделка про обратный выкуп номер {i}") for i in range(12)]
    summary = ("Сделок с условием: обратный выкуп в «Компасе» — 34.\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id}) — 2024" for d in docs[:6]) + "\n…и ещё 28.")
    ret = _ret(intent="term", answer=summary, docs=docs, pool=docs)
    text = ("В Компасе зафиксировано 12 сделок, в которых предусмотрён опцион на обратный выкуп.\n\n"
            + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:10])
            + "\n\nещё 2 сделки с аналогичным условием:\n"
            + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[10:])
            + "\n\nДанные могут быть неполными.")
    source = f"СВОДКА из «Компаса» по вопросу (проверена, опирайся на неё):\n{summary}\n\nВопрос посетителя: выкуп"
    out = main._polish_answer(text, _idx(docs), ret=ret, source=source)
    assert "12 сделок" not in out and "ещё 2" not in out
    # Ленты с отбором по условию сделки нет: «Показаны 12 из 34», без ленты.
    assert "Показаны 12 из 34." in out and out.index("Показаны 12") > out.index("#/deal/g11")
    assert "](#/deals)" not in out
    assert out.count("](#/deal/") == 12 and out.endswith("Данные могут быть неполными.")


def test_more_line_counts_what_the_answer_did_not_name():
    """№66: «ещё 2 на странице» при восьми сделках и семи названных; №26: «ещё
    1 сделка», когда названы все семь. Ссылка — та же, что в сводке."""
    docs = [_doc(f"m{i}", f"Магнит купил компанию номер {i}") for i in range(8)]
    summary = ("Компания [Магнит](#/companies/mg) в «Компасе»: 8 сделок:\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:6])
               + "\n…и ещё 2 — на [странице компании](#/companies/mg).")
    ret = _ret(answer=summary, docs=docs, pool=docs)
    source = f"СВОДКА из «Компаса» по вопросу (проверена, опирайся на неё):\n{summary}\n\nВопрос посетителя: Магнит"
    seven = "\n".join(f"- [{d.title}](#/deal/{d.id}) — 2025" for d in docs[:7])
    out = main._polish_answer("«Магнит» — 8 сделок.\n\n" + seven + "\n\n*Ещё 2 сделки указаны на странице компании "
                              "[Магнит](#/companies/mg).*", _idx(docs), ret=ret, source=source)
    assert "Ещё 2" not in out and "Ещё 1 — на [странице компании](#/companies/mg)." in out
    assert out.startswith("«Магнит» — 8 сделок.")
    eight = "\n".join(f"- [{d.title}](#/deal/{d.id}) — 2025" for d in docs)
    out = main._polish_answer(eight + "\n\nНа странице компании указана ещё 1 сделка. Данные могут быть неполными.",
                              _idx(docs), ret=ret, source=source)
    assert "ещё 1" not in out.lower() and out.endswith("Данные могут быть неполными.")


def test_ratios_and_shares_counted_by_the_model_are_dropped():
    """№32: «в 10 раз больше сделок» при 14 против 2; №58: «более половины»
    при 46%. Числа из сводки, суммы, доли, даты и годы остаются."""
    source = ("СВОДКА из «Компаса» по вопросу (проверена, опирайся на неё):\nOzon — 2 сделки. РВБ — 14 сделок. "
              "Всего сделок — 1450.\n\nВопрос посетителя: сравни")
    text = ("Ozon — 2 сделки, у РВБ — 14 сделок. У РВБ в 10‑раз больше сделок. "
            "Пять отраслей охватывают более половины всех 1450 сделок. "
            "Последняя закрыта 2 марта 2026: 51 % за 10 млрд ₽, в 2025 году — ещё одна.")
    out = main._polish_answer(text, None, source=source)
    assert out == ("Ozon — 2 сделки, у РВБ — 14 сделок. "
                   "Последняя закрыта 2 марта 2026: 51 % за 10 млрд ₽, в 2025 году — ещё одна.")
    # Своё число в фразе со счётом — тоже снимается (№61: «7 в 2023 году» без «7» в сводке).
    out = main._polish_answer("Среди найденных — 2 закрытых в 2024 году и 7 в 2023 году. Сумма раскрыта.",
                              None, source=source)
    assert out == "Сумма раскрыта."
    # «Вот 3 крупнейшие сделки» — счёт своего же списка, он верен.
    listed = "Вот 3 крупнейшие сделки:\n- [А](#/deal/a)\n- [Б](#/deal/b)\n- [В](#/deal/c)"
    assert main._polish_answer(listed, _idx([_doc(x, x.upper()) for x in "abc"]), source=source) == listed


# Пункты из ответов третьей проверки, которые получили ссылку на чужую сделку
# (описание компании, советы, места работы): ни один не должен её получить.
FALSE_LINK_LINES = [
    ("- ВТБ — один из крупнейших банков‑холдингов России, владеющий широким портфелем непрофильных активов "
     "(гостиницы, недвижимость, агробизнес, страхование, транспорт).", "gc3d735fc", True),
    ("- **Подчеркнуть юридический опыт**: отметьте, что в сделке с «Авророй Инвест» банк привлекал юрфирму; "
     "предложите свои услуги.", "gb101d54d", True),
    ("- Акционеры — публичные и институциональные инвесторы; контрольный пакет держит МКПАО «Яндекс».",
     "gd73fd825", True),
    ("- Финансовый советник в сделке «Бери заряд!» — Orion (не банк, но финансовый консультант).",
     "berizaryad", True),
    ("- За 2025‑2026 годы «Самолёт» активно монетизирует активы: продаёт готовые проекты и доли.",
     "g1e37f107", True),
    ("- Крупный российский ритейлер, владеет сетью продуктовых магазинов и онлайн‑платформой — маркетплейс "
     "KazanExpress.", "g25448b74", True),
    ("- Внутри стратегических подразделений указанных выше компаний (например, в «Яндексе», VK, Сбербанке, "
     "Softline) – для формирования портфеля сделок.", "g15386e04", False),
]


def test_list_items_do_not_get_a_link_to_an_unrelated_deal():
    """Регрессия второй волны (№74, 93, 96, пять подготовок к встрече из шести):
    ссылка ставилась по двум общим словам. Теперь — только когда пункт
    называет сделку, а в подготовке к встрече — только в разделе о сделках."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    for line, did, meeting in FALSE_LINK_LINES:
        if did not in idx.by_id:
            continue
        docs = [idx.by_id[did]] + idx.docs[:20]
        head = "**Что важно знать о компании**\n" if meeting else "**Где может понадобиться директор по M&A**\n"
        out = main._link_list_items(head + line, docs, meeting=meeting)
        assert "](#/deal/" not in out, out
        # И без подготовки к встрече: пункт не называет сделку.
        assert "](#/deal/" not in main._link_list_items(line, docs), line
    # В разделе о сделках подготовки к встрече ссылка ставится как прежде.
    d = idx.by_id.get("g35357328")
    if d:
        text = f"**Что важно знать**\n- {d.title} — продавец.\n\n**Главные сделки**\n- {d.title} — 2026, продавец."
        out = main._link_list_items(text, [d], meeting=True)
        assert out.count("](#/deal/") == 1 and out.splitlines()[-1].startswith(f"- [{d.title}](#/deal/")


def test_list_links_on_all_answers_of_the_third_check():
    """Все ответы проверки 18 октября 2026: из пунктов списка убираем ссылки и
    ставим заново. Ссылка не должна вести на другую сделку, чем у модели, и в
    подготовке к встрече не должна появляться вне раздела о сделках."""
    import json as _json
    import re as _re
    import assistant_retrieval
    path = main.pathlib.Path(main.__file__).parent / "data" / "inbox" / "assistant_eval" / "answers_2026-10-18_0650.jsonl"
    if not path.exists():
        pytest.skip("ответов проверки нет (data/inbox не в git)")
    idx = assistant_retrieval.get_index()
    rows = [_json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()][1:]
    wrong, outside, checked = [], [], 0
    false_lines = [line[2:40] for line, _, _ in FALSE_LINK_LINES]
    for r in rows:
        answer = r.get("answer") or ""
        if not answer or r.get("model") is False:
            continue
        q = main._CONTEXT_PREFIX_RE.sub("", r["question"]).strip()
        ret = assistant_retrieval.retrieve(q, r.get("context_type"), r.get("context_id"), idx)
        meeting = main._is_meeting_prep(q)
        lines, orig = [], {}
        for i, line in enumerate(answer.split("\n")):
            if main._is_list_line(line):
                orig[i] = _re.findall(r"\(#/deal/([^)\s]+)\)", line)
                line = _re.sub(r"\[([^\]]+)\]\(#/deal/[^)\s]+\)", r"\1", line)
            lines.append(line)
        out = main._link_list_items("\n".join(lines), main._candidate_docs(ret), meeting=meeting).split("\n")
        section_ok = not meeting
        for i, line in enumerate(out):
            if line.strip() and not main._is_list_line(line) and main._looks_like_heading(line):
                section_ok = not meeting or bool(main._DEALS_HEADING.search(line))
            ids = _re.findall(r"\(#/deal/([^)\s]+)\)", line) if i in orig else []
            if not ids:
                continue
            checked += 1
            if orig[i] and ids[0] not in orig[i]:
                wrong.append((r["n"], line[:120]))
            if not section_ok:
                outside.append((r["n"], line[:120]))
            if any(f in line for f in false_lines):
                wrong.append((r["n"], line[:120]))
    assert checked > 100 and not wrong and not outside, (wrong[:5], outside[:5])


def test_meeting_prep_gets_the_company_profile_and_strict_rules():
    """Подготовка к встрече выдумывала о компании («WB Банк — дочка ВТБ»,
    владельцы Яндекса, «порог ФАС 10%»): модель получает профиль из базы, где
    сказано и то, чего в нём нет, а правила запрещают общие знания."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    if "gcafc31dc" not in idx.companies:
        pytest.skip("ВТБ нет в базе")
    q = "Готовлюсь к встрече с компанией «ВТБ». Коротко, по пунктам."
    ret = assistant_retrieval.retrieve(q, "company", "gcafc31dc", idx)
    prep = main._prepare_ask(q, ret, "base", "", "company", "gcafc31dc", idx)
    assert "ПРОФИЛЬ КОМПАНИИ" in prep.user_msg and "Название: ВТБ" in prep.user_msg
    assert "Собственники:" in prep.user_msg and "Дочерние компании" in prep.user_msg or "Компании группы" in prep.user_msg
    if "gcafc31dc" in main._bank_finance():
        assert "Отчётность в Банке России" in prep.user_msg and "трлн ₽" in prep.user_msg
    plain = main._prepare_ask("Какие сделки были у ВТБ?", ret, "base", "", "company", "gcafc31dc", idx)
    assert "ПРОФИЛЬ КОМПАНИИ" not in plain.user_msg
    rules = main.MEETING_PREP_RULES
    for must in ("ПРОФИЛЬ КОМПАНИИ", "не делает её дочерней", "порог", "не называй консультантов",
                 "юрфирму не называй финансовым консультантом", "кириллицу не переводи в латиницу"):
        assert must in rules, must
    assert "сервер допишет сам" in main.COMPLETENESS_RULES


def test_meeting_advice_does_not_rest_on_one_consultant():
    """Партнёр: совет «предложите себя как альтернативу VERBA LEGAL». Пункт
    совета с именем консультанта снимается; в разделе о сделках и о том, с кем
    работала компания, имена остаются; сама компания-банк — не консультант."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    text = ("**Что важно знать о Сбербанке**\n- Сбербанк — крупнейший банк. В сделках часто привлекал VERBA LEGAL.\n"
            "- Сбербанк покупал и продавал активы.\n\n"
            "**Главные сделки**\n- Продажа отеля — юрфирма VERBA LEGAL на стороне продавца.\n\n"
            "**С кем работала компания**\n- VERBA LEGAL, Orion.\n\n"
            "**Как подготовиться**\n- **Подчеркните опыт** — предложите себя как альтернативу VERBA LEGAL.\n"
            "- Изучите сделки Сбербанка за 2025 год.\nОпирайтесь на участие Orion. Возьмите презентацию.")
    out = main._polish_answer(text, idx, meeting=True)
    assert "крупнейший банк" not in out and "часто привлекал" not in out  # пункт с фирмой — целиком
    assert "юрфирма VERBA LEGAL на стороне продавца" in out and "- VERBA LEGAL, Orion." in out
    assert "альтернативу" not in out and "Подчеркните опыт" not in out and "участие Orion" not in out
    assert "- Изучите сделки Сбербанка за 2025 год." in out and "Возьмите презентацию." in out
    assert "- Сбербанк покупал и продавал активы." in out  # банк-сторона — не консультант


def test_how_to_use_kompas_is_answered_about_the_service(client, monkeypatch):
    """№88: «Как пользоваться Компасом?» — отказ модели вместо рассказа о сервисе."""
    def no_llm(*a, **k):
        raise AssertionError("модель не должна вызываться")
    monkeypatch.setattr(main, "call_llm", no_llm)
    for q in ("Как пользоваться Компасом?", "как пользоваться сервисом", "Как работать с ассистентом?"):
        body = client.post("/api/ask", json={"question": q, "mode": "base"}).json()
        assert body["intent"] == "about" and "#/deals" in body["answer"], (q, body)
    assert main._ready_reply("Как пользоваться правом обратного выкупа?") is None


def test_grow_by_acquisitions_is_answered_with_buyers_from_the_base():
    """№90: «Как вырастить свой бизнес через покупки?» — не отказ, а примеры
    покупателей из базы со ссылками; вопрос о названной компании идёт к её сделкам."""
    import re as _re
    import assistant_policy
    import assistant_product as ap
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    q = "Как вырастить свой бизнес через покупки?"
    assert not assistant_policy.classify(q).refused and ap.kind(q) == ap.GROW_BY_MA
    for other in ("Как Яндекс растёт через покупки?", "Какие компании активнее всего растут через покупки?",
                  "Как рос рынок сделок в 2025 году?"):
        assert ap.kind(other) is None, other
    text = ap.answer(ap.GROW_BY_MA, idx)
    companies = _re.findall(r"#/companies/([^)\s]+)", text)
    assert len(companies) >= 3 and all(c in idx.companies for c in companies)
    assert all(d in idx.by_id for d in _re.findall(r"#/deal/([^)\s]+)", text))
    assert "только" not in text.split("\n")[0] or "сделк" not in text.split("\n")[0]


def test_theme_links_are_built_the_way_the_site_builds_them():
    """№25: модель собрала «#/theme/Венчур%20/раунд», а сайт режет адрес по «/»
    (route() → h.split("/")) — тема открывалась пустой. Имя сверяется с темами
    базы и кодируется, как encodeURIComponent; неизвестная тема — без ссылки."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    themes = {t for d in idx.docs for t in d.themes}
    if "Венчур / раунд" not in themes:
        pytest.skip("темы «Венчур / раунд» нет в базе")
    out = main._fix_section_links("См. [все по теме](#/theme/Венчур%20/раунд) и [тему](#/theme/Венчур / раунд). "
                                  "[Отрасль](#/industry/ИТ%20и%20интернет), [нет такой](#/theme/Космос).", idx)
    assert out == ("См. [все по теме](#/theme/Венчур %2F раунд) и [тему](#/theme/Венчур %2F раунд). "
                   "[Отрасль](#/industry/ИТ и интернет), нет такой.")
    # Сводка без модели (быстрый ответ, запасной ответ) — тоже.
    ret = assistant_retrieval.Retrieval("theme", "…и ещё 2 — [все по теме](#/theme/Венчур / раунд).", [], None)
    assert "(#/theme/Венчур %2F раунд)" in main._summary_text(ret, idx)
    html = (main.pathlib.Path(main.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    assert 'filterTheme = arg?decodeURIComponent(arg):"Все"' in html


def test_raw_codes_firm_links_bold_and_double_brackets_are_fixed():
    """№65: «в сделке «…» [gc44de028]» и «**[АЛРУД](#/deal/…)**»; №18:
    «**IPO девелопера GloraX (ПАО «Глоракс**)»; №59: «[[название](#/deal/…)]»."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    d = next(x for x in idx.docs if x.id.startswith("g") and len(x.id) == 9 and "«" not in x.title)
    firm = next(f for f in idx.firms if f.id == "alrud") if any(f.id == "alrud" for f in idx.firms) else None
    text = f"- **[{firm.name if firm else 'АЛРУД'}](#/deal/{d.id})** – продавец в сделке «{d.title}» [{d.id}] и в сделке [ g0000000f]."
    out = main._polish_answer(text, idx)
    assert f"[{d.title}](#/deal/{d.id})" in out and f"[{d.id}]" not in out and "g0000000f" not in out
    if firm:
        assert f"**[{firm.name}](#/advisors/{firm.id})**" in out
    out = main._polish_answer("- **IPO девелопера GloraX (ПАО «Глоракс**) – 31 октября 2025.\n"
                              "- **IPO «ВсеИнструменты.ру** – 5 июля 2024.\n- **Обычный «жирный»** — ок.", None)
    assert out.splitlines() == ["- **IPO девелопера GloraX (ПАО «Глоракс»)** – 31 октября 2025.",
                                "- **IPO «ВсеИнструменты.ру»** – 5 июля 2024.", "- **Обычный «жирный»** — ок."]
    out = main._polish_answer(f"Пример: [[{d.title}](#/deal/{d.id})], "
                              "[[https://pravo.ru/opinion/1/](https://pravo.ru/opinion/1/)].", idx)
    assert out == f"Пример: [{d.title}](#/deal/{d.id}), [pravo.ru](https://pravo.ru/opinion/1/)."


# ── Четвёртая проверка на 100 вопросах (18 октября 2026): ответ ──────────────

def _summary_source(summary, question="вопрос"):
    return f"СВОДКА из «Компаса» по вопросу (проверена, опирайся на неё):\n{summary}\n\nВопрос посетителя: {question}"


def test_own_counts_in_bold_after_the_noun_and_in_words_are_dropped():
    """№1: «ещё **40 сделок**» в жирном; №36: «закрытых покупок — 7 штук»;
    №3: «прошла только одна» при семи найденных; №14: «во всех остальных
    мультипликаторы не раскрывались»; №58: «большую часть активности»."""
    docs = [_doc(f"g{i}", f"Сделка в отрасли номер {i}") for i in range(12)]
    summary = ("В отрасли [ИТ](#/industry/ИТ) 46 сделок.\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:6])
               + "\n…и ещё 40 — на [странице отрасли](#/industry/ИТ).")
    ret = _ret(intent="industry", answer=summary, docs=docs, pool=docs)
    listed = "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs)
    text = (f"В отрасли — **46 сделок**:\n\n{listed}\n\nЭто часть списка — по сводке ещё **40 сделок** на странице. "
            "По нашим данным, закрытых покупок — 7 штук. Через правкомиссию прошла только одна. "
            "Во всех остальных сделках мультипликаторы не раскрывались. Эти отрасли формируют большую часть "
            "активности. Данные могут быть неполными.")
    out = main._polish_answer(text, _idx(docs), ret=ret, source=_summary_source(summary))
    for gone in ("**40 сделок**", "7 штук", "только одна", "остальных", "большую часть"):
        assert gone not in out, gone
    assert out.count("Ещё 34 — на [странице отрасли](#/industry/ИТ).") == 1
    assert out.startswith("В отрасли — **46 сделок**:") and out.endswith("Данные могут быть неполными.")
    # Счёт своего же списка над ним остаётся: «В «Компасе» есть две сделки, где…:» (№12).
    two = "В «Компасе» есть две сделки с таким условием:\n\n" + "\n".join(
        f"- [{d.title}](#/deal/{d.id})" for d in docs[:2])
    assert main._polish_answer(two, _idx(docs), source=_summary_source("Сделок с условием — 4.")) == two
    # А «остальные — ниже» в рейтинге — правда, её не трогаем.
    assert main._COMPLETE_CLAIM.search("у остальных сделок суммы либо не раскрыты, либо ниже") is None


def test_sentences_are_not_cut_inside_names_quotes_and_brackets():
    """№3: «По остальным 6 сделкам (Henkel, Yum! Brands‑KFC…)» резалось по «Yum!» —
    от фразы оставался обрывок «Brands‑KFC, FM Logistic…»."""
    assert main._sentences("По остальным сделкам (Henkel, Yum! Brands‑KFC, FM Logistic) данных нет. Сумма раскрыта.") \
        == ["По остальным сделкам (Henkel, Yum! Brands‑KFC, FM Logistic) данных нет.", "Сумма раскрыта."]
    assert main._sentences("Yum! Brands продала KFC. Сделка закрыта.") == ["Yum! Brands продала KFC.", "Сделка закрыта."]
    assert len(main._sentences("Сервис «Бери заряд! Плюс» куплен. Это всё.")) == 2
    out = main._drop_generalizations("Как правило, Yum! Brands и «Бери заряд!» Яндекса покупают дорого. Сумма раскрыта.")
    assert out == "Сумма раскрыта."


def test_a_list_item_is_not_left_as_a_bare_link():
    """№66: от пункта о выкупе акций «Магнита» осталась голая «[Подробнее]».
    Пункт со ссылкой на сделку счёт не трогает; пункт из одной «[Подробнее]» —
    название сделки; от снятой фразы не остаётся одна ссылка."""
    d = _doc("geb946158", "«Магнит» выкупил свои акции у иностранных инвесторов с дисконтом")
    src = _summary_source("Сделок у компании — 8.")
    item = f"- **Выкуп своих акций** — 2 сделки по 50 % дисконту. [Подробнее](#/deal/{d.id})"
    assert main._polish_answer(item, _idx([d]), source=src) == item
    assert main._polish_answer(f"- [Подробнее](#/deal/{d.id})", _idx([d])) == f"- [{d.title}](#/deal/{d.id})"
    assert main._polish_answer(f"Как правило, такое бывает. [Подробнее](#/deal/{d.id})\n\nСумма раскрыта.",
                               _idx([d])) == "Сумма раскрыта."
    assert main._polish_answer(f"Пример — указ [link](#/deal/{d.id}).", _idx([d])) == \
        f"Пример — указ [подробнее](#/deal/{d.id})."


def test_empty_links_become_text_or_a_deal_link():
    """№95: «[сумма известна]()» и «[сумма известна]([berizaryad])»."""
    d = _doc("berizaryad", "«Яндекс» приобрёл 100 % сервиса «Бери заряд!»")
    out = main._polish_answer("- Т‑Технологии купила Авто.ру — [сумма известна]().\n"
                              "- «Бери заряд!» — [сумма известна]([berizaryad]).\n- Pruffme — [сумма не раскрыта]( ).",
                              _idx([d]))
    assert out.splitlines() == ["- Т‑Технологии купила Авто.ру — сумма известна.",
                                "- «Бери заряд!» — [сумма известна](#/deal/berizaryad).",
                                "- Pruffme — сумма не раскрыта."]
    assert main._polish_answer("[Сделки](#/deals) и [РБК](https://rbc.ru/x)", None) == "[Сделки](#/deals) и [РБК](https://rbc.ru/x)"


def test_more_line_goes_after_the_right_list_and_always_with_a_link():
    """№5: «Ещё 7» АЛРУД — под списком ЕПАМ; №72: посреди нумерованного
    списка; P1: в разделе о консультантах; №4: «Ещё 22.» без ссылки; №100:
    «Здесь показана часть найденных сделок» в ответе без сделок."""
    a = [_doc(f"a{i}", f"Сделка фирмы А номер {i}") for i in range(4)]
    b = [_doc(f"b{i}", f"Сделка фирмы Б номер {i}") for i in range(4)]
    summary = ("**[А](#/advisors/a)** — 11 сделок:\n" + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in a)
               + "\n…и ещё 7 — на [странице фирмы](#/advisors/a).\n**[Б](#/advisors/b)** — 4 сделки:\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in b))
    ret = _ret(intent="advisor", answer=summary, docs=a + b, pool=a + b)
    assert main._summary_more(ret) is None
    text = ("**А**:\n" + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in a) + "\n\n**Б**:\n"
            + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in b))
    assert "Ещё" not in main._polish_answer(text, _idx(a + b), ret=ret, source=_summary_source(summary))
    # Нумерованный список с продолжениями пунктов — строка после всего списка.
    docs = [_doc(f"r{i}", f"Росатом сделка номер {i}") for i in range(10)]
    summary = ("Компания [Росатом](#/companies/rosatom): 10 сделок:\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:6])
               + "\n…и ещё 4 — на [странице компании](#/companies/rosatom).")
    ret = _ret(answer=summary, docs=docs, pool=docs)
    text = (f"1. **Продажа доли.**\n   – Источник: [{docs[0].title}](#/deal/{docs[0].id}).\n\n"
            "2. **Покупка активов.**\n   – Источник: [РБК](https://rbc.ru/1).\n\n3. **СП.**\n   – Сумма не раскрыта.\n\n"
            "Вывод: сделки идут.")
    out = main._polish_answer(text, _idx(docs), ret=ret, source=_summary_source(summary))
    assert out.index("Ещё 9 — на [странице компании](#/companies/rosatom).") > out.index("3. **СП.**")
    assert out.index("Ещё 9") < out.index("Вывод")
    # Подготовка к встрече: не в разделе о консультантах.
    text = ("**Главные сделки**\n" + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:3])
            + f"\n\n**Юридические консультанты**\n- VERBA LEGAL — [{docs[3].title}](#/deal/{docs[3].id})\n\n"
            "**Как подготовиться**\n- Возьмите презентацию.")
    out = main._polish_answer(text, _idx(docs), ret=ret, source=_summary_source(summary), meeting=True)
    assert out.index("Ещё 6 — на") < out.index("**Юридические консультанты**")
    # Сводка без ссылки — строка всё равно говорит, где искать.
    summary = "Сделок с условием — 34.\n" + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:6]) + "\n…и ещё 28."
    ret = _ret(intent="term", answer=summary, docs=docs, pool=docs)
    out = main._polish_answer("\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:2]), _idx(docs), ret=ret,
                              source=_summary_source(summary))
    # Названы две из 34: ещё пять найденных ссылками и «Показаны 7 из 34».
    assert "Ещё из найденных:" in out and out.count("](#/deal/") == 7
    assert "Показаны 7 из 34. Остальные покажу, если уточните вопрос" in out and "](#/deals)" not in out
    # Ответ без сделок (прогноз рынка) — без пометки о части найденных сделок.
    out = main._polish_answer("Прогноз — рост. Это все данные, что есть.", _idx(docs), ret=ret,
                              source=_summary_source(summary))
    assert "часть найденных" not in out and "Ещё" not in out


def test_meeting_profile_names_the_one_legal_entity_and_rules_forbid_it_as_scale():
    """«Магнит» — «выручка ≈ 412 млн ₽», «Самолёт» — 15 млрд ₽: отчётность
    одного юрлица подавалась как масштаб сети."""
    from types import SimpleNamespace
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    cid = next((k for k, c in idx.companies.items() if c.get("name") == "Магнит"), None)
    if cid is None or cid in main._bank_finance():
        pytest.skip("Магнита нет в базе")
    entity = SimpleNamespace(id=1, legal_name="ПАО «Магнит»", inn="2309085638")
    # Операционное юрлицо (прибыль меньше выручки) — цифры с подписью.
    report = SimpleNamespace(revenue_rub=15.1e9, net_profit_rub=1.6e9, year=2025)
    answers = iter([entity, report])
    db = SimpleNamespace(scalar=lambda *_: next(answers))
    text = main._company_profile_text(cid, idx, db)
    assert "ОДНОГО юрлица — ПАО «Магнит», ИНН 2309085638 — за 2025 год: выручка 15,1 млрд ₽" in text
    assert "чистая прибыль 1,6 млрд ₽" in text and "не масштаб всей компании" in text
    assert "цифры ОДНОГО юрлица, а не масштаб компании" in main.MEETING_PREP_RULES


def test_latin_names_are_written_as_in_the_base():
    """P3: «Netology‑группу»; №66: «Andrey Gorodissky и партнёры». Если и в
    базе имя латиницей (Melling, Voitishkin & Partners), оно остаётся."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    src = _summary_source("Сбер приобрел Нетологию и Фоксфорд. Консультант — Андрей Городисский и партнеры. "
                          "Юрфирма Melling, Voitishkin & Partners.")
    out = main._polish_answer("Сбербанк купил Netology‑группу; консультант — Andrey Gorodissky и партнёры; "
                              "юрист — Melling, Voitishkin & Partners. Источник: Compass, Interfax.",
                              idx, source=src)
    if not any(c.get("name") == "Нетология-групп" for c in idx.companies.values()):
        pytest.skip("Нетологии нет в базе")
    assert "Нетология‑группу" in out and "Netology" not in out
    assert "Андрей Городисский и партнёры" in out
    assert "Melling, Voitishkin & Partners" in out and "Compass, Interfax" in out


def test_decree_is_not_said_to_be_approved_by_the_commission():
    """№59: «указ подписан после согласования с комиссией» — в карточке этого
    нет; временное управление по указу — не решение правкомиссии."""
    d = _doc("g8a599c40", "Активы Tarkett в России переданы во временное управление «Центр Капиталу»")
    e = _doc("g1", "Покупка завода")
    cards = json.dumps(
        [{"id": d.id, "title": d.title, "terms": "указ президента; документы лежали в правкомиссии без одобрения"},
         {"id": e.id, "title": e.title, "terms": "сделку одобрила правкомиссия"}], ensure_ascii=False)
    src = f"СВОДКА из «Компаса»:\nтема\n\n{main._CARDS_MARK}\n{cards}\n\nВопрос посетителя: правкомиссия"
    text = (f"- Активы Tarkett переданы во временное управление — указ подписан после согласования с комиссией "
            f"[подробнее](#/deal/{d.id}).\n- Завод куплен, сделку одобрила правкомиссия [подробнее](#/deal/{e.id}).\n\n"
            "Временное управление вводится после согласования с правкомиссией. Сумма не раскрыта.")
    out = main._polish_answer(text, _idx([d, e]), source=src)
    assert "Tarkett" not in out and "вводится после" not in out
    assert "сделку одобрила правкомиссия" in out and out.endswith("Сумма не раскрыта.")
    assert "временное управление по указу президента — не решение правкомиссии" in main.COMPLETENESS_RULES.lower()


def test_web_mode_puts_kompas_first_and_does_not_deny_what_the_search_found():
    """№72: закрытая в «Компасе» покупка «Дела» подана как будущая по июльской
    новости; №78: найденная статья Forbes о смене гендиректора отвергнута."""
    web = main.SYSTEM_WEB
    assert "«КОМПАС» ГЛАВНЕЕ, СЕТЬ ДОПОЛНЯЕТ, А НЕ ОПРОВЕРГАЕТ" in web
    assert "сделка закрыта: не называй её готовящейся или новой" in web
    assert "Не пиши «в открытых источниках подтверждения нет»" in web


def test_polish_on_all_answers_of_the_fourth_check():
    """Все ответы проверки 18 октября 2026, 08:21: чистка не оставляет
    голых ссылок, пустых «[…]()», обрывков с лишней «)», второй строки
    «Ещё N» и строки «Ещё N» без ссылки, и повторная чистка ничего не
    меняет (полный разбор «до/после» — в отчёте проверки)."""
    import json as _json
    import re as _re
    import assistant_retrieval
    path = main.pathlib.Path(main.__file__).parent / "data" / "inbox" / "assistant_eval" / "answers_2026-10-18_0821.jsonl"
    if not path.exists():
        pytest.skip("ответов проверки нет (data/inbox не в git)")
    idx = assistant_retrieval.get_index()
    rows = [_json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()][1:]
    problems, checked = [], 0
    for r in rows:
        answer = r.get("answer") or ""
        if not answer or r.get("model") is False:
            continue
        q = main._CONTEXT_PREFIX_RE.sub("", r["question"]).strip()
        ret = assistant_retrieval.retrieve(q, r.get("context_type"), r.get("context_id"), idx)
        prep = main._prepare_ask(q, ret, "base", "", r.get("context_type"), r.get("context_id"), idx)
        out = main._polish_answer(answer, idx, ret=ret, source=prep.user_msg, meeting=prep.meeting)
        checked += 1
        if main._polish_answer(out, idx, ret=ret, source=prep.user_msg, meeting=prep.meeting) != out:
            problems.append((r["n"], "повторная чистка меняет ответ"))
        for line in out.split("\n"):
            body = _re.sub(r"^\s*(?:[-•*]|\d+[.)])\s+", "", line)
            if main._is_list_line(line) and main._only_links_left(body):
                problems.append((r["n"], "голая ссылка: " + line[:80]))
            if "]()" in line:
                problems.append((r["n"], "пустая ссылка"))
            depth = 0
            for ch in main._LINK_SPAN.sub(" ", line):
                depth += (ch == "(") - (ch == ")")
                if depth < 0:
                    problems.append((r["n"], "обрывок: " + line[:80]))
                    break
        mores = _re.findall(r"(?m)^Ещё \d+.*$", out)
        if any(x.startswith("Показаны") for x in out.split("\n")):
            mores.append("Показаны …](#/")      # строка «Показаны N из M» — вместо «Ещё N»
        if len(mores) > 1 or any("](#/" not in m for m in mores):
            problems.append((r["n"], mores))
        if r["n"] in (1, 61):
            assert len(mores) == 1 and not _re.search(r"ещё \*\*\d", out), out
        if r["n"] == 3:
            assert "только одна" not in out and "Brands‑KFC, FM" not in out
        if r["n"] == 95:
            assert "]()" not in answer or out.count("](#/deal/") >= 8
    assert checked > 80 and not problems, problems[:5]


def test_fifth_check_leftovers_link_only_item_and_other_deals_claim():
    """Пятая проверка (18 октября 2026): №59 — от пункта осталась одна ссылка
    «[Активы Tarkett…]»; №14 — «другие сделки либо не раскрывали EV/EBITDA»."""
    out = main._filter_sentences("- [Активы Tarkett…](#/deal/x). Указ согласован с комиссией.\n- Сумма раскрыта.",
                                 lambda x: "Указ" in x, lists_too=True)
    assert out == "- Сумма раскрыта."
    assert main._COMPLETE_CLAIM.search("Другие сделки в списке либо не раскрывали EV/EBITDA, либо приводили их к выручке")
    # Пункт, который и был одной ссылкой с названием сделки, — не трогаем.
    assert main._filter_sentences("- [Сделка](#/deal/x)", lambda x: False, lists_too=True) == "- [Сделка](#/deal/x)"


# ── Пятая проверка на 100 вопросах (18 октября 2026): пятая волна ───────────

def _closed_doc(did, title, date, status="Закрыта", **kw):
    d = _doc(did, title, **kw)
    d.status, d.date = status, date
    return d


def test_web_mode_status_of_a_closed_deal_beats_an_old_news_item():
    """№72: закрытая 7 октября покупка «Дела» подана как «переговоры
    продолжаются» по новости от 3 сентября. Статус и дата «Компаса» идут
    модели отдельным блоком; фраза о закрытой сделке как о готовящейся —
    заменяется статусом, датированная старая новость получает пометку, фраза
    о нескольких сделках — пометку по закрытой."""
    delo = _closed_doc("g5eb6ff22", "«Росатом» завершил выкуп у Сергея Шишкарева 51% в группе компаний «Дело»",
                       "2026-10-07", target="Группа компаний «Дело»")
    old = _closed_doc("cdfe91cd0", "«Росатом» увеличивает долю в ГК «Дело» до 49%, реализовав опцион", "2022-08-09",
                      target="Группа компаний «Дело»")
    akk = _closed_doc("g2f22b1dc", "Росатом рассматривает продажу до 49% в проекте АЭС «Аккую» внешним инвесторам",
                      "2026-08-07", status="Обсуждается")
    toys = _closed_doc("gbdd4f990", "Hobby World приобрел контроль в производителе игрушек «Звезда»", "2024-10-23",
                       target="Звезда")
    ret = _ret(intent="company", docs=[delo, old, akk, toys])
    block = main._kompas_status_block(ret)
    assert "«Росатом» завершил выкуп у Сергея Шишкарева 51% в группе компаний «Дело» — закрыта, 7 октября 2026" in block
    text = ("Росатом в данный момент готовит:\n\n"
            "* переговоры о выкупе 51 % в группе компаний «Дело» продолжаются (в свежих новостях 3 сентября 2026 г. "
            "сообщается о несостоявшемся завершении).\n"
            "- Интерфакс сообщает, что 3 сентября 2026 г. «Росатом» не смог завершить выкуп доли Шишкарева в «Дело» – "
            "[источник](https://www.interfax.ru/russia/1112881).\n\n"
            "Таким образом, Росатом готовит продажу части проекта «Аккую» и продолжает переговоры о выкупе доли "
            "в группе «Дело».\n\n"
            "Продажа судоверфи «Звезда» отменена – сделка не состоялась.")
    out = main._web_guard(text, "Какие сделки сейчас готовит Росатом?", ret, [])
    assert "переговоры о выкупе 51 % в группе компаний «Дело» продолжаются" not in out
    assert ("* По данным «Компаса», сделка закрыта 7 октября 2026: [«Росатом» завершил выкуп у Сергея Шишкарева 51% "
            "в группе компаний «Дело»](#/deal/g5eb6ff22).") in out
    assert "(позже, 7 октября 2026, по данным «Компаса», сделка закрыта)" in out
    assert "«Аккую» и продолжает переговоры о выкупе доли в группе «Дело» (по данным «Компаса», сделка по «Дело» " \
           "закрыта 7 октября 2026)." in out
    # Судоверфь «Звезда» — не игрушки «Звезда»: одно имя ещё не та сделка.
    assert out.endswith("Продажа судоверфи «Звезда» отменена – сделка не состоялась.")
    assert main._web_guard(out, "Какие сделки сейчас готовит Росатом?", ret, []) == out
    # Новость новее карточки — не трогаем.
    newer = "- 12 октября 2026 года стороны сообщили, что переговоры о выкупе доли в «Дело» продолжаются."
    assert main._web_guard(newer, "Росатом", ret, []) == newer


def test_web_mode_does_not_deny_a_found_article():
    """№78: «в найденных открытых источниках я не нашёл примеров», а в выдаче
    — Forbes «В «Лемана ПРО» сменился гендиректор после…». Фраза об
    отсутствии в сети снимается, на её место — найденные статьи; фраза о
    «Компасе» остаётся."""
    from yandex_search import SearchResult
    results = [SearchResult("В «Лемана ПРО» сменился гендиректор после передачи активов | Forbes.ru",
                            "https://www.forbes.ru/biznes/569062", ""),
               SearchResult("Смена директора в ООО в 2026: пошаговая инструкция", "https://kurs.alfabank.ru/a", "")]
    text = ("Среди сделок «Компаса» данных о смене генерального директора нет.\n\n"
            "По результатам свежего поиска обнаружены лишь общие материалы о порядке смены директора в ООО.\n\n"
            "Таким образом, в найденных открытых источниках я не нашёл примеров компаний, где после сделки "
            "сменился гендиректор. Уточните запрос.")
    q = "В каких компаниях после сделки сменился гендиректор?"
    out = main._web_guard(text, q, _ret(), results)
    assert "лишь общие материалы" not in out and "я не нашёл" not in out
    assert "В открытых источниках по вопросу нашлось:\n- [В «Лемана ПРО» сменился гендиректор" in out
    assert "alfabank" not in out
    assert out.startswith("Среди сделок «Компаса» данных о смене генерального директора нет.")
    assert out.endswith("Уточните запрос.")
    # Выдача не о том — отказ модели остаётся как есть.
    assert main._web_guard(text, q, _ret(), results[1:]) == text


def test_own_valuation_from_an_invented_margin_is_dropped():
    """№64: «при типичной марже EBITDA ≈ 10 % … стоимость ≈ 4‑5 × 50 млн ₽ =
    200‑250 млн ₽». Маржа, которой нет в данных, формула и цена, которой нет
    в данных, снимаются; мультипликатор из сделок и сумма сделки остаются."""
    src = _summary_source("Юнифрост купил Меридиан: EV/EBITDA 4–5x. Росспиртпром продан за 8,3 млрд ₽. "
                          "Сделка оценивается в 1,2–1,5 млрд ₽.",
                          "Сколько может стоить пищевое производство с выручкой 500 млн рублей?")
    text = ("В наших данных такие сделки шли по EV/EBITDA ≈ 4‑5 ×. При типичной марже EBITDA ≈ 10 % от выручки "
            "EBITDA будет около 50 млн ₽, а стоимость компании ≈ 4‑5 × 50 млн ₽ = 200‑250 млн ₽.\n\n"
            "Бизнес оценивается примерно в 300 млн ₽. Другая сделка оценивается в 1,2‑1,5 млрд ₽.\n\n"
            "- [Росспиртпром продан](#/deal/g1) — 8,3 млрд ₽.\n\n"
            "Точная оценка требует анализа отчётности.")
    out = main._polish_answer(text, _idx([_doc("g1", "Росспиртпром продан")]), source=src)
    assert "марж" not in out and "200‑250" not in out and "300 млн" not in out
    assert "EV/EBITDA ≈ 4‑5 ×" in out and "оценивается в 1,2‑1,5 млрд ₽" in out and "8,3 млрд ₽" in out
    assert out.endswith("Точная оценка требует анализа отчётности.")
    # Маржа из самой сделки — остаётся; «сценарий» — не «цена».
    src2 = _summary_source("Маржа EBITDA компании — 18%. Объём рынка $22–26 млрд.")
    keep = "Маржа EBITDA компании — 18 %. Базовый сценарий: объём рынка $22‑26 млрд."
    assert main._polish_answer(keep, None, source=src2) == keep


def test_compare_more_line_is_per_side_and_under_its_list():
    """№32: модель написала у Wildberries «(ещё 9 сделок, в том числе …)» при
    14 сделках и четырёх названных. «Ещё N» — у каждой стороны своё, по
    сводке, под её списком; число модели в пункте со ссылкой снимается."""
    from types import SimpleNamespace
    oz = [_doc("o1", "Сбер может получить долю в Ozon"), _doc("o2", "Восток продала акции Ozon")]
    wb = [_doc(f"w{i}", f"Wildberries купила актив номер {i}") for i in range(14)]
    summary = ("Ozon и ООО «РВБ» — рядом:\n**[Ozon](#/companies/oz)** — 2 сделки (предмет сделки — 2).\n"
               "**[ООО «РВБ» (Wildberries & Russ)](#/companies/wb)** — 14 сделок (покупатель — 13).\n"
               "Сделок у ООО «РВБ» больше: 14 против 2 — в 7 раз.")
    ret = _ret(intent="compare", answer=summary, docs=oz + wb[:4], pool=[])
    idx = SimpleNamespace(by_id={d.id: d for d in oz + wb}, company_deals={"oz": oz, "wb": wb}, firm_deals={})
    text = ("**Ozon**\n" + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in oz) + "\n\n**Wildberries**\n"
            + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in wb[:3])
            + f"\n- (ещё 9 сделок, в том числе обсуждение покупки Росгосстраха) — [{wb[3].title}](#/deal/w3).\n\n"
            "Таким образом, у Wildberries сделок больше.")
    out = main._polish_answer(text, idx, ret=ret, source=_summary_source(summary))
    assert "ещё 9" not in out and "- (обсуждение покупки Росгосстраха)" in out
    line = "ООО «РВБ» (Wildberries & Russ): ещё 10 сделок — на [странице компании](#/companies/wb)."
    assert out.count(line) == 1 and out.index("#/deal/w3") < out.index(line) < out.index("Таким образом")
    assert "Ozon: ещё" not in out                      # названы обе сделки Ozon
    assert main._polish_answer(out, idx, ret=ret, source=_summary_source(summary)) == out
    # Сделки обеих сторон в одном списке — одна строка после списка.
    mixed = f"- [{oz[0].title}](#/deal/o1)\n- [{wb[0].title}](#/deal/w0)\n\nВывод."
    out = main._polish_answer(mixed, idx, ret=ret, source=_summary_source(summary))
    assert ("Ozon: ещё 1 сделка — на [странице компании](#/companies/oz); ООО «РВБ» (Wildberries & Russ): ещё 13 "
            "сделок — на [странице компании](#/companies/wb).") in out
    assert out.index("#/deal/w0") < out.index("Ozon: ещё 1") < out.index("Вывод.")


def test_meeting_profile_gives_no_single_entity_figures_for_groups_and_holdings():
    """P4 (Яндекс: выручка 88 млрд ₽ при прибыли 826 млрд ₽ под словом
    «Масштаб») и №96 («Магнит»: прибыль «5,4 млн ₽» вместо 5,4 млрд): у
    группы и у головного юрлица, чья прибыль больше выручки, цифр одного
    юрлица модель не получает; «Масштаб — у юрлица …» переподписывается."""
    from types import SimpleNamespace
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    assert main._rub_text(5354640000.0) == "5,4 млрд ₽" and main._rub_text(412062000.0) == "412 млн ₽"
    entity = SimpleNamespace(id=1, legal_name="ПАО «Магнит»", inn="2309085638")
    magnit = next((k for k, c in idx.companies.items() if c.get("name") == "Магнит"), None)
    if magnit and magnit not in main._bank_finance():
        answers = iter([entity, SimpleNamespace(revenue_rub=412062000.0, net_profit_rub=5354640000.0, year=2025)])
        text = main._company_profile_text(magnit, idx, SimpleNamespace(scalar=lambda *_: next(answers)))
        assert "412 млн" not in text and "5,4 млрд" not in text
        assert "Цифр выручки и прибыли не называй" in text
    group = next((k for k, c in idx.companies.items() if c.get("group") and k not in main._bank_finance()), None)
    if group:
        def boom(*_):
            raise AssertionError("у группы отчётность одного юрлица не запрашивается")
        text = main._company_profile_text(group, idx, SimpleNamespace(scalar=boom))
        assert "Масштаб (выручка и прибыль всей компании или группы): в наших данных не указан" in text
    line = ("- **Масштаб** — у юрлица МКПАО «Яндекс», ИНН 3900019850 (по отчётности ФНС за 2025 г.) — "
            "выручка 88 млрд ₽.")
    out = main._relabel_entity_scale(line)
    assert out.startswith("- Отчётность одного юрлица (не всей компании): у юрлица МКПАО «Яндекс»")
    assert main._relabel_entity_scale("- **Масштаб**: крупнейший банк страны.") == "- **Масштаб**: крупнейший банк страны."


def test_condition_and_region_lists_do_not_promise_a_feed_without_that_filter():
    """№4, 14, 60, 69: «общий список — в ленте сделок», а в ленте нет отбора
    по условию сделки и региону. Ссылка на ленту — только с тем же отбором
    (статус, годы, отрасль, тема); иначе — ещё несколько найденных сделок
    ссылками и «Показаны N из M»."""
    import assistant_retrieval as ar
    idx = ar.get_index()
    region = ar.retrieve("Какие сделки были в Татарстане?", None, None, idx)
    assert region.intent == "filter" and "#/deals" not in (region.answer or "")
    failed = ar.retrieve("Какие сделки не состоялись в 2025 году?", None, None, idx)
    if "…и ещё" in (failed.answer or ""):
        assert "[ленте сделок](#/deals?status=Не состоялась&year=2025)" in failed.answer
    intent = ar.Intent("filter", span=(2024, None), status="closed")
    link = ar.feed_link(intent)
    assert link.startswith("#/deals?status=Закрыта&year=2024,2025") and ar.feed_link(
        ar.Intent("filter", region="Татарстан")) is None
    # Модельная «полный список — в ленте сделок» при отборе, которого лента не умеет, снимается…
    docs = [_doc(f"t{i}", f"Сделка в Татарстане номер {i}") for i in range(12)]
    summary = ("В базе «Компаса» 34 сделки с упоминанием региона «Татарстан».\n"
               + "\n".join(f"- [{d.title}](#/deal/{d.id})" for d in docs[:6]) + "\n…и ещё 28.")
    ret = _ret(intent="filter", answer=summary, docs=docs, pool=docs)
    text = ("- [Сделка в Татарстане номер 0](#/deal/t0)\n\nПолный список доступен в [ленте сделок](#/deals). "
            "Данные могут быть неполными.")
    out = main._polish_answer(text, _idx(docs), ret=ret, source=_summary_source(summary))
    assert "](#/deals)" not in out and "Данные могут быть неполными." in out
    assert "Показаны 6 из 34." in out and out.count("](#/deal/") == 6
    assert main._polish_answer(out, _idx(docs), ret=ret, source=_summary_source(summary)) == out
    # …а при отборе, который лента умеет, голая лента становится лентой с отбором.
    summary2 = summary.replace("…и ещё 28.", "…и ещё 28 — в [ленте сделок](#/deals?status=Закрыта&year=2025).")
    ret2 = _ret(intent="filter", answer=summary2, docs=docs, pool=docs)
    out = main._polish_answer(text, _idx(docs), ret=ret2, source=_summary_source(summary2))
    assert "Полный список доступен в [ленте сделок](#/deals?status=Закрыта&year=2025)." in out


def test_sentence_is_not_cut_after_the_year_abbreviation():
    """№72: «7 апреля 2026 г. ФАС согласовала сделку…» резалось после «г.»."""
    assert main._sentences("7 апреля 2026 г. ФАС согласовала сделку. Сумма не раскрыта.") == [
        "7 апреля 2026 г. ФАС согласовала сделку.", "Сумма не раскрыта."]


def test_polish_on_all_saved_answers_of_all_checks():
    """Все сохранённые ответы проверок (data/inbox/assistant_eval/*.jsonl):
    чистка идемпотентна, не оставляет голых ссылок и второй строки «Ещё N»
    (сравнение — по одной на сторону), не обещает голую ленту там, где
    сводка её не давала, и не меняет ответы, которых пятая волна не касается."""
    import json as _json
    import re as _re
    import assistant_retrieval
    folder = main.pathlib.Path(main.__file__).parent / "data" / "inbox" / "assistant_eval"
    files = sorted(folder.glob("answers_*.jsonl")) if folder.exists() else []
    if not files:
        pytest.skip("ответов проверок нет (data/inbox не в git)")
    idx = assistant_retrieval.get_index()
    problems, checked = [], 0
    for path in files:
        for r in [_json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()][1:]:
            answer = r.get("answer") or ""
            if not answer or r.get("model") is False:
                continue
            q = main._CONTEXT_PREFIX_RE.sub("", r["question"]).strip()
            ret = assistant_retrieval.retrieve(q, r.get("context_type"), r.get("context_id"), idx)
            prep = main._prepare_ask(q, ret, "base", "", r.get("context_type"), r.get("context_id"), idx)
            out = main._polish_answer(answer, idx, ret=ret, source=prep.user_msg, meeting=prep.meeting)
            checked += 1
            if main._polish_answer(out, idx, ret=ret, source=prep.user_msg, meeting=prep.meeting) != out:
                problems.append((path.name, r["n"], "повторная чистка меняет ответ"))
            mores = _re.findall(r"(?m)^(?:Ещё \d+|Показаны \d+ из \d+).*$", out)
            if len(mores) > 1:
                problems.append((path.name, r["n"], mores))
            if _shows_part_without_feed(ret) and _re.search(r"(?:полн\w+ список|остальн\w*)[^\n]*\]\(#/deals\)", out):
                problems.append((path.name, r["n"], "обещана голая лента"))
            if r["n"] == 64 and _re.search(r"марж\w*[^.\n]*\d+\s*%", out):
                problems.append((path.name, r["n"], "маржа модели"))
    assert checked > 200 and not problems, problems[:5]


def _shows_part_without_feed(ret):
    import re as _re
    return main._shows_part(ret) and not _re.search(r"\]\(#/deals[)?]", ret.answer or "")


# --- Признаки будущих сделок: маршрут ассистента (19 октября 2026) ----------

_SIGNAL_ROWS = [
    {"id": "t1", "company_id": "gcafc31dc", "object_id": None, "date": "2026-09-11", "kind": "sell",
     "summary": "ВТБ — возможная продажа: Росгосстрах", "source": ["Известия", "https://iz.ru/test"],
     "origin": "news", "strength": "strong"},
    {"id": "t2", "company_id": "g63ba8735", "date": "2025-07-29", "kind": "sell",
     "summary": "Агрохолдинг «Степь» — обсуждается сделка «Тест»", "source": ["Коммерсантъ", "https://kommersant.ru/t"],
     "origin": "card"},
]


@pytest.mark.parametrize("q", [
    "Будут ли у ВТБ сделки?", "Кто сейчас продаёт агроактивы?", "У кого возможна M&A-активность в ритейле?",
    "Планирует ли Яндекс новые покупки?", "Кто готовится к IPO?", "Кто ищет инвестора?",
    "Какие компании могут продать бизнес в этом году?", "Есть ли признаки сделок у Магнита?",
])
def test_signal_questions_are_recognised(q):
    import assistant_signals
    assert assistant_signals.is_signal_question(q), q


@pytest.mark.parametrize("q", [
    "Кто купил Азбуку вкуса?", "Кто выставил на торги Рижский вокзал?", "Какие сделки обсуждаются в ритейле?",
    "Какие сделки были у ВТБ в 2025 году?", "Кто продал Ситибанк?", "Будет ли одобрена сделка Ленты и Марии-Ра?",
    "Готовлюсь к встрече с компанией «ВТБ». Будут ли у неё сделки?",
])
def test_ordinary_questions_do_not_take_the_signal_route(q):
    import assistant_signals
    assert not assistant_signals.is_signal_question(q), q


def test_the_hundred_question_set_keeps_its_routes():
    """Набор из ста вопросов писался до маршрута признаков — ни один из них
    не должен в него уйти; группа «signals» — вся уходит."""
    import sys as _sys
    _sys.path.insert(0, "pipeline/assistant_eval")
    import questions
    import assistant_signals
    assert not [q["n"] for q in questions.QUESTIONS if assistant_signals.is_signal_question(q["question"])]
    assert 6 <= len(questions.SIGNALS) <= 8
    assert all(assistant_signals.is_signal_question(q["question"]) for q in questions.SIGNALS)


def test_signal_answer_has_three_blocks_with_dates_and_links():
    import assistant_retrieval
    import assistant_signals
    from datetime import date as _date
    idx = assistant_retrieval.get_index()
    ret = assistant_signals.answer("Будут ли у ВТБ сделки?", idx=idx, rows=_SIGNAL_ROWS, today=_date(2026, 10, 19))
    assert ret.intent == "signals" and ret.company_id == "gcafc31dc"
    text = ret.answer
    assert text.index("**Признаки**") < text.index("**Что это может значить**") < text.index("**Кто подходит**")
    assert "- 11 сентября 2026 — ВТБ — возможная продажа: Росгосстрах ([Известия](https://iz.ru/test))" in text
    assert "есть основания ожидать продажи актива или доли" in text and "не прогноз" in text
    meaning = text.split("**Что это может значить**", 1)[1].split("**Кто подходит**", 1)[0]
    assert "%" not in meaning and "вероятн" not in text.lower()
    # «Кто подходит» — только из базы, ссылками на компании и сделки
    tail = text.split("**Кто подходит**", 1)[1]
    assert "](#/companies/" in tail and "](#/deal/" in tail
    for m in __import__("re").finditer(r"\(#/deal/([^)]+)\)", text):
        assert m.group(1) in idx.by_id, m.group(1)


def test_signal_answer_says_plainly_when_there_are_none():
    import assistant_retrieval
    import assistant_signals
    idx = assistant_retrieval.get_index()
    ret = assistant_signals.answer("Будут ли у этой компании сделки?", "company", "gda7d982b", idx=idx, rows=[])
    assert "Явных признаков будущих сделок у [Softline](#/companies/gda7d982b) в наших данных нет" in ret.answer
    assert "**Кто подходит**" not in ret.answer
    ret = assistant_signals.answer("Будут ли у компании «Ромашка-Ультра» сделки?", idx=idx, rows=_SIGNAL_ROWS)
    assert "не нашёл" in ret.answer and "ВТБ" not in ret.answer, "чужие признаки — не ответ о неизвестной компании"


def test_signal_market_answer_filters_by_industry_and_kind():
    import assistant_retrieval
    import assistant_signals
    idx = assistant_retrieval.get_index()
    ret = assistant_signals.answer("Кто сейчас продаёт агроактивы?", idx=idx, rows=_SIGNAL_ROWS)
    assert ret.subject == "Агро"
    assert "Агрохолдинг «Степь»" in ret.answer and "Росгосстрах" not in ret.answer
    assert "Недавно покупали в отрасли «Агро»" in ret.answer


def test_signal_route_goes_first_in_retrieve_and_uses_the_page():
    import assistant_retrieval
    ret = assistant_retrieval.retrieve("Будут ли у этой компании сделки? Разбери признаки.", "company", "gcafc31dc")
    assert ret.intent == "signals" and ret.subject == "ВТБ"


def test_signal_prompt_rules_and_forecast_cleanup():
    """Модель получает SIGNAL_RULES и профиль компании; после модели фраза с
    вероятностью, «скорее всего» или процентом, которого нет в сводке,
    снимается, а «это не прогноз» и доля из сводки остаются."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    ret = assistant_retrieval.retrieve("Будут ли у ВТБ сделки?", None, None, idx)
    prep = main._prepare_ask("Будут ли у ВТБ сделки?", ret, "base", "", None, None, idx)
    assert main.SIGNAL_RULES in prep.system and "ПРОФИЛЬ КОМПАНИИ" in prep.user_msg
    assert "никаких процентов, вероятностей" in prep.system.lower()
    assert "процентов, вероятностей" in main.COMPLETENESS_RULES
    out = main._polish_answer(
        "**Что это может значить**\n- Есть основания ожидать продажи. Вероятность сделки — 70%.\n"
        "- Скорее всего, покупателем станет РВБ.\n- Продаётся 51% актива.\n"
        "- Это не прогноз: заявление не всегда заканчивается сделкой.",
        idx, ret=ret, source="СВОДКА: продажа 51% актива")
    assert "70%" not in out and "Скорее всего" not in out
    assert "Есть основания ожидать продажи." in out and "51%" in out and "не прогноз" in out
    # точная сводка сама проходит чистку без правок
    assert main._polish_answer(ret.answer, idx, ret=ret, source=prep.user_msg).strip() == ret.answer.strip()


def test_finance_question_about_the_base_gets_what_is_really_there():
    """Партнёр, 21 октября 2026: «В базе есть информация о EBIT компаний?» —
    ассистент ответил «не найдено», «А какие финансовые метрики есть в базе?» —
    «финансовых показателей нет». Профиль компании показывает отчётность ФНС,
    «Аналитика» — мультипликаторы. Вопрос о названной компании идёт обычным путём."""
    import assistant_product as ap
    for q in ("В базе есть информация о EBIT компаний?", "А какие финансовые метрики есть в базе?",
              "Какие данные о прибыли есть в Компасе?"):
        assert ap.kind(q) == ap.FINANCE, q
    for q in ("Какая выручка у Магнита?", "EBIT Яндекса за 2024", "Какая выручка у вас в базе у Магнита?"):
        assert ap.kind(q) is None, q
    text = ap.answer(ap.FINANCE)
    assert "прибыль от продаж" in text and "EBIT" in text and "#/analytics" in text


def test_finance_question_about_a_company_sends_its_fns_report_to_the_model():
    """21 октября 2026, 20 вопросов о финансах: «Какая выручка у Озона?» —
    «не указана», «Прибыль от продаж у Positive Technologies» — отказ, хотя
    отчётность ФНС лежит в профиле. Вопрос о деньгах компании получает её
    отчётность и правила; «Ренессанс Кредит» не подменяется «Ренессанс Капиталом»."""
    from types import SimpleNamespace
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    ozon = main._finance_company_ids("Какая выручка у Озона?", None, idx)
    if not ozon:
        pytest.skip("Озона нет в базе")
    assert main._finance_company_ids("Какие активы у банка Ренессанс Кредит?", None, idx) == []
    assert len(main._finance_company_ids("Сравни выручку X5 и Магнита", None, idx)) == 2
    entity = SimpleNamespace(id=1, legal_name="ООО «Интернет Решения»", inn="7704217370")
    report = SimpleNamespace(year=2024, revenue_rub=615e9, gross_profit_rub=None, operating_profit_rub=-12e9,
                             profit_before_tax_rub=None, net_profit_rub=-40e9, assets_rub=None, equity_rub=None,
                             borrowings_rub=None, raw_lines_json=None)
    db = SimpleNamespace(scalar=lambda *_: entity, scalars=lambda *_: SimpleNamespace(all=lambda: [report]))
    text = main._company_finance_text(ozon[0], idx, db)
    assert "ООО «Интернет Решения»" in text and "2024 год: выручка 615 млрд ₽" in text
    assert "прибыль от продаж (ближайший к EBIT показатель) -12 млрд ₽" in text
    assert "#/companies/%s" % ozon[0] in text
    assert "EBITDA в «Компасе» нет" in main.FINANCE_RULES


def test_revenue_screen_question_gets_the_feed_filter_link():
    hint = main._revenue_screen_hint("Покажи компании с выручкой больше 10 млрд, которые продали в 2025 году")
    assert "#/deals?rev=1e10&year=2025" in hint
    assert "#/deals?rev=5e10" in main._revenue_screen_hint("сделки с выручкой от 70 млрд")
    assert main._revenue_screen_hint("Какая выручка у Озона?") == ""
    assert "не делай вывода, чья компания больше" in main.FINANCE_RULES


def test_deal_multiple_of_a_bought_company_reaches_the_model(monkeypatch):
    """«За сколько выручек купили Азбуку вкуса?» — мультипликатор сделки в базе
    посчитан, а ассистент отвечал «посчитать невозможно» (21 октября 2026)."""
    import assistant_retrieval
    idx = assistant_retrieval.get_index()
    monkeypatch.setattr(main, "_sector_multiples", lambda db=None: {
        "metrics": [{"key": "ev_op", "label": "EV / операционная прибыль"}, {"key": "ps", "label": "P/S"}],
        "rows": [{"id": "g91ec3558", "title": "«Магнит» купил контрольный пакет «Азбуки вкуса»", "year": 2025,
                  "target_id": "g52fa4c83", "price_full_rub": 36.36e9, "stake": 81.55, "report_year": 2024,
                  "metrics": {"ev_op": {"value": 4.64}, "ps": {"value": 0.36}}}]})
    text = main._company_deal_multiples_text("g52fa4c83", idx)
    assert "EV / операционная прибыль 4,64" in text and "P/S 0,36" in text and "#/deal/g91ec3558" in text
    assert main._DEAL_MULTIPLE_Q.search("За сколько выручек купили Азбуку вкуса?")
    assert "последняя закрытая сделка" in main.SYSTEM_BASE
