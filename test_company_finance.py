# -*- coding: utf-8 -*-
"""Показатели, посчитанные из отчётности: арифметика и границы честности.

Запуск: python3 -m pytest test_company_finance.py -q
"""
import company_finance as cf


def _report(**kw):
    base = {
        "year": 2024,
        "revenue_rub": 10_000_000_000.0,
        "gross_profit_rub": 3_000_000_000.0,
        "operating_profit_rub": 2_000_000_000.0,
        "profit_before_tax_rub": 1_500_000_000.0,
        "net_profit_rub": 1_200_000_000.0,
        "assets_rub": 20_000_000_000.0,
        "current_assets_rub": 8_000_000_000.0,
        "short_term_liabilities_rub": 5_000_000_000.0,
        "long_term_liabilities_rub": 4_000_000_000.0,
        "equity_rub": 11_000_000_000.0,
        "borrowings_rub": 6_000_000_000.0,
        "cash_rub": 1_000_000_000.0,
        "inventory_rub": 2_000_000_000.0,
        "receivables_rub": 3_000_000_000.0,
        "payables_rub": 1_500_000_000.0,
        "full_lines": [{"title": "Отчёт о финансовых результатах", "rows": [
            {"code": "2330", "name": "Проценты к уплате", "value_rub": 500_000_000},
        ]}],
    }
    base.update(kw)
    return base


def _by_key(report):
    return {m["key"]: m for m in cf.derive(report)["metrics"]}


def test_working_capital_and_debt_are_counted():
    m = _by_key(_report())
    assert m["working_capital"]["value_rub"] == 3_000_000_000.0     # 8 − 5
    assert m["operating_working_capital"]["value_rub"] == 3_500_000_000.0  # 2 + 3 − 1,5
    assert m["net_debt"]["value_rub"] == 5_000_000_000.0            # 6 − 1
    assert round(m["debt_to_equity"]["value"], 3) == round(6 / 11, 2)
    assert m["net_debt_to_operating_profit"]["value"] == 2.5        # 5 / 2
    assert m["interest_coverage"]["value"] == 4.0                   # 2 / 0,5
    assert m["operating_margin"]["value"] == 20.0
    assert m["net_margin"]["value"] == 12.0


def test_interest_is_added_back_not_subtracted():
    """Проценты к уплате стоят в отчёте уже вычтенными из прибыли до налога.
    Знак в источнике встречается и с минусом, и без — берём модуль, иначе у
    компании с большим долгом величина уедет ровно в другую сторону."""
    plus = _by_key(_report())["ebit"]["value_rub"]
    lines = [{"title": "Отчёт о финансовых результатах",
              "rows": [{"code": "2330", "name": "Проценты к уплате", "value_rub": -500_000_000}]}]
    minus = _by_key(_report(full_lines=lines))["ebit"]["value_rub"]
    assert plus == minus == 2_000_000_000.0


def test_ebitda_is_never_promised():
    """Главное правило этого модуля: амортизации в открытой отчётности нет,
    значит EBITDA не считается. Написать это слово над числом, в котором
    амортизации нет, — соврать в самом заметном месте карточки."""
    out = cf.derive(_report())
    for m in out["metrics"]:
        assert "ebitda" not in m["key"].lower()
        assert "EBITDA" not in m["label"]
    assert any("EBITDA" in n and "нельзя" in n for n in out["notes"]), out["notes"]
    # Слово всё-таки встречается — но только чтобы объяснить, чем показатель
    # от неё отличается, а не как название самого показателя.
    assert "амортизаци" in " ".join(out["notes"]).lower()


def test_missing_line_means_no_metric_at_all():
    """Пустое поле честнее прочерка: прочерк на экране читается как
    «посчитали и вышло ноль» (то же правило, что у full_lines_payload)."""
    m = _by_key(_report(borrowings_rub=None, cash_rub=None))
    assert "debt" not in m and "net_debt" not in m and "debt_to_equity" not in m
    assert "working_capital" in m, "остальное считаться не перестаёт"
    m2 = _by_key(_report(full_lines=[]))
    assert "ebit" not in m2 and "interest_coverage" not in m2


def test_negative_equity_is_explained_not_divided():
    out = cf.derive(_report(equity_rub=-2_000_000_000.0))
    assert "debt_to_equity" not in {m["key"] for m in out["metrics"]}
    assert any("капитал отрицательный" in n for n in out["notes"])


def test_loss_year_does_not_divide_debt_by_a_loss():
    out = cf.derive(_report(operating_profit_rub=-300_000_000.0))
    keys = {m["key"] for m in out["metrics"]}
    assert "net_debt_to_operating_profit" not in keys
    assert any("делить на убыток" in n for n in out["notes"])
    # А сама прибыль от продаж и рентабельность по ней остаются — убыток это
    # факт отчётности, а не повод прятать строку.
    assert "operating_margin" in keys


def test_tiny_denominators_do_not_make_giant_ratios():
    """У спящего юрлица в отчётности встречаются рубли и десятки рублей:
    деление на них даёт «долг к капиталу ×4 000 000» — число верное и
    бессмысленное."""
    out = cf.derive(_report(equity_rub=1000.0, revenue_rub=500.0))
    keys = {m["key"] for m in out["metrics"]}
    assert "debt_to_equity" not in keys
    assert "operating_margin" not in keys and "net_margin" not in keys


def test_empty_report_gives_nothing_and_says_nothing():
    out = cf.derive({})
    assert out == {"metrics": [], "notes": []}
    assert cf.derive(None) == {"metrics": [], "notes": []}


def test_every_metric_explains_itself_in_human_words():
    """Правило CLAUDE.md «пояснение объясняет смысл числа, а не устройство
    базы»: у каждого показателя есть подпись, как он посчитан, и она без
    кодов строк отчётности и без слов нашего диалекта."""
    for m in cf.derive(_report())["metrics"]:
        assert m["how"] and len(m["how"]) > 25, m["key"]
        assert m["label"] and m["group"], m["key"]
        assert not any(code in m["how"] for code in ("1200", "1500", "2110", "2200", "2330")), m["key"]
        assert m["kind"] in ("money", "ratio", "percent")


def test_decimal_and_string_values_survive():
    """Numeric из SQLAlchemy приходит Decimal, из JSON — строкой."""
    from decimal import Decimal
    m = _by_key(_report(current_assets_rub=Decimal("8000000000"),
                        short_term_liabilities_rub="5000000000"))
    assert m["working_capital"]["value_rub"] == 3_000_000_000.0
