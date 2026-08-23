# -*- coding: utf-8 -*-
"""`classify_row()` — чистая функция, разбирает строку `Data101FNewXML` на
актив/пассив/исключено. Тесты ловят ровно тот класс регрессии, что уже был
найден вживую 23 августа 2026: пропуск фильтра по `pln` (внебалансовые и
производные счета молча попадают в сумму активов) и подсчёт `ITGAP`
(контрольного итога) как настоящего счёта."""
from pipeline.cbr_account_types import (
    ASSET,
    CAPITAL_LIABILITY,
    EXCLUDED,
    UNKNOWN,
    classify_row,
)


def test_active_balance_account_is_asset():
    kind, _ = classify_row("А", "604", "1")
    assert kind == ASSET


def test_passive_balance_account_is_capital_liability():
    kind, _ = classify_row("А", "108", "2")
    assert kind == CAPITAL_LIABILITY


def test_dotted_aggregate_code_uses_ap_same_as_plain_account():
    """«45.0»/«32.2» и т. п. — укрупнённые агрегаты, а не отдельные счета
    первого порядка, но `ap` у них читается тем же способом."""
    kind, _ = classify_row("А", "45.0", "1")
    assert kind == ASSET
    kind, _ = classify_row("А", "31.1", "2")
    assert kind == CAPITAL_LIABILITY


def test_off_balance_chapter_is_excluded_even_with_active_flag():
    """Найденный вживую баг: счета главы «В» (внебалансовые — гарантии,
    поручительства) несут `ap=1` совершенно так же, как балансовые, и без
    фильтра по `pln` тихо прибавлялись к активам банка."""
    kind, reason = classify_row("В", "90.5", "1")
    assert kind == EXCLUDED
    assert "В" in reason


def test_derivatives_chapter_is_excluded():
    kind, _ = classify_row("Г", "933", "1")
    assert kind == EXCLUDED


def test_trust_management_chapter_is_excluded():
    kind, _ = classify_row("Б", "801", "1")
    assert kind == EXCLUDED


def test_depo_chapter_is_excluded():
    kind, _ = classify_row("Д", "980", "2")
    assert kind == EXCLUDED


def test_control_total_row_is_excluded_not_counted_as_unknown():
    kind, reason = classify_row("А", "ITGAP", "1")
    assert kind == EXCLUDED
    assert "итог" in reason.lower()


def test_transit_accounts_are_excluded_regardless_of_ap():
    """303/706/612/616 — счета внутреннего оборота (клиринг, все доходы и
    расходы года и т. п.), их остаток не равен сумме на конец периода ни
    на активной, ни на пассивной стороне — см. докстроку модуля для
    источников (прямая цитата 809-П для 612, масштаб для 303/706)."""
    for account in ["303", "706", "612", "616"]:
        for ap in ["1", "2"]:
            kind, _ = classify_row("А", account, ap)
            assert kind == EXCLUDED, f"{account}/{ap} должен быть исключён"


def test_unexpected_ap_value_is_unknown_not_silently_dropped():
    kind, reason = classify_row("А", "999", "3")
    assert kind == UNKNOWN
    assert "3" in reason
