"""Инварианты притока: фильтр, сопоставление и формат телеграм-поста.

Приток — единственная часть системы, которая работает без человека, поэтому её
правила должны быть измеримы и закреплены. Сети тестам не нужно: фильтр и
сопоставление меряются на 1333 заголовках собственной базы, формат поста —
чистая функция, а забор проверяется на фикстуре.

Запуск: python3 -m pytest test_ingest.py -q
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
sys.path.insert(0, str(ROOT / "pipeline" / "publish"))

import classify              # noqa: E402
import format_post           # noqa: E402
import match as matcher      # noqa: E402


@pytest.fixture(scope="module")
def base():
    return json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))


# ---------- фильтр «сделка или нет» ----------

def test_filter_recognises_own_deals(base):
    """Полнота: заголовки настоящих сделок фильтр обязан узнавать.

    Замер прогона 46 — 95,3%. Порог 90% оставлен с запасом: правило будут
    менять, и падение ниже означает, что приток начал терять сделки.
    """
    titles = [str(d.get("title") or "") for d in base["deals"]]
    found = sum(1 for t in titles if classify.looks_like_deal(t))
    share = found / len(titles)
    assert share >= 0.90, f"фильтр узнаёт только {share:.1%} заголовков базы"


def test_filter_rejects_neighbouring_topics():
    """Точность: котировки, отчётность, назначения и суды — не сделки.

    Список живёт в самом фильтре: он написан руками именно из тех тем, на
    которых правило легко ошибается («акции подорожали после новости о
    покупке» содержит слово «покупка», но сделкой не является).
    """
    passed = [t for t in classify.NOT_DEALS if classify.looks_like_deal(t)]
    assert not passed, f"не-сделки прошли фильтр: {passed[:3]}"


def test_filter_is_not_a_keyword_match():
    """Проверка на себе: одно наличие слова «покупка» ничего не решает."""
    assert classify.looks_like_deal("«Лента» купила сеть магазинов «Монетка»")
    assert not classify.looks_like_deal(
        "Акции «Ленты» подорожали на 5% после покупки сети «Монетка»")


# ---------- сопоставление «новое или уже есть» ----------

def test_match_finds_the_same_deal(base):
    """Заголовок карточки обязан находить сам себя, иначе правило слепое."""
    idx = matcher.index_base(base["deals"])
    deal = next(d for d in base["deals"] if len(matcher.stems(d.get("title"))) >= 4)
    found, why = matcher.match(
        {"title": deal["title"], "date": deal["date"], "url": None}, idx)
    assert found == deal["id"], f"{deal['id']} не нашёл сам себя ({why})"


def test_match_does_not_glue_unrelated_news(base):
    """Чужая новость не должна прилипать к карточке базы."""
    idx = matcher.index_base(base["deals"])
    found, _ = matcher.match(
        {"title": "Правительство утвердило новую стратегию развития электротранспорта",
         "date": "2026-07-28", "url": None}, idx)
    assert found is None, f"постороннюю новость приняли за сделку {found}"


def test_match_keeps_a_long_deal_in_one_card():
    """Переговоры и закрытие через девять месяцев — этапы одной карточки."""
    idx = matcher.index_base([{
        "id": "long-stage", "date": "2026-01-10",
        "title": "«Альфа» ведёт переговоры о покупке «Беты»",
        "status": "Обсуждается", "src": [],
    }])
    found, why = matcher.match({
        "title": "«Альфа» получила согласие на приобретение «Беты»",
        "date": "2026-10-12", "url": None,
    }, idx)
    assert found == "long-stage" and "этап" in why


def test_match_does_not_merge_a_changed_bidder():
    """Тот же продавец и актив, но другой покупатель — другая сделка."""
    idx = matcher.index_base([{
        "id": "first-bidder", "date": "2026-01-10",
        "title": "Банк «Траст» продаёт «Точку» банку «Тинькофф»",
        "status": "Обсуждается", "src": [],
    }])
    found, _ = matcher.match({
        "title": "Банк «Траст» продал «Точку» компании «Интеррос»",
        "date": "2026-09-12", "url": None,
    }, idx)
    assert found is None


def test_match_does_not_extend_one_name_forever():
    idx = matcher.index_base([{
        "id": "old-alpha", "date": "2024-01-10",
        "title": "«Альфа» купила логистический актив",
        "status": "Закрыта", "src": [],
    }])
    found, _ = matcher.match({
        "title": "«Альфа» купила другой банк", "date": "2026-01-20", "url": None,
    }, idx)
    assert found is None


def test_match_uses_the_source_url(base):
    """Тот же адрес источника — самый сильный признак повтора."""
    deal = next(d for d in base["deals"]
                if d.get("src") and len(d["src"][0]) > 1 and str(d["src"][0][1]).startswith("http"))
    idx = matcher.index_base(base["deals"])
    found, why = matcher.match(
        {"title": "совершенно другой заголовок", "date": "2020-01-01",
         "url": deal["src"][0][1]}, idx)
    assert found == deal["id"] and "адрес" in why


# ---------- формат телеграм-поста ----------

def test_post_has_no_placeholder_lines(base):
    """В посте не должно быть строк «не раскрыта» и «Не привлекался».

    То же правило, что на экране: пустое поле честнее строки-заглушки, а в
    телеграме она ещё и занимает место, за которое читатель платит вниманием.
    """
    comps = base["companies"]
    for deal in base["deals"][:200]:
        text = format_post.render(deal, comps)
        low = text.lower()
        for stub in ("не раскры", "не привлекал", "публично не сообщал", "н/д"):
            assert stub not in low, f"{deal['id']}: заглушка в посте — {stub}"


def test_post_links_to_the_card_and_the_source(base):
    comps = base["companies"]
    deal = next(d for d in base["deals"]
                if d.get("src") and len(d["src"][0]) > 1 and str(d["src"][0][1]).startswith("http"))
    text = format_post.render(deal, comps)
    assert f"/#/deal/{deal['id']}" in text
    assert deal["src"][0][1] in text


def test_update_notifies_only_when_a_fact_is_added(base):
    """Добавился факт — уведомляем; переформулировали — правим молча."""
    deal = next(d for d in base["deals"] if format_post.has(d.get("sum")))
    without = json.loads(json.dumps(deal))
    without["sum"] = "—"
    added = format_post.changes(without, deal)
    assert added and format_post.should_notify(added)

    reworded = json.loads(json.dumps(deal))
    reworded["sum"] = str(deal["sum"]) + " (по оценке)"
    tweak = format_post.changes(deal, reworded)
    assert tweak and not format_post.should_notify(tweak)


# ---------- реестр источников ----------

def test_sources_registry_is_honest():
    """Непроверенная лента не может быть помечена проверенной.

    В среде разработки исходящий доступ к новостным сайтам закрыт политикой
    прокси, поэтому адреса лент в реестре — предположения. Пометку `feed_checked`
    ставит только `fetch.py --verify` там, где сеть есть.
    """
    reg = json.loads((ROOT / "pipeline" / "ingest" / "sources.json").read_text(encoding="utf-8"))
    sources = reg["sources"]
    assert len(sources) >= 100, "реестр подозрительно мал"
    for s in sources:
        assert s["id"] and s["name"] and s["kind"] in ("rss", "html", "telegram")
        if s.get("feed_checked"):
            assert s.get("last_check"), f"{s['id']}: помечен проверенным без даты проверки"
    assert any(s["kind"] == "telegram" for s in sources)
    assert all(not s["enabled"] or s.get("feed") for s in sources), \
        "включён источник без адреса ленты — забор молча ничего не даст"


# ---------- черновик карточки ----------

def test_draft_sum_is_written_our_way():
    """Валюта — значком: «12 млрд рублей» -> «12 млрд ₽» (соглашение базы)."""
    import draft
    assert draft.guess_sum("Куплено за 12 млрд рублей") == "12 млрд ₽"
    assert draft.guess_sum("Сделка на $230 млн") == "$230 млн"
    assert draft.guess_sum("Компания подвела итоги года") is None


def test_draft_never_invents_a_party():
    """Имя стороны обязано стоять в заголовке дословно."""
    import draft
    title = "«Лента» купила сеть магазинов «Монетка» у структуры Сбербанка"
    buyer, asset, seller = draft.guess_parties(title)
    for value in (buyer, asset, seller):
        if value:
            core = value.strip('«»" ').split()[0]
            assert core in title, f"{core!r} нет в заголовке"


def test_draft_keeps_silent_when_there_is_no_seller():
    """Нет продавца в заголовке — поле остаётся пустым, а не додумывается."""
    import draft
    _, _, seller = draft.guess_parties("«Лента» купила сеть магазинов «Монетка»")
    assert seller is None


def test_draft_records_the_first_deal_stage():
    """Первая новость создаёт не только статус, но и начало маршрута сделки."""
    import draft
    item = {"title": "Компания ведёт переговоры о покупке актива",
            "summary": "Стороны обсуждают условия.", "date": "2026-07-29",
            "url": "https://example.invalid/talks", "source_name": "Источник"}
    card = draft.build(item, {})
    assert card["status"] == "Обсуждается"
    assert card["events"] and card["events"][0]["kind"] == "negotiations"


def test_draft_error_rate_stays_low(base):
    """Разбор ошибается реже, чем молчит: замер на 1333 выверенных карточках.

    Пороги — сторож от ухудшения: на прогоне 47 ошибка составила 3% у продавца
    и 10% у покупателя. Если правило станет смелее и начнёт врать, тест упадёт.
    """
    import draft
    comps = base["companies"]
    wrong = {"buyer": 0, "seller": 0}
    said = {"buyer": 0, "seller": 0}

    def same(a, b):
        na, nb = (re.sub(r"[«»\"'(),.\s]", "", str(x or "").lower()) for x in (a, b))
        return na == nb or na in nb or nb in na

    for deal in base["deals"]:
        buyer, _, seller = draft.guess_parties(str(deal.get("title") or ""))
        truth_b = (comps.get(deal.get("buyer")) or {}).get("name") or deal.get("buyer_name")
        truth_s = (comps.get(deal.get("seller_id")) or {}).get("name") or deal.get("seller")
        if buyer and truth_b:
            said["buyer"] += 1
            wrong["buyer"] += not same(buyer, truth_b)
        if seller and truth_s:
            said["seller"] += 1
            wrong["seller"] += not same(seller, truth_s)
    assert wrong["seller"] / max(said["seller"], 1) < 0.10, "продавец стал врать чаще"
    assert wrong["buyer"] / max(said["buyer"], 1) < 0.25, "покупатель стал врать чаще"


# ---------- ворота в базу ----------

def test_promote_refuses_a_duplicate(base):
    """Сделка, которая уже есть в базе, второй карточкой не становится."""
    import promote
    deal = next(d for d in base["deals"]
                if d.get("src") and len(d["src"][0]) > 1 and str(d["src"][0][1]).startswith("http")
                and d.get("ind"))
    draft = {"title": deal["title"], "date": deal["date"], "ind": deal["ind"],
             "src": [["источник", deal["src"][0][1]]]}
    bad, hold = promote.check(draft, base, matcher.index_base(base["deals"]), promote.industries())
    assert any("уже есть в базе" in r for r in bad), bad


def test_promote_refuses_word_currency_and_placeholder_seller(base):
    """Сумма словом и «продавец не раскрыт» — нарушения соглашений базы."""
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "Компания «Тест-Альфа» купила завод «Тест-Бета»",
             "date": "2026-07-28", "ind": sorted(inds)[0],
             "src": [["источник", "https://example.invalid/x"]],
             "sum": "12 млрд рублей", "seller": "не раскрыт"}
    bad, _ = promote.check(draft, base, idx, inds)
    assert any("валюта словом" in r for r in bad)
    assert any("заглушка" in r for r in bad)


def test_enrich_never_overwrites_a_filled_field(base):
    """Новость называет другую сумму — это расхождение, а не правка.

    Замер на 1333 карточках: 933 подтверждения против 114 расхождений. Если бы
    правило переписывало, каждое девятое выверенное значение заменилось бы
    догадкой — ровно то, что двадцать прогонов исправляли.
    """
    import enrich
    deal = next(d for d in base["deals"] if format_post.has(d.get("sum")))
    item = {"title": "Стороны раскрыли сумму сделки — 999 млрд рублей",
            "url": "https://example.invalid/enrich-1", "source_id": "web:kommersant.ru"}
    props = enrich.proposals(deal, item, {}, base["companies"])
    kinds = {field: kind for field, _v, kind, _w in props}
    assert kinds.get("sum") == "расхождение", props
    assert deal["sum"] != "999 млрд ₽"


def test_enrich_only_moves_status_forward(base):
    """«Обсуждается» -> «Закрыта» можно, обратно — нет.

    Замер: правило ни разу не назвало закрытой сделку, которая в базе не
    закрыта (0 раз из 256), а все расхождения статуса — обратного вида.
    """
    import enrich
    news_closed = {"title": "Стороны завершили сделку", "url": "https://example.invalid/e2"}
    news_intent = {"title": "Компания планирует продать актив", "url": "https://example.invalid/e3"}

    talking = next(d for d in base["deals"] if d.get("status") == "Обсуждается")
    props = enrich.proposals(talking, news_closed, {}, base["companies"])
    assert ("status", "Закрыта", "обновить") in [(f, v, k) for f, v, k, _ in props]

    closed = next(d for d in base["deals"] if d.get("status") == "Закрыта")
    props = enrich.proposals(closed, news_intent, {}, base["companies"])
    assert not [p for p in props if p[0] == "status"], "статус поехал назад"


def test_enrich_adds_a_new_stage_to_the_same_card(base):
    """Новость о закрытии дополняет маршрут, а повтор не создаёт второй этап."""
    import enrich
    deal = {"id": "stage-test", "title": "Тестовая сделка", "date": "2026-07-01",
            "status": "Обсуждается", "src": [], "events": [
                {"kind": "negotiations", "date": "2026-07-01", "title": "Переговоры"}
            ]}
    item = {"title": "Стороны завершили сделку", "summary": "Сделка закрыта.",
            "date": "2026-07-29", "url": "https://example.invalid/closed"}
    props = enrich.proposals(deal, item, {}, base["companies"])
    assert any(p[0] == "event" and p[1]["kind"] == "closed" for p in props)
    enrich.apply_props(deal, props)
    assert deal["status"] == "Закрыта" and len(deal["events"]) == 2
    again = enrich.proposals(deal, item, {}, base["companies"])
    assert not [p for p in again if p[0] == "event"], "этап закрытия задублировался"


def test_enrich_updates_title_from_the_new_stage_source(base):
    import enrich
    deal = {"id": "title-stage", "title": "«Альфа» покупает «Бету»",
            "date": "2026-01-01", "status": "Обсуждается", "src": [], "events": []}
    item = {"title": "«Альфа» получила согласие на покупку «Беты»",
            "summary": "Регулятор одобрил сделку.", "date": "2026-07-29",
            "url": "https://example.invalid/approval"}
    props = enrich.proposals(deal, item, {}, base["companies"])
    assert any(p[0] == "title" and p[1] == item["title"] for p in props)
    enrich.apply_props(deal, props)
    assert deal["status"] == "Согласование получено" and deal["title"] == item["title"]


def test_enrich_accepts_extended_stage_headline():
    """Префикс регулятора не должен мешать обновить старый заголовок."""
    import enrich
    old = "«Альфа» покупает «Бету»"
    new = "ФАС одобрила сделку: «Альфа» покупает «Бету»"
    assert enrich.informative_title_update(old, new)


def test_promote_holds_closed_title_in_present_tense(base):
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "«Тест-Альфа» покупает «Тест-Бету»",
             "date": "2026-07-28", "ind": sorted(inds)[0], "status": "Закрыта",
             "src": [["источник", "https://example.invalid/closed-present"]]}
    bad, hold = promote.check(draft, base, idx, inds)
    assert not any("заголовок" in reason for reason in bad)
    assert any("настоящим временем" in reason for reason in hold)


def test_enrich_adds_a_new_source_but_not_a_known_one(base):
    """Ссылка на источник — главный вклад обогащения, но дублей быть не должно."""
    import enrich
    deal = next(d for d in base["deals"]
                if d.get("src") and len(d["src"][0]) > 1 and str(d["src"][0][1]).startswith("http"))
    known = {"title": "Та же новость", "url": deal["src"][0][1]}
    assert not [p for p in enrich.proposals(deal, known, {}, base["companies"]) if p[0] == "src"]

    fresh = {"title": "Другое издание о той же сделке",
             "url": "https://example.invalid/another", "source_id": "web:rbc.ru"}
    assert [p for p in enrich.proposals(deal, fresh, {}, base["companies"]) if p[0] == "src"]


def test_enrich_writes_only_on_a_strong_match():
    """Слабое совпадение в базу не пишет: в корзине «общие слова заголовка»
    33 совпадения из 541 ведут на ЧУЖУЮ карточку (6,1%), а в корзине с
    названием в кавычках — 4 из 568 (0,7%)."""
    import enrich
    assert enrich.is_strong("тот же адрес источника")
    assert enrich.is_strong("совпали название в кавычках и сумма")
    assert enrich.is_strong("общее название в кавычках и два общих слова")
    assert enrich.is_strong("совпал набор названий в кавычках на разных этапах")
    assert not enrich.is_strong("общие слова заголовка: 4")


def test_post_notifies_when_the_deal_closes(base):
    """Закрытие сделки — событие, а не переформулировка: о нём уведомляем."""
    deal = next(d for d in base["deals"] if d.get("status") == "Закрыта")
    before = json.loads(json.dumps(deal))
    before["status"] = "Обсуждается"
    ch = format_post.changes(before, deal)
    assert "сделка закрыта" in ch and format_post.should_notify(ch)


def test_post_notifies_when_a_stage_is_added():
    before = {"events": [{"kind": "negotiations"}]}
    after = {"events": [{"kind": "negotiations"}, {"kind": "approval"}]}
    ch = format_post.changes(before, after)
    assert "добавлен этап сделки" in ch and format_post.should_notify(ch)


def test_promote_holds_instead_of_guessing_industry(base):
    """Не хватает отрасли — карточка ждёт человека, а не выдумывает поле."""
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "Компания «Тест-Гамма» купила завод «Тест-Дельта»",
             "date": "2026-07-28", "ind": None,
             "src": [["источник", "https://example.invalid/y"]]}
    bad, hold = promote.check(draft, base, idx, inds)
    assert not bad and hold and "отрасль" in hold[0]


def test_promote_holds_even_a_clean_new_card_pending_filter_review(base):
    """Временная страховка (E9): «это сделка» не проверено на живом потоке.

    Первый прогон на реальной сети (28 июля 2026) показал: из 11 карточек,
    которые классификатор пускал автоматически, сделкой была одна — «Внуково
    станет совладельцем Домодедово». Остальные десять — рост акций Ozon, суд
    по маскам с лицом Джигурды, футбольный «раунд» (совпал с «раунд»
    инвестиций) и подобное. Замер на 18 ручных соседних темах этот класс
    ошибок не увидел вовсе. Пока фильтр не переизмерен на реальном потоке,
    ни одна новая карточка не пишется в базу без человека — даже если она
    формально проходит все остальные проверки.
    """
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "Компания «Тест-Эпсилон» купила завод «Тест-Дзета»",
             "date": "2026-07-28", "ind": sorted(inds)[0],
             "src": [["источник", "https://example.invalid/z"]]}
    bad, hold = promote.check(draft, base, idx, inds)
    assert not bad, "чистый черновик не должен получать отказ"
    assert any("живом потоке" in r for r in hold), hold


def test_match_links_stage_by_explicit_buyer_and_asset():
    """Разные формулировки новости не разрывают один жизненный цикл сделки."""
    companies = {
        "buyer-1": {"name": "Альфа Холдинг"},
        "target-1": {"name": "Бета Сервис"},
    }
    idx = matcher.index_base([{
        "id": "explicit-stage", "date": "2024-01-10",
        "title": "Владелец рассматривает продажу сервиса",
        "status": "Обсуждается", "src": [],
        "buyer": "buyer-1", "target": "target-1",
    }], companies)
    found, why = matcher.match({
        "title": "Регулятор согласовал приобретение актива",
        "date": "2026-02-20", "url": None,
        "buyer": "Альфа Холдинг", "asset": "Бета Сервис",
    }, idx)
    assert found == "explicit-stage"
    assert "покупатель и предмет" in why


def test_match_respects_reviewed_separate_transaction():
    """Редакторская отметка запрещает склейку отдельного транша с этапом."""
    companies = {
        "buyer-1": {"name": "Альфа Холдинг"},
        "target-1": {"name": "Бета Сервис"},
    }
    idx = matcher.index_base([{
        "id": "separate-tranche", "date": "2025-01-10",
        "title": "Первый отдельный транш",
        "status": "Обсуждается", "src": [],
        "buyer": "buyer-1", "target": "target-1",
        "separate_transaction_reviewed": True,
    }], companies)
    found, _ = matcher.match({
        "title": "Регулятор согласовал отдельную транзакцию",
        "date": "2025-02-20", "url": None,
        "buyer": "Альфа Холдинг", "asset": "Бета Сервис",
    }, idx)
    assert found is None


# ---------- отправка в Telegram ----------

import send_telegram  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    """Подставной httpx-клиент: запоминает вызовы, ничего не шлёт по сети."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def post(self, url, json):
        self.calls.append((url, json))
        return _FakeResponse(self.replies.pop(0))


def test_sendable_requires_at_least_one_real_fact():
    assert send_telegram.sendable({"sum": "12 млрд ₽"})
    assert send_telegram.sendable({"seller": "«Продавец»"})
    assert send_telegram.sendable({"target": "«Актив»"})
    assert not send_telegram.sendable({"sum": "Не раскрыта", "title": "Пустая карточка"})


def test_post_message_returns_new_message_id():
    client = _FakeClient([{"ok": True, "result": {"message_id": 555}}])
    mid = send_telegram.post_message(client, "TOKEN", "@channel", "текст поста")
    assert mid == 555
    url, payload = client.calls[0]
    assert url.endswith("/bottoken/sendMessage".replace("token", "TOKEN")) or "sendMessage" in url
    assert payload["chat_id"] == "@channel" and payload["text"] == "текст поста"
    assert payload["parse_mode"] == "HTML"


def test_post_message_raises_on_api_error():
    client = _FakeClient([{"ok": False, "description": "chat not found"}])
    with pytest.raises(send_telegram.TelegramError):
        send_telegram.post_message(client, "TOKEN", "@channel", "текст")


def test_edit_message_tolerates_not_modified():
    """Telegram считает правкой даже пробел — повторная отправка того же текста
    не должна валить весь прогон рутины притока."""
    client = _FakeClient([{"ok": False, "description": "Bad Request: message is not modified"}])
    send_telegram.edit_message(client, "TOKEN", "@channel", 555, "тот же текст")  # не бросает


def test_edit_message_raises_on_real_error():
    client = _FakeClient([{"ok": False, "description": "message to edit not found"}])
    with pytest.raises(send_telegram.TelegramError):
        send_telegram.edit_message(client, "TOKEN", "@channel", 555, "текст")


def test_main_without_token_never_touches_network_or_writes(monkeypatch, tmp_path, base):
    """Без токена/канала — план на экран, ни одного сетевого вызова, файл базы не тронут."""
    def boom():
        raise AssertionError("_client() не должен вызываться без токена")
    monkeypatch.setattr(send_telegram, "_client", boom)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
    before = send_telegram.DATA
    mtime_before = Path(before).stat().st_mtime
    send_telegram.main(write=True)  # write=True тоже не должен ничего слать без токена
    assert Path(before).stat().st_mtime == mtime_before
