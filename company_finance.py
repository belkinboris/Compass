# -*- coding: utf-8 -*-
"""Показатели, которые считаются ИЗ отчётности, а не лежат в ней готовыми.

Просьба Дани (19 сентября 2026): «из БФО реально наверное из финансовых
результатов можно подгрузить ебитду», плюс оборотный капитал и
закредитованность. Разбор, что из этого правда:

  * ОБОРОТНЫЙ КАПИТАЛ и ЗАКРЕДИТОВАННОСТЬ — считаются полностью, из строк,
    которые у нас уже лежат в базе с первого дня синхронизации с ФНС
    (`db/models.FinancialReport`). Отдельно ходить никуда не нужно.
  * EBITDA — НЕ СЧИТАЕТСЯ, и это не «пока не сделали», а свойство
    источника. Амортизации нет ни в балансе, ни в отчёте о финансовых
    результатах, ни в отчёте о движении денежных средств: её раскрывают в
    пояснениях к отчётности, а в ГИР БО пояснения машинно не отдаются
    (см. `fns_client.FULL_LINE_SECTIONS` — весь набор строк, который
    приходит от API, там перечислен построчно). Написать «EBITDA» над
    числом, в котором нет амортизации, значит соврать в самом заметном
    месте карточки — тем более что у производственной компании амортизация
    легко составляет десятки процентов этой величины.

    Поэтому считаем и называем своим именем то, что действительно
    выводится: прибыль до процентов и налога (2300 + 2330). Это ближайшая
    к EBITDA величина из открытых данных, и в подписи прямо сказано, чем
    она от EBITDA отличается. Тот же принцип, по которому мультипликаторы
    считаются «цена ÷ выручка или операционная прибыль», а не «EV/EBITDA»,
    которого у нас нет (CLAUDE.md, разбор рецензента, находка 7).

ГРАНИЦА МОДУЛЯ. Здесь только арифметика над одним годом одного юрлица: ни
сети, ни базы, ни суждений о периметре. Вопрос «описывает ли отчётность
этого юрлица купленный бизнес» решается чтением в слое фактов и сюда не
относится — на профиле компании мы показываем показатели ИМЕННО ЭТОГО
юрлица и так и подписываем.

ОДИН ИСПОЛНИТЕЛЬ. Считает сервер, клиент только рисует готовые числа с
готовыми подписями (`static/index.html`, вкладка «Финансы»). Клиентских
копий формул нет намеренно: две копии правил в Python и JS уже разъезжались
(CLAUDE.md, «Слой фактов»), и повторять это ради четырёх делений незачем.
"""
from __future__ import annotations

# Знаменатель меньше этой величины считаем нулём: у спящего юрлица в
# отчётности встречаются рубли и десятки рублей, и деление на них даёт
# «долг к капиталу ×4 000 000» — число верное и бессмысленное.
MIN_DENOMINATOR_RUB = 100_000.0

# Строка отчёта о финансовых результатах, которой нет среди 15
# нормализованных полей: проценты к уплате. Берём из полного набора строк.
INTEREST_PAID_CODE = "2330"


def _f(value) -> float | None:
    """Число или None. Numeric из SQLAlchemy приходит как Decimal, из JSON —
    как int/float/str; всё это одинаково годится для арифметики."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _line(full_lines, code: str) -> float | None:
    """Значение строки БФО по коду из payload полной отчётности (уже в рублях,
    см. `fns_client.full_lines_payload`)."""
    for section in full_lines or []:
        for row in section.get("rows") or []:
            if row.get("code") == code:
                return _f(row.get("value_rub"))
    return None


def _money(key, label, value, how, group):
    return {"key": key, "label": label, "kind": "money",
            "value_rub": value, "how": how, "group": group}


def _ratio(key, label, value, how, group, unit="x"):
    return {"key": key, "label": label, "kind": "ratio",
            "value": round(value, 2), "unit": unit, "how": how, "group": group}


def _percent(key, label, value, how, group):
    return {"key": key, "label": label, "kind": "percent",
            "value": round(value, 1), "how": how, "group": group}


def derive(report: dict) -> dict:
    """Посчитанное по одному годовому отчёту.

    На входе — payload отчёта (`main._report_payload`): 15 нормализованных
    полей в рублях плюс `full_lines`. На выходе — `{"metrics": [...],
    "notes": [...]}`. Метрика, у которой не хватило исходной строки, В ОТВЕТ
    НЕ ПОПАДАЕТ ВОВСЕ: пустое поле честнее прочерка, и прочерк на экране
    читается как «посчитали и вышло ноль».
    """
    r = report or {}
    full_lines = r.get("full_lines")

    revenue = _f(r.get("revenue_rub"))
    op_profit = _f(r.get("operating_profit_rub"))
    pre_tax = _f(r.get("profit_before_tax_rub"))
    net_profit = _f(r.get("net_profit_rub"))
    current_assets = _f(r.get("current_assets_rub"))
    short_term = _f(r.get("short_term_liabilities_rub"))
    long_term = _f(r.get("long_term_liabilities_rub"))
    equity = _f(r.get("equity_rub"))
    borrowings = _f(r.get("borrowings_rub"))
    cash = _f(r.get("cash_rub"))
    inventory = _f(r.get("inventory_rub"))
    receivables = _f(r.get("receivables_rub"))
    payables = _f(r.get("payables_rub"))
    interest = _line(full_lines, INTEREST_PAID_CODE)

    metrics: list[dict] = []
    notes: list[str] = []

    # --- прибыльность --------------------------------------------------
    PROFIT = "Прибыльность"
    # Прибыль до процентов и налога. Проценты к уплате в отчёте стоят со
    # знаком «минус» внутри прибыли до налогообложения — прибавляем модуль,
    # иначе у компании с большим долгом величина уедет в другую сторону.
    if pre_tax is not None and interest is not None:
        metrics.append(_money(
            "ebit", "Прибыль до процентов и налога", pre_tax + abs(interest),
            "Прибыль до налогообложения плюс проценты по кредитам. "
            "От EBITDA отличается на амортизацию — её в открытой отчётности не раскрывают.",
            PROFIT))
    if revenue is not None and revenue >= MIN_DENOMINATOR_RUB and op_profit is not None:
        metrics.append(_percent(
            "operating_margin", "Рентабельность по прибыли от продаж",
            op_profit / revenue * 100,
            "Прибыль от продаж, делённая на выручку.", PROFIT))
    if revenue is not None and revenue >= MIN_DENOMINATOR_RUB and net_profit is not None:
        metrics.append(_percent(
            "net_margin", "Рентабельность по чистой прибыли",
            net_profit / revenue * 100,
            "Чистая прибыль, делённая на выручку.", PROFIT))

    # --- оборотный капитал ----------------------------------------------
    WC = "Оборотный капитал"
    if current_assets is not None and short_term is not None:
        metrics.append(_money(
            "working_capital", "Оборотный капитал", current_assets - short_term,
            "Оборотные активы минус краткосрочные обязательства. "
            "Со знаком «минус» — короткие долги больше того, чем компания может их закрыть.",
            WC))
    # Операционный рабочий капитал — то, что в сделках обсуждают как «уровень
    # оборотного капитала на закрытии»: запасы и дебиторка за вычетом того,
    # что компания должна поставщикам. Деньги и кредиты сюда не входят.
    if inventory is not None and receivables is not None and payables is not None:
        metrics.append(_money(
            "operating_working_capital", "Запасы и дебиторка за вычетом кредиторки",
            inventory + receivables - payables,
            "Запасы плюс дебиторская задолженность минус кредиторская. "
            "Столько денег заморожено в текущей работе компании.", WC))

    # --- долговая нагрузка ----------------------------------------------
    DEBT = "Долговая нагрузка"
    if borrowings is not None:
        metrics.append(_money(
            "debt", "Кредиты и займы", borrowings,
            "Долгосрочные и краткосрочные заёмные средства вместе. "
            "Задолженность перед поставщиками сюда не входит.", DEBT))
        if cash is not None:
            metrics.append(_money(
                "net_debt", "Чистый долг", borrowings - cash,
                "Кредиты и займы минус деньги на счетах. "
                "Со знаком «минус» — денег на счетах больше, чем долгов.", DEBT))
        if equity is not None and equity >= MIN_DENOMINATOR_RUB:
            metrics.append(_ratio(
                "debt_to_equity", "Долг к собственному капиталу", borrowings / equity,
                "Кредиты и займы, делённые на собственный капитал.", DEBT))
        elif equity is not None and equity < 0:
            notes.append(
                "Собственный капитал отрицательный — накопленные убытки превысили вложения "
                "в компанию. Отношение долга к капиталу в таком случае не считают.")
        if op_profit is not None and cash is not None:
            if op_profit >= MIN_DENOMINATOR_RUB:
                metrics.append(_ratio(
                    "net_debt_to_operating_profit", "Чистый долг к прибыли от продаж",
                    (borrowings - cash) / op_profit,
                    "Примерно столько лет компании нужно работать с такой же прибылью, "
                    "чтобы закрыть долг. Обычно это отношение считают к EBITDA — "
                    "её по открытой отчётности не посчитать, поэтому в знаменателе прибыль от продаж.",
                    DEBT))
            elif op_profit <= 0:
                notes.append(
                    "Прибыли от продаж за этот год нет, поэтому отношение долга к прибыли "
                    "не считаем: делить на убыток бессмысленно.")
    if op_profit is not None and interest is not None and abs(interest) >= MIN_DENOMINATOR_RUB:
        metrics.append(_ratio(
            "interest_coverage", "Прибыль от продаж к процентам по кредитам",
            op_profit / abs(interest),
            "Во сколько раз прибыль от продаж больше процентов, которые компания платит "
            "по кредитам. Меньше единицы — прибыли не хватает даже на проценты.", DEBT))

    if not metrics:
        return {"metrics": [], "notes": []}

    notes.append(
        "EBITDA по открытой отчётности посчитать нельзя: амортизацию раскрывают в "
        "пояснениях к отчётности, а они в машинном виде не публикуются. Ближайшее, что "
        "считается, — прибыль до процентов и налога.")
    return {"metrics": metrics, "notes": notes}
