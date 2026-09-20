# -*- coding: utf-8 -*-
"""Очередь находок аудита: память о разобранном не должна врать."""
import io
import json

from pipeline import audit_queue as aq

FINDINGS = aq.load_findings()
KEYS = {aq.key_of(f) for f in FINDINGS}
DONE = aq.load_done()
DATA = json.load(io.open(aq.DATA, encoding="utf-8"))
CARDS = {d["id"]: d for d in DATA["deals"]}


def test_every_closed_finding_exists():
    unknown = set(DONE) - KEYS
    assert not unknown, "закрыто то, чего нет в списке находок: %s" % sorted(unknown)[:5]


def test_closing_note_says_what_was_done():
    for k, note in DONE.items():
        assert len(note) > 40, "слишком короткая запись о том, чем закрыто: %s" % k
        assert "2026" in note, "не сказано, когда закрыто: %s" % k


def test_finding_keys_are_unique_enough():
    assert len(KEYS) > len(FINDINGS) * 0.95, (
        "ключи находок слишком часто совпадают: %d ключей на %d находок"
        % (len(KEYS), len(FINDINGS)))


def test_ipo_cards_do_not_buy_themselves():
    """Та же проверка, что и в приёмке, но по всей живой базе."""
    bad = [d["id"] for d in DATA["deals"]
           if (d.get("type") or "") == "IPO" and d.get("buyer") and not d.get("target")
           and "фонд" not in (d.get("title") or "").lower()]
    assert not bad, "эмитент стоит покупателем: %s" % bad


def test_the_sum_on_the_overview_is_the_sum_in_the_economist():
    """Пустая сумма в «Экономисте» при заполненной на «Обзоре» — молчание
    там, где цена известна (аудит 13 сентября 2026, сквозной паттерн 2)."""
    silent = [d["id"] for d in DATA["deals"]
              if (d.get("sum") or "").strip() not in ("", "Не раскрыта")
              and isinstance(d.get("eco"), dict)
              and ((d["eco"].get("sum") or "").strip() in ("", "—", "-", "–"))]
    assert not silent, "сумма есть на «Обзоре», но не в «Экономисте»: %s" % silent[:5]


def test_no_tilde_instead_of_the_approximation_sign_in_sums():
    bad = [d["id"] for d in DATA["deals"]
           if "~" in (d.get("sum") or "")
           or "~" in ((d.get("eco") or {}).get("sum") or "")]
    assert not bad, "тильда вместо «≈» в сумме: %s" % bad[:5]


def test_queue_state_is_computed_from_todays_data():
    """Находка, чей дефект уже починен, в очередь возвращаться не должна."""
    fixed = [f for f in FINDINGS
             if f["class"] == "SUM_FIELDS_DIFFER" and f["card_id"] in CARDS]
    assert fixed, "в списке нет находок этого класса — проверять нечего"
    assert any(not aq.still_broken(CARDS[f["card_id"]], f["class"]) for f in fixed)
