# -*- coding: utf-8 -*-
"""Книга финмодели сходится с двойником на Python — клетка за клеткой.

Зачем тест, а не разовая сверка. Формулы в Excel не читаются глазами, и
22 сентября 2026 ошибка INDEX добавила во втором месяце подписчиков, которых
там быть не могло: её нашла только сверка книги с `finance/check_model.py`.
Тест держит эту сверку на каждом коммите — и заодно ловит книгу, собранную
без пересчёта (на телефоне такая показывает нули).
"""
import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "finance"))
import check_model as cm  # noqa: E402

BOOK = ROOT / "finance" / "Компас_финмодель_24м.xlsx"


@pytest.fixture(scope="module")
def book():
    return openpyxl.load_workbook(BOOK, data_only=True)


def _rows_by_label(ws):
    out = {}
    for row in ws.iter_rows(min_col=1, max_col=1):
        v = row[0].value
        if isinstance(v, str):
            out.setdefault(v.strip(), row[0].row)
    return out


def _close(x, y):
    return x is not None and abs(float(x) - y) <= max(0.5, abs(y) * 0.001)


def test_every_formula_has_a_computed_value():
    """Книга пересчитана: у каждой формулы рядом лежит значение."""
    formulas = openpyxl.load_workbook(BOOK)
    values = openpyxl.load_workbook(BOOK, data_only=True)
    empty = [(ws.title, c.coordinate)
             for ws in formulas for row in ws.iter_rows() for c in row
             if isinstance(c.value, str) and c.value.startswith("=")
             and values[ws.title][c.coordinate].value is None]
    assert not empty, "формулы без посчитанного значения (соберите через build_model.py): %s" % empty[:5]


def test_monthly_sheet_matches_the_twin(book):
    ws = book["По месяцам"]
    idx = _rows_by_label(ws)
    rows = cm.run()
    pairs = [("Регистраций за месяц", "reg"), ("Платящих на конец месяца", "paid"),
             ("Pro на конец месяца", "corp"), ("Выручка от Pro", "corp_rev"),
             ("Выручка всего", "rev"), ("Расходы всего", "costs"),
             ("Налоги всего", "taxes"), ("Чистая прибыль", "net"),
             ("Деньги на конец месяца", "cash")]
    bad = []
    for label, key in pairs:
        for i in range(cm.MONTHS):
            x = ws.cell(row=idx[label], column=2 + i).value
            if not _close(x, rows[i][key]):
                bad.append((label, i + 1, x, round(rows[i][key], 2)))
    assert not bad, bad[:10]


def test_unit_economics_sheet_matches_the_twin(book):
    ws = book["Экономика клиента"]
    idx = _rows_by_label(ws)
    u = cm.unit()
    pairs = [("ВКЛАД ОДНОГО ПОДПИСЧИКА В МЕСЯЦ", "contrib"), ("LTV ÷ CAC", "ratio"),
             ("ВКЛАД ОДНОГО ДОГОВОРА В МЕСЯЦ", "corp_contrib"),
             ("Один Pro = столько подписчиков One", "corp_eq"),
             ("Постоянные расходы в месяц", "fixed"),
             ("Нужно подписчиков One, если нет Pro", "be"),
             ("Нужно договоров Pro, если нет One", "be_corp")]
    bad = [(label, ws.cell(row=idx[label], column=2).value, u[key])
           for label, key in pairs if not _close(ws.cell(row=idx[label], column=2).value, u[key])]
    assert not bad, bad


def test_assumptions_sheet_holds_the_twin_numbers(book):
    """Жёлтые клетки и двойник говорят об одних и тех же числах."""
    ws = book["Допущения"]
    idx = _rows_by_label(ws)
    for label, want in (("One, ₽ в месяц", cm.P["price_m"]), ("Pro, ₽ в год", cm.P["corp_price"]),
                        ("Новых Pro в месяц", cm.P["corp_per_month"]),
                        ("Отток в месяц", cm.P["churn"]), ("Платная реклама", cm.FIX["mkt"])):
        assert ws.cell(row=idx[label], column=2).value == want, label
