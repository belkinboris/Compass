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


def test_promote_holds_instead_of_guessing_industry(base):
    """Не хватает отрасли — карточка ждёт человека, а не выдумывает поле."""
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "Компания «Тест-Гамма» купила завод «Тест-Дельта»",
             "date": "2026-07-28", "ind": None,
             "src": [["источник", "https://example.invalid/y"]]}
    bad, hold = promote.check(draft, base, idx, inds)
    assert not bad and hold and "отрасль" in hold[0]
