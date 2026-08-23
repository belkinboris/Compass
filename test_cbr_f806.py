# -*- coding: utf-8 -*-
"""`pipeline/cbr_f806.py` — разбор официального баланса банка (форма 806)
со страницы ЦБ. Фикстуры — реальные страницы, собранные вживую 23 августа
2026 (`pipeline/fixtures/f806_sberbank_*.html`): одна с опубликованными
цифрами, вторая — квартал, который на дату сбора ещё не был опубликован
(значения есть в разметке, но пустые)."""
from datetime import date
from pathlib import Path

from pipeline.cbr_f806 import (
    F806Balance,
    _quarter_start_on_or_before,
    _step_back_one_quarter,
    parse_balance,
)

FIXTURES = Path(__file__).resolve().parent / "pipeline" / "fixtures"


def test_parse_balance_reads_assets_and_equity_from_real_page():
    html = (FIXTURES / "f806_sberbank_202604.html").read_text(encoding="utf-8")
    balance = parse_balance(html, regnum=1481)
    assert balance is not None
    assert balance.as_of == date(2026, 4, 1)
    assert balance.assets_rub == 65_137_327_668_000
    assert balance.assets_rub_prior_year == 65_210_686_723_000
    assert balance.equity_rub == 8_627_750_211_000
    assert balance.equity_rub_prior_year == 8_115_080_880_000
    assert balance.legal_name == "Публичное акционерное общество «Сбербанк России»"


def test_parse_balance_returns_none_for_unpublished_quarter():
    """Квартал заявлен на странице, но банк ещё не отчитался — значения
    пустые (`<nobr></nobr>`), не 0 и не ошибка."""
    html = (FIXTURES / "f806_sberbank_202607_empty.html").read_text(encoding="utf-8")
    assert parse_balance(html, regnum=1481) is None


def test_parse_balance_returns_none_for_page_without_the_data_table():
    assert parse_balance("<html><body>не форма 806</body></html>", regnum=1481) is None


def test_quarter_start_on_or_before_picks_the_most_recent_quarter():
    assert _quarter_start_on_or_before(date(2026, 8, 23)) == date(2026, 7, 1)
    assert _quarter_start_on_or_before(date(2026, 4, 1)) == date(2026, 4, 1)
    assert _quarter_start_on_or_before(date(2026, 2, 15)) == date(2026, 1, 1)


def test_step_back_one_quarter_crosses_year_boundary():
    assert _step_back_one_quarter(date(2026, 4, 1)) == date(2026, 1, 1)
    assert _step_back_one_quarter(date(2026, 1, 1)) == date(2025, 10, 1)


def test_gross_from_form_101_exceeds_net_from_form_806_by_a_plausible_margin():
    """Санити-проверка метода, а не воспроизводимый тест на сеть: валовая
    сумма из формы 101 (см. CLAUDE.md, «Активы/капитал банков через ЦБ»)
    обязана быть БОЛЬШЕ чистой цифры формы 806 на разумные 3-20% (живой
    замер 23 августа дал 103-116% на трёх банках), а не меньше и не в разы
    больше — если разница выйдет за эти рамки, один из двух разборов
    (101 или 806) сломан."""
    gross_by_net_ratio = {
        "Сбербанк": (73.61, 65.14),
        "ВТБ": (39.23, 34.87),
        "Альфа-Банк": (15.49, 13.35),
    }
    for name, (gross, net) in gross_by_net_ratio.items():
        ratio = gross / net
        assert 1.03 <= ratio <= 1.20, f"{name}: gross/net={ratio:.2f} вне ожидаемого диапазона"


def test_f806balance_is_a_frozen_dataclass_with_expected_fields():
    b = F806Balance(regnum=1481, as_of=date(2026, 4, 1), assets_rub=1, assets_rub_prior_year=2,
                     equity_rub=3, equity_rub_prior_year=4, legal_name="Тест")
    assert b.regnum == 1481 and b.assets_rub == 1 and b.equity_rub == 3
