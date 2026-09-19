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


# --------------------------------------------- проверка на живых данных ---
# Числа ниже — ответ боевого сайта 19 сентября 2026, не придуманный пример.
# Придуманный пример проверяет, что код делает заложенное; живой отчёт
# проверяет, что заложенное верно — в том числе знаки строк, которые до
# этого замера были догадкой.

LUZALES_2025 = {           # ООО «Лузалес», ИНН 1112003481, лесопереработка
    "year": 2025, "revenue_rub": 10_265_287_000, "gross_profit_rub": 4_367_668_000,
    "operating_profit_rub": 1_169_669_000, "profit_before_tax_rub": -355_342_000,
    "net_profit_rub": -320_288_000, "inventory_rub": 5_528_430_000,
    "receivables_rub": 2_839_540_000, "payables_rub": 4_053_483_000,
    "full_lines": [{"title": "Отчёт о финансовых результатах", "rows": [
        {"code": "2120", "name": "Себестоимость продаж", "value_rub": 5_897_619_000},
        {"code": "2330", "name": "Проценты к уплате", "value_rub": 1_373_392_000},
        {"code": "4100", "name": "Сальдо от текущих операций", "value_rub": 177_142_000},
    ]}],
}

URBANTECH_2025 = {         # ГК «Урбантех», ИНН 9714071941, дорожные технологии
    "year": 2025, "revenue_rub": 2_367_248_000, "gross_profit_rub": 767_420_000,
    "operating_profit_rub": 163_960_000, "profit_before_tax_rub": 2_202_875_000,
    "net_profit_rub": 2_215_706_000, "inventory_rub": 380_937_000,
    "receivables_rub": 667_215_000, "payables_rub": 1_249_434_000,
    "equity_rub": 3_000_000_000,
    "full_lines": [{"title": "Отчёт о финансовых результатах", "rows": [
        {"code": "2120", "name": "Себестоимость продаж", "value_rub": 1_599_828_000},
        {"code": "2330", "name": "Проценты к уплате", "value_rub": 353_383_000},
        {"code": "4100", "name": "Сальдо от текущих операций", "value_rub": 689_855_000},
    ]}],
}


def test_expense_lines_arrive_positive_so_we_subtract_them_ourselves():
    """Знаки строк отчёта — измерены, а не угаданы. Расходные строки приходят
    ПОЛОЖИТЕЛЬНЫМИ: у «Лузалеса» 2110 − 2120 сходится с 2100 до рубля.
    Перепутать знак здесь — значит показать валовую рентабельность 142%
    вместо 42%."""
    revenue, cost = 10_265_287_000, 5_897_619_000
    assert revenue - cost == LUZALES_2025["gross_profit_rub"]
    m = _by_key(LUZALES_2025)
    assert m["gross_margin"]["value"] == 42.5


def test_sgna_is_computed_without_touching_raw_lines():
    """Коммерческие и управленческие расходы считаем как «валовая прибыль
    минус прибыль от продаж»: знак в этой формуле не участвует вовсе, и
    упрощённая форма отчётности её не ломает."""
    m = _by_key(LUZALES_2025)
    # 4 367 668 − 1 169 669 = 3 197 999 из выручки 10 265 287 → 31,15%.
    assert m["sgna_share"]["value"] == 31.2
    # Считать эту долю как разность УЖЕ ОКРУГЛЁННЫХ рентабельностей нельзя:
    # 42,5 − 11,4 = 31,1, и на экране стояли бы два числа, которые не сходятся
    # друг с другом. Поэтому каждая доля считается от своей исходной величины.
    assert round(m["gross_margin"]["value"] - m["operating_margin"]["value"], 1) == 31.1


def test_cash_cycle_counts_whole_days_not_hundredths():
    """Цикл оборотного капитала: 342 дня запасов + 101 день дебиторки −
    251 день кредиторки. Дни считаются целыми — «192,25 дня» это ложная
    точность, а не аккуратность."""
    m = _by_key(LUZALES_2025)
    assert m["cash_cycle"]["value"] == 192
    assert m["cash_cycle"]["unit"] == "дн."
    assert isinstance(m["cash_cycle"]["value"], int)
    # У «Урбантеха» цикл отрицательный — поставщики финансируют работу.
    assert _by_key(URBANTECH_2025)["cash_cycle"]["value"] == -95


def test_profit_that_did_not_come_from_sales_is_named():
    """Главная находка замера: у «Урбантеха» прибыль до налога 2,2 млрд ₽ при
    прибыли от продаж 164 млн ₽ — в тринадцать раз больше, и рентабельность
    по чистой прибыли выходит 93,6%. Само по себе это число вводит в
    заблуждение; рядом обязана стоять строка, которая говорит, откуда прибыль.
    """
    m = _by_key(URBANTECH_2025)
    assert m["net_margin"]["value"] == 93.6
    assert m["non_operating_profit"]["value_rub"] == 2_038_915_000
    # И третья строка того же сюжета: живыми деньгами пришла треть прибыли.
    assert m["cash_conversion"]["value"] == 0.31 and m["cash_conversion"]["unit"] == "₽"
    # У «Лузалеса» наоборот: прибыль от продаж съедена процентами и прочим.
    assert _by_key(LUZALES_2025)["non_operating_profit"]["value_rub"] == -1_525_011_000


def test_loss_year_hides_the_ratios_that_would_lie():
    """У «Лузалеса» чистый убыток: отдачу на капитал и «деньги на рубль
    прибыли» в таком году не считаем — делить на убыток бессмысленно, а
    отрицательное отношение читается как достижение."""
    m = _by_key(LUZALES_2025)
    assert "cash_conversion" not in m
    assert "roe" not in m
    # Но рентабельность по чистой прибыли остаётся: −3,1% это честный факт.
    assert m["net_margin"]["value"] == -3.1
