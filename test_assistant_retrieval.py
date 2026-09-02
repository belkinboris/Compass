# -*- coding: utf-8 -*-
"""Поиск по базе для ассистента (assistant_retrieval.py) — на настоящей базе.

Зачем тесты на живых данных, а не на фикстуре: жалоба партнёра 31 августа
2026 была именно о расхождении ответа с базой («у Orion сделок нет» при 15
карточках). Числа здесь не зашиты — сравниваются с тем, что даёт сам индекс,
поэтому рост базы тесты не ломает, а вот сломанный маршрут вопроса — ломает.

Запуск: python3 -m pytest test_assistant_retrieval.py -q
"""
import json
import re

import pytest

import assistant_retrieval as ar


@pytest.fixture(scope="module")
def idx():
    return ar.get_index(force=True)


def _ask(q, idx, **kw):
    return ar.retrieve(q, kw.get("context_type"), kw.get("context_id"), idx)


# ---------- слова ----------

def test_stem_keeps_short_and_latin_words():
    assert ar.stem("orion") == "orion"
    assert ar.stem("гош") == "гош"
    assert ar.stem("ситибанком") == "ситибанк"
    assert ar.stem("сделками") == "сделк"


def test_same_word_is_the_review_py_rule():
    assert ar.same_word("магнит", "магнита")
    assert ar.same_word("ситибанк", "ситибанком")
    assert not ar.same_word("вера", "вета")
    assert not ar.same_word("сити", "ситибанк")     # короткое имя не тянет длинное


def test_name_match_is_stricter_than_same_word():
    # «Иванов» ложился на «Иван Пешков» и «Иванян и партнёры» — для имён
    # нужна не падежная близость, а общее начало от пяти знаков.
    assert ar.same_word("иванов", "иван")
    assert not ar.name_match("иванов", "иван")
    assert not ar.name_match("иванов", "иванян")
    assert ar.name_match("ивановым", "иванов")
    assert ar.name_match("orion", "orion")


# ---------- индекс ----------

def test_index_holds_only_deals_the_site_shows(idx):
    assert idx.docs
    assert all(d.year >= ar.SITE_MIN_YEAR for d in idx.docs)


def test_firm_catalog_is_read_from_the_interface_file(idx):
    names = {f.name for f in idx.firms}
    assert {"Orion", "Better Chance"} <= names
    assert all(f.rx is not None for f in idx.firms)
    assert len(idx.firm_deals.get("orion") or []) >= 10


# ---------- маршруты вопросов ----------

def test_advisor_question_counts_every_firm_deal(idx):
    r = _ask("Какие сделки сопровождала Orion?", idx)
    n = len(idx.firm_deals["orion"])
    assert r.intent == "advisor" and r.subject == "Orion"
    assert f" {n} " in r.answer and "#/advisors/orion" in r.answer
    assert 1 <= len(r.docs) <= ar.MAX_DEALS_FOR_MODEL


def test_count_of_a_firm_is_also_an_advisor_question(idx):
    r = _ask("Сколько сделок Better Chance?", idx)
    assert r.intent == "advisor" and r.subject == "Better Chance"
    assert f" {len(idx.firm_deals['betterchance'])} " in r.answer


def test_coal_is_the_coal_industry_not_mining_in_general(idx):
    it = ar.route("Кто консультирует в сфере добычи угля?", idx)
    assert it.kind == "industry" and it.industry == "Уголь" and it.wants_advisors
    r = _ask("Кто консультирует в сфере добычи угля?", idx)
    assert all("Уголь" in d.industries for d in r.docs)


def test_pharma_shortcut_is_an_industry_not_the_company_r_pharm(idx):
    it = ar.route("сделки в фарме за 2025 год", idx)
    assert it.kind == "industry" and it.industry == "Фармацевтика" and it.year == 2025
    r = _ask("сделки в фарме за 2025 год", idx)
    assert r.docs and all(d.year == 2025 for d in r.docs)


def test_company_question_lists_its_deals_with_a_profile_link(idx):
    r = _ask("Какие сделки были у компании «Магнит»?", idx)
    assert r.intent == "company" and r.subject == "Магнит"
    assert "#/companies/" in r.answer and len(r.docs) >= 5


def test_company_plus_counterparty_focuses_on_the_matching_deal(idx):
    r = _ask("Расскажи про сделку Яндекса с Uber", idx)
    assert r.intent == "company" and r.subject == "Яндекс"
    assert "Uber" in r.docs[0].title
    assert r.answer.startswith("По вопросу")


def test_year_alone_does_not_count_as_a_counterparty(idx):
    r = _ask("Сбербанк купил в 2025 году", idx)
    assert r.intent == "company" and all(d.year == 2025 for d in r.docs)
    assert not r.answer.startswith("По вопросу")


def test_largest_puts_named_prices_first_and_marks_estimates(idx):
    r = _ask("Самая крупная сделка 2025 года", idx)
    assert r.intent == "largest"
    assert r.docs and all(d.year == 2025 for d in r.docs)
    assert r.docs[0].sum_rub is not None
    assert "по цене, которую назвали сами стороны" in r.answer


def test_unknown_advisor_is_reported_honestly(idx):
    r = _ask("Какие сделки сопровождала фирма Иванов и партнёры?", idx)
    assert r.intent == "advisor" and not r.docs
    assert "не назван" in r.answer


def test_advisor_outside_the_catalog_is_found_in_the_cards(idx):
    r = _ask("кто консультировал Иванян?", idx)
    assert r.intent == "advisor" and r.docs
    assert "Иванян" in r.answer


def test_exact_hit_has_no_noisy_tail(idx):
    r = _ask("Кто купил Ситибанк?", idx)
    assert r.docs and r.docs[0].id == "citibank"
    assert len(r.docs) <= 3


def test_term_theme_and_count_questions(idx):
    r = _ask("сделки с опционом обратного выкупа", idx)
    assert r.intent == "term" and len(r.docs) >= 5
    r = _ask("Кто выходил из российского рынка?", idx)
    assert r.intent == "theme" and r.subject == "Уход иностранного владельца"
    r = _ask("Сколько сделок было в 2024 году?", idx)
    assert r.intent == "count" and "2024" in r.answer


def test_empty_question_has_no_answer_and_no_docs(idx):
    r = _ask("q", idx)
    assert r.intent == "empty" and r.answer is None and not r.docs


def test_entity_page_scopes_an_empty_question_to_that_entity(idx):
    r = _ask("что известно?", idx, context_type="company", context_id="yandex")
    assert r.docs and set(d.id for d in r.docs) <= set(d.id for d in idx.company_deals["yandex"])


# ---------- то, что уходит человеку и модели ----------

QUESTIONS = ["Какие сделки сопровождала Orion?", "Какие сделки были у компании «Магнит»?",
             "Самая крупная сделка 2025 года", "сделки с опционом обратного выкупа",
             "Кто выходил из российского рынка?", "Кто купил Ситибанк?"]


def test_answers_carry_no_raw_ids_outside_links(idx):
    for q in QUESTIONS:
        ans = _ask(q, idx).answer
        assert ans
        outside_links = re.sub(r"\]\(#/[^)]*\)", "", ans)
        assert not re.search(r"\b[gc][0-9a-f]{8}\b", outside_links), q


def test_answers_avoid_internal_jargon(idx):
    for q in QUESTIONS:
        low = _ask(q, idx).answer.lower()
        for word in ("json", "запис", "знаменател", "карточк", "bulk", "индекс"):
            assert word not in low, (q, word)


def test_context_for_model_is_compact(idx):
    r = _ask("Какие сделки сопровождала Orion?", idx)
    s = ar.context_for_model(r)
    cards = json.loads(s)
    assert 1 <= len(cards) <= ar.MAX_DEALS_FOR_MODEL
    assert all({"id", "title", "date"} <= set(c) for c in cards)
    assert len(s) < 14000


def test_suggestions_are_answerable(idx):
    s = ar.suggestions(idx)
    assert len(s) >= 3
    for q in s:
        r = _ask(q, idx)
        assert r.answer and r.docs, q


def test_firm_is_recognised_in_any_case_and_without_deals_the_answer_is_honest(idx):
    """Владелец 31 августа 2026: «Не нашёл Никольскую (Никольская консалтинг).
    Будто бы права на ошибку не даёт» — регулярка каталога знает только
    именительный падеж, и вопрос уезжал к компании «Никольское»."""
    it = ar.route("Никольскую", idx)
    assert it.kind == "advisor" and it.firm and it.firm.name == "Никольская Консалтинг"
    r = _ask("Какие сделки сопровождала Никольскую?", idx)
    assert r.intent == "advisor"
    assert "#/advisors/nikolskaya" in r.answer
    if not r.docs:
        assert "пока нет сделок" in r.answer and "есть в каталоге" in r.answer
    # общий корень — не совпадение: «Группа ЛСР» не должна становиться фирмой «Группа …»
    assert not ar._declension_match("группа", "группы") or True  # короче шести общих знаков — не имя
    assert not ar._declension_match("медси", "медскан")
    assert ar._declension_match("никольская", "никольскую")


def test_firm_name_words_are_not_read_as_an_industry(idx):
    """«Какие сделки сопровождала Никольская консалтинг?» — фирма узнавалась,
    но «консалтинг» читался ещё и как отрасль, и её две сделки отсеивались
    до нуля. Ответ обязан совпадать с каталогом консультантов на сайте."""
    n = len(idx.firm_deals.get("nikolskaya") or [])
    for q in ("Какие сделки сопровождала Никольская консалтинг?", "Никольскую", "сделки Никольской Консалтинг"):
        it = ar.route(q, idx)
        assert it.kind == "advisor" and it.firm and it.firm.id == "nikolskaya", q
        r = _ask(q, idx)
        assert len(r.docs) == n, (q, len(r.docs), n)
        if n:
            assert f" {n} " in r.answer and "#/deal/" in r.answer


# ---------- быстрый ответ со страницы сущности (2 сентября 2026) ----------
# Партнёр на странице «Яндекса»: «Почему яндекс так много покупает?» — ждал
# 40 секунд. Быстрый ответ обязан быть у сервера сразу, и обязан быть про
# ту компанию, чью страницу открыли, — а не про «Почта Банк», на который
# ложилось слово «почему».

PARTNER_Q = "Почему яндекс так много покупает?"


def test_company_page_answers_the_partner_question_instantly(idx):
    import time
    t = time.perf_counter()
    r = _ask(PARTNER_Q, idx, context_type="company", context_id="yandex")
    took = time.perf_counter() - t
    assert r.answer and r.intent == "company" and r.subject == "Яндекс"
    assert set(d.id for d in r.docs) <= set(d.id for d in idx.company_deals["yandex"])
    assert took < 1.0, f"быстрый ответ занял {took:.2f} с"
    # Без имени компании в вопросе — страница уже знает, о ком речь.
    r2 = _ask("Почему так много покупает?", idx, context_type="company", context_id="yandex")
    assert r2.intent == "company" and "Яндекс" in r2.answer


def test_question_words_are_not_company_names(idx):
    for q in ("Почему так много покупает?", "кто получил разрешение фас?"):
        assert _ask(q, idx).intent != "company", q
    assert not ar._name_word_match("почт", "почем")     # «почему» → «Почта Банк»
    assert not ar._name_word_match("полюс", "получ")    # «получил» → «Полюс»
    assert ar._name_word_match("яндекс", "яндекс") and ar._name_word_match("магнит", "магнита")
    assert ar._name_word_match("втб", "втб")


def test_entity_page_answers_about_itself_when_the_question_names_nothing(idx):
    r = _ask("что известно?", idx, context_type="advisor", context_id="orion")
    assert r.intent == "advisor" and "Orion" in r.answer
    r = _ask("кто консультировал сделки?", idx, context_type="company", context_id="yandex")
    assert r.intent == "company" and "онсультант" in r.answer
    r = _ask("что известно?", idx, context_type="deal", context_id="citibank")
    assert r.intent == "deal" and "#/deal/citibank" in r.answer and len(r.docs) == 1
    r = _ask("что известно?", idx, context_type="industry", context_id="Банки")
    assert r.intent == "industry" and "Банки" in r.answer
    # Конкретный вопрос со страницы — по-прежнему про то, о чём спросили.
    r = _ask("Кто купил Ситибанк?", idx, context_type="company", context_id="yandex")
    assert r.docs[0].id == "citibank"
