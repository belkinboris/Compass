# -*- coding: utf-8 -*-
"""Двойник финмодели на Python: те же допущения, тот же счёт, без Excel.

Зачем двойник. Формулы в книге нельзя прочитать глазами и проверить — openpyxl
их не считает, а показать владельцу таблицу, в которой число получилось «само»,
значит показать неизвестно что. Этот файл считает то же самое обычным кодом,
печатает результат и прямо называет, где он выглядит неправдоподобно.

    python3 finance/check_model.py
"""
from __future__ import annotations

MONTHS = 24


def xlround(x):
    """Округление как в Excel — половину ВВЕРХ, а не к чётному.

    Питоновский round() округляет 62,5 до 62 (банковское правило), Excel и
    LibreOffice — до 63. На шаге «регистраций за месяц» это давало расхождение
    двойника с книгой уже в первом месяце (22 сентября 2026).
    """
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

# Три сценария — три цены. Числа те же, что в build_model.py (лист «Допущения»).
# Подписка для человека ОДНА (990 ₽). Три сценария — три цены корпоративного
# тарифа; у каждой свой темп прихода клиентов: дешевле — решают быстрее.
HUMAN = dict(price_m=990, price_y=9900, share_y=0.22, churn=0.10, refund=0.05,
             ceiling=25000, pay_share=0.035, reg_org0=25, reg_growth=0.10,
             cpr=800, conv=0.07, conv_lag=2, ai_q=12, ai_cost_q=1.0)
SCEN = {
    "120 тыс": dict(HUMAN, corp_price=120000, corp_every=2.0, corp_start=4),
    "200 тыс": dict(HUMAN, corp_price=200000, corp_every=2.5, corp_start=4),
    "250 тыс": dict(HUMAN, corp_price=250000, corp_every=3.0, corp_start=5),
}
CORP_CHURN, CORP_VAR = 0.20, 1500

# ООО + АУСН (решение владельца 23 сентября): регистратора нет, учёт проще.
FIX = dict(timeweb=5300, ycloud=7000, claude_sub=20000, office=1908,
           fns=8000, kassa=2500, acc=7000, legal=10000, mkt=30000, misc=8000,
           gd_salary=0, team_cost=0)
INJURY_YEAR = 2959.0        # единственный обязательный взнос на АУСН
# Разработчик лесенкой: первый квартал никого, месяцы 4–12 по 50 тыс, с 13-го
# по 100 тыс. Оба этапа — подряд с самозанятым или ИП, поэтому без взносов.
DEV_FREE, DEV1_UNTIL, DEV1_COST, DEV2_COST = 3, 12, 50000, 100000


def dev_cost(month):
    """month — номер месяца от старта, начиная с 1."""
    if month <= DEV_FREE:
        return 0
    return DEV1_COST if month <= DEV1_UNTIL else DEV2_COST


MROT, INS_RATE, ACQ = 27093, 0.30, 0.030   # МРОТ и тариф — справочно: на АУСН 0%
USN, USN_MIN, VAT_LIMIT, VAT_RATE = 0.20, 0.03, 60_000_000, 0.05   # АУСН: 20%, минимум 3% ЗА МЕСЯЦ
CASH0 = 500_000


def unit(p):
    arpu = p["price_m"] * (1 - p["share_y"]) + p["price_y"] / 12 * p["share_y"]
    # Возврат возможен только с ГОДОВОЙ подписки и только за неиспользованный
    # остаток — в среднем половина срока. Раньше здесь стояло «доля ВСЕЙ выручки».
    contrib = arpu * (1 - ACQ - p["share_y"] * p["refund"] / 2) - p["ai_q"] * p["ai_cost_q"]
    ltv = contrib / p["churn"]
    cac = p["cpr"] / p["conv"]
    fixed = sum(FIX.values()) + INJURY_YEAR / 12
    corp_contrib = p["corp_price"] / 12 - CORP_VAR
    return dict(arpu=arpu, contrib=contrib, ltv=ltv, cac=cac,
                corp_contrib=corp_contrib,
                corp_eq=round(corp_contrib / contrib) if contrib > 0 else None,
                be_corp=-(-fixed // corp_contrib) if corp_contrib > 0 else None,
                ratio=ltv / cac, life=1 / p["churn"],
                payback=cac / contrib if contrib > 0 else None,
                cpr_ok=ltv * p["conv"] / 3,
                fixed=fixed, be=-(-fixed // contrib) if contrib > 0 else None,
                be_dev1=-(-(fixed + DEV1_COST) // contrib) if contrib > 0 else None,
                be_dev2=-(-(fixed + DEV2_COST) // contrib) if contrib > 0 else None,
                vat_subs=-(-VAT_LIMIT / 12 // arpu))


def run(name, p):
    u = unit(p)
    seen = 0.0
    regs, paid_hist, rows = [], [], []
    paid, cash, year_rev = 0.0, float(CASH0), 0.0
    corp = 0.0
    for i in range(MONTHS):
        org = p["reg_org0"] * (1 + p["reg_growth"]) ** i
        bought = FIX["mkt"] / p["cpr"]
        room = max(0.0, 1 - seen / p["ceiling"]) if i else 1.0
        reg = xlround((org + bought) * room)
        regs.append(reg)
        seen += reg

        j = i - p["conv_lag"]
        new = xlround(regs[j] * p["conv"]) if j >= 0 else 0
        share_y_now = p["share_y"] * i / MONTHS
        paid = min(paid * (1 - p["churn"] * (1 - share_y_now)) + new,
                   p["ceiling"] * p["pay_share"])
        paid_hist.append(paid)

        m = i + 1
        corp_new = 1 if (m >= p["corp_start"] and (m - p["corp_start"]) % p["corp_every"] < 1) else 0
        corp = corp * (1 - CORP_CHURN / 12) + corp_new
        corp_rev = corp * p["corp_price"] / 12

        rev_b2c = paid * (p["price_m"] * (1 - share_y_now) + p["price_y"] / 12 * share_y_now)
        rev = rev_b2c + corp_rev
        year_sold = new * share_y_now * p["price_y"]
        cash_in = (rev_b2c + year_sold - new * share_y_now * p["price_y"] / 12
                   + corp_new * p["corp_price"])

        costs = (FIX["timeweb"] + FIX["ycloud"] + p["ai_q"] * p["ai_cost_q"] * paid
                 + FIX["claude_sub"] + FIX["office"] + FIX["fns"] + FIX["kassa"] + FIX["acc"]
                 + FIX["legal"] + FIX["mkt"] + FIX["misc"]
                 + corp * CORP_VAR
                 + cash_in * ACQ + year_sold * p["refund"] / 2
                 + FIX["gd_salary"] + FIX["team_cost"]
                 + dev_cost(i + 1)
                 + INJURY_YEAR / 12)

        if i == 3:          # январь: новый календарный год
            year_rev = 0.0
        year_rev += rev
        vat = rev * VAT_RATE if year_rev > VAT_LIMIT else 0.0
        usn = max((rev - costs - vat) * USN, rev * USN_MIN)
        taxes = vat + usn
        net = rev - costs - taxes
        cash += cash_in - costs - taxes
        rows.append(dict(m=m, reg=reg, paid=paid, corp=corp, corp_rev=corp_rev,
                         rev=rev, costs=costs, taxes=taxes, net=net, cash=cash))
    return u, rows


def money(x):
    return "%s ₽" % format(int(round(x)), ",d").replace(",", " ")


print("ЕДИНИЦА ЭКОНОМИКИ — сходится ли один подписчик")
print("%-42s %14s %14s %14s" % ("", *SCEN))
lines = [("Средний платёж в месяц", "arpu", money),
         ("Вклад одного подписчика в месяц", "contrib", money),
         ("Срок жизни подписки, месяцев", "life", lambda v: "%.1f" % v),
         ("Принесёт за всю жизнь (LTV)", "ltv", money),
         ("Стоит привести одного платящего (CAC)", "cac", money),
         ("LTV ÷ CAC", "ratio", lambda v: "%.2f" % v),
         ("Окупаемость привлечения, месяцев", "payback", lambda v: "%.1f" % v),
         ("Нужная цена регистрации (окупаемость ×3)", "cpr_ok", money),
         ("Постоянные расходы в месяц", "fixed", money),
         ("Вклад одной компании в месяц", "corp_contrib", money),
         ("Одна компания = столько подписчиков", "corp_eq", lambda v: "%d" % v),
         ("ПОРОГ: только людьми, подписчиков", "be", lambda v: "%d" % v),
         ("ПОРОГ: только компаниями, клиентов", "be_corp", lambda v: "%d" % v),
         ("  то же с разработчиком за 50 тыс ₽", "be_dev1", lambda v: "%d" % v),
         ("  то же с разработчиком за 100 тыс ₽", "be_dev2", lambda v: "%d" % v),
         ("60 млн ₽ в год (предел АУСН) — это подписчиков", "vat_subs", lambda v: "%d" % v)]
units = {n: unit(p) for n, p in SCEN.items()}
for title, key, fmt in lines:
    print("%-42s %14s %14s %14s" % (title, *[fmt(units[n][key]) for n in SCEN]))

print()
print("ДВА ГОДА")
res = {n: run(n, p) for n, p in SCEN.items()}
out = [("Платящих людей через 12 месяцев", lambda r: "%d" % round(r[11]["paid"])),
       ("Платящих людей через 24 месяца", lambda r: "%d" % round(r[23]["paid"])),
       ("Компаний через 24 месяца", lambda r: "%.1f" % r[23]["corp"]),
       ("Выручка от компаний за 24 мес", lambda r: money(sum(x["corp_rev"] for x in r))),
       ("Регистраций всего за 24 месяца", lambda r: "%d" % sum(x["reg"] for x in r)),
       ("Выручка за 12 месяцев", lambda r: money(sum(x["rev"] for x in r[:12]))),
       ("Выручка за 24 месяца", lambda r: money(sum(x["rev"] for x in r))),
       ("Чистая прибыль за 24 месяца", lambda r: money(sum(x["net"] for x in r))),
       ("Деньги на конец 24-го месяца", lambda r: money(r[-1]["cash"])),
       ("Месяц выхода в прибыль",
        lambda r: next((str(x["m"]) for x in r if x["net"] > 0), "не выходим")),
       ("Месяц, когда деньги в минусе",
        lambda r: next((str(x["m"]) for x in r if x["cash"] < 0), "не уходят")),
       ("Нужно денег сверх стартовых",
        lambda r: money(max(0, -min(x["cash"] for x in r))))]
print("%-42s %14s %14s %14s" % ("", *SCEN))
for title, fmt in out:
    print("%-42s %14s %14s %14s" % (title, *[fmt(res[n][1]) for n in SCEN]))

print()
print("ЧТО ЗДЕСЬ ВЫГЛЯДИТ ПОДОЗРИТЕЛЬНО")
flag = False
for n in SCEN:
    u, rows = res[n]
    if u["ratio"] < 1:
        flag = True
        print("  %-7s платное привлечение НЕ окупается: LTV ÷ CAC = %.2f. "
              "Регистрация должна стоить не дороже %s, а заложено %s."
              % (n, u["ratio"], money(u["cpr_ok"]), money(SCEN[n]["cpr"])))
    last = rows[-1]["paid"]
    if last >= SCEN[n]["ceiling"] * SCEN[n]["pay_share"] - 0.5:
        flag = True
        print("  %-7s упёрлись в потолок рынка (%d человек) — рост дальше модель не описывает."
              % (n, round(SCEN[n]["ceiling"] * SCEN[n]["pay_share"])))
    if not any(x["net"] > 0 for x in rows):
        print("  %-7s за 24 месяца в прибыль не выходим (порог к концу — %d подписчиков, "
              "получается %d)." % (n, u["be_dev2"], round(last)))
        flag = True
if not flag:
    print("  — ничего")


# --------------------------------------------------------------- что меняет исход
print()
print("ЧТО ЗАКРЫВАЕТ РАЗРЫВ — по одной правке за раз, сценарий 990 ₽")
print("Каждая строка: меняем ОДНО допущение и смотрим, где оказывается порог")
print("безубыточности и доходим ли до него за 24 месяца.")
print()

BASE = "200 тыс"


def variant(title, scen=None, fix=None, no_dev=False):
    p = dict(SCEN[BASE]); p.update(scen or {})
    global FIX, DEV1_COST, DEV2_COST
    fix_was, d1, d2 = dict(FIX), DEV1_COST, DEV2_COST
    if fix:
        FIX = dict(FIX); FIX.update(fix)
    if no_dev:
        DEV1_COST = DEV2_COST = 0
    u = unit(p)
    _, rows = run(BASE, p)
    month = next((x["m"] for x in rows if x["net"] > 0), None)
    threshold = u["be"] if no_dev else u["be_dev2"]
    FIX, DEV1_COST, DEV2_COST = fix_was, d1, d2
    print("%-46s порог %3d чел.%s   к 24-му месяцу %3d   в плюс: %s"
          % (title, threshold,
             "                   " if no_dev else " (со 100 тыс ₽ с 13-го)",
             round(rows[-1]["paid"]),
             ("с %d-го месяца" % month) if month else "не выходим"))


variant("как есть")
variant("не нанимаем разработчика вовсе", no_dev=True)
variant("без платного продвижения (−30 тыс ₽/мес)", fix={"mkt": 0})
variant("без продвижения и без разработчика", fix={"mkt": 0}, no_dev=True)
variant("без подписки Claude (−20 тыс ₽/мес)", fix={"claude_sub": 0})
variant("отток 7% вместо 10%", scen={"churn": 0.07})
variant("конверсия в оплату 10% вместо 7%", scen={"conv": 0.10})
variant("оплата через СБП: комиссия 0,6% вместо 3%")
_acq_was = ACQ
ACQ = 0.006
variant("  (пересчёт с СБП)")
ACQ = _acq_was
variant("органика стартует с 40 в месяц вместо 25", scen={"reg_org0": 40})
variant("всё вместе: без продвижения, без разработчика,\n  отток 7%, конверсия 10%, органика 40",
        scen={"churn": 0.07, "conv": 0.10, "reg_org0": 40}, fix={"mkt": 0}, no_dev=True)
print()
print("ОТДЕЛЬНО — ПРО КОРПОРАТИВНУЮ ЦЕНУ. Вывод «200 и 250 почти равны» держится")
print("на моём допущении, что дороже тариф — медленнее решение. Если это неверно")
print("и темп один и тот же, картина другая:")
for price in (120000, 200000, 250000):
    p2 = dict(SCEN["200 тыс"]); p2["corp_price"] = price
    _, rr = run("200 тыс", p2)
    m = next((x["m"] for x in rr if x["net"] > 0), None)
    print("  %s в год при ОДНОМ темпе (1 клиент в 2,5 месяца): выручка за 24 мес %s, "
          "в плюс %s" % (money(price), money(sum(x["rev"] for x in rr)),
                         ("с %d-го месяца" % m) if m else "не выходим"))
print()
print("А ТЕПЕРЬ ВАШ ПЛАН ЦЕЛИКОМ — разработчик по лесенке 0 → 50 → 100 остаётся,")
print("убрано только то, что по расчёту не окупается:")
variant("без платного продвижения", fix={"mkt": 0})
variant("без продвижения и без подписки Claude", fix={"mkt": 0, "claude_sub": 0})
variant("то же и отток 7%, конверсия 10%, органика 40",
        scen={"churn": 0.07, "conv": 0.10, "reg_org0": 40}, fix={"mkt": 0})
