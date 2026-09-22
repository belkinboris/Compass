# -*- coding: utf-8 -*-
"""Проверка модели счётом: тот же расчёт на Python, чтобы увидеть числа.

Excel в этом контейнере не пересчитать (LibreOffice не открывает даже пустой
файл), а отдавать модель, ни разу не посмотрев на её результат, нельзя:
формула может быть синтаксически верной и при этом считать чепуху. Здесь
повторён тот же расчёт — если числа осмысленные, значит осмысленна и модель.

    python3 finance/check_model.py
"""
MONTHS = 24

# ПОТОЛОК РЫНКА. Без него экспонента за 24 месяца улетает в фантазию:
# первая версия смелого сценария давала 1413 подписчиков и 97 млн ₽ выручки
# на втором году. Рынок конечен, и его размер можно прикинуть от нашей же
# базы: в сделках поимённо названы 164 юридических и 122 финансовых
# консультанта — это ядро аудитории. Плюс корпоративные отделы развития,
# фонды и оценщики. Реалистичный круг тех, кто ВООБЩЕ может это купить, —
# несколько тысяч человек, а платит из них меньшинство.
SCEN = {
    "Осторожный": dict(price_m=6900, price_y=69000, share_y=.15, churn=.09, reg0=10,
                       growth=.04, conv=.06, lag=3, ceiling=3000, pay_share=.03,
                       host=4000, ai=8000, ai_u=80, fns=5000,
                       acc=8000, reg=3000, legal=5000, mkt=25000, misc=5000, gd=0, team=0,
                       dev_start=19, dev=180000, cash0=200000),
    "Базовый":    dict(price_m=9900, price_y=99000, share_y=.30, churn=.06, reg0=12,
                       growth=.10, conv=.10, lag=2, ceiling=5000, pay_share=.06,
                       host=6000, ai=15000, ai_u=120, fns=8000,
                       acc=12000, reg=4000, legal=10000, mkt=60000, misc=8000, gd=0, team=0,
                       dev_start=13, dev=220000, cash0=500000),
    "Смелый":     dict(price_m=14900, price_y=149000, share_y=.45, churn=.04, reg0=20,
                       growth=.16, conv=.15, lag=1, ceiling=8000, pay_share=.08,
                       host=9000, ai=40000, ai_u=200, fns=12000,
                       acc=18000, reg=7000, legal=20000, mkt=150000, misc=15000, gd=100000,
                       team=150000, dev_start=7, dev=300000, cash0=1500000),
}
USN, USN_MIN = .15, .01
VAT_LIMIT, VAT_RATE = 20_000_000, .05
MROT, INS = 27_093, .30
ACQ = .035


def run(p):
    # Регистрации растут, пока в рынке остаются незарегистрированные: чем
    # ближе к потолку, тем медленнее прирост. Это обычная S-кривая, и без неё
    # модель обещает рост, которому неоткуда взяться.
    regs, seen = [], 0.0
    for i in range(MONTHS):
        want = p["reg0"] * (1 + p["growth"]) ** i
        room = max(0.0, 1 - seen / p["ceiling"])
        got = want * room
        seen += got
        regs.append(got)
    new = [regs[i - p["lag"]] * p["conv"] if i - p["lag"] >= 0 else 0 for i in range(MONTHS)]
    cap = p["ceiling"] * p["pay_share"]          # больше этого платить некому
    paid, out = [], 0.0
    for i in range(MONTHS):
        share_y = p["share_y"] * i / MONTHS
        out = (out * (1 - p["churn"] * (1 - share_y)) + new[i]) if i else new[i]
        out = min(out, cap)
        paid.append(out)

    res = dict(rev=[], cash_in=[], costs=[], vat=[], usn=[], net=[], flow=[], cash=[], ins=[])
    cash, ytd = p["cash0"], 0.0
    for i in range(MONTHS):
        share_y = p["share_y"] * i / MONTHS
        rev = paid[i] * (p["price_m"] * (1 - share_y) + p["price_y"] / 12 * share_y)
        cash_in = rev + new[i] * share_y * (p["price_y"] - p["price_y"] / 12)
        ins = max(p["gd"], MROT) * INS
        costs = (p["host"] + p["ai"] + paid[i] * p["ai_u"] + p["fns"] + p["acc"] + p["reg"]
                 + p["legal"] + p["mkt"] + p["misc"] + cash_in * ACQ + p["gd"] + p["team"]
                 + (p["dev"] if i + 1 >= p["dev_start"] else 0) + ins)
        if i % 12 == 0:
            ytd = 0.0
        ytd += rev
        vat = rev * VAT_RATE if ytd > VAT_LIMIT else 0.0
        usn = max((rev - costs - vat) * USN, rev * USN_MIN)
        net = rev - costs - vat - usn
        flow = cash_in - costs - vat - usn
        cash += flow
        for k, v in (("rev", rev), ("cash_in", cash_in), ("costs", costs), ("vat", vat),
                     ("usn", usn), ("net", net), ("flow", flow), ("cash", cash), ("ins", ins)):
            res[k].append(v)
    res["paid"] = paid
    return res


def money(x):
    return "%s ₽" % format(int(round(x)), ",d").replace(",", " ")


for name, p in SCEN.items():
    r = run(p)
    first_plus = next((i + 1 for i, v in enumerate(r["net"]) if v > 0), None)
    broke = next((i + 1 for i, v in enumerate(r["cash"]) if v < 0), None)
    print("=" * 74)
    print("%s — подписка %s/мес" % (name, money(p["price_m"])))
    print("  потолок:   рынок %d чел., платить могут до %d"
          % (p["ceiling"], round(p["ceiling"] * p["pay_share"])))
    print("  платящих:  через 12 мес %3d   через 24 мес %3d"
          % (round(r["paid"][11]), round(r["paid"][23])))
    print("  выручка:   за 1-й год %14s   за 2-й год %14s"
          % (money(sum(r["rev"][:12])), money(sum(r["rev"][12:]))))
    print("  расходы:   за 1-й год %14s   за 2-й год %14s"
          % (money(sum(r["costs"][:12])), money(sum(r["costs"][12:]))))
    print("  налоги:    за 24 мес %15s   (в т.ч. НДС %s)"
          % (money(sum(r["usn"]) + sum(r["vat"])), money(sum(r["vat"]))))
    print("  взносы за ГД за 24 мес: %s" % money(sum(r["ins"])))
    print("  прибыль:   за 24 мес %15s" % money(sum(r["net"])))
    print("  выход в плюс: %s   деньги кончаются: %s"
          % ("месяц %d" % first_plus if first_plus else "не выходим",
             "месяц %d" % broke if broke else "не кончаются"))
    print("  самая глубокая яма: %s" % money(min(r["cash"])))
    print("  нужно денег сверх стартовых: %s" % money(max(0, -min(r["cash"]))))
