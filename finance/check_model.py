# -*- coding: utf-8 -*-
"""Двойник финмодели на Python: те же допущения, тот же счёт, без Excel.

Зачем двойник. Формулы в книге нельзя проверить глазами, а openpyxl их не
считает. Этот файл считает то же самое обычным кодом, а
`test_finance_model.py` сверяет книгу с ним клетка за клеткой: так 22
сентября 2026 нашлась ошибка INDEX, из-за которой во втором месяце
появлялись подписчики, которых там быть не могло.

    python3 finance/check_model.py
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MONTHS = 24


def xlround(x):
    """Округление как в Excel — половину вверх, а не к чётному (62,5 -> 63)."""
    return float(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# Те же числа, что на листе «Допущения» в build_model.py.
P = dict(price_m=990, price_y=9900, share_y=0.22, churn=0.10, refund=0.05,
         ceiling=25000, pay_share=0.035, reg_org0=25, reg_growth=0.10,
         cpr=800, conv=0.07, conv_lag=2, ai_q=12, ai_cost_q=1.0,
         corp_price=49900, corp_per_month=2.0, corp_start=4,
         corp_churn=0.20, corp_var=400)
FIX = dict(timeweb=5300, ycloud=7000, claude_sub=20000, office=1908,
           fns=8000, kassa=2500, acc=7000, legal=10000, mkt=30000, misc=8000,
           gd_salary=0, team_cost=0)
INJURY_YEAR = 2959.0
DEV_FREE, DEV1_UNTIL, DEV1_COST, DEV2_COST = 6, 12, 50000, 100000
ACQ = 0.030
USN, USN_MIN, VAT_LIMIT, VAT_RATE = 0.20, 0.03, 60_000_000, 0.05
CASH0 = 500_000


def dev_cost(month, d1=None, d2=None):
    """month — номер месяца от старта, начиная с 1."""
    d1 = DEV1_COST if d1 is None else d1
    d2 = DEV2_COST if d2 is None else d2
    if month <= DEV_FREE:
        return 0
    return d1 if month <= DEV1_UNTIL else d2


def unit(p=P, fix=None):
    fix = FIX if fix is None else fix
    arpu = p["price_m"] * (1 - p["share_y"]) + p["price_y"] / 12 * p["share_y"]
    contrib = arpu * (1 - ACQ - p["share_y"] * p["refund"] / 2) - p["ai_q"] * p["ai_cost_q"]
    ltv = contrib / p["churn"]
    cac = p["cpr"] / p["conv"]
    fixed = sum(fix.values()) + INJURY_YEAR / 12
    corp_contrib = p["corp_price"] / 12 - p["corp_var"]
    up = lambda x: int(-(-x // 1))    # noqa: E731
    return dict(arpu=arpu, contrib=contrib, ltv=ltv, cac=cac, ratio=ltv / cac,
                cpr_max=ltv * p["conv"] / 3,
                corp_contrib=corp_contrib, corp_eq=round(corp_contrib / contrib, 1),
                fixed=fixed, be=up(fixed / contrib), be_corp=up(fixed / corp_contrib),
                be_dev1=up((fixed + DEV1_COST) / contrib),
                be_dev2=up((fixed + DEV2_COST) / contrib))


def run(p=P, fix=None, d1=None, d2=None):
    """Помесячные строки. fix, d1, d2 — чтобы менять одно допущение, не трогая общих."""
    fix = FIX if fix is None else fix
    seen, regs, rows = 0.0, [], []
    paid, corp, cash, year_rev = 0.0, 0.0, float(CASH0), 0.0
    for i in range(MONTHS):
        org = p["reg_org0"] * (1 + p["reg_growth"]) ** i
        room = max(0.0, 1 - seen / p["ceiling"]) if i else 1.0
        reg = xlround((org + fix["mkt"] / p["cpr"]) * room)
        regs.append(reg)
        seen += reg

        j = i - p["conv_lag"]
        new = xlround(regs[j] * p["conv"]) if j >= 0 else 0
        sy = p["share_y"] * i / MONTHS
        paid = min(paid * (1 - p["churn"] * (1 - sy)) + new, p["ceiling"] * p["pay_share"])

        m = i + 1
        corp_new = p["corp_per_month"] if m >= p["corp_start"] else 0.0
        corp = corp * (1 - p["corp_churn"] / 12) + corp_new
        corp_rev = corp * p["corp_price"] / 12

        rev_b2c = paid * (p["price_m"] * (1 - sy) + p["price_y"] / 12 * sy)
        rev = rev_b2c + corp_rev
        year_sold = new * sy * p["price_y"]
        cash_in = rev_b2c + year_sold - new * sy * p["price_y"] / 12 + corp_new * p["corp_price"]

        costs = (sum(fix.values()) + p["ai_q"] * p["ai_cost_q"] * paid
                 + corp * p["corp_var"] + cash_in * ACQ + year_sold * p["refund"] / 2
                 + dev_cost(m, d1, d2) + INJURY_YEAR / 12)

        if i == 3:          # январь: новый календарный год
            year_rev = 0.0
        year_rev += rev
        vat = rev * VAT_RATE if year_rev > VAT_LIMIT else 0.0
        taxes = vat + max((rev - costs - vat) * USN, rev * USN_MIN)
        net = rev - costs - taxes
        cash += cash_in - costs - taxes
        rows.append(dict(m=m, reg=reg, paid=paid, corp=corp, corp_rev=corp_rev,
                         rev=rev, costs=costs, taxes=taxes, net=net, cash=cash))
    return rows


def first_plus(rows):
    return next((x["m"] for x in rows if x["net"] > 0), None)


def money(x):
    return "%s ₽" % format(int(round(x)), ",d").replace(",", " ")


def main():
    u, rows = unit(), run()
    print("ОДИН КЛИЕНТ")
    for title, v in (("Вклад подписчика One в месяц", money(u["contrib"])),
                     ("Вклад договора Pro в месяц", money(u["corp_contrib"])),
                     ("Один Pro = подписчиков One", "%.1f" % u["corp_eq"]),
                     ("LTV ÷ CAC", "%.2f" % u["ratio"]),
                     ("Цена регистрации, при которой реклама окупается втрое", money(u["cpr_max"])),
                     ("Постоянные расходы в месяц", money(u["fixed"])),
                     ("Порог: подписчиков One без Pro", u["be"]),
                     ("Порог: договоров Pro без One", u["be_corp"]),
                     ("  подписчиков One с разработчиком за 100 тыс", u["be_dev2"])):
        print("  %-56s %12s" % (title, v))

    print()
    print("ДВА ГОДА")
    cash_low = min(x["cash"] for x in rows)
    for title, v in (("Платящих One через 12 / 24 месяца",
                      "%d / %d" % (round(rows[11]["paid"]), round(rows[23]["paid"]))),
                     ("Договоров Pro через 24 месяца", "%.1f" % rows[23]["corp"]),
                     ("Выручка за 24 месяца", money(sum(x["rev"] for x in rows))),
                     ("  из неё от Pro", money(sum(x["corp_rev"] for x in rows))),
                     ("Чистая прибыль за 24 месяца", money(sum(x["net"] for x in rows))),
                     ("Месяц выхода в прибыль", first_plus(rows) or "не выходим"),
                     ("Месяц, когда кончаются стартовые деньги",
                      next((x["m"] for x in rows if x["cash"] < 0), "не кончаются")),
                     ("Нужно денег сверх стартовых", money(max(0, -cash_low)))):
        print("  %-56s %12s" % (title, v))

    print()
    print("ЧТО МЕНЯЕТ ИСХОД — одно допущение за раз")

    def what_if(title, p=None, fix=None, no_dev=False):
        rr = run(dict(P, **(p or {})), dict(FIX, **(fix or {})),
                 *((0, 0) if no_dev else (None, None)))
        m = first_plus(rr)
        need = max(0, -min(x["cash"] for x in rr))
        print("  %-48s в плюс: %-12s денег нужно: %s"
              % (title, ("%d-й месяц" % m) if m else "не выходим", money(need)))

    what_if("как есть")
    what_if("без разработчика", no_dev=True)
    what_if("без платной рекламы", fix={"mkt": 0})
    what_if("один Pro в месяц вместо двух", p={"corp_per_month": 1.0})
    what_if("три Pro в месяц вместо двух", p={"corp_per_month": 3.0})
    what_if("отток One 7% вместо 10%", p={"churn": 0.07})
    what_if("отток One 13% вместо 10%", p={"churn": 0.13})
    what_if("Pro 45 000 ₽ вместо 49 900 ₽", p={"corp_price": 45000})
    what_if("Pro 60 000 ₽ вместо 49 900 ₽", p={"corp_price": 60000})


if __name__ == "__main__":
    main()
