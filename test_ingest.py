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

import casing                 # noqa: E402
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


def test_filter_rejects_a_company_buying_back_its_own_bonds():
    """Выкуп компанией СОБСТВЕННЫХ облигаций по оферте — казначейская
    операция с долгом, не сделка со сменой контроля: эмитент не может
    купить сам себя. Найдено 21 августа — карточка «Норникель выкупил по
    оферте... облигаций» дошла до pending.json с buyer=эмитент,
    asset=сами облигации (бессмыслица). Выкуп ДОЛИ/АКЦИЙ (buyback) —
    профильная сделка и должен по-прежнему проходить фильтр."""
    assert not classify.looks_like_deal(
        '«Норникель» выкупил по оферте 95,5% выпуска облигаций '
        'с погашением в мае 2030 г. на $477,65 млн')
    assert classify.looks_like_deal('«Норникель» выкупил 10% собственных акций')


def test_filter_rejects_political_rhetoric_using_business_words_metaphorically():
    """Найдено 22 августа: владелец увидел в консоли «сомнительных»
    «"Единая Россия" консолидирует общество, заявил Путин» и «Лавров:
    Россия избавилась от тех, кто считает СВО "чужой войной"» — оба слова
    («консолидир», «избавилась от») законные признаки сделки для настоящих
    заголовков («консолидировала пакет акций», «избавилась от непрофильных
    активов»), но здесь объект метафоры — общество/люди, а не бизнес.
    Проверяем, что слова остаются рабочими для реальных сделок."""
    assert not classify.looks_like_deal('«Единая Россия» консолидирует общество, заявил Путин')
    assert not classify.looks_like_deal(
        'Лавров: Россия избавилась от тех, кто считает СВО «чужой войной»')
    assert classify.looks_like_deal('«Северсталь» консолидировала 100% ЧТПЗ')
    assert classify.looks_like_deal('Компания избавилась от непрофильных активов, продав завод')


# ---------- сопоставление «новое или уже есть» ----------

def test_match_finds_the_same_deal(base):
    """Заголовок карточки обязан находить сам себя, иначе правило слепое."""
    idx = matcher.index_base(base["deals"])
    deal = next(d for d in base["deals"] if len(matcher.stems(d.get("title"))) >= 4)
    found, why = matcher.match(
        {"title": deal["title"], "date": deal["date"], "url": None}, idx)
    assert found == deal["id"], f"{deal['id']} не нашёл сам себя ({why})"


def test_amount_does_not_cross_a_sentence_boundary():
    """Год в конце предложения не должен склеиваться со следующим числом.

    16 августа `triage.py` упал с ValueError на заголовке телеграм-канала
    «...на 15 августа 2026. 2,968 млн рублей...»: старый шаблон
    `[\\d\\s.,]*` не знал, что «. » — конец предложения, и склеил «2026» с
    «2,968» в одно число «2026.2,968», у которого при разборе оказывалось
    две точки подряд — `float()` падал. Замер по всей базе и всему кэшу
    притока (11164 заголовка): пострадал только этот один.
    """
    assert matcher.amount(
        '💼 Мой портфель акций на 15 августа 2026. 2,968 млн рублей. '
        'Покупка акций под пассивный доход') == 2.968
    assert matcher.amount('сделка оценивается в 12,5 млн долларов') == 12.5
    assert matcher.amount('выкупили за 18 500 млн рублей') == 18500
    assert matcher.amount('сумма составила 1.5 млрд рублей') == 1500


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


def test_draft_event_note_does_not_cut_a_word_in_half():
    """`events[].note` резался ровно на 260-м знаке — 31 из 79 note по базе

    обрывались в этом диапазоне буквально на полуслове (пример: карточка
    ALMI Partner, «…«Башк»), и обрыв ничем не был помечен. `truncate_note()`
    режет по границе слова и ставит «…», чтобы читатель видел обрыв, а не
    принимал его за короткий, но полный текст.
    """
    import draft
    prefix = "A" * 255
    text = prefix + " Башкортостана далее ещё текст сверх лимита длиной"
    assert text[:260].rstrip(" ,;:-—").endswith("Башк"), "тест сам не бьёт по границе слова"
    result = draft.truncate_note(text)
    assert result.endswith("…")
    assert not result.rstrip("…").endswith("Башк"), "слово всё ещё режется пополам"
    short = "Короткий текст без обрыва."
    assert draft.truncate_note(short) == short


def test_draft_error_rate_stays_low(base):
    """Разбор ошибается реже, чем молчит: замер на 1333 выверенных карточках.

    Пороги — сторож от ухудшения: на прогоне 47 ошибка составила 3% у продавца
    и 10% у покупателя. Если правило станет смелее и начнёт врать, тест упадёт.

    ЗАМЕР СРАВНИВАЕТ ТО, ЧТО СРАВНИМО (урок CLAUDE.md). Строгий substring-
    компаратор не различал «Романа Абрамовича» и «Роман Абрамов, Александр
    Абрамов и партнёры» как совпадение — оба верно называют продавца, просто
    один в косвенном падеже, а другой в перечислении. По мере роста базы
    дочитанных карточек (кампания G9) такие пары стали попадаться чаще, и
    ошибка перевалила за порог не потому, что `guess_parties()` стал хуже
    угадывать, а потому что линейка перестала их различать. Используем ту же
    словную проверку на падеж, что уже проверена в review.py
    (`_same_word` — общее начало ≥3 знаков и ≥60% длины короткого слова):
    каждое слово короткой фразы обязано найтись похожим словом в длинной.
    Замер после правки — 10 расхождений на 326 (3,1%), совпадает с
    исторической цифрой прогона 47; из них видно, что осталось —
    транслитерация (ИСТ/ICT Holding, Softline/«Софтлайн»), аббревиатуры без
    расшифровки (СГК, JSS) и по-настоящему кривые извлечения («ВТБ под
    Домодедовым» вместо «Группа ВТБ») — то есть остаток объясним, а не
    натянут заменой линейки под удобный результат.
    """
    import draft
    import review
    comps = base["companies"]
    wrong = {"buyer": 0, "seller": 0}
    said = {"buyer": 0, "seller": 0}

    def words(s):
        return [w for w in re.split(r"[^\wЀ-ӿ]+", str(s or ""), flags=re.I) if len(w) > 1]

    def same(a, b):
        wa, wb = words(a), words(b)
        if not wa or not wb:
            return False
        short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
        return all(any(review._same_word(sw, lw) for lw in long_) for sw in short)

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


def test_to_card_resolves_telegram_source_label_not_the_feed_id():
    """`tg:rusven` не должен доехать до экрана — как раньше не доезжал `web:`.

    Замечание владельца 6 августа починило `web:kommersant.ru` в `src`, но
    условие в `to_card()` было завязано на префикс `web:` — сырьё «на решение»
    (кнопка «это сделка — в работу») приходит с префиксом `tg:` (внутренний
    тег ленты Telegram-канала), и то же условие его пропускало: карточка
    Wegosty/rusven 21 августа несла бы «tg:rusven» вместо «Телеграм-канал:
    Русский Венчур». Резолвить обязан сам факт, что ссылка http(s), а не то,
    каким тегом её пометила лента.
    """
    import promote
    draft = {"title": "Компания «Тест-Ню» привлекла инвестиции",
             "date": "2026-08-13", "ind": "Искусственный интеллект",
             "asset": "«Тест-Ню»",
             "src": [["tg:rusven", "https://t.me/rusven/7666"]],
             "events": [{"kind": "closed", "date": "2026-08-13", "title": "…",
                         "note": "…", "source": ["tg:rusven", "https://t.me/rusven/7666"]}]}
    card = promote.to_card(draft, "gtest0002")
    assert card["src"][0][0] == "Телеграм-канал: Русский Венчур", card["src"]
    assert card["events"][0]["source"][0] == "Телеграм-канал: Русский Венчур"


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


# ---------- вехи в канале (раздел A, 22 августа) ----------

def test_render_milestone_uses_the_snapshot_not_live_fields():
    """Пост-веха обязан показывать то, что было известно НА МОМЕНТ ЭТОГО
    ЭТАПА (снимок события), а не текущие поля сделки — иначе, если карточку
    обогатили позже более точной суммой, старая веха молча «переписалась бы
    задним числом» при каждом повторном рендере."""
    deal = {"id": "d1", "title": "СЕГОДНЯШНИЙ заголовок сделки", "sum": "999 млрд ₽ (сегодня)"}
    event = {"kind": "closed", "headline": "Сделка закрыта",
             "snapshot": {"title": "Заголовок на момент этапа", "sum": "100 млн ₽ (на момент)",
                         "status": "Закрыта", "buyer": "ООО «Покупатель»"}}
    text = format_post.render_milestone(deal, event)
    assert "Заголовок на момент этапа" in text
    assert "100 млн ₽ (на момент)" in text
    assert "СЕГОДНЯШНИЙ" not in text and "999 млрд" not in text
    assert "ООО «Покупатель»" in text
    assert "/#/deal/d1" in text


def test_milestone_candidates_requires_headline_and_postworthy_kind():
    """Веха без заголовка (переходное состояние — снимок части 1 без headline,
    см. review.py) или неизвестного/не-постворси вида (negotiations/signed) —
    не кандидат: без заголовка нечего писать в посте, а «Переговоры» вообще
    не входят в список видов, достойных отдельного поста."""
    deals = [{"id": "d2", "events": [
        {"kind": "approval", "newsworthy": True, "headline": None, "id": "d2-approval"},
        {"kind": "negotiations", "newsworthy": True, "headline": "Заголовок", "id": "d2-negotiations"},
        {"kind": "closed", "newsworthy": True, "headline": "Сделка закрыта", "id": "d2-closed"},
    ]}]
    out = send_telegram.milestone_candidates(deals, {})
    assert [e["id"] for _d, e in out] == ["d2-closed"]


def test_milestone_candidates_dedups_by_stage_posts():
    """Веха, у которой `event['id']` уже есть в `stage_posts`, — больше не
    кандидат никогда, независимо от решений в консоли: тот же приём, что
    `posts[did]` для обычных постов, только на уровне одного события."""
    deals = [{"id": "d3", "events": [
        {"kind": "closed", "newsworthy": True, "headline": "Х", "id": "d3-closed"},
    ]}]
    assert send_telegram.milestone_candidates(deals, {}) != []
    assert send_telegram.milestone_candidates(deals, {"d3-closed": {"message_id": 1}}) == []


def test_milestone_decisions_parses_the_tilde_separated_id():
    """Разделитель `~` в `deal_id` решения — не двоеточие (занято разбором
    `mod:<id>:<вердикт>`) и не дефис (сами id сделок бывают с дефисами:
    `gmru-nspk-privatization` резался бы неоднозначно). `event_id`
    восстанавливается конкатенацией через дефис — тот же формат, что уже
    присваивает `mark_milestone()` в review.py."""
    decisions = [
        {"id": 1, "deal_id": "gmru-nspk-privatization~approval", "verdict": "post_yes"},
        {"id": 2, "deal_id": "plain-card-id", "verdict": "post_yes"},   # обычный пост — не веха
        {"id": 3, "deal_id": "d4~closed", "verdict": "post_no"},
    ]
    by_event = send_telegram.milestone_decisions(decisions)
    assert by_event == {
        "gmru-nspk-privatization-approval": ("post_yes", 1),
        "d4-closed": ("post_no", 3),
    }


def test_plan_milestones_sends_on_silence_holds_before_it_and_respects_post_no():
    """Три ветки одной функции: явное «пост в канал» — отправить сразу;
    молчание меньше суток — придержать; молчание МЕНЬШЕ суток, но БЕЗ
    решения, — тоже придержать; явное «без поста» — не отправлять никогда,
    но decision id всё равно идёт на consume (иначе кнопка будет спрашивать
    о себе на каждом прогоне)."""
    from datetime import datetime, timedelta, timezone
    now = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
    old = (now - timedelta(hours=30)).isoformat()
    fresh = (now - timedelta(hours=2)).isoformat()
    deals = [{"id": "d5", "events": [
        {"kind": "approval", "newsworthy": True, "headline": "Одобрено", "id": "d5-approval",
         "milestone_drafted_at": old},
        {"kind": "closed", "newsworthy": True, "headline": "Закрыто", "id": "d5-closed",
         "milestone_drafted_at": fresh},
    ]}, {"id": "d6", "events": [
        {"kind": "cancelled", "newsworthy": True, "headline": "Сорвалось", "id": "d6-cancelled",
         "milestone_drafted_at": old},
    ]}]
    decisions = [{"id": 9, "deal_id": "d6~cancelled", "verdict": "post_no"}]
    send, hold, discard_ids, sent_ids = send_telegram.plan_milestones(deals, {}, decisions, now)
    assert [e["id"] for _d, e in send] == ["d5-approval"], "истёкшее молчание без решения — отправить"
    hold_ids = {e["id"] for _d, e, *_ in hold}
    assert "d5-closed" in hold_ids, "молчание ещё не истекло — придержать"
    assert discard_ids == [9]
    assert sent_ids == []


def test_main_sends_an_approved_milestone_and_records_dedup(monkeypatch, tmp_path):
    """Сквозной прогон: явное решение «пост в канал» из консоли шлёт веху
    ОТДЕЛЬНЫМ сообщением (не правкой живого поста), записывает id в
    `telegram_milestones` и консуммирует решение — повторный прогон с теми
    же данными больше не считает эту веху кандидатом. Сама сделка НАРОЧНО
    без суммы/сторон (`sendable()` вернёт False) — иначе в этом же прогоне
    ушёл бы ещё и её обычный первый пост, и тест проверял бы два сообщения
    сразу вместо одной вехи."""
    deal = {"id": "dmilestone1", "title": "Сделка Х", "type": "M&A", "ind": "Не определена",
            "events": [{"kind": "closed", "newsworthy": True, "headline": "Сделка Х закрыта",
                       "id": "dmilestone1-closed",
                       "snapshot": {"title": "Сделка Х", "status": "Закрыта",
                                    "sum": "500 млн ₽", "buyer": "ООО «Покупатель Х»"},
                       "milestone_drafted_at": "2020-01-01T00:00:00+00:00"}]}
    real_data = {"deals": [deal], "companies": {}, "telegram_posts": {}, "telegram_milestones": {}}
    tmp_data = tmp_path / "deals_promoted.json"
    tmp_data.write_text(json.dumps(real_data), encoding="utf-8")
    monkeypatch.setattr(send_telegram, "DATA", str(tmp_data))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@channel")
    monkeypatch.setenv("MODERATION_TOKEN", "тайна")

    consumed = []
    monkeypatch.setattr(send_telegram.approve, "fetch_decisions",
                        lambda: ([{"id": 5, "deal_id": "%s~closed" % deal["id"], "verdict": "post_yes"}],
                                 ("https://site", "тайна")))
    monkeypatch.setattr(send_telegram.approve, "consume",
                        lambda handle, ids: consumed.extend(ids))

    fake = _FakeClient([{"ok": True, "result": {"message_id": 4242}}])
    monkeypatch.setattr(send_telegram, "_client", lambda: fake)

    send_telegram.main(write=True, ignore_pace=True)

    assert len(fake.calls) == 1
    url, payload = fake.calls[0]
    assert "sendMessage" in url
    assert "Сделка Х закрыта" in payload["text"]
    written = json.loads(tmp_data.read_text(encoding="utf-8"))
    assert written["telegram_milestones"]["%s-closed" % deal["id"]]["message_id"] == 4242
    assert consumed == [5]
    # ...и в живом посте сделки НИЧЕГО не менялось — это отдельное сообщение.
    assert not written["telegram_posts"]


def test_send_milestone_drafts_uses_a_tilde_separated_callback():
    """Кнопки черновика вехи несут `deal_id~kind` — тот же вид id, который
    main.py режет по `~`, а не по `:` (занят) и не по `-` (id сделок сами
    бывают с дефисами)."""
    import send_milestone_drafts
    kb = send_milestone_drafts.milestone_keyboard("gmru-nspk-privatization", "approval")
    buttons = kb["inline_keyboard"][0]
    assert buttons[0]["callback_data"] == "mod:gmru-nspk-privatization~approval:post_ok"
    assert buttons[1]["callback_data"] == "mod:gmru-nspk-privatization~approval:post_no"


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
    for hour in (0, 3, 7, 9, 21, 22, 23):
        allowed, why = sender.pace_allowance(5, datetime(2026, 8, 4, hour, 0, tzinfo=sender.MSK))
        assert allowed == 0, f"в {hour}:00 отправили бы {allowed} — окно нарушено ({why})"
    for hour in (10, 13, 18, 20):
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
    at2030, _ = sender.pace_allowance(3, datetime(2026, 8, 4, 20, 30, tzinfo=sender.MSK))
    assert at2030 == 3, "остаток очереди не ушёл в последнем слоте"
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
    fresh_text = format_post.render(fresh, {}, today=today)
    assert "Новое о сделке" not in fresh_text and "Сделка из базы" not in fresh_text, \
        "свежая сделка не должна получать шапку про архив"

    # Год без месяца свежим не считается: не зная месяца, объявлять сделку
    # сегодняшней нельзя.
    assert "Сделка из базы" in format_post.render(dict(old, date="2026"), {}, today=today)

    # НОВИЗНУ ОБЕЩАЕМ, ТОЛЬКО ЕСЛИ ЕСТЬ ЧТО СКАЗАТЬ. 7 августа в канал ушёл пост
    # «Новое о сделке · май 2026» про бизнес-центр «Обсидиан», в котором про
    # новое не было ни слова, — владелец справедливо спросил, что же в нём
    # нового. Ответ: ничего, просто карточка впервые дошла до канала. Обещание
    # новизны без единого нового факта — это обман читателя, пусть и мелкий.
    silent = format_post.render(old, {}, today=today)          # старая, без updates
    assert "Новое о сделке" not in silent, "обещали новое, не сказав ни слова о нём"
    assert "Сделка из базы" in silent and "июнь 2026" in silent
    assert "Публикуем впервые" in silent, "не объяснили, почему сделка июня всплыла сегодня"

    # А дату появления карточки в базе называем, если она известна: это и есть
    # ответ на «почему я вижу это сегодня».
    dated = format_post.render(dict(old, added="2026-08-04"), {}, today=today)
    assert "карточка появилась в «Компасе» 4 августа 2026" in dated


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


def test_survey_and_trading_digest_headlines_are_not_a_party():
    """Доля демографической группы и обстоятельство места — не сторона сделки.

    14 августа ворота пропустили две карточки без единой настоящей сделки:
    «59% россиян покупают книги на маркетплейсах — исследование» (опросная
    статистика, покупателем стояло «59% россиян») и «На Петербургской бирже
    в первом полугодии продали 505 кг серебра» (сводка объёма торгов,
    продавцом стояло «На Петербургской бирже в первом полугодии» — предлог
    и обстоятельство места-времени, не имя). Замер по всей базе: НИ ОДИН
    настоящий buyer_name/seller не начинается ни с «N% строчное слово», ни
    с предлога перед словом (0 из 1571 в обоих случаях) — правило ничего не
    стоит.
    """
    import draft
    assert draft._named("59% россиян") is None
    assert draft._named("70% сотрудников") is None
    assert draft._named("На Петербургской бирже в первом полугодии") is None
    assert draft._named("В Курганской области") is None
    # …но доля предмета (после родового слова «акций»/«долей») не задета —
    # это не подлежащее, и `_named` его вообще не видит в такой роли.
    assert draft._named("ПСБ") == "ПСБ"
    assert draft._named("Все ставки против ЦБ") == "Все ставки против ЦБ"
    buyer, asset, seller = draft.guess_parties(
        "59% россиян покупают книги на маркетплейсах — исследование")
    assert buyer is None, buyer
    buyer, asset, seller = draft.guess_parties(
        "На Петербургской бирже в первом полугодии продали 505 кг серебра")
    assert seller is None, seller


def test_headline_label_before_colon_is_not_a_party():
    """«Тема: подробности» — ярлык жанра, а не подлежащее.

    16 августа ворота ПРОПУСТИЛИ «Акции, облигации, паи: как инвестировали
    кандидаты в Госдуму. Инфографика» — не сделку вовсе, а инфографику РБК.
    «как» перед глаголом покупки разобралось «покупателем», обрезанным ровно
    на двоеточии («Акции, облигации, паи: как»): весь кусок до двоеточия —
    тема-ярлык, не имя стороны. Тот же дефект — на «Nikkei: Sony и TSMC…» и
    «МИД РФ: Европа получила…» (атрибуция источника/подлежащее другой
    новости, тоже не сторона нашей сделки). Замер по всей базе: ни один
    настоящий buyer_name/seller не содержит двоеточия (0 из 1574).
    """
    import draft
    assert draft._named("Акции, облигации, паи: как") is None
    assert draft._named("Nikkei: Sony и TSMC") is None
    assert draft._named("МИД РФ: Европа") is None
    buyer, asset, seller = draft.guess_parties(
        "Акции, облигации, паи: как инвестировали кандидаты в Госдуму. Инфографика")
    assert buyer is None, buyer


def test_quote_cut_open_by_a_verb_is_not_a_party():
    """Заголовок-цитата обрывает голову ровно на открывающей кавычке.

    18 августа ворота пропустили «„Не купят — буду деактивировать". Что
    происходит с рынком ПВЗ маркетплейсов» — глагол покупки («купят») стоит
    ВНУТРИ цитаты-крючка, и голова обрезалась на «„Не» — открывающая кавычка
    без единой закрывающей в оставшемся куске. Отличается от вложенных
    названий («ООО «ТД «Нефтетехснаб»» и подобных, держит
    test_no_company_twins и смежные): те не начинаются с самой кавычки, тут
    же кавычка — первый символ. Замер по базе и кэшу притока (11648
    заголовков): 0 настоящих buyer_name/seller начинаются с незакрытой
    кавычки.
    """
    import draft
    assert draft._named("«Не") is None
    assert draft._named("«Компания") is None  # тоже незакрытая — не имя
    assert draft._named('ООО «ТД «Нефтетехснаб»') == 'ООО «ТД «Нефтетехснаб»'
    buyer, asset, seller = draft.guess_parties(
        "«Не купят — буду деактивировать». Что происходит с рынком ПВЗ маркетплейсов")
    assert buyer is None, buyer


def test_negated_verb_is_not_a_completed_transaction():
    """«Не продал» — это НЕ сделка, а отрицание сделки.

    19 августа ворота пропустили «Пашинян не продал абрикосы европейцам:
    как его курс на ЕС замучил фермеров Армении» — SELL_VERB находил
    «продал» и не проверял, что перед ним стоит «не»: продавцом записался
    «Пашинян не» (частица приклеилась к имени), предметом — обрывок
    заголовка после двоеточия. Источник сообщает об ОТСУТСТВИИ продажи, а
    не о сделке. Замер по базе и кэшу притока (14613 заголовков): 3
    заголовка с «не» перед глаголом покупки/продажи/инвестиции, и ни один
    не был бы настоящей сделкой.
    """
    import draft
    assert draft.guess_parties(
        "Пашинян не продал абрикосы европейцам: как его курс на ЕС "
        "замучил фермеров Армении") == (None, None, None)
    # Утвердительная форма по-прежнему разбирается.
    b, a, s = draft.guess_parties("Пашинян продал абрикосы европейцам")
    assert b is None and a == "абрикосы европейцам" and s == "Пашинян"


def test_residents_of_a_place_are_not_a_party():
    """«Жители X» — демографическая группа, а не сторона сделки.

    19 августа ворота пропустили «Жители Подмосковья за месяц купили почти
    22 млн кг мяса» — сводку розничных продаж, а не сделку; покупателем
    записался «Жители Подмосковья за месяц». Родня уже исключённой «N%
    демографической группы» («59% россиян покупают...»). Замер: 0 из 1571
    настоящих buyer_name/seller начинаются с «Жител…».
    """
    import draft
    assert draft._named("Жители Подмосковья за месяц") is None
    assert draft._named("Жительница Хабаровского края") is None
    buyer, asset, seller = draft.guess_parties(
        "Жители Подмосковья за месяц купили почти 22 млн кг мяса")
    assert buyer is None, buyer


def test_russians_as_a_group_are_not_a_party():
    """«Россияне купили…» — демонимическая группа, а не сторона сделки.

    21 августа ворота пропустили «Россияне купили в июле рекордные 549
    тыс. подержанных авто» — сводку вторичного рынка авто, а не сделку.
    Родня «Жителей X»; исключение — только форма множественного числа
    демонима («Россиян…»), а не «Россия»/«Российская Федерация», которая
    дважды в базе — законный продавец (приватизационные сделки).
    """
    import draft
    assert draft._named("Россияне") is None
    assert draft._named("Россиян") is None
    assert draft._named("Российская Федерация") == "Российская Федерация"
    buyer, asset, seller = draft.guess_parties(
        "Россияне купили в июле рекордные 549 тыс. подержанных авто: "
        "в топе продаж — машины Lada, Kia и Toyota")
    assert buyer is None, buyer


def test_player_transfer_is_not_ma():
    """Трансфер футболиста — не M&A, даже когда стороны звучат как компании.

    21 августа ворота пропустили «"Динамо" покупает форварда у
    "Индепендьенте"» — язык трансферов и M&A совпадает («купил», «продал»,
    «у»), но предмет здесь — футбольная позиция, а не актив или компания.
    Оба клуба разобрались бы верно как стороны в кавычках — проблема
    именно в предмете. Замер по базе (1565 карточек) и кэшу притока: 0
    настоящих asset начинаются с позиции футболиста.
    """
    import draft
    assert draft.guess_parties(
        '«Динамо» покупает форварда у «Индепендьенте», пишут СМИ'
    ) == (None, None, None)
    assert draft.guess_parties(
        'Итальянский клуб продал вратаря российскому «Спартаку»'
    ) == (None, None, None)
    # Настоящая M&A с похожим глаголом по-прежнему разбирается.
    b, a, s = draft.guess_parties('Selectel покупает облачного провайдера servers.ru')
    assert b == 'Selectel' and a == 'облачный провайдер servers.ru'


def test_farm_club_is_not_ma():
    """«Фарм-клуб» — спортивный термин в СТОРОНЕ сделки, не в предмете.

    21 августа ворота пропустили «Фарм-клуб "Сакраменто" приобрел права на
    Лахина» (РИА со ссылкой на NBA) — резервная команда баскетбольного
    клуба выкупила права на игрока, а не купила компанию. SPORTS_POSITION
    здесь не срабатывает (предмет — «права на Лахина», не футбольная
    позиция); спортивный термин стоит в buyer_name. Замер: 0 из 1565
    настоящих buyer_name/seller начинаются с «Фарм-клуб».
    """
    import draft
    assert draft._named('Фарм-клуб «Сакраменто»') is None
    buyer, asset, seller = draft.guess_parties(
        'Фарм-клуб «Сакраменто» приобрел права на Лахина')
    assert buyer is None, buyer


def test_spot_commodity_purchase_is_not_ma():
    """«Партия СПГ»/«партия нефти» — спотовая закупка товара, не M&A.

    21 августа ворота пропустили «Индия купила партию СПГ по рекордно
    высокой цене» (Lenta.ru со ссылкой на Bloomberg) — государственная
    компания Gail купила груз топлива на споте, а покупателем в заголовке
    стала целая СТРАНА, а не юрлицо. Стороны разобрались бы верно (страна
    выглядит именем), предмет — груз биржевого товара, не компания и не
    доля. Замер: 0 из 1567 настоящих asset в базе начинаются с
    «партия»/«партию» (омоним «Партия «Новые люди»» тоже не встречается в
    этой позиции).
    """
    import draft
    buyer, asset, seller = draft.guess_parties(
        'Индия купила партию СПГ по рекордно высокой цене')
    assert buyer is None, buyer
    # Настоящую M&A-сделку с обычным предметом правило не трогает.
    buyer, asset, seller = draft.guess_parties(
        'Selectel купил облачного провайдера servers.ru')
    assert buyer == 'Selectel', buyer


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
        norm = lambda s: re.sub(r"[«»\"'’(),.\s]", "", str(s or "")).lower()
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


def test_site_visible_matches_the_frontend_rule():
    """`review.site_visible()` обязана совпадать с `isDealShownOnSite()` из
    static/index.html — иначе замер очереди чтения снова примет архивные
    карточки 2017-2021 (191 из 197 «непрочитанных» 18 августа) за настоящую
    очередь, как уже однажды случилось."""
    import review
    assert review.site_min_year() == 2022
    assert review.site_visible({"date": "2022-01-01"}) is True
    assert review.site_visible({"date": "2021-12-31"}) is False
    assert review.site_visible({"date": "2017-05-03"}) is False
    assert review.site_visible({"date": "unknown"}) is True
    assert review.site_visible({}) is True


def test_review_flags_cash_in_and_unlinked_party_without_blocking():
    """Подсказки review.py (18-19 августа, уроки ПСБ/«Атом» и «М.видео») —

    не блокируют запись, но обязаны сработать на всех сигналах, что нашли на
    живых карточках: допэмиссия в тексте при типе, который не «Инвестиция»
    (сначала проверялось только type==M&A — «М.видео» имела другой неверный
    тип и проскочила); сторона текстом, для которой уже есть профиль с точно
    таким именем; продавец текстом совпадает с предметом сделки (компания не
    может продавать саму себя). Проверено и на честном случае: карточка без
    этих признаков не получает подсказок — иначе консоль, куда валят всё,
    быстро перестанут читать.
    """
    import review
    companies = {"gdc4235da": {"name": "Банк «Траст»"}, "g444cac01": {"name": "М.Видео"}}

    cash_in_card = dict(type="M&A", seller=None, seller_id=None,
                         extra="Пакет выкуплен в рамках дополнительной эмиссии за денежные средства.")
    hints = review.advisories(cash_in_card, companies)
    assert any("cash-in" in h or "Инвестиция" in h for h in hints), "не поймали допэмиссию под видом M&A"

    wrong_type_card = dict(type="Финансирование · структурная сделка", seller="ПАО «М.видео»", seller_id=None,
                            target="g444cac01",
                            asset="дополнительный выпуск обыкновенных акций ПАО «М.видео» по закрытой подписке")
    hints = review.advisories(wrong_type_card, companies)
    assert any("cash-in" in h or "Инвестиция" in h for h in hints), \
        "не поймали допэмиссию под видом НЕ-M&A типа (карточка «М.видео»)"
    assert any("продавцом самой себя" in h for h in hints), \
        "не поймали продавца, совпадающего с предметом сделки"

    unlinked_card = dict(type="M&A", seller="Банк «Траст»", seller_id=None)
    hints = review.advisories(unlinked_card, companies)
    assert any("gdc4235da" in h for h in hints), "не поймали продавца текстом при готовом профиле"

    clean_card = dict(type="M&A", seller="Частное лицо, имя не раскрыто", seller_id=None,
                       extra="Сделка закрыта, сумма не раскрывается.")
    assert review.advisories(clean_card, companies) == [], "честная карточка не должна получать подсказок"


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


def test_gate_remembers_a_card_discarded_by_source_url(capsys):
    """Выкинутая карточка не должна возвращаться под новым id.

    11 августа draft-файл с прошлого дня (промоут перечитывает ВСЕ файлы
    партии на каждом прогоне, а старые никто не чистит) принёс тот же
    черновик, что владелец накануне выкинул («RTP Global/Ahead Health»,
    тот же адрес t.me/rusven/7641) — карточка получила новый id и снова
    ушла на решение владельца, хотя решение уже было. Причина: `discard`
    снимал карточку из pending.json, но не оставлял памяти нигде — та же
    болезнь, что raw_titles/decided_raw для сырья решают на уровне
    черновика, а не уже прошедшей ворота карточки. `approve.py` теперь
    пишет `discarded_urls` при вердикте `discard`, `promote.py` фильтрует
    по нему ДО проверки на дубль (см. `test_gate_sees_cards_waiting_in_the_preview_queue`
    для дублей внутри одного прогона — это соседний, но другой случай:
    там очередь ещё жива, здесь она уже опустела)."""
    import promote
    marker_title = "«Ромашка-Тест» снова инвестировала в стартап Виджет"
    draft = {
        "title": marker_title,
        "date": "2026-08-05", "type": "Инвестиция", "ind": "ИТ и интернет",
        "buyer_name": "«Ромашка-Тест»", "asset": "стартап Виджет",
        "src": [["tg:test", "https://t.me/test-channel/999"]],
    }
    with tempfile.TemporaryDirectory() as tmp:
        drafts_dir = Path(tmp) / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "2026-08-05.json").write_text(
            json.dumps({"drafts": [draft]}, ensure_ascii=False), encoding="utf-8")
        pending_file = Path(tmp) / "pending.json"
        pending_file.write_text(json.dumps({"cards": []}, ensure_ascii=False),
                                encoding="utf-8")
        state_file = Path(tmp) / "moderation_state.json"
        state_file.write_text(json.dumps({
            "decided_raw": {}, "sent_raw": [], "raw_titles": {},
            "discarded_urls": {"https://t.me/test-channel/999":
                                {"id": "gold1", "title": "старое решение"}},
        }, ensure_ascii=False), encoding="utf-8")
        old = (promote.DRAFTS, promote.PENDING, promote.STATE)
        try:
            promote.DRAFTS, promote.PENDING, promote.STATE = (
                str(drafts_dir), str(pending_file), str(state_file))
            promote.main(write=False)
        finally:
            promote.DRAFTS, promote.PENDING, promote.STATE = old
    out = capsys.readouterr().out
    assert "Черновиков: 0" in out, (
        "черновик с адресом уже выкинутой карточки не отфильтрован до счёта: %s" % out)
    assert marker_title not in out, (
        "черновик с адресом уже выкинутой карточки прошёл ворота повторно: %s" % out)


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
                    "Bloomberg: AstraZeneca изучает возможность покупки Bristol Myers Squibb",
                    # 14 августа: «ЦБ» само по себе законное доказательство
                    # (см. ниже, «ВТБ»/акроним), но «ЦБ Кореи» — родительный
                    # падеж чужой страны сразу после аббревиатуры превращает
                    # её в голову ИНОСТРАННОГО учреждения того же типа, а не
                    # в наш регулятор.
                    "ЦБ Кореи впервые за 13 лет купил активы, связанные с золотом",
                    # 15 августа: обе карточки о продаже доли в «Ливерпуле»
                    # прошли ворота — «Ливерпуле»/«Ливерпуля» (транслитерация
                    # футбольного клуба/города в кавычках) и «Джеффа»/«Безоса»
                    # в косвенном падеже засчитывались за российское имя
                    # собственное. Сделка полностью британская.
                    "Консорциум с участием Джеффа Безоса договорился о покупке доли в «Ливерпуле»",
                    "Консорциум Безоса приобрел 30% акций «Ливерпуля»",
                    # «Информационного» (родительный падеж «информационный») —
                    # обычное прилагательное-описание типа учреждения, а не
                    # имя; всё название учреждения нероссийское (НАТО, ЕС).
                    "Грузинские власти продали с аукциона здание Информационного центра НАТО и ЕС",
                    # 18 августа: «Саудовская BinDawood купила обанкротившийся
                    # сырный завод E-Piim в Эстонии» — «Эстонии» прошло как
                    # имя собственное; сделка полностью саудовско-эстонская.
                    "Саудовская BinDawood купила обанкротившийся сырный завод E-Piim в Эстонии",
                    # Родня «„Не купят — буду деактивировать". Что происходит
                    # с рынком ПВЗ маркетплейсов» (18 августа) без самого ПВЗ
                    # (легитимной аббревиатуры «пункт выдачи заказов», она
                    # сама по себе — российский маркер): цитата-крючок в
                    # кавычках («Не» — первое слово) и «Что» (начало
                    # предложения после закрывающей кавычки) оба ловились как
                    # имя собственное кириллицей.
                    "«Не купят». Что происходит с рынком гаджетов",
                    # 18 августа: «Первый серийный электромобиль Ferrari Luce
                    # продали на аукционе за $40 млн» — после починки суммы
                    # (см. test_amount_does_not_cross_a_sentence_boundary,
                    # родственный класс в match.amount) карточка держалась на
                    # профиле базы «Первый» (девелопер, семья основателя
                    # «Марии-Ра») — слово встретилось в тексте как порядковое
                    # числительное, а не имя компании. Сделка — американский
                    # аукцион коллекционного автомобиля, к России отношения
                    # не имеет.
                    "Первый серийный электромобиль Ferrari Luce продали на аукционе "
                    "за $40 млн — в 63 раза дороже стартовой цены модели",
                    # 21 августа: «Марк Цукерберг приобрел старинный замок
                    # Странкалли в Ирландии» — «Цукерберг» уже исключён
                    # (NOT_RUSSIAN_PERSON), но следующим кандидатом прошло
                    # «Странкалли» (замок), а после его исключения — сама
                    # «Ирландия», которой не было в NOT_RUSSIAN_PLACE.
                    "Марк Цукерберг приобрел старинный замок Странкалли в Ирландии"):
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


def test_common_word_profile_name_is_not_a_market_signal(base):
    """Профиль компании, названный обычным словом, не годится в маркер рынка.

    18 августа «Первый серийный электромобиль Ferrari Luce продали на
    аукционе за $40 млн» (RM Sotheby's, США — ни одной российской стороны)
    прошло ворота через профиль базы «Первый» (девелопер, семья основателя
    «Марии-Ра»): слово встретилось как порядковое числительное, а не имя
    компании. Замер: без «первый» в списке ни одна карточка базы не теряет
    единственного доказательства (0 из 1562) — у всех, кому эта компания
    реально сторона, есть и другой признак.
    """
    import promote
    names = promote.profile_names(base["companies"])
    assert "первый" not in names
    d = {"title": "Первый серийный электромобиль Ferrari Luce продали на "
                   "аукционе за $40 млн — в 63 раза дороже стартовой цены модели",
         "asset": "на аукционе",
         "seller": "Первый серийный электромобиль Ferrari Luce"}
    assert promote.russian_evidence(d, names) is None


def test_sum_prefers_the_earlier_currency_in_the_sentence():
    """Первая по тексту сумма — цена сделки, а не её конвертация в скобках.

    18 августа «...продали на аукционе за $40 млн (около 3,38 млрд рублей)»
    (аукцион Ferrari, RM Sotheby's) бралась не первично названная сумма
    ($40 млн), а рублёвая конвертация в скобках — `SUM_RE` (число ПЕРЕД
    словом-валютой) проверялся раньше `SUM_RE_PRE` (число ПОСЛЕ значка $/€)
    безусловно, а не по тому, какое совпадение раньше по тексту. Заодно
    чинит независимый случай: «Alibaba продала игровое подразделение за
    $1,5 млрд» в потоке рядом с чужой рублёвой цифрой из соседней новости
    («...сумма составляет 15 тыс. ₽») — раньше бралась чужая цифра.
    """
    import draft
    assert draft.guess_sum(
        "Первый серийный экземпляр продали на аукционе RM Sotheby's за "
        "$40 млн (около 3,38 млрд рублей).") == "$40 млн"
    assert draft.guess_sum("12 млн ₽ (примерно $150 тыс.)") == "12 млн ₽"


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


def test_fish_industry_word_ignores_surnames_and_places():
    """«рыб» голым стволом не годится — измерено на живом потоке 21 августа.

    Карточка «Русская рыбная компания» / «Морская миля» (почасовой приток,
    21 августа) прошла ворота с ind=«Не определена»: словарь отраслей вообще
    не знал слова про рыбу и морепродукты. Первая попытка добавить голый
    ствол «рыб» без правой границы слова дала бы 11 ложных срабатываний на
    том же дне живого потока — фамилии («Рыбакина», «Рыбальченко»,
    «Рыбалкин», «Рыбальского») и топоним («Рыбинске») начинаются с тех же
    букв. Правило держит явные формы существительного с правой границей
    (рыба/рыбы/рыбу/рыбой/рыбе) и стволы с суффиксом, где границы не нужно
    (рыбн, рыболовств, рыбхоз, рыбозавод, рыбоперераб, рыбопромышленн,
    морепродукт).
    """
    import draft
    assert draft.industry_by_words("дистрибуторов рыбы и морепродуктов") == "Пищепром и напитки"
    assert draft.industry_by_words("рыбная продукция") == "Пищепром и напитки"
    assert draft.industry_by_words("рыболовство северного бассейна") == "Пищепром и напитки"
    for phrase in ("Елена Рыбакина выиграла турнир",
                   "Светлана Рыбальченко",
                   "в Рыбинске открылся завод",
                   "Иван Рыбалкин",
                   "Рыбальского осудили"):
        assert draft.industry_by_words(phrase) is None, phrase


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
    plan, _p, _s, _deferred, _postponed, _foreign, _unread = send_drafts.build_plan()
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
    plan, _p, _s, _deferred, _postponed, foreign, _unread = send_drafts.build_plan()
    assert foreign == 1
    assert not [1 for _t, _kb, (kind, _i, _m) in plan if kind == "raw"], \
        "иностранный черновик всё равно попал в план рассылки"


def test_console_withholds_unreviewed_cards(monkeypatch):
    """Непрочитанная карточка не уходит в консоль — ни постом, ни карточкой.

    10 августа `g15386e04` дошла до Telegram без единой правки чтением:
    заголовок называл «340 миллионов», поле «Сумма» несло механически
    вырезанные частичные «113 млн ₽» — владелец увидел противоречие раньше
    любого чтения. Документированный порядок притока («promote → сборка
    чтением → консоль») зависел от того, что рутина не забудет прочитать
    карточку перед отправкой, — а это не проверялось нигде в коде. Отметку
    `reviewed` ставит только `review.py`; гейт здесь делает шаг обязательным
    механически, а не по памяти рутины.
    """
    import promote
    import send_drafts
    cards = [
        {"id": "g-unread", "title": "Непрочитанная карточка",
         "src": [["Т", "https://t.example/1"]]},
        {"id": "g-read", "title": "Прочитанная карточка", "reviewed": "2026-08-10",
         "src": [["Т", "https://t.example/2"]]},
    ]
    monkeypatch.setattr(send_drafts.promote, "load_pending", lambda: {"cards": cards})
    monkeypatch.setattr(send_drafts, "site_pending_ids", lambda: None)
    monkeypatch.setattr(send_drafts, "latest_hold_drafts", lambda: [])
    monkeypatch.setattr(send_drafts.promote, "load_state",
                        lambda: {"decided_raw": {}, "sent_raw": []})
    plan, _p, _s, _deferred, _postponed, _foreign, unread = send_drafts.build_plan()
    ids_in_plan = {item["id"] for _t, _kb, (kind, item, _m) in plan if kind == "card"}
    assert "g-unread" not in ids_in_plan, "непрочитанная карточка попала в план консоли"
    assert "g-read" in ids_in_plan
    assert unread == 1


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


# ---------- сборка карточки чтением: полный текст и отметка прочтения ----------

def test_reviewed_stamp_is_idempotent():
    """Отметка «читали» ставится один раз и не переписывается повторным прогоном.

    Иначе каждый прогон review.py выдавал бы старое чтение за свежее, и по
    дате отметки нельзя было бы искать карточки, не читанные давно.
    """
    import review
    card = {"id": "x"}
    assert review.stamp_reviewed(card, day="2026-08-08") is True
    assert card["reviewed"] == "2026-08-08"
    assert review.stamp_reviewed(card, day="2026-09-01") is False
    assert card["reviewed"] == "2026-08-08", "повторный прогон переписал дату чтения"


def test_deep_researched_stamp_is_idempotent_and_separate_from_reviewed():
    """`deep_researched` — отдельная, более сильная планка, чем `reviewed`.

    Владелец 10 августа: обычного чтения одного источника мало, карточку
    надо обыскать по стандарту 2026 года. Отметка идемпотентна, как и
    `reviewed`, и не появляется сама по себе — только по `--mark-deep`.
    """
    import review
    card = {"id": "y"}
    assert review.stamp_reviewed(card, day="2026-08-10") is True
    assert "deep_researched" not in card, "reviewed не должен подразумевать deep_researched"
    assert review.stamp_deep_researched(card, day="2026-08-10") is True
    assert card["deep_researched"] == "2026-08-10"
    assert review.stamp_deep_researched(card, day="2026-09-01") is False
    assert card["deep_researched"] == "2026-08-10", "повторный прогон переписал дату"


def test_milestone_snapshot_captures_resolved_party_names():
    """`build_snapshot` резолвит стороны до имени компании там, где есть
    ссылка (`buyer`/`target`/`seller_id`), а не оставляет id или голый текст,
    если профиль найден. Без ссылки — честный текст, как он есть в карточке."""
    import review
    companies = {"cbuy": {"name": "ООО «Покупатель»"},
                 "ctarget": {"name": "ООО «Предмет»"}}
    card = {"id": "d1", "title": "Тестовая сделка", "type": "M&A",
            "status": "Обсуждается", "sum": "100 млн ₽",
            "buyer": "cbuy", "buyer_name": "текст на случай отсутствия ссылки",
            "target": "ctarget", "asset": "текст предмета",
            "seller": "Иван Иванов", "ind": "ИТ и интернет"}
    snap = review.build_snapshot(card, companies)
    assert snap["buyer"] == "ООО «Покупатель»"
    assert snap["asset"] == "ООО «Предмет»"
    assert snap["seller"] == "Иван Иванов", "без seller_id остаётся текст"
    assert snap["title"] == "Тестовая сделка" and snap["sum"] == "100 млн ₽"


def test_mark_milestone_finds_event_by_kind_and_assigns_a_stable_id():
    """`mark_milestone` ищет этап по `kind` в `events[]` и, если у него ещё
    нет своего `id`, присваивает стабильный — иначе ссылка на этап
    (`#/deal/<id>/stage/<key>`) в старых постах и закладках поплыла бы при
    любой перестановке массива `events`."""
    import review
    card = {"id": "d2", "events": [{"kind": "negotiations", "date": "2026-08-01"},
                                    {"kind": "closed", "date": "2026-08-10"}]}
    event = review.mark_milestone(card, "closed")
    assert event is not None and event["kind"] == "closed"
    assert event["id"] == "d2-closed"
    # этапа такого kind нет — честный None, а не выдуманное совпадение
    assert review.mark_milestone(card, "approval") is None


def test_review_cli_milestone_writes_newsworthy_flag_and_snapshot(tmp_path, monkeypatch):
    """Сквозной прогон: `--milestone <id> <kind> <headline> --write` ставит
    `newsworthy`, снимок и заголовок ОДИН раз; повторный вызов на уже
    помеченном этапе — честный отказ, а не тихая перезапись снимка (тот же
    принцип, что и остальные отметки review.py — идемпотентность против
    случайного повторного прогона)."""
    import json as _json
    import review
    base = {"deals": [{"id": "d3", "title": "Сделка X", "type": "M&A",
                        "status": "Согласование получено", "sum": "—",
                        "ind": "Не определена",
                        "events": [{"kind": "negotiations", "date": "2026-08-01"},
                                   {"kind": "approval", "date": "2026-08-15"}]}],
            "companies": {}}
    data_path = tmp_path / "milestone_base.json"
    pending_path = tmp_path / "milestone_pending.json"
    data_path.write_text(_json.dumps(base), encoding="utf-8")
    pending_path.write_text(_json.dumps({"cards": []}), encoding="utf-8")
    monkeypatch.setattr(review, "DATA", str(data_path))
    monkeypatch.setattr(review, "PENDING", str(pending_path))
    monkeypatch.setattr(review, "FIXES", [])

    rc = review.main(write=True, milestone=("d3", "approval", "Согласование получено по сделке X"))
    assert rc == 0
    written = _json.loads(data_path.read_text(encoding="utf-8"))
    card = written["deals"][0]
    event = next(e for e in card["events"] if e["kind"] == "approval")
    assert event["newsworthy"] is True
    assert event["snapshot"]["title"] == "Сделка X"
    assert event["snapshot"]["status"] == "Согласование получено"
    assert event["headline"] == "Согласование получено по сделке X"

    # тот же вызов повторно — отклонён, снимок не переписан
    written["deals"][0]["events"][1]["snapshot"]["title"] = "не трогать"
    data_path.write_text(_json.dumps(written), encoding="utf-8")
    rc2 = review.main(write=True, milestone=("d3", "approval", "Другой заголовок"))
    assert rc2 == 1
    unchanged = _json.loads(data_path.read_text(encoding="utf-8"))
    assert unchanged["deals"][0]["events"][1]["snapshot"]["title"] == "не трогать"


def test_review_cli_milestone_refuses_an_empty_headline(tmp_path, monkeypatch):
    """Заголовок вехи обязателен — пустая строка не должна тихо создать
    веху без человеческого текста для ленты и поста."""
    import json as _json
    import review
    base = {"deals": [{"id": "d4", "title": "Сделка Y", "type": "M&A",
                        "status": "Закрыта", "sum": "—", "ind": "Не определена",
                        "events": [{"kind": "closed", "date": "2026-08-20"}]}],
            "companies": {}}
    data_path = tmp_path / "milestone_base2.json"
    pending_path = tmp_path / "milestone_pending2.json"
    data_path.write_text(_json.dumps(base), encoding="utf-8")
    pending_path.write_text(_json.dumps({"cards": []}), encoding="utf-8")
    monkeypatch.setattr(review, "DATA", str(data_path))
    monkeypatch.setattr(review, "PENDING", str(pending_path))
    monkeypatch.setattr(review, "FIXES", [])

    rc = review.main(write=True, milestone=("d4", "closed", "   "))
    assert rc == 1
    unchanged = _json.loads(data_path.read_text(encoding="utf-8"))
    assert "newsworthy" not in unchanged["deals"][0]["events"][0]


def test_review_cli_milestone_backfills_headline_without_retaking_snapshot(tmp_path, monkeypatch):
    """До 22 августа `--milestone` ставил `newsworthy`/`snapshot`, но заголовка
    в схеме ещё не было — часть 1 уже так пометила два события в живой базе.
    Если бы «уже newsworthy» отклоняло ВСЕГДА, эти события не смогли бы
    получить заголовок никогда. Дописать заголовок задним числом можно, но
    снимок при этом переснимать нельзя — он обязан остаться снимком МОМЕНТА
    первой отметки, а не сегодняшнего дня."""
    import json as _json
    import review
    base = {"deals": [{"id": "d5", "title": "Сделка Z", "type": "M&A",
                        "status": "Закрыта", "sum": "старая сумма", "ind": "Не определена",
                        "events": [{"kind": "closed", "date": "2026-08-01",
                                    "id": "d5-closed", "newsworthy": True,
                                    "snapshot": {"title": "Сделка Z", "sum": "старая сумма"}}]}],
            "companies": {}}
    data_path = tmp_path / "milestone_base3.json"
    pending_path = tmp_path / "milestone_pending3.json"
    data_path.write_text(_json.dumps(base), encoding="utf-8")
    pending_path.write_text(_json.dumps({"cards": []}), encoding="utf-8")
    monkeypatch.setattr(review, "DATA", str(data_path))
    monkeypatch.setattr(review, "PENDING", str(pending_path))
    monkeypatch.setattr(review, "FIXES", [])

    # карточку тем временем обновили — сумма сегодня другая
    base["deals"][0]["sum"] = "новая сумма"
    data_path.write_text(_json.dumps(base), encoding="utf-8")

    rc = review.main(write=True, milestone=("d5", "closed", "Сделка Z закрыта"))
    assert rc == 0
    written = _json.loads(data_path.read_text(encoding="utf-8"))
    event = written["deals"][0]["events"][0]
    assert event["headline"] == "Сделка Z закрыта"
    assert event["snapshot"]["sum"] == "старая сумма", "снимок задним числом переснят — потеряна честность момента"


def test_postworthy_milestone_kinds_is_the_closed_v1_list():
    """Раздел A: список видов, достойных отдельной строки в ленте и поста в
    канал, закрытый и узкий — `signed` сознательно не в v1, `negotiations`
    никогда не был кандидатом (это состояние сделки, а не новость о ней)."""
    import review
    assert review.POSTWORTHY_MILESTONE_KINDS == {"approval", "closed", "cancelled"}


def test_enrich_does_not_duplicate_an_event_of_the_same_kind_and_date():
    """Раздел A требует проверить, есть ли у enrich.py защита от дубля
    события того же вида (два издания об одном одобрении ФАС = одно
    событие), — она уже есть, ключ дедупа `(kind, date)`: та же новость в
    тот же день не добавляет вторую строку в `events[]`."""
    import enrich
    deal = {"id": "d6", "title": "Сделка", "type": "M&A",
            "events": [{"kind": "approval", "date": "2026-08-10"}]}
    item = {"title": "Сделка получила одобрение ФАС", "url": "https://x.example/a",
            "date": "2026-08-10", "source_id": "x"}
    props = enrich.proposals(deal, item, {}, {})
    assert not any(p[0] == "event" for p in props), \
        "то же (kind, date) породило вторую запись события"


def test_enrich_allows_a_second_event_of_the_same_kind_on_a_different_date():
    """Дедуп по (kind, date) намеренно НЕ мешает двум РАЗНЫМ одобрениям одной
    сделки в разные даты (например, ФАС и отдельно правкомиссия) — это
    сознательное, уже задокументированное решение (комментарий в
    enrich.proposals), а не пропуск в защите. Раздел A просил ПРОВЕРИТЬ, что
    защита есть и что она не ломает этот легитимный случай, — фиксируем
    поведение тестом, а не меняем его."""
    import enrich
    deal = {"id": "d7", "title": "Сделка", "type": "M&A",
            "events": [{"kind": "approval", "date": "2026-08-10"}]}
    item = {"title": "Сделка получила одобрение регулятора", "url": "https://x.example/b",
            "date": "2026-08-20", "source_id": "x"}
    props = enrich.proposals(deal, item, {}, {})
    assert any(p[0] == "event" for p in props), \
        "второе одобрение в другую дату обязано остаться отдельным событием"


def _write_hold_file(tmp_path, name, drafts):
    import json as _json
    hold_dir = tmp_path / "data" / "inbox" / "hold"
    hold_dir.mkdir(parents=True, exist_ok=True)
    (hold_dir / name).write_text(_json.dumps({"drafts": drafts}), encoding="utf-8")
    return hold_dir


def test_raw_screen_deduplicates_the_same_draft_across_hold_files(tmp_path, monkeypatch):
    """Тот же дефект, что чинили в approve.py: недорешённый черновик
    переносится в КАЖДЫЙ следующий дневной hold-файл, пока по нему нет
    решения — `all_raw_drafts()` обязан вернуть его один раз, а не по разу
    за файл, иначе список на отсев дублируется вместе с решениями."""
    import raw_screen
    draft = {"draft_id": "dX", "title": "Один и тот же черновик", "date": "2026-08-01"}
    _write_hold_file(tmp_path, "2026-08-18.json", [draft])
    _write_hold_file(tmp_path, "2026-08-19.json", [draft])
    monkeypatch.setattr(raw_screen, "HOLD_DIR", str(tmp_path / "data" / "inbox" / "hold"))
    out = raw_screen.all_raw_drafts()
    assert len(out) == 1


def test_raw_screen_undecided_skips_id_title_and_batch_duplicates(tmp_path, monkeypatch):
    """`undecided()` обязан фильтровать теми же тремя признаками, что
    `send_drafts.build_plan()` — решено по draft_id, решено по заголовку
    (id меняется от прогона к прогону), дубль внутри партии."""
    import promote
    import raw_screen
    drafts = [
        {"draft_id": "d1", "title": "Решено по id"},
        {"draft_id": "d2", "title": "Решено по заголовку — новый id"},
        {"draft_id": "d3", "title": "Дубль внутри партии", "dup_in_batch": True},
        {"draft_id": "d4", "title": "Свежее, никем не тронуто"},
    ]
    _write_hold_file(tmp_path, "2026-08-21.json", drafts)
    monkeypatch.setattr(raw_screen, "HOLD_DIR", str(tmp_path / "data" / "inbox" / "hold"))
    state = {"decided_raw": {"d1": "drop"},
             "raw_titles": {promote.raw_key("Решено по заголовку — новый id"): "auto-drop"}}
    left = raw_screen.undecided(state)
    assert [d["draft_id"] for d in left] == ["d4"]


def test_raw_screen_drop_writes_auto_drop_and_blocks_regate(tmp_path, monkeypatch):
    """`--drop --write` метит решённым ОТДЕЛЬНЫМ от ручного 'drop' значением
    ('auto-drop' — аудит различает, кто решил), и то же самое сырьё,
    передрафченное завтра под новым draft_id с тем же заголовком, не должно
    заново пройти ворота `promote.py` (rejected_titles)."""
    import promote
    import raw_screen
    draft = {"draft_id": "dW", "title": "Выкуп, каравай и икона в банкетном зале"}
    _write_hold_file(tmp_path, "2026-08-21.json", [draft])
    monkeypatch.setattr(raw_screen, "HOLD_DIR", str(tmp_path / "data" / "inbox" / "hold"))
    state_path = tmp_path / "moderation_state.json"
    monkeypatch.setattr(promote, "STATE", str(state_path))

    rc = raw_screen.apply_drop(["dW"], "свадебный гайд, не сделка", write=True)
    assert rc == 0
    state = promote.load_state()
    assert state["decided_raw"]["dW"] == "auto-drop"
    title_key = promote.raw_key(draft["title"])
    assert state["raw_titles"][title_key] == "auto-drop"

    # то же сырьё под новым draft_id, тем же заголовком, назавтра —
    # rejected_titles (promote.py) обязан его знать
    rejected = {k for k, v in state.get("raw_titles", {}).items()
               if v == "drop" or v == "auto-drop" or str(v).startswith("enrich:")}
    assert title_key in rejected


def test_raw_screen_enrich_marks_decided_without_dropping_the_story(tmp_path, monkeypatch):
    """`--enrich draft_id=deal_id` метит черновик решённым (не спросит
    повторно), но НЕ вердиктом 'drop' — это дополнение к уже известной
    сделке (случай Alumni Partners/«Полекс»: объявление консультанта),
    аудит обязан отличать этот случай от мусора."""
    import promote
    import raw_screen
    draft = {"draft_id": "dE", "title": "Юрфирма сопровождала сделку по «Полексу»"}
    _write_hold_file(tmp_path, "2026-08-21.json", [draft])
    monkeypatch.setattr(raw_screen, "HOLD_DIR", str(tmp_path / "data" / "inbox" / "hold"))
    state_path = tmp_path / "moderation_state.json"
    monkeypatch.setattr(promote, "STATE", str(state_path))

    rc = raw_screen.apply_enrich([("dE", "gpoleks123")], write=True)
    assert rc == 0
    state = promote.load_state()
    assert state["decided_raw"]["dE"] == "enrich:gpoleks123"


def test_raw_screen_refuses_dropping_an_unknown_draft_id(tmp_path, monkeypatch):
    """Опечатка в id не должна молча ничего не сделать — честный отказ,
    как и у остальных отметок review.py/approve.py."""
    import raw_screen
    monkeypatch.setattr(raw_screen, "HOLD_DIR", str(tmp_path / "data" / "inbox" / "hold"))
    rc = raw_screen.apply_drop(["не-существует"], "проверка", write=True)
    assert rc == 1


def test_read_notes_reply_sends_to_the_stored_chat_and_message(monkeypatch):
    """`--reply <id> "текст"` бьёт в Telegram с `reply_to_message_id` из
    заметки — раздел C MILESTONES_BRIEF.md (22 августа): без этого рутина
    подтверждала заметку мгновенно, но содержательного ответа не давала
    никогда, и второй человек в группе не видел, что рутина вообще прочитала."""
    import read_notes
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(read_notes, "fetch_notes",
                        lambda: [{"id": 56, "deal_id": "gnote1", "chat_id": "111",
                                  "reply_message_id": 777, "verdict": "note"}])
    calls = []

    class _Resp:
        status_code = 200
        def json(self):
            return {"ok": True}

    def _fake_post(url, json=None, timeout=None):
        calls.append((url, json))
        return _Resp()

    import httpx as _httpx
    monkeypatch.setattr(_httpx, "post", _fake_post)

    ok = read_notes.send_reply(56, "Это отдельная веха, а не новая сделка.")
    assert ok is True
    assert calls, "запрос к Telegram не ушёл"
    url, body = calls[0]
    assert "bot" in url and "sendMessage" in url
    assert body["chat_id"] == "111" and body["reply_to_message_id"] == 777
    assert body["text"] == "Это отдельная веха, а не новая сделка."


def test_read_notes_reply_refuses_without_a_reply_target(monkeypatch):
    """Заметка без chat_id/reply_message_id (старая, до 22 августа) — честный
    отказ, а не тихая попытка отправить в никуда."""
    import read_notes
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(read_notes, "fetch_notes",
                        lambda: [{"id": 1, "deal_id": "gx", "chat_id": None,
                                  "reply_message_id": None, "verdict": "note"}])
    ok = read_notes.send_reply(1, "текст")
    assert ok is False


def test_weekly_researched_stamp_requires_deep_researched_first():
    """`weekly_researched` — второй из трёх уровней (неделя после появления
    карточки), дельта ПОВЕРХ `deep_researched`, а не независимая отметка.
    Отметка идемпотентна тем же способом, что `reviewed` и `deep_researched`.
    """
    import review
    card = {"id": "w"}
    assert review.stamp_weekly_researched(card, day="2026-08-17") is False, \
        "без deep_researched второй уровень не должен ставиться"
    assert "weekly_researched" not in card

    assert review.stamp_deep_researched(card, day="2026-08-10") is True
    assert review.stamp_weekly_researched(card, day="2026-08-17") is True
    assert card["weekly_researched"] == "2026-08-17"
    assert review.stamp_weekly_researched(card, day="2026-08-20") is False
    assert card["weekly_researched"] == "2026-08-17", "повторный прогон переписал дату"


def test_followup_researched_stamp_requires_weekly_researched_first():
    """`followup_researched` — третий, самый поздний уровень (месяц после
    появления карточки), дельта ПОВЕРХ `weekly_researched` (а через него —
    и поверх `deep_researched`), а не независимая отметка. Владелец
    16 августа: приток видит только 51 источник реестра, а то, что
    публикуется позже — поздние объявления консультантов, смена статуса, —
    сейчас не ловится ничем; нужен третий проход, но он не имеет смысла без
    второго. Отметка идемпотентна тем же способом, что `reviewed` и
    `deep_researched`.
    """
    import review
    card = {"id": "z"}
    assert review.stamp_followup_researched(card, day="2026-09-15") is False, \
        "без weekly_researched третий уровень не должен ставиться"
    assert "followup_researched" not in card

    assert review.stamp_deep_researched(card, day="2026-08-10") is True
    assert review.stamp_followup_researched(card, day="2026-09-15") is False, \
        "deep_researched без weekly_researched — третий уровень всё ещё рано"
    assert review.stamp_weekly_researched(card, day="2026-08-17") is True
    assert review.stamp_followup_researched(card, day="2026-09-15") is True
    assert card["followup_researched"] == "2026-09-15"
    assert review.stamp_followup_researched(card, day="2026-10-01") is False
    assert card["followup_researched"] == "2026-09-15", "повторный прогон переписал дату"


def test_mark_deep_auto_backfills_weekly_and_followup_when_window_already_passed():
    """Владелец 16 августа: «нам же нет смысла эти же которые сейчас
    просматриваем месячно делать?» — и был прав. Почти весь бэклог
    REVISION_BRIEF несёт `added=2026-07-15`; к моменту, когда до карточки
    доходят руки, с добавления в базу прошло больше месяца, и `--mark-deep`
    в этот день значит, что `deep_researched` УЖЕ случился на 30+ день
    после `added`. Без этой правки такая карточка немедленно попадала бы
    в очереди второго и третьего уровня с нулевым отступом от только что
    законченного первого прохода — 40 карточек партий 2 и 3 обнаружились в
    этом состоянии прямо в базе. `stamp_deep_researched` теперь закрывает
    оба следующих уровня сам, тем же днём, что и первый — второй при
    разрыве от 7 дней, третий при разрыве от 30, независимо друг от друга.
    """
    import review
    old_card = {"id": "old", "added": "2026-07-15"}
    assert review.stamp_deep_researched(old_card, day="2026-08-16") is True
    assert old_card["weekly_researched"] == "2026-08-16", \
        "32 дня между added и deep_researched — недельное окно тоже пройдено"
    assert old_card["followup_researched"] == "2026-08-16", \
        "32 дня между added и deep_researched — месячное окно тоже пройдено"

    # Свежая карточка — ни одно окно ещё не пройдено, автозакрытия быть не должно.
    fresh_card = {"id": "fresh", "added": "2026-08-10"}
    assert review.stamp_deep_researched(fresh_card, day="2026-08-16") is True
    assert "weekly_researched" not in fresh_card, \
        "6 дней между added и deep_researched — рано закрывать даже второй уровень"
    assert "followup_researched" not in fresh_card

    # Между неделей и месяцем — только второй уровень закрыт, третий ещё впереди.
    mid_card = {"id": "mid", "added": "2026-08-06"}
    assert review.stamp_deep_researched(mid_card, day="2026-08-16") is True
    assert mid_card["weekly_researched"] == "2026-08-16", \
        "10 дней между added и deep_researched — недельное окно пройдено"
    assert "followup_researched" not in mid_card, \
        "10 дней — месячное окно ещё не пройдено"

    # Ровно на границе недели (7 дней).
    week_boundary_card = {"id": "week-boundary", "added": "2026-08-09"}
    assert review.stamp_deep_researched(week_boundary_card, day="2026-08-16") is True
    assert week_boundary_card["weekly_researched"] == "2026-08-16"
    assert "followup_researched" not in week_boundary_card

    # Ровно на границе месяца (30 дней).
    boundary_card = {"id": "boundary", "added": "2026-07-17"}
    assert review.stamp_deep_researched(boundary_card, day="2026-08-16") is True
    assert boundary_card["weekly_researched"] == "2026-08-16"
    assert boundary_card["followup_researched"] == "2026-08-16"

    # Без added (кураторская запись без даты) — не падает, просто не бэкфиллит.
    no_added_card = {"id": "no-added"}
    assert review.stamp_deep_researched(no_added_card, day="2026-08-16") is True
    assert "weekly_researched" not in no_added_card
    assert "followup_researched" not in no_added_card


def test_every_fixed_card_carries_a_reviewed_mark():
    """Карточка, к которой применялась правка чтением, помечена прочитанной.

    Отметка — единственное, что отличает «не читали» от «читали, добавить
    нечего»: без неё пропуск шага чтения незаметен, пока источник не откроет
    человек (так владелец 8 августа нашёл пустую карточку NexTouch/«Квант»
    при 326 КБ текста статьи в кэше притока).
    """
    import review
    base = json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in base["deals"]}
    pending_file = ROOT / "static" / "data" / "pending.json"
    if pending_file.exists():
        cards.update({c["id"]: c for c in
                      json.loads(pending_file.read_text(encoding="utf-8"))["cards"]})
    unmarked = [f["id"] for f in review.FIXES
                if f["id"] in cards and not cards[f["id"]].get("reviewed")]
    assert not unmarked, ("карточки с правками чтения не помечены прочитанными "
                          "(запустите review.py --write): %s" % sorted(set(unmarked))[:5])
    # Формат отметки — дата, а не булево: по ней ищут давно не читанные.
    for d in cards.values():
        if d.get("reviewed"):
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", str(d["reviewed"])), \
                "reviewed должен быть датой ГГГГ-ММ-ДД: %r" % d["reviewed"]


def test_full_text_fetch_skips_already_cached_urls(monkeypatch, tmp_path):
    """Дозабор не качает статью второй раз: повторный прогон promote не должен
    ходить по тем же адресам (лимиты чужих сайтов, время прогона).

    Проверяется без сети и без реального data/inbox/raw — эта папка в git не
    хранится (.gitignore), значит в свежем контейнере её нет вовсе: тест,
    полагавшийся на файл в НАСТОЯЩЕМ data/inbox/raw, зелен только в той
    сессии, где он уже был создан вручную, и красен в любой другой (см. урок
    CLAUDE.md про сетевую политику одной сессии — родня того же класса
    ошибки). Кэш строится тут же, во временной директории.
    """
    import fetch_article_texts as articles
    monkeypatch.setattr(articles, "RAW", str(tmp_path))
    cache_file = tmp_path / "2026-08-01-articles.jsonl"
    cache_file.write_text(json.dumps({
        "url": "https://www.tadviser.ru/a/589723",
        "title": "проверка кэша",
        "summary": "текст статьи для проверки кэша" * 10,
    }, ensure_ascii=False) + "\n", encoding="utf-8")

    cached = articles.already_fetched()
    assert "https://www.tadviser.ru/a/589723" in cached, \
        "кэш полных текстов не читается (метод already_fetched)"
    got, lost = articles.fetch_and_store(
        [("test", "https://www.tadviser.ru/a/589723", "проверка кэша")], write=False)
    assert (got, lost) == (0, 0), "закэшированный адрес ушёл в сеть повторно"


# ---------- статус прогона в консоль основателей (ops_status.py) ----------

sys.path.insert(0, str(ROOT / "pipeline"))
import ops_status  # noqa: E402
import source_names  # noqa: E402


def test_ops_status_reports_success_to_the_console():
    """«Прогон был, ничего не нашлось» и «прогона не было вовсе» до 9 августа
    выглядели снаружи одинаково — молчанием (см. урок в CLAUDE.md про
    пропавший из расписания триггер притока). Статус обязан реально уйти
    подставному клиенту, а не только напечататься в лог, который никто не
    читает."""
    client = _FakeClient([{"ok": True, "result": {"message_id": 1}}])
    ok, why = ops_status.post_status(client, "TOKEN", "-1001", "приток: 32 кандидата, 0 новых")
    assert ok and why is None
    url, payload = client.calls[0]
    assert url == "https://api.telegram.org/botTOKEN/sendMessage"
    assert payload["chat_id"] == "-1001"
    assert "0 новых" in payload["text"]


def test_ops_status_honestly_reports_telegram_error():
    client = _FakeClient([{"ok": False, "description": "chat not found"}])
    ok, why = ops_status.post_status(client, "TOKEN", "-1001", "качество: нечего доработать")
    assert not ok
    assert "chat not found" in why


def test_quality_report_links_cards_and_counts_the_whole_queue():
    """Просьба владельца 21 августа, две части сразу.

    1. Имена дополненных карточек — ссылки на сами карточки, а не голый
       текст: из отчёта «дополнили X» должно быть видно, что именно
       дополнили, в один клик.
    2. Остаток считает САМ скрипт по всем трём уровням очереди и печатает
       всегда: рутина передавала `--left` только по уровню, по которому
       работала, — закрыла дневной в ноль, и строка исчезала, хотя
       недельная и месячная очереди не пусты («как узнать, сколько ещё
       переносить?»)."""
    base = {
        "deals": [
            # дополненная карточка — имя должно стать ссылкой
            {"id": "gaaa11111", "title": "Сделка «Альфа-Тест»",
             "added": "2026-08-01", "reviewed": "2026-08-01",
             "deep_researched": "2026-08-01", "weekly_researched": "2026-08-10",
             "followup_researched": "2026-08-10"},
            # дневная очередь: прочитана, полного обыска нет, старше суток
            {"id": "gbbb22222", "title": "Сделка «Бета-Тест»",
             "added": "2026-08-01", "reviewed": "2026-08-01"},
            # недельная: обыск был, недельной сверки нет, старше 7 дней
            {"id": "gccc33333", "title": "Сделка «Гамма-Тест»",
             "added": "2026-08-01", "reviewed": "2026-08-01",
             "deep_researched": "2026-08-02"},
            # слишком свежая для любой очереди — не должна считаться
            {"id": "gddd44444", "title": "Сделка «Дельта-Тест»",
             "added": "2099-01-01", "reviewed": "2099-01-01"},
        ],
        "companies": {},
    }
    from datetime import date
    day, week, month = ops_status.reading_queues(base, today=date(2026, 8, 21))
    assert (day, week, month) == (1, 1, 0)

    text = ops_status.render_quality(did="", ids=["gaaa11111"], facts=2, base=base)
    assert '/#/deal/gaaa11111"' in text, text
    assert "«Альфа-Тест»" in text
    assert "Ещё в очереди на проверку" in text
    assert "1 — первое полное чтение" in text
    assert "1 — недельная сверка" in text
    # пустая очередь называется пустой, а не пропадает из отчёта
    empty = {"deals": [], "companies": {}}
    text2 = ops_status.render_quality(did="Проверили платформу.", base=empty)
    assert "очередь пуста" in text2


def test_quality_report_month_line_does_not_read_as_posts_this_month():
    """22 августа владелец прочитал «837 — месячная» как «837 постов вышло
    за месяц» и спросил, не бесполезна ли такая проверка для месячного
    поста. Строка на самом деле про СТАРЫЕ карточки (обычно давно в базе, а
    не опубликованные недавно), которым положена лёгкая сверка на новые
    факты, — и число просто растёт разом, когда опустевает недельная
    очередь. Голое «N — месячная» это не объясняло; текст обязан называть,
    что именно проверяется."""
    from datetime import date
    base = {
        "deals": [
            {"id": "geee55555", "title": "Сделка «Эпсилон-Тест»",
             "added": "2026-01-01", "reviewed": "2026-01-01",
             "deep_researched": "2026-01-02", "weekly_researched": "2026-01-10"},
        ],
        "companies": {},
    }
    day, week, month = ops_status.reading_queues(base, today=date(2026, 8, 21))
    assert (day, week, month) == (0, 0, 1)
    text = ops_status.render_quality(did="Проверили платформу.", base=base)
    assert "1 — месячная" not in text
    assert "старых карточек" in text and "новые факты" in text


def test_quality_report_shows_fns_budget_line_only_when_routine_provides_it():
    """23 августа: строку остатка квоты ФНС печатаем, только если рутина в
    этот прогон реально ходила в API-ФНС и передала готовую строку —
    ops_status.py сам сети не касается, чтобы отчёт не стал источником
    побочных трат."""
    text_with = ops_status.render_quality(
        did="Проверили платформу.",
        fns_budget="Квота ФНС: search 482/3000, bo 164/3000 (до 2027-08-17)")
    assert "💳" in text_with and "Квота ФНС" in text_with

    text_without = ops_status.render_quality(did="Проверили платформу.")
    assert "💳" not in text_without and "Квота ФНС" not in text_without


def test_ops_status_main_without_token_does_not_pretend_to_send(monkeypatch, capsys):
    """Без токена/чата — честная строка в лог прогона, а не тихая имитация
    успеха (тот же принцип, что у send_telegram.py без TELEGRAM_BOT_TOKEN)."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_REVIEW_GROUP_ID", raising=False)
    assert ops_status.main(["публикация", "--nothing"]) == 1
    assert "не заданы" in capsys.readouterr().out


def test_ops_status_main_requires_text():
    assert ops_status.main([]) == 1


def test_ops_status_refuses_internal_jargon_reaching_the_console():
    """Ровно те две фразы, которые владелец прислал 9 августа как непонятные
    партнёру. Тот же класс ошибки, что «знаменатель» и «bulk» на экране сайта
    (CLAUDE.md), только вылез в отчётах рутин."""
    assert ops_status.find_jargon('G7 — дочитана карточка, 6 полей заполнено')
    assert ops_status.find_jargon('очередь решений пуста, 6 внутри 24ч тишины')
    assert ops_status.find_jargon('карточка ушла в предпросмотр, from_ingest')
    # Человеческая формулировка того же самого проходит.
    assert not ops_status.find_jargon(
        'Дополнили карточку «Родные поля» — перенесли 6 фактов из статьи.')


def test_ops_status_jargon_pattern_does_not_catch_deal_names():
    """23 августа 2026 отчёт про карточку Capital Group/ТВК «Тишинка»
    отклонило собственное правило ops_status.py: `тишин\\w+` без границы
    слова совпадало внутри имени сделки. Тот же класс дефекта, что уже
    записан в CLAUDE.md («ствол словаря без границы слова ловится внутри
    чужого слова»), только здесь — в JARGON, а не в словаре отраслей."""
    assert not ops_status.find_jargon(
        'Нашли суд по несостоявшейся сделке Capital Group/ТВК «Тишинка».')
    assert not ops_status.find_jargon(
        'Иск подан по объекту на Тишинской площади.')
    # Настоящий жаргон по-прежнему ловится во всех словоформах.
    assert ops_status.find_jargon('карточки выйдут сами в тишине')
    assert ops_status.find_jargon('6 внутри 24ч тишины')
    assert ops_status.find_jargon('решение примут в тишину')


def test_ops_status_does_not_send_when_jargon_slipped_in(monkeypatch, capsys):
    """Мало найти жаргон — надо не отправить. Иначе проверка декоративная."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_REVIEW_GROUP_ID", "-1001")
    monkeypatch.setattr(ops_status, "post_status",
                        lambda *a, **k: pytest.fail("жаргон ушёл в консоль"))
    assert ops_status.main(["качество", "--did", "G7: дочитана карточка"]) == 1
    assert "жаргон" in capsys.readouterr().out


def test_ops_status_writes_human_russian_with_correct_plurals():
    """Партнёр читает «6 карточек», а не «6 карточка»: склонение — часть
    понятности, а не украшение."""
    assert "1 карточка выйдут" not in ops_status.render_publish(nothing=True, soon=1)
    assert "карточка" in ops_status.render_publish(nothing=True, soon=1)
    assert "карточки" in ops_status.render_publish(nothing=True, soon=3)
    assert "карточек" in ops_status.render_publish(nothing=True, soon=6)
    # 1633 -> «новости» (оканчивается на 3), 1635 -> «новостей», 11 -> «новостей»
    # (11–14 — исключение, несмотря на последнюю цифру).
    assert "1633 новости" in ops_status.render_intake(looked=1633)
    assert "1635 новостей" in ops_status.render_intake(looked=1635)
    assert "11 новостей" in ops_status.render_intake(looked=11)
    assert "1 новость" in ops_status.render_intake(looked=1)


def test_ops_status_empty_run_says_so_plainly():
    """Пустой прогон обязан быть внятным, а не молчаливым — иначе возвращаемся
    к тому, из-за чего приток простоял несколько дней незамеченным."""
    text = ops_status.render_publish(nothing=True)
    assert "публиковать нечего" in text.lower()
    assert "тихие дни" in ops_status.render_intake(looked=1633)
    assert "чинить нечего" in ops_status.render_quality()


def test_ops_status_offers_buttons_only_when_there_is_something_to_show():
    assert ops_status.queue_keyboard(0, 0) is None
    kb = ops_status.queue_keyboard(6, 4)["inline_keyboard"][0]
    assert [b["callback_data"] for b in kb] == ["show:soon", "show:held"]
    assert ops_status.queue_keyboard(6, 0)["inline_keyboard"][0][0]["callback_data"] == "show:soon"
    # «Ждёт прочтения» — третья, отдельная причина ждать (не «скоро выйдет»,
    # не «придержано человеком») — своя кнопка между ними.
    kb3 = ops_status.queue_keyboard(6, 4, 2)["inline_keyboard"][0]
    assert [b["callback_data"] for b in kb3] == ["show:soon", "show:unread", "show:held"]


def test_site_answers_the_queue_buttons():
    """Кнопка, на которую никто не отвечает, выглядит рабочей и молчит — тот
    же класс, что забытый callback_query в подписке вебхука (CLAUDE.md)."""
    src = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "show:(soon|held|raw|unread)" in src, "сайт не разбирает callback_data кнопок отчёта"
    assert "Очередь видят только владелец и партнёр" in src, "нет проверки права"


# ---------- предмет сделки в именительном падеже (casing.py) ----------

def test_asset_case_matches_the_four_examples_owner_reported():
    """9 августа владелец нашёл падеж в постах канала — ровно эти четыре
    карточки на скриншотах ('МКБ/Дальневосточный банк', 'Еврострой',
    'Ситилинк/Lay's', 'Аптечная сеть 36,6/Диалог')."""
    cases = [
        ("Дальневосточного банка", "Дальневосточный банк"),
        ("производственную базу", "производственная база"),
        ("производителе картошки для чипсов Lay’s",
         "производитель картошки для чипсов Lay’s"),
        ("московского фармритейлера «Диалог»",
         "московский фармритейлер «Диалог»"),
    ]
    for old, new in cases:
        got, changed = casing.to_nominative_asset(old)
        assert changed and got == new, (old, got)


def test_asset_case_leaves_percent_and_number_phrases_alone():
    """После «%» или числительного дальше идёт управляемый родительный
    («96% акций», «45% сети», «5 гектаров земли») — это НЕ сказуемое,
    трогать нельзя. Первая версия правила именно тут дала ложные срабатывания
    ('45% сети X' -> '45% сеть X')."""
    for phrase in ("96% акций Челябинского завода металлоконструкций",
                   "45% сети «Глобус Гурмэ»",
                   "5 гектаров земли в бывшей промзоне «Свиблово»",
                   "14% в группе «Полипластик»"):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_never_touches_quoted_names():
    """Имя/бренд в кавычках не склоняем — но узнаём его по ЗАГЛАВНОЙ БУКВЕ
    ядра, а не по самому факту кавычек.

    Первая версия правила отказывалась работать, если кавычки встречались
    где угодно во фразе, — и молчала на 244 предметах из 1027 (замер по
    точке производства, см. docstring casing.py): у предмета почти всегда
    есть хвост с названием, и запрет, написанный для головы, глушил всю
    фразу. Теперь запрет проверяется там, где он и задуман."""
    for phrase in ('сети «Здоровый город» в Воронежской области',
                   '«Моторику» (производителя бионических протезов)',
                   '«Уфабурмаша»'):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase
    # А нарицательное в кавычках — склоняем, кавычки остаются на месте.
    got, changed = casing.to_nominative_asset('бывшую лизинговую «дочку» Mercedes-Benz')
    assert changed and got == 'бывшая лизинговая «дочка» Mercedes-Benz'


def test_asset_case_skips_ambiguous_word_forms():
    """«права» — одна и та же словоформа для родительного ед. числа («права»
    закона) и именительного/винительного мн. числа («права» = rights); без
    контекста предложения смена числа исказила бы смысл ('право' вместо
    'права'). Тот же класс защиты, что для plural/singular неоднозначности."""
    for phrase in ('права на СУБД «Персей»', 'права на три гинекологических препарата'):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_skips_capitalized_bare_words():
    """Слово с заглавной буквы похоже на имя/бренд — pymorphy угадывает
    падеж бренда наугад ('Рив Гош' -> 'Рив Гоши', 'Квант' -> 'Кванты',
    'Оней Банк' -> 'Они Банк' были реальными ложными срабатываниями)."""
    for phrase in ('Рив Гош', 'Квант', 'Оней Банк', 'Синтезе'):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_leaves_dependent_genitive_after_the_head_alone():
    """Голова словосочетания — ПЕРВОЕ существительное; всё, что после неё
    (зависимый родительный/предложный оборот), не трогаем. 'Группа компаний
    X' и 'Магазин приложений X' уже согласованы — голова 'Группа'/'Магазин'
    стоит в именительном, а 'компаний'/'приложений' — верный родительный."""
    for phrase in ('Группа компаний «Зельгрос Россия»', 'Магазин приложений RuStore'):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_is_a_noop_on_already_nominative_phrases():
    for phrase in ('здание Рижского вокзала', 'мажоритарная доля в «Еаптеке»',
                   'торговый комплекс «Среда. Царицыно» на юге Москвы'):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_keeps_the_prefix_of_a_compound_word():
    """Регистр берём посимвольно у исходного слова: pymorphy отдаёт лемму
    строчными, и «ИТ-компанию» превращалось в «Ит-компания». Заодно проверка,
    что аббревиатура в начале слова не считается именем бренда — имя узнаём
    по ПОСЛЕДНЕЙ части составного слова («Рив-Гош» — имя, «ИТ-компанию» —
    нарицательное)."""
    got, changed = casing.to_nominative_asset("казахстанскую ИТ-компанию Bilim Group")
    assert changed and got == "казахстанская ИТ-компания Bilim Group"


def test_asset_case_refuses_when_the_word_form_may_be_nominative_already():
    """«телеком провайдера «Уфанета»» превращалось в «телек провайдера»:
    лучший разбор «телеком» — творительный от «телек» (score 0,333), а два
    других дают именительный от «телеком» с ТОЙ ЖЕ вероятностью. Сравнивать
    надо словоформу, а не лемму. При этом шумный именительный терять нельзя:
    у «банка» он есть («банка» как ёмкость), но со score 0,045 против 0,955 —
    и именно на нём держится правка, с которой всё началось."""
    got, changed = casing.to_nominative_asset("телеком провайдера «Уфанета»")
    assert not changed and got == "телеком провайдера «Уфанета»"
    got, changed = casing.to_nominative_asset("Дальневосточного банка")
    assert changed and got == "Дальневосточный банк"


def test_asset_case_uses_the_adjective_as_a_witness_of_the_case():
    """У женского 3-го склонения винительный совпадает с именительным
    («сеть»), и правило считало фразу уже нормальной — «частную сеть АЗС
    Elke Auto» уезжало в канал как есть. Падеж выдаёт прилагательное: если ни
    один его разбор не даёт именительный, согласуем прилагательные, голову не
    трогая. Неоднозначное прилагательное («российская» — и им., и род.) такой
    уверенности не даёт и правило молчит."""
    got, changed = casing.to_nominative_asset("частную сеть АЗС Elke Auto в Томске")
    assert changed and got == "частная сеть АЗС Elke Auto в Томске"
    for phrase in ("розничная сеть «Пятёрочка»", "торговая сеть в Сибири"):
        got, changed = casing.to_nominative_asset(phrase)
        assert not changed and got == phrase


def test_asset_case_rule_measured_on_the_whole_base():
    """ЗАМЕР ВАЖНЕЕ ВПЕЧАТЛЕНИЯ, и мерить надо в точке ПРОИЗВОДСТВА.

    Первый замер правила («19 срабатываний на 183 сохранённых полях `asset`»)
    выглядел законченным — а по заголовкам, из которых предмет РОЖДАЕТСЯ,
    правило чинило 0 из 26 найденных косвенных. Здесь замер закреплён: гоняем
    `guess_parties()` с выключенной нормализацией по всем заголовкам базы и
    считаем, скольким предметам правило меняет падеж. Порог снизу — чтобы
    правка, снова заглушившая правило целиком (как запрет на кавычки во всей
    фразе), упала тестом, а не через месяц в канале.
    """
    import json
    import draft as drafter
    base = json.loads((ROOT / "static/data/deals_promoted.json").read_text(encoding="utf-8"))
    cards = base.get("deals") or base.get("cards") or []
    real = casing.to_nominative_asset
    drafter.to_nominative_asset = lambda s: (s, False)
    try:
        assets = []
        for c in cards:
            try:
                _, asset, _ = drafter.guess_parties(str(c.get("title") or ""))
            except Exception:
                continue
            if asset:
                assets.append(asset)
    finally:
        drafter.to_nominative_asset = real
    assert len(assets) > 900, f"предмет разбирается лишь у {len(assets)} заголовков"
    fixed = sum(1 for a in assets if real(a)[1])
    assert fixed >= 200, f"правило падежа чинит всего {fixed} предметов из {len(assets)}"


def test_draft_extraction_normalizes_asset_case():
    """Правило подключено в draft.py — тот же путь, каким собираются черновики
    притока, а не только отдельно проверенная функция."""
    import draft as drafter
    _, asset, _ = drafter.guess_parties("МКБ завершил присоединение Дальневосточного банка")
    assert asset == "Дальневосточный банк"


# ---------- механика учится на правках чтением (learn.py) ----------

def test_sum_is_refused_when_the_sentence_is_about_another_figure():
    """Самый дорогой класс вранья механики: число есть, оно верное, но это НЕ
    цена сделки. Три пойманных чтением случая — чистые инвестиции в лизинг,
    бухгалтерский убыток продавца, выручка предмета."""
    import draft as drafter
    cases = [
        'Сумму сделки в компании не раскрывают, однако уточняют, что после ее '
        'завершения чистые инвестиции в лизинг (ЧИЛ) «Флит Лизинга» превысят 32 млрд руб.',
        'Сумма сделки не раскрывается. Но по ее итогу Reckitt ожидает убыток '
        'на £175 млн (около 18 млрд руб.)',
        'По итогам 2025 года выручка операционной компании «Пролайф» сократилась '
        'примерно на пятую часть, до 711,7 млн руб.',
    ]
    for text in cases:
        assert drafter.guess_sum(text), 'предпосылка теста: число тут вообще есть'
        assert drafter.sum_from_text(text) is None, text[:60]


def test_real_deal_sum_still_survives_the_guard():
    """Защита обязана быть узкой: обычная цена сделки проходит как раньше."""
    import draft as drafter
    assert drafter.sum_from_text('Сделка оценивается в 2 млрд руб.') == '2 млрд ₽'
    assert drafter.sum_from_text('«Флит Лизинг» купил актив за 404 млн рублей') == '404 млн ₽'


def test_generic_role_description_is_not_accepted_as_a_party_name():
    """«Владелец Yadro» — это не имя покупателя, а описание роли; настоящее имя
    в статье обычно есть, просто ниже заголовка. Молчание честнее."""
    import draft as drafter
    for name in ('Владелец Yadro', 'Бывший топ-менеджер «Лукойла»', 'ресторатора Флеганова',
                 'Экс-акционер Башкирской содовой компании', 'Группа инвесторов',
                 'Совладелец R-Vision', 'фонд под управлением «ВИМ Сбережения»'):
        assert drafter.is_generic_description(name), name
        assert drafter._named(name) is None, name


def test_real_party_names_pass_the_generic_description_guard():
    """Проверено на себе с обеих сторон: у роли-ОРГАНИЗАЦИИ имя своё
    («Группа «Астра»», «Группа Циан»), у роли-ЧЕЛОВЕКА — чужое."""
    import draft as drafter
    for name in ('«Аптечная сеть 36,6»', 'МКБ', 'Wildberries', 'ООО «Икс Холдинг»',
                 'Freedom Тимура Турлова', 'Семья бизнесмена Говора',
                 'Создатели «Ситилинка»', 'Группа «Астра»', 'Группа Циан', 'Холдинг Т1'):
        assert not drafter.is_generic_description(name), name


def test_learning_log_records_every_rejected_hypothesis_with_numbers():
    """Отвергнутая гипотеза с цифрами ценнее ненаписанного правила: без записи
    следующий прогон переоткрывает её за токены. Каждая запись обязана нести
    замер и причину, а не только формулировку."""
    import learn
    assert learn.REJECTED and learn.LEARNED
    for entry in learn.REJECTED + learn.LEARNED:
        for key in ('date', 'field', 'rule', 'measured', 'result'):
            assert entry.get(key), (entry.get('rule'), key)
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', entry['date'])
    for entry in learn.REJECTED:
        assert entry.get('why'), entry['rule']


def test_post_proofreading_catches_the_case_that_reached_readers():
    """Вычитка обязана ловить ровно то, что 9 августа ушло в канал четырьмя
    постами подряд. Проверено на себе: на исправленном тексте — молчит."""
    import check_post
    bad = ('<b>МКБ завершил присоединение</b>\n\n'
           'Предмет: Дальневосточного банка\nПокупатель: МКБ\n\nСтатус: Закрыта')
    assert any('косвенный падеж' in p for p in check_post.check(bad))
    good = bad.replace('Дальневосточного банка', 'Дальневосточный банк')
    assert not check_post.check(good)


def test_post_proofreading_does_not_flag_legitimate_subjects():
    """Правило узкое: множественное число, прилагательное в именительном и
    доля с процентом — законные значения, их трогать нельзя."""
    import check_post
    for value in ('права на СУБД «Персей»', 'производственная база',
                  'московский фармритейлер «Диалог»', '96% акций Челябинского завода',
                  'Дальневосточный банк'):
        post = '<b>Заголовок</b>\n\nПредмет: %s\nПокупатель: МКБ' % value
        assert not check_post.check(post), (value, check_post.check(post))


def test_post_proofreading_catches_placeholders_and_empty_posts():
    import check_post
    assert any('undefined' in p for p in
               check_post.check('<b>X</b>\n\nСтатус: undefined\nСумма: 1 млрд ₽'))
    assert any('заглушкой' in p for p in
               check_post.check('<b>X</b>\n\nПредмет: —\nСумма: 1 млрд ₽'))
    assert any('нечего узнать' in p for p in
               check_post.check('<b>Просто заголовок</b>\n\nОтрасль: Банки'))


def test_send_telegram_proofreads_before_the_dry_run_report():
    """Задержанный пост должен быть виден В ПЛАНЕ: план читает человек, и
    первая версия проверки стояла ПОСЛЕ выхода из сухого прогона — то есть в
    плане её не было видно вовсе."""
    import inspect
    import send_telegram
    src = inspect.getsource(send_telegram.main)
    proof = src.index('check_post.check')
    dry_exit = src.index('Сухой прогон с настоящим токеном')
    assert proof < dry_exit, 'вычитка стоит после выхода из сухого прогона'


def test_learning_log_separates_lies_from_silence():
    """Механика, которая соврала, и механика, которая промолчала, — разные
    классы: первое уезжает в базу и в канал как факт, второе дочитывается."""
    import learn, review
    classes = learn.failure_classes(review.FIXES)
    assert any(k[1] == 'СОВРАЛА' for k in classes)
    assert any(k[1] == 'промолчала' for k in classes)
    lied = sum(v for k, v in classes.items() if k[1] == 'СОВРАЛА')
    assert lied == sum(1 for f in review.FIXES if f['old'] not in (None, '—', ''))


def test_no_duplicate_fix_for_one_field():
    """Две записи на одно поле одной карточки — запрещены, теперь и между файлами.

    `main()` читает состояние карточки ОДИН раз в начале прогона и сверяет
    КАЖДУЮ запись таблицы с этим состоянием, не применяя промежуточные правки
    по цепочке. Поэтому две записи на одно поле не могут обе описывать текущую
    реальность: вторая всегда получит «поле уже другое». Когда таблица была
    одна, это ловилось глазами при редактировании; после разрезания на файлы
    партий (`fixes/*.py`) задвоение может приехать из ДВУХ РАЗНЫХ файлов —
    например, когда два потока читают пересекающиеся партии. Тест это ловит.

    Исключение — `src`: поле аддитивное, `already_applied` проверяет наличие
    адреса в списке, а не равенство, и несколько записей туда законны.
    """
    import collections
    import review
    seen = collections.Counter((f["id"], f["field"]) for f in review.FIXES
                               if f["field"] != "src")
    dups = [k for k, n in seen.items() if n > 1]
    assert not dups, f"на одно поле приходится больше одной правки: {dups[:5]}"


def test_fix_batches_live_in_separate_files():
    """Партии правок разложены по файлам — иначе параллельное чтение невозможно.

    Пока таблица одна, два потока, читающие разные партии, конфликтуют в git на
    каждом коммите: 9 августа это случилось при ДВУХ параллельных прогонах, и
    слияние пришлось разбирать руками. Плюс единая таблица росла на ~3 тыс.
    знаков с каждой прочитанной карточки — на 1210 карточках дочитывания она
    перестала бы помещаться в контекст.
    """
    folder = ROOT / "pipeline" / "ingest" / "fixes"
    assert folder.is_dir(), "папки с партиями правок нет"
    batches = sorted(p.name for p in folder.glob("*.py") if p.name != "__init__.py")
    assert batches, "в папке нет ни одной партии"
    src = (ROOT / "pipeline" / "ingest" / "review.py").read_text(encoding="utf-8")
    assert "FIXES = load_fixes()" in src, "review.py снова держит таблицу в себе"
    assert len(src) < 60000, (
        f"review.py разбух до {len(src)} знаков — правки снова пишут в него, "
        "а не в отдельный файл партии")


def test_report_never_invents_a_deal_category():
    """«Восемь заводских и биржевых сделок» — категория, которой у нас нет.

    Владелец 9 августа прислал из консоли два вопроса: что значит «восемь
    заводских и биржевых сделок» и что значит «показатели компаний и
    терминалов». Ответа не нашлось — обе фразы родились из попытки свести
    партию РАЗНОРОДНЫХ карточек (завод, приватизация, фонд, торговый комплекс)
    к одному ярлыку. Пока рутина читала одну карточку за прогон, обобщать было
    нечего; с переходом на партии обобщение стало обязательным — и выдуманным.

    Признак узкий намеренно: величина и наши настоящие типы сделок проходят.
    """
    assert ops_status.find_invented_category("Дополнили восемь заводских и биржевых сделок")
    assert ops_status.find_invented_category("шесть портовых и складских сделок")
    for ok in ("восемь крупных сделок", "12 инвестиционных сделок",
               "три новые карточки", "Дополнили двенадцать карточек"):
        assert not ops_status.find_invented_category(ok), ok


def test_report_names_deals_from_the_base_not_from_the_head():
    """Первую фразу отчёта строит скрипт из заголовков карточек.

    Так исчезает сама нужда обобщать: рутина передаёт id, имена берутся из
    базы, и выдумать категорию негде. `did` остаётся — но описывает НАХОДКИ
    («независимые оценки экспертов», «кто владел активом до сделки»), где
    обобщение уместно и ничего не сочиняет.
    """
    base = json.loads((ROOT / "static/data/deals_promoted.json").read_text(encoding="utf-8"))
    ids = [d["id"] for d in base["deals"][:5]]
    text = ops_status.render_quality(did="", left=1297, ids=ids, facts=42)
    assert "Дополнили 5 карточек:" in text
    assert "42 факта" in text
    # Имена — настоящие: каждое лежит в самой карточке (заголовок дословно
    # ИЛИ структурное поле стороны/предмета), а не выдумано.
    by_id = {d["id"]: d for d in base["deals"]}
    companies = base["companies"]
    for cid in ids[:3]:
        card = by_id[cid]
        name = ops_status.short_name(card, companies).strip("«»")
        assert name
        grounded = (
            name in card["title"]
            or name == companies.get(card.get("target") or "", {}).get("name")
            or name == card.get("asset")
            or name == companies.get(card.get("buyer") or "", {}).get("name")
            or name == card.get("buyer_name")
            or name == card.get("seller")
        )
        assert grounded, "%r не выводится ни из одного поля карточки %s" % (name, cid)
    # Остаток очереди скрипт с 21 августа считает САМ по базе и печатает
    # всегда; переданное рукой `--left` при живой базе игнорируется —
    # замер важнее записанной цифры (владелец: «как узнать, сколько ещё
    # переносить?» — ответ не должен зависеть от того, что рутина не
    # забыла передать).
    assert "1297" not in text
    assert "Ещё в очереди на проверку" in text or "очередь пуста" in text


def test_report_deal_name_is_not_the_first_capitalized_word():
    """Владелец 16 августа прислал два отчёта подряд, назвавшие сделки
    «Российские», «Продажа», «Яндексу», «Слияние», «Государственный» — и
    справедливо спросил, что это за карточки. Причина: в русском заголовке
    с заглавной буквы начинается ЛЮБОЕ первое слово, а не только имя
    собственное, а старая `short_name` брала именно первое слово с
    заглавной. `short_name` теперь смотрит на структурные поля (предмет,
    покупатель, продавец) раньше текста заголовка — тест держит РЕАЛЬНЫЕ
    карточки, на которых нашёлся баг, а не синтетический пример.
    """
    base = json.loads((ROOT / "static/data/deals_promoted.json").read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in base["deals"]}
    companies = base["companies"]
    cases = {
        "g6f83d85e": "Продажа",           # Продажа Veeam Software фонду Insight Partners...
        "gdde6bef5": "Слияние",           # Слияние Whoosh и МТС Юрент...
        "g9c4b80a7": "Российские",        # Российские активы CanPack...
        "g3074f98b": "Государственный",   # Государственный пенсионный фонд Норвегии...
        "ga5336065": "Продажа",           # Продажа золоторудного месторождения Ямалзолото
    }
    for cid, banned in cases.items():
        name = ops_status.short_name(by_id[cid], companies)
        assert name != banned, "%s: имя снова свелось к слову «%s»" % (cid, banned)


# ---------- имя издания по адресу (source_names.py) ----------

def test_telegram_channel_gets_a_name_not_a_raw_feed_id():
    """Карточка ПСБ/«Атом» несла источником «tg:rusven» — внутренний id ленты
    (build_sources.py: `'id': 'tg:' + name`), а не имя канала. Тот же класс
    дефекта, что уже чинили для «web:kommersant.ru» (докстрока файла), только
    для t.me: домен в адресе не несёт имени канала, только @username.
    """
    assert source_names.edition_label("https://t.me/rusven/7661") == "Телеграм-канал: Русский Венчур"
    # Незнакомый канал — честно по @username, а не выдуманное название и не
    # голый домен «T.me».
    assert source_names.edition_label("https://t.me/unknownchannel/1") == "Телеграм-канал @unknownchannel"
    # Обычные http(s)-адреса эта правка не трогает.
    assert source_names.edition_label("https://www.kommersant.ru/doc/1") == "Коммерсантъ"
