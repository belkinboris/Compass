"""Инварианты базы: то, что должно быть верно после любого прогона pipeline.

Раньше эти проверки жили одноразовыми скриптами в прогонах и умирали вместе с
ними: каждое соглашение из CLAUDE.md приходилось перепроверять руками. Здесь
закреплены те инварианты, которые сегодня держатся, — тест, падающий с первого
дня, никто не чинит, его отключают.

Запуск: python3 -m pytest test_data.py -q
"""
import json
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "static" / "data" / "deals_promoted.json"
INDEX = ROOT / "static" / "index.html"
REF_FIELDS = ("buyer", "target", "seller_id", "asset_id")


@pytest.fixture(scope="module")
def base():
    return json.loads(DATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def deals(base):
    return base["deals"]


@pytest.fixture(scope="module")
def all_company_ids(base):
    """Профили лежат в двух местах: JSON и захардкоженный блок в index.html.

    Без второго 68 ссылок из сделок выглядят битыми, хотя они рабочие.
    """
    html = INDEX.read_text(encoding="utf-8")
    tail = html[html.index("const COMPANIES = {"):]
    block = tail[:tail.index("\n};")]
    hardcoded = set(re.findall(r"^\s{2}([A-Za-z0-9_-]+)\s*:\s*\{", block, re.M))
    assert hardcoded, "не удалось прочитать захардкоженные профили из index.html"
    return set(base["companies"]) | hardcoded


def ids_of(rows):
    return [r["id"] for r in rows]


# ---------- целостность ----------

def test_ids_unique(deals):
    dups = [i for i, n in Counter(ids_of(deals)).items() if n > 1]
    assert not dups, f"повторяющиеся id сделок: {dups[:5]}"


def test_company_refs_resolve(deals, all_company_ids):
    broken = [(d["id"], f, d[f]) for d in deals for f in REF_FIELDS
              if d.get(f) and d[f] not in all_company_ids]
    assert not broken, f"ссылки на несуществующие профили: {broken[:5]}"


def test_match_keys_point_to_existing_profiles(base, all_company_ids):
    orphan = [k for k in base["match_keys"] if k not in all_company_ids]
    assert not orphan, f"match_keys без профиля: {orphan[:5]}"


def test_match_key_aliases_are_non_empty_strings(base):
    """Пустой СПИСОК алиасов допустим и осмыслен: у профиля «Первый» он пуст
    нарочно — по такому слову автопоиск дал бы сплошные ложные совпадения.
    А вот пустая строка внутри списка совпала бы с чем угодно."""
    bad = [k for k, v in base["match_keys"].items()
           if any(not str(x).strip() for x in v)]
    assert not bad, f"пустые алиасы: {bad[:5]}"


# ---------- роли сторон ----------

def test_buyer_is_not_seller(deals):
    conflict = [(d["id"], d["buyer"]) for d in deals
                if d.get("buyer") and d.get("buyer") == d.get("seller_id")]
    assert not conflict, f"компания одновременно покупатель и продавец: {conflict[:5]}"


PLACEHOLDER = re.compile(
    r"^(?:[—-]|н/д|не\s+раскры[а-яё]*|публично\s+не\s+[а-яё]+)[.\s]*$", re.I)


def test_seller_is_not_a_placeholder(deals):
    """«Продавец: не раскрыт» — это пустое поле, а не имя стороны."""
    bad = [(d["id"], d["seller"]) for d in deals
           if d.get("seller") and PLACEHOLDER.match(str(d["seller"]).strip())]
    assert not bad, f"заглушка записана как продавец: {bad[:5]}"


# ---------- обязательные поля ----------

def test_every_deal_has_a_source_link(deals):
    bad = [d["id"] for d in deals
           if not (d.get("src") and any(str(s[1]).startswith("http")
                                        for s in d["src"] if len(s) > 1))]
    assert not bad, f"сделки без ссылки на источник: {bad[:5]}"


def test_dates_are_parseable(deals):
    bad = [(d["id"], d.get("date")) for d in deals
           if not re.fullmatch(r"\d{4}-\d{2}-\d{2}|unknown", str(d.get("date") or ""))]
    assert not bad, f"нераспознаваемая дата: {bad[:5]}"


def test_industry_is_set(deals):
    bad = [d["id"] for d in deals if not d.get("ind")]
    assert not bad, f"сделки без отрасли: {bad[:5]}"


def test_industries_are_from_the_known_list(deals):
    html = INDEX.read_text(encoding="utf-8")
    listed = set(re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
                 .replace('"', '').split(","))
    listed = {x.strip() for x in listed if x.strip()}
    unknown = sorted({d["ind"] for d in deals if d.get("ind")} - listed)
    assert not unknown, f"отрасль вне списка INDUSTRIES: {unknown}"


# ---------- соглашения о записи (CLAUDE.md) ----------

WORD_CURRENCY = re.compile(
    r"\b(?:руб(?:лей|ля|\.)?|долл(?:аров|\.)?|евро|USD|EUR|RUB)\b", re.I)


def test_cover_sum_uses_currency_symbol(deals):
    """Валюта — только значком: ₽ после числа, $ и € перед (прогон 14)."""
    bad = [(d["id"], d["sum"]) for d in deals
           if d.get("sum") and WORD_CURRENCY.search(str(d["sum"]))]
    assert not bad, f"валюта словом в обложке: {bad[:5]}"


NAMED_ESTIMATOR = re.compile(r"\((?:по\s+)?оценк[а-яё]*\s+(?-i:[А-ЯЁA-Z])", re.I)


def test_estimate_note_does_not_name_the_estimator(deals):
    """Пометка недостоверности — «(по оценке)»; кто именно оценил, живёт в
    «Оценке и дисконте». Уточнение ПРЕДМЕТА оценки («оценка 100%») — не имя
    оценщика и правилу не противоречит, поэтому проверяем заглавную букву."""
    bad = [(d["id"], d["sum"]) for d in deals
           if d.get("sum") and NAMED_ESTIMATOR.search(str(d["sum"]))]
    assert not bad, f"имя оценщика в пометке суммы: {bad[:5]}"


META_OPENER = re.compile(
    r"^(?:в\s+)?(?:стать[её]|публикаци|сообщени|материал|заметк|издани)[а-яё]*\b", re.I)


def test_rationale_does_not_retell_the_article(deals):
    """«Цель сделки» описывает сделку, а не источник (прогон 9)."""
    bad = [(d["id"], str(d.get("eco", {}).get("rationale"))[:60]) for d in deals
           if META_OPENER.match(str(d.get("eco", {}).get("rationale") or "").strip())]
    assert not bad, f"пересказ статьи в «Цели сделки»: {bad[:5]}"


INTERNAL_JARGON = re.compile(r"bulk|партия\s*\d|тестовый\s+прогон|pipeline|json", re.I)


def test_company_descriptions_have_no_internal_jargon(base):
    """Описание компании — для читателя, а не рассказ о нашем процессе
    («Профиль сформирован по итогам чтения bulk-базы, партия 4») — прогон 23."""
    bad = [(cid, str(c.get("desc"))[:60]) for cid, c in base["companies"].items()
           if INTERNAL_JARGON.search(str(c.get("desc") or ""))]
    assert not bad, f"внутренняя кухня в описании профиля: {bad[:5]}"
