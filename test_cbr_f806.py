# -*- coding: utf-8 -*-
"""`pipeline/cbr_f806.py` — разбор официального баланса банка (форма 806)
со страницы ЦБ. Фикстуры — реальные страницы, собранные вживую 23 августа
2026 (`pipeline/fixtures/f806_sberbank_*.html`): одна с опубликованными
цифрами, вторая — квартал, который на дату сбора ещё не был опубликован
(значения есть в разметке, но пустые)."""
from datetime import date
from pathlib import Path

from pipeline.cbr_f806 import (
    BALANCE_SECTIONS,
    F806Balance,
    _quarter_start_on_or_before,
    _step_back_one_quarter,
    parse_balance,
    parse_full_table,
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


def test_parse_full_table_covers_all_three_balance_sections():
    """Этап 8, П2-8: владелец и партнёр попросили полный баланс («Активы и
    пассивы, 1-2 странички»), не только два итога. Разделы I-III — реальные
    цифры Сбербанка на 1.04.2026 (сверено вручную по той же странице)."""
    html = (FIXTURES / "f806_sberbank_202604.html").read_text(encoding="utf-8")
    table = parse_full_table(html)
    assert table is not None
    assert table["as_of"] == date(2026, 4, 1)
    assert table["legal_name"] == "Публичное акционерное общество «Сбербанк России»"
    titles = [s["title"] for s in table["sections"]]
    assert titles == list(BALANCE_SECTIONS), "разделы обязаны идти в порядке страницы, ровно I-III"

    by_title = {s["title"]: s for s in table["sections"]}
    assert len(by_title["I. Активы"]["rows"]) == 16
    assert len(by_title["II. Пассивы"]["rows"]) == 17
    assert len(by_title["III. Источники собственных средств"]["rows"]) == 14

    total_row = by_title["I. Активы"]["rows"][-1]
    assert total_row["name"] == "Всего активов"
    assert total_row["period_rub"] == 65_137_327_668_000
    assert total_row["prior_year_rub"] == 65_210_686_723_000

    first_row = by_title["I. Активы"]["rows"][0]
    assert first_row["num"] == "1"
    assert first_row["name"] == "Денежные средства"
    assert first_row["period_rub"] == 702_499_267_000


def test_parse_full_table_keeps_negative_values_and_empty_rows():
    """«Переоценка финансовых активов» у Сбербанка отрицательна (убыток по
    справедливой стоимости), а часть строк (например «Инвестиции в дочерние
    и зависимые организации») не заполнена вовсе — обе особенности должны
    пережить разбор, а не сломать его или тихо занулиться."""
    html = (FIXTURES / "f806_sberbank_202604.html").read_text(encoding="utf-8")
    table = parse_full_table(html)
    by_title = {s["title"]: s for s in table["sections"]}
    rows_by_name = {r["name"]: r for r in by_title["III. Источники собственных средств"]["rows"]}
    revaluation = rows_by_name["Переоценка финансовых активов, оцениваемых по справедливой стоимости через прочий совокупный доход, "
                                "уменьшенная на отложенное налоговое обязательство (увеличенная на отложенный налоговый актив)"]
    assert revaluation["period_rub"] == -311_872_957_000
    assert revaluation["prior_year_rub"] == -333_059_648_000

    assets_rows = {r["name"]: r for r in by_title["I. Активы"]["rows"]}
    empty_row = assets_rows["Прочие активы"]
    assert empty_row["period_rub"] is None
    assert empty_row["prior_year_rub"] is None


def test_parse_full_table_excludes_off_balance_section():
    """Раздел IV «Внебалансовые обязательства» на той же странице — уже не
    баланс в бухгалтерском смысле (гарантии, условные обязательства), и не
    входит в «1-2 странички», о которых просили; сознательно не разбирается."""
    html = (FIXTURES / "f806_sberbank_202604.html").read_text(encoding="utf-8")
    table = parse_full_table(html)
    titles = [s["title"] for s in table["sections"]]
    assert "IV. Внебалансовые обязательства" not in titles
    all_names = [r["name"] for s in table["sections"] for r in s["rows"]]
    assert "Безотзывные обязательства кредитной организации" not in all_names


def test_parse_full_table_returns_none_for_unpublished_quarter():
    html = (FIXTURES / "f806_sberbank_202607_empty.html").read_text(encoding="utf-8")
    assert parse_full_table(html) is None


def test_parse_full_table_returns_none_for_page_without_the_data_table():
    assert parse_full_table("<html><body>не форма 806</body></html>") is None
