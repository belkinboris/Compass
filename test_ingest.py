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
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
sys.path.insert(0, str(ROOT / "pipeline" / "publish"))

import classify              # noqa: E402
import discover_feeds         # noqa: E402
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


def test_match_sees_short_names():
    """Порог «слово длиннее четырёх знаков» делал короткие имена невидимыми.

    «Hugo Boss», «VK», «МТС», «X5» — это названия, а не служебные слова, и
    объявление о такой сделке не находило свою карточку ни разу. Исключение
    сделано ровно для имён: латиница и аббревиатуры заглавными. Правовые формы
    и слова из имён фирм («ГК», «АО», «Group», «Capital») по-прежнему
    выбрасываются — иначе по ним слипнется пол-базы.
    """
    assert {"hugo", "boss"} <= matcher.stems("«Стокманн» купил российский бизнес Hugo Boss")
    for name in ("VK", "МТС", "X5"):
        assert matcher.stems("%s выкупила долю" % name), "%s не виден сопоставлению" % name
    assert matcher.stems("ООО ГК АО ЗАО Group Holding Capital Partners Ltd LLC") == set()


def test_quoted_common_counts_every_shared_name():
    """Ранжирование кандидатов и развилка «сильное совпадение» считают одинаково.

    `quoted_overlap` отвечает да/нет, но человеку в списке кандидатов важно,
    СКОЛЬКО названий общих: одно случайное («Лента» есть у десятка карточек)
    и три подряд («Лента» + «О'Кей» + «РБФ ритейл») — разной силы признак.
    Обе функции обязаны опираться на одно правило вхождения, иначе показанный
    список разойдётся с тем, что пускается в базу.
    """
    post = {"лент", "о кей", "рбф ритейл"}
    card = {"лент", "земун", "рбф ритейл", "о кей"}
    assert matcher.quoted_common(post, card) == {"лент", "о кей", "рбф ритейл"}
    assert matcher.quoted_common(post, {"северсталь"}) == set()
    # Вхождение, а не только равенство: «Заряд» и «Бери заряд» — одна компания.
    assert matcher.quoted_common({"заряд"}, {"бери заряд"}) == {"заряд"}
    for a, b in (({"лент"}, {"лент"}), ({"заряд"}, {"бери заряд"}), ({"лент"}, {"мегафон"})):
        assert matcher.quoted_overlap(a, b) is bool(matcher.quoted_common(a, b))


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
        assert s["id"] and s["name"] and s["kind"] in ("rss", "html", "html_mergers", "telegram")
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


def test_unknown_industry_does_not_hold_the_card(base):
    """Неизвестная отрасль — не повод не пускать сделку на сайт.

    Проверка перевёрнута сознательно, и вот почему. Неделю «отрасль не
    определилась» было причиной задержки номер один (21 черновик из 41), и
    держалась она на ложной посылке: будто карточка без отрасли базе не
    годится. В `INDUSTRIES` есть значение «Не определена», интерфейс его
    показывает — просто до 5 августа им не была помечена ни одна карточка из
    1541. Отрасль дописывается позже (профилем компании, обогащением,
    человеком), а сделка, которой на сайте нет вовсе, не дописывается ничем.
    """
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    draft = {"title": "Компания «Тест-Гамма» купила завод «Тест-Дельта»",
             "date": "2026-07-28", "ind": None,
             "buyer_name": "«Тест-Гамма»", "asset": "завод «Тест-Дельта»",
             "src": [["источник", "https://example.invalid/y"]]}
    bad, hold = promote.check(draft, base, idx, inds)
    assert not bad and not hold, (bad, hold)
    # …и в карточке отрасль подписана честно, а не выдумана.
    assert promote.to_card(draft, "gtest0001")["ind"] == "Не определена"
    assert "Не определена" in inds


def test_promote_holds_a_card_without_a_subject_or_a_party(base):
    """Предмет и хотя бы одна сторона обязательны — для ЛЮБОГО типа сделки.

    Требовать именно ПОКУПАТЕЛЯ нельзя: 431 карточка базы из 1541 (28%) его не
    называет вовсе, потому что его не назвал источник. А вот заголовок, из
    которого не видно ни что продают, ни кто участвует, — это не сделка.
    Проверка распространена на все типы: раньше её обходило всё, что разбор
    счёл размещением, и «Shein выплатит инвесторам не менее $1,1 млрд перед
    IPO» проходило ворота насквозь.
    """
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    common = {"date": "2026-07-28", "ind": "ИТ и интернет",
              "src": [["источник", "https://example.invalid/z"]]}
    no_subject = dict(common, title="Тест-Эпсилон выплатит инвесторам перед IPO",
                      type="IPO", buyer_name="Тест-Эпсилон")
    bad, hold = promote.check(no_subject, base, idx, inds)
    assert not bad and any("предмет" in r for r in hold), (bad, hold)

    no_party = dict(common, title="Продаётся завод «Тест-Дзета»", type="M&A",
                    asset="завод «Тест-Дзета»")
    bad, hold = promote.check(no_party, base, idx, inds)
    assert not bad and any("сторона" in r for r in hold), (bad, hold)


def test_promote_holds_a_paraphrase_of_a_fresh_card(base):
    """Одна новость в двух изданиях не должна стать двумя карточками.

    `match.py` объявляет дубль по трём общим словам заголовка — порог выбран
    замером (два слова уводили на чужую карточку в 6,1% случаев) и снижать его
    там нельзя. Но «отказать» и «показать человеку» стоят разного: ««Тантор
    Лабс» купил права на СУБД «Персей»» и «Создатель российского Linux купил
    полсотни разработчиков суверенной СУБД «Персей»» — это одна сделка, и
    общего названия в кавычках за одну неделю тут достаточно.
    """
    import promote
    existing = {"id": "gtest-persei", "date": "2026-08-04",
                "title": "«Тантор Лабс» купил права на СУБД «Персей»",
                "ind": "ИТ и интернет", "type": "M&A", "status": "Закрыта",
                "src": [["источник", "https://example.invalid/persei"]]}
    idx = matcher.index_base(base["deals"] + [existing])
    df = promote.stem_frequency(idx)
    twin = {"title": "Создатель российского Linux купил полсотни разработчиков "
                     "суверенной СУБД «Персей»", "date": "2026-08-04"}
    found = promote.near_duplicate(twin, idx, df)
    assert found, "перефразировка свежей карточки прошла как новая сделка"
    # В базе уже есть настоящая карточка про «Персей» — правило находит ту или
    # другую, обе верны; важно, что найденная говорит о том же предмете.
    titles = {d["id"]: str(d.get("title") or "")
              for d in base["deals"] + [existing]}
    assert "Персей" in titles[found[0]]
    # Общие слова без единого РЕДКОГО дублем не считаются. Без этого условия
    # «Совладелец „Депо Три Вокзала" продал долю в разработчике» слипался с
    # «Владельцы ATI.SU купили разработчика» по словам «владел» и «разраб»,
    # которые стоят в 25 и 34 заголовках базы и не значат ничего. Проверяем сам
    # механизм: если ни одно слово не редкое, правило обязано промолчать.
    other = {"title": "Владельцы платформы купили разработчика системы",
             "date": "2026-08-04"}
    all_frequent = {stem: 99 for row in idx for stem in row["stems"]}
    all_frequent.update({s: 99 for s in matcher.stems(other["title"])})
    assert promote.near_duplicate(other, idx, all_frequent) is None


def test_promote_lets_a_confident_card_through_and_holds_a_thin_one(base):
    """Тормоз E9 снят — но дверь не распахнута, а стала развилкой.

    Он был поставлен 28 июля верно: на первом реальном потоке из 11 карточек,
    которые классификатор пускал автоматически, сделкой была одна. Но за неделю
    он не пропустил НИ ОДНОЙ карточки, а очередь «на решение» падала в
    одноразовый контейнер рутины и исчезала вместе с ним.

    Теперь решает уверенность: карточка с покупателем, предметом и отраслью
    идёт в базу, а карточка без сторон — человеку. Замер на потоке 4 августа:
    из 44 черновиков автоматически прошли 5, и все пять — настоящие сделки.
    """
    import promote
    idx, inds = matcher.index_base(base["deals"]), promote.industries()
    confident = {"title": "Компания «Тест-Эпсилон» купила завод «Тест-Дзета»",
                 "date": "2026-07-28", "ind": sorted(inds)[0], "type": "M&A",
                 "buyer_name": "Тест-Эпсилон", "asset": "завод «Тест-Дзета»",
                 "src": [["источник", "https://example.invalid/z"]]}
    bad, hold = promote.check(confident, base, idx, inds)
    assert not bad and not hold, f"уверенная карточка не прошла: {bad or hold}"
    assert set(promote.confidence(confident)) >= {"покупатель", "предмет", "отрасль"}

    thin = dict(confident); thin.pop("buyer_name"); thin.pop("asset")
    bad, hold = promote.check(thin, base, idx, inds)
    assert not bad, "карточка без сторон — не отказ, а вопрос человеку"
    assert hold, "карточка без покупателя и предмета обязана уйти на решение"


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


# ---------- кто сопровождал сделку ----------

import advisors  # noqa: E402


def test_advisor_is_taken_from_the_start_of_the_announcement():
    """Объявление о сопровождении — пресс-релиз: имя фирмы стоит первым, за ним
    глагол действия по сделке. Замер на 2544 постах @LawFirms: 65 срабатываний,
    ложных среди проверенных нет."""
    firms, role, _ = advisors.lead_advisor(
        'White Square консультировала Nordgold в связи с приобретением актива на Чукотке.')
    assert firms == ['White Square'] and role.startswith('Юридический консультант')


def test_advisor_rule_ignores_job_titles_and_rankings():
    """Первая версия правила искала «консультант»/«советник» где угодно в тексте
    и дала 11 срабатываний на 133 живых постах, из которых верных НОЛЬ: в
    юридических каналах «советник» — должность сотрудника, а «консультант» —
    слово из рейтинга. Эти три строки — те самые ложные срабатывания."""
    assert advisors.lead_advisor('советник LEVEL Legal Services провела мастер-класс по арбитражу') is None
    assert advisors.lead_advisor('ALUMNI Partners вошла в топ-5 юридических консультантов рейтинга') is None
    assert advisors.lead_advisor('Присутствовать на этом событии удалось советнику ККМП Алексею Чернышеву') is None


def test_advisor_rule_needs_a_role_next_to_vystupil():
    """«Прокуратура выступила ПРОТИВ выселения певицы» — не объявление о
    сопровождении. Глагол «выступил» засчитывается только с ролью рядом."""
    assert advisors.lead_advisor('Прокуратура выступила против принудительного выселения певицы.') is None
    assert advisors.lead_advisor('NSP выступила юридическим консультантом покупателя.') is not None


def test_advisor_name_keeps_commas_inside_a_quoted_firm():
    """«Меллинг, Войтишкин и Партнеры» — одна фирма, а Freshfields, Latham &
    Watkins и Hengeler Mueller — три. Различает их кавычка, а не запятая."""
    one, _, _ = advisors.lead_advisor(
        '«Меллинг, Войтишкин и Партнеры» сообщает: её команда представляла интересы группы.')
    assert one == ['Меллинг, Войтишкин и Партнеры']
    many, _, _ = advisors.lead_advisor(
        'Freshfields, Latham & Watkins и Hengeler Mueller сопровождали IPO.')
    assert many == ['Freshfields', 'Latham & Watkins', 'Hengeler Mueller']
    # Родовое слово снаружи собственных кавычек имени — тоже одна фирма.
    nested, _, _ = advisors.lead_advisor(
        'АБ «Андрей Городисский и Партнеры» выступили юридическим консультантом сделки.')
    assert nested == ['Андрей Городисский и Партнеры']


def test_advisor_rule_survives_the_latin_homoglyph():
    """В самом канале встречается ЛАТИНСКАЯ «c» вместо кириллической
    («Nextons cообщает…»): шаблон с одной кириллицей молча не сработал бы."""
    firms, _, _ = advisors.lead_advisor('Nextons cообщает о сопровождении сделки.')
    assert firms == ['Nextons']


def test_advisor_rule_knows_more_than_one_way_to_say_the_same_thing():
    """Список формулировок был собран по одной партии постов — и оказался
    списком ТЕХ формулировок, а не всех.

    «Обеспечила сопровождение», «осуществила сопровождение» и «сообщает о
    консультировании» значат ровно то же, что «сопровождала», но правило их не
    знало и молча пропускало объявления. Замер по архиву канала: срабатываний
    было 115, стало 128, и все 13 добавившихся — настоящие объявления фирм
    (Orion/ВТБ, Better Chance/«Инкаб Холдинг», VERBA LEGAL/RWB, АЛРУД/«Пункт Е»,
    Nextons/SPO «Эталон», BIRCH/«ВИМ Инвестиции», White Square/Softline и др.),
    ни одного ложного и ни одного потерянного.
    """
    for text in (
        'Команда Orion сообщает о консультировании банка ВТБ в связи со сделкой.',
        'Better Chance обеспечила полное юридическое сопровождение размещения акций.',
        'Nextons осуществила комплексное юридическое сопровождение SPO «Эталон Груп».',
    ):
        assert advisors.lead_advisor(text), 'правило не увидело объявление: %s' % text[:48]
    # Границу не размываем: те же глаголы без сделки и без роли не проходят.
    assert advisors.lead_advisor('White Square приглашает вас на вебинар про IPO.') is None
    assert advisors.lead_advisor('BIRCH сообщает о присоединении Ивана Фрышкина партнером.') is None


def test_advisor_name_drops_every_generic_prefix_not_just_one():
    """Родовых слов бывает два подряд, а `sub` с якорем `^` снимает одно.

    «Команда практики рынков капитала White Square» превращалась в «практики
    рынков капитала White Square» — и такой «консультант» попадал бы на экран.
    Заодно проверяется ленивый квантификатор: жадный съедал «рынков капитала
    Better» целиком (за ним тоже заглавная) и оставлял имя «Chance».
    """
    assert advisors.lead_advisor(
        'Команда практики рынков капитала White Square выступила юридическим консультантом SPO.'
    )[0] == ['White Square']
    assert advisors.lead_advisor(
        'Практика рынков капитала Better Chance обеспечила сопровождение размещения акций.'
    )[0] == ['Better Chance']
    # Имя фирмы, начинающееся с родового слова в кавычках, резать нельзя.
    assert advisors.lead_advisor(
        'АБ «Андрей Городисский и Партнеры» выступили юридическим консультантом сделки.'
    )[0] == ['Андрей Городисский и Партнеры']


def test_advisor_side_is_set_only_when_one_party_is_named():
    """Сторона — факт из текста, а не догадка: названы обе — роль остаётся общей."""
    assert advisors.lead_advisor('NSP сопровождало продавца в сделке.')[1] == 'Юридический консультант продавца'
    assert advisors.lead_advisor('NSP сопровождало покупателя и продавца в сделке.')[1] == 'Юридический консультант'


# ---------- отправка в Telegram ----------

import send_telegram  # noqa: E402
import seed_telegram_posts_backlog  # noqa: E402
import telegram_endpoint  # noqa: E402


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


def test_api_root_is_telegram_directly_when_relay_is_not_configured(monkeypatch):
    monkeypatch.delenv("TELEGRAM_API_BASE", raising=False)
    assert telegram_endpoint.api_root() == "https://api.telegram.org"
    assert telegram_endpoint.method_url("TOKEN", "sendMessage") == \
        "https://api.telegram.org/botTOKEN/sendMessage"


def test_api_root_uses_relay_when_configured(monkeypatch):
    """Прямая связь Timeweb (РФ) -> api.telegram.org даёт ~32% отказов
    (замер соседнего проекта «Автопост», 19 июля 2026) — релей на Cloudflare
    Workers убирает причину на уровне сети. Путь /bot<токен>/<метод> воркер
    пробрасывает как есть, поэтому один воркер обслуживает любого бота."""
    monkeypatch.setenv("TELEGRAM_API_BASE", "https://relay.workers.dev")
    assert telegram_endpoint.method_url("TOKEN", "sendMessage") == \
        "https://relay.workers.dev/botTOKEN/sendMessage"


def test_api_root_survives_relay_address_without_scheme(monkeypatch):
    """Значение без «https://» даёт UnsupportedProtocol мгновенно, без единой
    попытки сети, — такую ошибку легко принять за сетевую и искать причину не
    там (ровно это и произошло в «Автопосте» 19 июля 2026). Схему дописываем
    сами, а не надеемся, что её не забудут в панели хостинга."""
    monkeypatch.setenv("TELEGRAM_API_BASE", "relay.workers.dev")
    assert telegram_endpoint.method_url("TOKEN", "sendMessage") == \
        "https://relay.workers.dev/botTOKEN/sendMessage"


def test_api_root_ignores_trailing_slash(monkeypatch):
    monkeypatch.setenv("TELEGRAM_API_BASE", "https://relay.workers.dev/")
    assert telegram_endpoint.method_url("TOKEN", "sendMessage") == \
        "https://relay.workers.dev/botTOKEN/sendMessage"


def test_send_telegram_actually_calls_the_relay(monkeypatch):
    """Мало иметь верный адрес — отправка обязана им пользоваться. Раньше
    адрес был захардкожен в константе модуля, и подмена переменной окружения
    на него бы не повлияла."""
    monkeypatch.setenv("TELEGRAM_API_BASE", "https://relay.workers.dev")
    client = _FakeClient([{"ok": True, "result": {"message_id": 1}}])
    send_telegram.post_message(client, "TOKEN", "@channel", "текст")
    url, _payload = client.calls[0]
    assert url.startswith("https://relay.workers.dev/"), url


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


def test_main_caps_sends_per_run_and_paces_them(monkeypatch, tmp_path):
    """Без ограничения первый прогон с настоящим токеном разослал бы весь бэклог
    (у нас — больше тысячи карточек) одним залпом без пауз и упёрся бы в лимит
    Telegram (~1 сообщение/сек на канал) — см. docstring send_telegram.py,
    «защита от первого запуска». За один прогон должно уходить не больше
    MAX_SENDS_PER_RUN сообщений, и между ними — пауза."""
    # Свой telegram_posts = {}, а не унаследованный от боевого файла: после
    # seed_telegram_posts_backlog.py в реальной базе почти всё уже засеяно
    # как бэклог (см. ниже), и тест не должен зависеть от того, сколько
    # карточек сейчас реально «новые» — это отдельная, самостоятельная проверка.
    real_data = json.loads(Path(send_telegram.DATA).read_text(encoding="utf-8"))
    real_data["telegram_posts"] = {}
    tmp_data = tmp_path / "deals_promoted.json"
    tmp_data.write_text(json.dumps(real_data), encoding="utf-8")
    monkeypatch.setattr(send_telegram, "DATA", str(tmp_data))
    monkeypatch.setattr(send_telegram, "MAX_SENDS_PER_RUN", 3)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@channel")

    sleeps = []
    monkeypatch.setattr(send_telegram.time, "sleep", lambda s: sleeps.append(s))
    fake = _FakeClient([{"ok": True, "result": {"message_id": 1000 + i}} for i in range(3)])
    monkeypatch.setattr(send_telegram, "_client", lambda: fake)

    # ignore_pace: тест про ЛИМИТ за прогон, а не про дневное окно. Без него
    # он проходил бы только с 10 до 19 по Москве и падал бы по вечерам.
    send_telegram.main(write=True, ignore_pace=True)

    assert len(fake.calls) == 3, "за один прогон ушло больше сообщений, чем разрешает лимит"
    assert len(sleeps) == 2, "между тремя отправками должно быть ровно две паузы"

    written = json.loads(tmp_data.read_text(encoding="utf-8"))
    assert len(written["telegram_posts"]) == 3


def test_main_skips_seeded_backlog_entries_without_new_facts(monkeypatch, tmp_path):
    """`telegram_posts[id] = null` — метка «эта карточка — бэклог, не
    публиковать при включении канала», а не забытая запись. Пока у неё нет
    настоящего нового факта в data/inbox/updates/, она молчит: ни новый пост,
    ни (тем более) правка несуществующего сообщения."""
    real_data = json.loads(Path(send_telegram.DATA).read_text(encoding="utf-8"))
    seeded_deal = real_data["deals"][0]
    real_data["deals"] = [seeded_deal]  # только эта карточка — никаких других кандидатов на отправку
    real_data["telegram_posts"] = {seeded_deal["id"]: None}
    tmp_data = tmp_path / "deals_promoted.json"
    tmp_data.write_text(json.dumps(real_data), encoding="utf-8")
    monkeypatch.setattr(send_telegram, "DATA", str(tmp_data))
    monkeypatch.setattr(send_telegram, "load_today_updates", lambda: {})
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@channel")

    boom = _FakeClient([])  # ни один вызов не ожидается вообще

    def no_client():
        return boom
    monkeypatch.setattr(send_telegram, "_client", no_client)

    # ignore_pace обязателен и здесь, хотя тест ждёт ПУСТОТЫ: вне дневного
    # окна не уходит ничего в принципе, и тест проходил бы по ложной причине —
    # не потому, что правило бэклога работает, а потому, что сейчас вечер.
    send_telegram.main(write=True, ignore_pace=True)

    assert boom.calls == [], "бэклог-карточку без нового факта нельзя ни публиковать, ни редактировать"


def test_main_sends_backlog_entry_as_fresh_post_when_new_fact_appears(monkeypatch, tmp_path):
    """Уточнение владельца (2 августа): бэклог — это «не публиковать историю
    разом при включении канала», а не «эта карточка никогда не появится в
    канале». Если у бэклог-сделки позже появляется настоящий новый факт из
    data/inbox/updates/, для читателя это первый пост про неё — уходит как
    НОВЫЙ (sendMessage, без «⟳ Обновлено» — сравнивать не с чем), а не
    молчит и не пытается редактировать несуществующее сообщение."""
    real_data = json.loads(Path(send_telegram.DATA).read_text(encoding="utf-8"))
    seeded_deal = real_data["deals"][0]
    real_data["deals"] = [seeded_deal]
    real_data["telegram_posts"] = {seeded_deal["id"]: None}
    tmp_data = tmp_path / "deals_promoted.json"
    tmp_data.write_text(json.dumps(real_data), encoding="utf-8")
    monkeypatch.setattr(send_telegram, "DATA", str(tmp_data))
    monkeypatch.setattr(send_telegram, "load_today_updates",
                         lambda: {seeded_deal["id"]: ["появилась сумма сделки"]})
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@channel")

    fake = _FakeClient([{"ok": True, "result": {"message_id": 777}}])
    monkeypatch.setattr(send_telegram, "_client", lambda: fake)

    # ignore_pace: тест про правило бэклога, а не про дневное окно (см. выше).
    send_telegram.main(write=True, ignore_pace=True)

    assert len(fake.calls) == 1, "у бэклог-карточки с новым фактом должна уйти ровно одна отправка"
    url, payload = fake.calls[0]
    assert "sendMessage" in url, "это первый пост, а не editMessageText — сравнивать не с чем"
    assert "Обновлено" not in payload["text"]

    written = json.loads(tmp_data.read_text(encoding="utf-8"))
    assert written["telegram_posts"][seeded_deal["id"]] == 777, "null должен смениться на настоящий message_id"


def test_seed_backlog_marks_every_existing_deal_and_nothing_else(tmp_path, monkeypatch):
    """Каждая существующая на момент запуска сделка получает telegram_posts[id]
    = null; уже присутствовавшие записи (например, реально опубликованные)
    не перезаписываются."""
    tmp_data = tmp_path / "deals_promoted.json"
    tmp_data.write_text(json.dumps({
        "deals": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        "telegram_posts": {"a": 555},  # уже реально опубликована — не трогаем
    }), encoding="utf-8")
    monkeypatch.setattr(seed_telegram_posts_backlog, "PATH", str(tmp_data))

    seed_telegram_posts_backlog.main(write=True)

    written = json.loads(tmp_data.read_text(encoding="utf-8"))
    assert written["telegram_posts"] == {"a": 555, "b": None, "c": None}


# ---------- обнаружение RSS-ленты у сайтов без известного адреса ----------

def test_discover_finds_feed_link_regardless_of_attribute_order(monkeypatch):
    """Реальные сайты пишут атрибуты `<link>` в разном порядке (rel до type и
    наоборот) — правило обязано ловить оба варианта, а не только один."""
    html_rel_first = '<head><link rel="alternate" type="application/rss+xml" href="/feed.xml"></head>'
    html_type_first = '<head><link type="application/rss+xml" rel="alternate" href="/feed.xml"></head>'
    for html in (html_rel_first, html_type_first):
        monkeypatch.setattr(discover_feeds, "http_get", lambda url, html=html: html.encode())
        feed_url, err = discover_feeds.discover("https://example.ru/")
        assert err is None and feed_url == "https://example.ru/feed.xml"


def test_discover_ignores_unrelated_link_tags(monkeypatch):
    html = '<head><link rel="stylesheet" href="/style.css"><link rel="icon" href="/favicon.ico"></head>'
    monkeypatch.setattr(discover_feeds, "http_get", lambda url: html.encode())
    feed_url, err = discover_feeds.discover("https://example.ru/")
    assert feed_url is None and err == "ленты в <head> нет"


def test_discover_resolves_relative_feed_url(monkeypatch):
    monkeypatch.setattr(discover_feeds, "http_get",
                         lambda url: b'<head><link rel="alternate" type="application/atom+xml" href="/feed/"></head>')
    feed_url, err = discover_feeds.discover("https://example.ru/about/")
    assert err is None
    assert feed_url == "https://example.ru/feed/"


def test_discover_reports_http_error_without_raising(monkeypatch):
    import urllib.error

    def boom(url):
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
    monkeypatch.setattr(discover_feeds, "http_get", boom)
    feed_url, err = discover_feeds.discover("https://blocked.example/")
    assert feed_url is None and "403" in err


def test_discover_main_dry_run_does_not_write(monkeypatch, tmp_path):
    """Без --write реестр не меняется, даже если все ленты нашлись бы."""
    sources = [{"id": "firm:test", "name": "Test", "kind": "html", "url": "https://test.example/",
                "feed": None, "feed_checked": False, "tier": 3, "enabled": False}]
    tmp_sources = tmp_path / "sources.json"
    tmp_sources.write_text(json.dumps({"sources": sources}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(discover_feeds, "SOURCES", str(tmp_sources))
    monkeypatch.setattr(discover_feeds, "load_sources",
                         lambda: json.loads(tmp_sources.read_text(encoding="utf-8"))["sources"])
    monkeypatch.setattr(discover_feeds, "http_get",
                         lambda url: b'<head><link rel="alternate" type="application/rss+xml" href="/f.xml"></head>'
                         if "f.xml" not in url else b'<rss><channel><item><title>T</title><link>u</link></item></channel></rss>')
    discover_feeds.main([])
    assert json.loads(tmp_sources.read_text(encoding="utf-8"))["sources"][0]["enabled"] is False


# ---------- равномерная выдача постов в канал ----------

def test_publisher_holds_everything_at_night():
    """Ночью новых постов не отправляем — никого не будим.

    Это прямое требование владельца, и оно важнее скорости: сделка, найденная
    в три часа ночи, подождёт до утра.
    """
    from datetime import datetime
    import importlib, sys as _sys
    _sys.path.insert(0, str(ROOT / "pipeline" / "publish"))
    sender = importlib.import_module("send_telegram")
    for hour in (0, 3, 7, 9, 19, 22, 23):
        allowed, why = sender.pace_allowance(5, datetime(2026, 8, 4, hour, 0, tzinfo=sender.MSK))
        assert allowed == 0, f"в {hour}:00 отправили бы {allowed} — окно нарушено ({why})"
    for hour in (10, 13, 18):
        allowed, _ = sender.pace_allowance(5, datetime(2026, 8, 4, hour, 0, tzinfo=sender.MSK))
        assert allowed >= 1, f"в {hour}:00 внутри окна не отправили ничего"


def test_publisher_spreads_the_queue_over_the_window():
    """Очередь делится на оставшиеся прогоны, а не уходит пачкой.

    Пять постов в 10:00 при часовом прогоне — это по одному за раз, а не пять
    уведомлений за десять секунд. Расчёт без состояния: доля считается от
    того, что осталось в очереди СЕЙЧАС, поэтому пропущенный прогон не копит
    долг, а просто делится на меньшее число слотов.
    """
    from datetime import datetime
    import importlib, sys as _sys
    _sys.path.insert(0, str(ROOT / "pipeline" / "publish"))
    sender = importlib.import_module("send_telegram")
    at10, _ = sender.pace_allowance(5, datetime(2026, 8, 4, 10, 0, tzinfo=sender.MSK))
    assert at10 == 1, f"в начале окна взяли {at10} из 5 — это не равномерно"
    # Ближе к концу окна остаток уходит целиком: иначе он завис бы до завтра.
    at1830, _ = sender.pace_allowance(3, datetime(2026, 8, 4, 18, 30, tzinfo=sender.MSK))
    assert at1830 == 3, "остаток очереди не ушёл в последнем слоте"
    # Но не в одну минуту: между новыми постами внутри прогона есть пауза.
    assert sender.SPREAD_S >= 60, "новые посты внутри прогона не разведены по времени"
    # Пустая очередь не заставляет отправлять «хоть что-нибудь».
    assert sender.pace_allowance(0, datetime(2026, 8, 4, 12, 0, tzinfo=sender.MSK))[0] == 0


# ---------- личные уведомления по подпискам ----------

class _Sub:
    """Подписка как её видит правило: те же три поля, что у SavedFilter."""

    def __init__(self, industry=None, keyword=None, min_amount_mln_rub=None):
        self.industry = industry
        self.keyword = keyword
        self.min_amount_mln_rub = min_amount_mln_rub


def _subs():
    import importlib
    return importlib.import_module("notify_subscribers")


def test_subscription_amount_is_silent_when_the_sum_is_unreadable():
    """Порог суммы не срабатывает на том, чего мы не сумели прочитать.

    Сумма в карточке — свободный текст, и валюту мы не конвертируем: курса в
    базе нет. Прислать письмо «сделка от 500 млн ₽» по карточке «$1,2 млрд»
    значило бы выдать догадку за факт — то же правило «ошибка дороже
    молчания», что у разбора новостей.
    """
    ns = _subs()
    big = _Sub(min_amount_mln_rub=500)
    for unreadable in ("Не раскрыта", "$1,2 млрд", "€800 млн",
                       "несколько млрд ₽ (точно не указана)"):
        assert ns.match_reason(big, {"sum": unreadable, "ind": "ИТ и интернет"}, {}) is None, \
            f"по сумме «{unreadable}» подписка сработала, хотя разобрать её нельзя"
    assert ns.match_reason(big, {"sum": "8,7 млрд ₽", "ind": "ИТ и интернет"}, {}), \
        "по разобранной сумме подписка не сработала"


def test_subscription_takes_the_lower_bound_of_a_range():
    """Из диапазона берётся нижняя граница, а «300+ млн» — тоже нижняя.

    Подписка «от 500 млн» не должна срабатывать на сделке, которая может
    стоить 200: верхняя граница — это чужая оценка сверху, а не цена.
    """
    ns = _subs()
    assert ns.amount_mln_rub("200–550 млн ₽ (по оценке)") == 200.0
    assert ns.match_reason(_Sub(min_amount_mln_rub=500),
                           {"sum": "200–550 млн ₽ (по оценке)"}, {}) is None
    assert ns.match_reason(_Sub(min_amount_mln_rub=100),
                           {"sum": "200–550 млн ₽ (по оценке)"}, {})
    # Значок без единицы — это рубли, а не миллионы: символическая цена в
    # 1 ₽ не должна проходить порог «от 500 млн».
    assert ns.amount_mln_rub("1 ₽") == 1e-6
    assert ns.match_reason(_Sub(min_amount_mln_rub=500), {"sum": "1 ₽"}, {}) is None


def test_subscription_conditions_are_combined_with_and():
    """«Отрасль X и от Y» — это про сделки в X дороже Y, а не две ленты сразу."""
    ns = _subs()
    both = _Sub(industry="ИТ и интернет", min_amount_mln_rub=1000)
    assert ns.match_reason(both, {"ind": "ИТ и интернет", "sum": "8,7 млрд ₽"}, {})
    assert ns.match_reason(both, {"ind": "ИТ и интернет", "sum": "200 млн ₽"}, {}) is None
    assert ns.match_reason(both, {"ind": "Финансы", "sum": "8,7 млрд ₽"}, {}) is None
    # Пустая подписка не подходит ничему: «сообщать обо всём» — не подписка.
    assert ns.match_reason(_Sub(), {"ind": "Финансы", "sum": "8,7 млрд ₽"}, {}) is None


def test_subscription_keyword_looks_at_names_not_at_the_whole_card():
    """Подписка на компанию — про её сделки, а не про упоминания в пояснении.

    «Сбер» стоит кредитором в десятках чужих карточек. Если искать слово по
    всему тексту, подписчик получит ленту рынка вместо ленты компании.
    """
    ns = _subs()
    sub = _Sub(keyword="Сбер")
    party = {"title": "Сбербанк увеличил долю в Rambler Group", "extra": ""}
    mention = {"title": "«Магнит» купил сеть «Дикси»",
               "extra": "Сделка профинансирована кредитом Сбербанка."}
    assert ns.match_reason(sub, party, {})
    assert ns.match_reason(sub, mention, {}) is None
    # Профиль стороны сделки — тоже имя: половина карточек хранит сторону
    # ссылкой, и поиск только по заголовку их бы не увидел.
    by_profile = {"title": "Покупка 100% оператора связи", "buyer": "sber"}
    assert ns.match_reason(sub, by_profile, {"sber": {"name": "Сбербанк"}})


def test_filter_is_measured_on_the_live_stream_not_on_a_wishlist():
    """Точность меряется на РЕАЛЬНОМ потоке, а не на придуманном списке.

    Первая версия фильтра показывала «95,3% полноты, 0% ложных» — на списке из
    18 тем, написанных руками. На живом потоке 4 августа (2167 записей за сутки,
    113 кандидатов размечены чтением) точность оказалась 35%: правило считало
    сделками «объём торгов на Мосбирже», «курс юаня вырос на копейку», «цена
    Brent ниже $81». Ручной список этого класса ошибок не содержал вовсе.

    Разметка лежит в `live_labels.json` и коммитится: без неё замер
    невоспроизводим, а «стало лучше» — не проверяемое утверждение.
    """
    labels = json.loads((ROOT / "pipeline" / "ingest" / "live_labels.json").read_text(encoding="utf-8"))
    items = labels["items"]
    assert len(items) >= 100, "разметка живого потока подозрительно мала"

    kept = [x for x in items if classify.looks_like_deal(x["title"], x["summary"])]
    deals = [x for x in kept if x["label"] == "deal"]
    junk = [x for x in kept if x["label"] == "no"]
    precision = len(deals) / len(kept)
    assert precision >= 0.70, (
        f"точность на живом потоке упала до {precision:.0%}: "
        f"мусор {[x['title'][:60] for x in junk][:5]}")

    # Полнота важнее точности: пропущенная сделка — это то, ради чего платформа
    # существует, а лишний кандидат всего лишь уходит человеку на решение.
    missed = [x for x in items if x["label"] == "deal"
              and not classify.looks_like_deal(x["title"], x["summary"])]
    assert not missed, f"фильтр перестал видеть настоящие сделки: {[x['title'][:60] for x in missed]}"


def test_exchange_trading_is_not_an_auction():
    """«Торги» по-русски — и продажа с молотка, и биржевые торги.

    Голое слово было САМОЙ частой ложной сработкой живого потока. Но зарезать
    его целиком нельзя: «Роснефть выкупила Саянскхимпласт на торгах» — наш
    профильный случай, а «IPO GloraX на Мосбирже» — размещение. Первая версия
    правила зарубила 16 настоящих карточек базы именно на этих двух словах.
    """
    for junk in ("Объем торгов на СПБ Бирже снизился на 8,7% в июле",
                 "Курс юаня по итогам торгов вторника вырос на 1 копейку",
                 "Рынок акций РФ завершил торги вторника ростом, несмотря на негатив",
                 "Объем торгов на рынках Мосбиржи вырос более чем на 40% в июле"):
        assert not classify.looks_like_deal(junk), f"биржевые торги приняты за сделку: {junk}"
    for deal in ("Роснефть выкупила Саянскхимпласт на торгах за 30,3 млрд рублей",
                 "Росимущество выставило на торги спиртзавод «Амбер Талвис»",
                 "IPO девелопера GloraX (ПАО «Глоракс») на Московской бирже"):
        assert classify.looks_like_deal(deal), f"продажа с торгов не признана сделкой: {deal}"


def test_deal_sign_must_be_in_the_title():
    """Признак сделки ищется в заголовке; текст может только ОТКАЗАТЬ.

    Обзор, дайджест и аналитическая колонка всегда упоминают чужие сделки
    мимоходом. Половина ложных срабатываний живого потока приходила именно
    оттуда: «Российский разработчик получил патент США» прошло из-за «вложил
    $5 млн в» в аннотации, «В Прикамье жителей проинформируют о выборах» — из-за
    «перешла к».
    """
    assert not classify.looks_like_deal(
        "Российский разработчик получил патент США на распознавание документов",
        "Ранее компания вложил $5 млн в развитие направления")
    # Обратное направление: текст не обязан подтверждать заголовок.
    assert classify.looks_like_deal("«Ригла» приобрела аптечную сеть «Здоровый город»", "")


def test_old_deal_is_posted_as_news_about_a_known_deal():
    """Пост про сделку месячной давности не выдаёт архив за сегодняшний рынок.

    4 августа в канал ушли посты о сделках 26 июня, 15 июня и 1 марта 2025 —
    каждый читался как объявление о свежей сделке. Причина в том, что правило
    смотрело, видел ли карточку КАНАЛ, а не что нового узнали МЫ: у карточки из
    бэклога обогащение дописало источник, и она ушла первым постом.
    """
    from datetime import date
    today = date(2026, 8, 4)
    old = {"id": "x1", "date": "2026-06-26", "title": "Свеза приобрела упаковочный завод",
           "ind": "Фармацевтика", "src": [["Ъ", "http://a/b"]]}
    text = format_post.render(old, {}, updates=["добавлен источник"], today=today)
    assert "Новое о сделке" in text, "старая сделка подана как свежая новость"
    assert "июнь 2026" in text, "не названа дата самой сделки"
    assert "Что стало известно: добавлен источник" in text, "не сказано, что именно добавилось"

    fresh = dict(old, date="2026-08-01")
    assert "Новое о сделке" not in format_post.render(fresh, {}, today=today), \
        "свежая сделка не должна получать шапку про архив"

    # Год без месяца свежим не считается: не зная месяца, объявлять сделку
    # сегодняшней нельзя.
    assert "Новое о сделке" in format_post.render(dict(old, date="2026"), {}, today=today)


def test_industry_is_read_from_the_deal_itself():
    """Отрасль перестала быть замкнутым кругом.

    Она бралась только у профиля компании, а у новой компании профиля нет и не
    будет, пока карточка не попадёт в базу. Из-за этого «пустить» было равно
    нулю ВСЕГДА — даже со снятым тормозом E9 все 113 черновиков живого потока
    упирались в «отрасль не определилась».
    """
    import draft
    assert draft.industry_for("«Ригла» приобрела аптечную сеть «Здоровый город»", {}) == "Фармацевтика"
    assert draft.industry_for("«Дом.РФ» приобрел бизнес-центр «Обсидиан»", {}) == "Недвижимость"
    assert draft.industry_for("«Тантор Лабс» купил права на СУБД «Персей»", {}) == "ИТ и интернет"
    # Молчание — допустимый ответ: выдуманная отрасль хуже пустой.
    assert draft.industry_by_words("«Альфа» купила «Бету»") is None


def test_industry_rule_is_measured_on_the_base():
    """Словарь отраслей проверяется на 1538 карточках с известной отраслью.

    Замер 4 августа: покрытие 74%, точность 84,5%. Выше согласованности
    собственной разметки правило не прыгнет — «аэропорт» в базе размечен как
    «Транспорт и логистика» 5 раз и как «Порты и инфраструктура» 5 раз.
    """
    import draft
    base = json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))
    deals = [d for d in base["deals"] if d.get("ind") and d["ind"] != "Не определена"]
    hit = fired = 0
    for d in deals:
        got = draft.industry_for(str(d.get("title") or ""), base["companies"])
        if not got:
            continue
        fired += 1
        hit += (got == d["ind"])
    coverage, precision = fired / len(deals), hit / max(fired, 1)
    assert coverage >= 0.65, f"покрытие правила отрасли упало до {coverage:.0%}"
    assert precision >= 0.78, f"точность правила отрасли упала до {precision:.0%}"


def test_industry_stem_is_not_found_inside_another_word():
    """Ствол словаря отраслей обязан быть отдельным словом.

    Без границы слова `рудник` совпадал внутри слова «сотрудники», `сельхоз` —
    внутри «Россельхознадзор», `телеком` — внутри «Ростелеком», `edtech` —
    внутри «MedTech». На живом потоке 4 августа (2167 записей) таких
    срабатываний внутри чужого слова было 65, и почти все — «сотрудники» ->
    «ГМК и добыча»: любая новость со словом «сотрудники» получала отрасль
    горнодобычи. На вычищенной базе дефект не виден вовсе, поэтому проверка
    написана по сырым фразам, а не по заголовкам карточек.
    """
    import draft
    for noise in ("сотрудники компании", "Россельхознадзор запретил ввоз",
                  "«Ростелеком» и «Сбер» обсуждают", "ветроэнергетических установок",
                  "MedTech-стартап Checkme", "союз автостраховщиков"):
        assert draft.industry_by_words(noise) is None, noise
    # Составные слова, где ствол стоит вторым, выписаны в словаре явно.
    for phrase, ind in (("завод железобетонных панелей", "Строительство"),
                        ("Окская судоверфь", "Машиностроение"),
                        ("рудник «Пионер»", "ГМК и добыча"),
                        ("телеком-оператор", "Телеком")):
        assert draft.industry_by_words(phrase) == ind, phrase


def test_buyer_is_found_when_the_verb_carries_a_prefix():
    """«Покупает» четыре прогона было невидимым для разбора сторон.

    `\\bкуп…` требует границы слова перед «куп», а в слове «покупает» перед ним
    стоит приставка — границы там нет. Тот же класс, что `^не\\s+раскры\\b` и
    `продавц\\w*`, не совпадающий со словом «Продавец»: правило молчит, а замер
    выглядит законченным. На базе это 40 заголовков с известным покупателем.
    """
    import draft
    assert draft.guess_parties("Selectel покупает облачного провайдера servers.ru")[0] == "Selectel"
    assert draft.guess_parties("VK покупает сеть школ английского языка Ufirst")[0] == "VK"
    # Существительное «покупку» глаголом не считается: «рассматривает покупку»
    # — это слух, а не сделка.
    assert draft.BUY_VERB.search("рассматривает покупку актива") is None


def test_buyer_is_found_when_the_action_is_a_noun():
    """«Закрыла сделку по покупке» — та же покупка, только существительным.

    Ровно так написан заголовок mergers.ru про «Риглу» и «Здоровый город»,
    из-за которого сделка неделю пролежала в очереди «на решение». Служебные
    глаголы берутся ТОЛЬКО завершающие: «изучает возможность покупки» —
    по-прежнему молчание.
    """
    import draft
    buyer, asset, _ = draft.guess_parties(
        "Группа «Ригла-Здравсити» закрыла сделку по покупке сети «Здоровый город» "
        "в Воронежской области")
    assert buyer == "«Ригла-Здравсити»" and asset.startswith("сети «Здоровый город»")
    assert draft.guess_parties("Freedom Holding закрыл сделку по покупке TurkishBank") \
        == ("Freedom Holding", "TurkishBank", None)
    for rumour in ("Bloomberg: AstraZeneca изучает возможность покупки Bristol Myers Squibb",
                   "ГК Merlion рассматривает покупку производителя техники Kuppersberg"):
        assert draft.guess_parties(rumour)[0] is None, rumour


def test_a_party_is_a_name_not_a_sentence():
    """Кусок обзорной статьи стороной сделки не становится.

    «Пошли в „отказ". Кто и почему продаёт пункты выдачи Wildberries» — это
    обзор, и «продаёт» стоит в нём после КОНЦА первого предложения. Если такой
    кусок записать продавцом, в базе появится карточка, у которой сторона
    сделки — заголовок статьи. Границу предложения ищем правилом «точка,
    пробел, заглавная»: список сокращений ненадёжен («18,8 млрд руб.»,
    «Fortum B.V.»), а это правило ошибается в безопасную сторону.
    """
    import draft
    assert draft.guess_parties(
        "Пошли в «отказ». Кто и почему продает пункты выдачи заказов "
        "Wildberries в Челябинске")[2] is None
    assert draft._named("новому собственнику") is None
    # …но точка внутри имени концом предложения не считается.
    assert draft._named("Fortum Russia B.V.") == "Fortum Russia B.V."
    assert draft._named("ООО «Дом.РФ»") == "ООО «Дом.РФ»"


def test_party_rules_are_measured_on_the_base(base):
    """Правила сторон меряются на выверенных карточках, а не на глаз.

    Замер 5 августа: покупатель 733 попал / 79 ошибся, продавец 306 / 11.
    Большая часть «ошибок» — наша же линейка: «Selectel» против «ООО
    «Селектел»», «Агрохолдинг „Таврос"» против «ГК „Таврос"». Порог держит
    ошибку дешевле молчания: если точность падает, правило стало выдумывать.
    """
    import draft
    comps = base["companies"]

    def same(a, b):
        norm = lambda s: re.sub(r"[«»\"'(),.\s]", "", str(s or "")).lower()
        return norm(a) == norm(b) or norm(a) in norm(b) or norm(b) in norm(a)

    hit = miss = 0
    for d in base["deals"]:
        guess = draft.guess_parties(str(d.get("title") or ""))[0]
        truth = (comps.get(d.get("buyer")) or {}).get("name") or d.get("buyer_name")
        if not (guess and truth):
            continue
        hit += same(guess, truth)
        miss += not same(guess, truth)
    assert hit >= 700, f"полнота разбора покупателя упала до {hit}"
    assert hit / (hit + miss) >= 0.85, f"точность разбора покупателя {hit/(hit+miss):.0%}"


# ---------- проверка карточки чтением (review.py) ----------

def test_review_refuses_to_write_what_is_not_in_the_source():
    """Читающий переносит факт, а не формулирует его.

    Шаг проверки чтением опасен ровно тем, чем ценен: он позволяет записать в
    базу то, чего правило не увидело. Граница проверяемая — каждая правка несёт
    дословную цитату источника, и значение обязано быть из неё выводимо. Тест
    проверяет ЗАЩИТУ, а не таблицу: шесть заведомо неверных правок обязаны
    получить отказ, иначе шаг превращается в канал для выдумки.
    """
    import review
    base = json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in base["deals"]}
    inds, texts = review.industries(), review.source_texts()
    card = next(iter(cards.values()))
    quote = "Продавцом актива выступала сеть сервисных офисов Business Club."

    bad_fixes = [
        ("имя не из цитаты", dict(field="seller", old=card.get("seller"),
                                  new="Сбербанк", quote=quote)),
        ("год перенесён", dict(field="date", old="2026-08-03", new="2025-05-04",
                               quote="сделка была закрыта 4 мая")),
        ("дня нет в цитате", dict(field="date", old="2026-08-03", new="2026-05-07",
                                  quote="сделка была закрыта 4 мая")),
        ("отрасль без обоснования", dict(field="ind", old=card.get("ind"), new="Медиа",
                                         quote="JPMorgan продал акции «Роснефти»")),
        ("статус без подтверждения", dict(field="status", old=card.get("status"),
                                          new="Не состоялась",
                                          quote="Visa объявила о приобретении BioCatch.")),
    ]
    for name, fix in bad_fixes:
        fix = dict(fix, id=card["id"])
        reasons = review.check(fix, card, texts, base["companies"], inds)
        assert reasons, f"защита пропустила выдумку: {name}"

    # Выдуманная цитата ловится отдельно — но только пока сырьё лежит на диске.
    if texts:
        made_up = dict(id=card["id"], field="seller", old=card.get("seller"),
                       new="Business Club",
                       quote="Продавцом выступил Business Club, сумма 900 млн рублей.")
        assert review.check(made_up, card, texts, base["companies"], inds)


def test_review_table_is_applied_and_not_pending(base):
    """Таблица правок применена: сухой прогон обязан быть пустым.

    Если правка осталась неприменённой, `old` в таблице совпадёт с тем, что в
    базе, и следующий прогон запишет её повторно — либо, что хуже, таблица
    начнёт расходиться с базой и молча копить отказы.
    """
    import review
    # СМОТРЕТЬ НАДО ТУДА ЖЕ, КУДА ПИШЕТ САМ СКРИПТ. С 5 августа promote кладёт
    # прошедшую ворота карточку не в базу, а в static/data/pending.json, и
    # review.py правит оба множества (он их так и читает). Тест же знал только
    # базу — и первая же правка к карточке, ждущей решения основателей, роняла
    # его с «карточки нет в базе», хотя её там и не должно быть. Тот же класс,
    # что «проверка „чем дополнить" не должна быть уже, чем карточка».
    cards = {d["id"]: d for d in base["deals"]}
    pending_file = ROOT / "static" / "data" / "pending.json"
    if pending_file.exists():
        cards.update({c["id"]: c for c in
                      json.loads(pending_file.read_text(encoding="utf-8"))["cards"]})
    for fix in review.FIXES:
        card = cards.get(fix["id"])
        assert card, (f"карточки {fix['id']} нет ни в базе, ни в очереди "
                      f"предпросмотра — правку надо снять вместе с карточкой")
        # `src` дописывается в список, а не присваивается, поэтому «применено ли»
        # знает сам скрипт: сравнивать поле со значением правки тут нельзя.
        assert review.already_applied(fix, card), (
            f"{fix['id']}.{fix['field']}: правка из таблицы не применена к базе")


def test_gate_sees_cards_waiting_in_the_preview_queue(base):
    """Очередь модерации — это тоже уже описанные сделки.

    С 5 августа прошедшая ворота карточка ложится не в базу, а в pending.json и
    ждёт решения основателей. Индекс дублей при этом строился по одной базе —
    и второй прогон в те же сутки (перезапуск рутины, ручная проверка) снова
    пропускал те же черновики: 6 августа так задвоились бы 10 карточек из 11, а
    в группу ушли бы те же карточка и пост под новыми id. Тест держит границу с
    двух сторон: без очереди в индексе черновик проходит, с очередью — отвергнут
    как дубль. Односторонняя проверка пропустила бы правило, которое отвергает
    вообще всё.
    """
    import promote
    import match as matcher
    inds = promote.industries()
    # Имя вымышленное нарочно: тест держал буквальную сделку из pending.json
    # («Нейропоток»/Frozella) на день, когда она реально лежала только в
    # очереди, — а 6 августа владелец её одобрил, и она переехала в базу.
    # Премиса «в базе такой сделки нет» тут же стала ложной не из-за дефекта
    # ворот, а из-за того, что тест был завязан на реальные данные, которые
    # меняются. Вымышленное имя не столкнётся с базой никогда.
    draft = {
        "title": "«Ромашка-Тест» выкупила линию по производству тестовых "
                 "виджетов под брендом Плейсхолдер",
        "date": "2026-08-05", "status": "Закрыта", "type": "M&A",
        "ind": "Пищепром и напитки", "buyer_name": "«Ромашка-Тест»",
        "asset": "линию по производству тестовых виджетов под брендом Плейсхолдер",
        "src": [["web:kommersant.ru", "https://www.kommersant.ru/doc/0000000-test-fixture"]],
    }
    dup = "уже есть"

    idx = matcher.index_base(base["deals"], base.get("companies"),
                             base.get("match_keys"))
    bad, _ = promote.check(draft, base, idx, inds)
    assert not any(dup in r for r in bad), (
        "в базе такой сделки нет — отвергать как дубль нечему: %s" % bad)

    queued = [dict(draft, id="pending-1")]
    idx_with_queue = matcher.index_base(base["deals"] + queued,
                                        base.get("companies"),
                                        base.get("match_keys"))
    bad_again, _ = promote.check(draft, base, idx_with_queue, inds)
    assert any(dup in r for r in bad_again), (
        "черновик, уже лежащий в очереди предпросмотра, прошёл ворота второй раз")

    # А ЭТО — ПРОВОДКА, А НЕ МЕХАНИЗМ. Проверка выше собирает индекс руками и
    # потому переживёт откат правки в promote.main: она доказывает, что дубль
    # ЛОВИТСЯ, но не то, что очередь вообще доходит до индекса. Смотрим, из чего
    # main строит индекс на самом деле.
    seen = []
    real_index_base = matcher.index_base
    with tempfile.TemporaryDirectory() as tmp:
        drafts_dir = Path(tmp) / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "2026-08-06.json").write_text(
            json.dumps({"drafts": [draft]}, ensure_ascii=False), encoding="utf-8")
        pending_file = Path(tmp) / "pending.json"
        pending_file.write_text(json.dumps({"cards": queued}, ensure_ascii=False),
                                encoding="utf-8")
        old = (promote.DRAFTS, promote.PENDING, matcher.index_base)
        try:
            promote.DRAFTS, promote.PENDING = str(drafts_dir), str(pending_file)
            matcher.index_base = lambda deals, *a, **k: (
                seen.append([d.get("id") for d in deals]) or real_index_base(deals, *a, **k))
            promote.main(write=False)
        finally:
            promote.DRAFTS, promote.PENDING, matcher.index_base = old
    assert seen and "pending-1" in seen[0], (
        "promote.main строит индекс дублей без очереди предпросмотра — "
        "повторный прогон заведёт те же карточки заново")


def test_gate_holds_a_deal_with_no_russian_connection(base):
    """Платформа — про российский рынок, и поток приносит чужие сделки.

    3 августа ворота пропустили «Visa купила BioCatch» (США — Израиль) и
    американский Smallest.ai. Признак измерен на 1551 карточке базы: подтвердить
    российский рынок он не может у 4 (0,26%), и лишь ДВЕ из них действительно
    чужие — остальные наши, просто написаны латиницей («MTS StartUp Hub»).
    Поэтому это «на решение», а не отказ: терять сделку молча дороже, чем
    показать четыре карточки человеку за три года.
    """
    import promote
    names = promote.profile_names(base["companies"])
    for foreign in ("Visa купила BioCatch за $2,4 млрд для защиты от кибермошенничества",
                    "TotalEnergies купит у Shell европейские активы в Европе",
                    "Bloomberg: AstraZeneca изучает возможность покупки Bristol Myers Squibb"):
        assert promote.russian_evidence({"title": foreign}, names) is None, foreign
    # Кириллица в ПРОЗЕ заголовка доказательством не является — она есть и у
    # «Visa купила BioCatch». Считаются только имена собственные и маркеры.
    for ours in ("ЭТМ приобрел АВС Электро",
                 "«Лента» покупает розничную сеть «Молл» в Челябинской области",
                 "ВТБ создаёт агрохолдинг на базе национализированных сельхозактивов",
                 "Mars продаёт завод соусов в Луховицах"):
        assert promote.russian_evidence({"title": ours}, names), ours


def test_russian_evidence_rule_is_measured_on_the_base(base):
    """Правило прогоняется по УЖЕ ЛЕЖАЩИМ данным: сколько своих же оно отвергает.

    Фильтр на вход, отвергающий заметную долю собственной базы, требует от
    новых сделок того, чего мы сами не делали. Порог 1% выбран по замеру:
    5 августа правило не смогло подтвердить российский рынок у 4 карточек
    из 1551 (0,26%).
    """
    import promote
    names = promote.profile_names(base["companies"])
    unproven = [d for d in base["deals"] if not promote.russian_evidence(d, names)]
    share = len(unproven) / len(base["deals"])
    assert share <= 0.01, (
        f"правило не подтверждает российский рынок у {share:.1%} собственной базы: "
        + "; ".join(str(d.get("title"))[:60] for d in unproven[:5]))


def test_packaging_is_its_own_industry(base):
    """Упаковка — отдельная отрасль, и это следствие замера, а не вкуса.

    До 5 августа отрасли «Производство тары» не было, и 14 карточек про упаковку
    лежали в ЧЕТЫРЁХ разных: «Химия и удобрения» 6, «Пищепром и напитки» 4,
    «Потребительские товары» 2, «Фармацевтика» 1. Разнобой был не небрежностью
    разметчика, а признаком нехватки категории: сделка про завод упаковки
    попадала то в химию (из чего сделана), то в пищепром (что в неё кладут), то
    в потребительские товары (кто в итоге покупает).

    Граница проведена по продукту: производит саму упаковку — сюда; сырьё и
    краски ДЛЯ упаковки, а также переработка отходов упаковки обратно в сырьё —
    остаются химией.
    """
    import draft
    for phrase in ("выпускает в Уфе пластиковую упаковку",
                   "Центр фармацевтической упаковки",
                   "три завода по производству упаковки",
                   "производство тары для агрохимии",
                   "производителя БОПП-пленки Manucor",
                   "гофрокартонный комбинат"):
        assert draft.industry_by_words(phrase) == "Производство тары", phrase
    # Сырьё и переработка отходов — не тара.
    assert draft.industry_by_words("завод по переработке пластика") == "Химия и удобрения"
    # Настоящий пищепром правило не забирает.
    assert draft.industry_by_words("молочный комбинат") == "Пищепром и напитки"
    assert draft.industry_by_words("хлебозавод в Подмосковье") == "Пищепром и напитки"
    # «Тара» не должна ловиться внутри «миноритарный», «санитарный»,
    # «депозитарный» — та же болезнь, что `рудник` в слове «сотрудники».
    assert draft.industry_by_words("миноритарный акционер") is None
    assert draft.industry_by_words("санитарная авиация") is None
    # «Депозитарные расписки» — это рынок ценных бумаг, но никак не тара.
    assert draft.industry_by_words("депозитарные расписки") == "Рынок ценных бумаг"

    # Отрасль объявлена в интерфейсе и реально используется: значение, которым
    # не помечено ничего, — непроверенный код (урок про «Не определена»).
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert '"Производство тары"' in html
    used = [d for d in base["deals"] if d.get("ind") == "Производство тары"]
    assert len(used) >= 10, f"отраслью помечено всего {len(used)} карточек"


def test_same_story_from_two_outlets_is_one_console_message(base):
    """Одна новость в двух изданиях — одно сообщение в группу, не два.

    6 августа «аукцион по Рижскому вокзалу не состоялся» пришёл из «Ведомостей»
    и «Коммерсанта» двумя одинаковыми сообщениями — владельцу пришлось решать
    дважды. Второй черновик с тем же названием в кавычках помечается
    `dup_in_batch` и в группу не идёт, но в hold-файле остаётся.
    """
    import promote
    hold_files = sorted(Path("data/inbox/hold").glob("2026-08-*.json"))
    assert hold_files, "нет hold-файла для проверки"
    drafts = json.loads(hold_files[-1].read_text(encoding="utf-8"))["drafts"]
    dups = [d for d in drafts if d.get("dup_in_batch")]
    # Свойство машинное, а не про конкретную сделку: у каждого помеченного
    # дубля обязан существовать «оригинал» с общим названием в кавычках,
    # который в группу ушёл (не помечен).
    import match as matcher
    for dup in dups:
        names = matcher.quoted(str(dup.get("title")))
        twin = [d for d in drafts if not d.get("dup_in_batch")
                and matcher.quoted_common(matcher.quoted(str(d.get("title"))), names)]
        assert twin, f"{dup.get('draft_id')}: помечен дублем, а оригинала нет"


def test_raw_console_remembers_the_news_not_the_draft_id(monkeypatch):
    """«Не сделка» и «уже показывали» помнятся по ЗАГОЛОВКУ, не по draft_id.

    Одна и та же новость назавтра приходит с новым draft_id: Рижский вокзал
    партнёр выкидывал трижды за два дня, «издание Гоголя» и Atomic dohaeris
    показались в консоли повторно. Память по id помнит прогон, память по
    заголовку — новость.
    """
    import promote
    import send_drafts
    drafts = [
        {"draft_id": "d-new-1", "title": "РЖД снова выставила Рижский вокзал на торги",
         "hold_reasons": ["не установлен предмет сделки"]},
        {"draft_id": "d-new-2", "title": "Совершенно новая сделка про завод",
         "hold_reasons": ["не установлен предмет сделки"]},
    ]
    state = {"decided_raw": {}, "sent_raw": [],
             "raw_titles": {promote.raw_key(drafts[0]["title"]): "drop"}}
    monkeypatch.setattr(send_drafts, "latest_hold_drafts", lambda: drafts)
    monkeypatch.setattr(send_drafts, "site_pending_ids", lambda: None)
    monkeypatch.setattr(send_drafts.promote, "load_state", lambda: state)
    plan, _p, _s, _deferred, _postponed, _foreign = send_drafts.build_plan()
    raw_titles = [item.get("title") for _t, _kb, (kind, item, _m) in plan if kind == "raw"]
    assert drafts[1]["title"] in raw_titles
    assert drafts[0]["title"] not in raw_titles, \
        "новость, выкинутая по заголовку, показана снова под новым draft_id"


def test_raw_console_hides_foreign_only_deals(monkeypatch):
    """Иностранный контур без российского элемента в консоль не носим.

    Решение владельца 5–6 августа: такие сделки не публикуем. Сырьё по
    молчанию не публикуется никогда, так что скрыть его безопасно; черновик
    остаётся в hold-файле, а вывод прогона называет число скрытых — молчащий
    предел читался бы как «это всё».
    """
    import send_drafts
    drafts = [
        {"draft_id": "d-f-1",
         "title": "Atomic dohaeris: стартап привлек $1 млрд на компактные реакторы",
         "hold_reasons": ["не названа ни одна сторона — ни покупатель, ни продавец",
                          "не видно связи с российским рынком — стороны и предмет "
                          "названы латиницей, российских признаков нет"]},
    ]
    monkeypatch.setattr(send_drafts, "latest_hold_drafts", lambda: drafts)
    monkeypatch.setattr(send_drafts, "site_pending_ids", lambda: None)
    monkeypatch.setattr(send_drafts.promote, "load_state",
                        lambda: {"decided_raw": {}, "sent_raw": []})
    plan, _p, _s, _deferred, _postponed, foreign = send_drafts.build_plan()
    assert foreign == 1
    assert not [1 for _t, _kb, (kind, _i, _m) in plan if kind == "raw"], \
        "иностранный черновик всё равно попал в план рассылки"


def test_classifier_rejects_live_console_junk():
    """Госзакупки, советы, антиквариат и операции Минфина — не кандидаты.

    Все четыре примера — живой поток 5–6 августа, дошедший до консоли
    основателей («как это вообще сюда попадает»). Обратная сторона проверена
    тем же тестом: тендерное предложение о выкупе акций (buyout offer) и
    раунд стартапа, АВТОМАТИЗИРУЮЩЕГО закупки, — настоящие сделки, и первая
    версия правила их зарубила.
    """
    import classify
    junk = [
        "В Петербурге ещё раз попытаются закупить автобусы особо большого класса",
        "Названы главные юридические риски при покупке жилья за границей",
        "Прижизненное издание Гоголя из типографии в Петербурге продают за 3,5 млн",
        "Минфин увеличит ежедневные покупки валюты на 20%",
    ]
    for t in junk:
        assert not classify.looks_like_deal(t), "мусор прошёл фильтр: %s" % t
    real = [
        "VEON: обязательное тендерное предложение о выкупе 42,31% акций "
        "Global Telecom Holding (GTH) за $600 млн",
        "Привлечение инвестиций раунда А российским сервисом автоматизации "
        "B2B-закупок Bidzaar ($2 млн)",
        "Роснефть выкупила Саянскхимпласт на торгах",
    ]
    for t in real:
        assert classify.looks_like_deal(t), "настоящая сделка отвергнута: %s" % t
