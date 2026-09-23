# -*- coding: utf-8 -*-
"""Минимальная цена тарифа Pro, при которой выходим в плюс за 24 месяца.

Это НЕ модель — таблица `Компас_финмодель_24м.xlsx` остаётся как есть.
Здесь считается один вопрос владельца от 23 сентября 2026.

ЧТО БЫЛО В ЭТОМ ФАЙЛЕ РАНЬШЕ. Он отвечал на вопросы, которые с тех пор
решены: ООО вместо АО, АУСН вместо УСН, выбор цены подписки из 490/790/990/
1490, цена корпоративного тарифа. Все ответы переехали в
`finance/ЗАПИСКА_финмодель.md`, а код под них ссылался на сценарии, которых
в модели больше нет, и просто перестал запускаться. Скрипт, который не
запускается, хуже отсутствующего: он выглядит проверкой, не будучи ею.

    python3 finance/scenarios.py
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_buf = io.StringIO()
with contextlib.redirect_stdout(_buf):
    import check_model as cm          # noqa: E402

# Фирм в досягаемости: 286 названы поимённо в наших же сделках (164
# юридических и 122 финансовых консультанта), плюс фонды, оценщики и
# корпоративное развитие компаний-покупателей. Число грубое, и оно нужно
# только для одного — чтобы видеть, не требует ли сценарий доли рынка,
# которой не бывает.
ADDRESSABLE = 400


def money(x):
    return "%s ₽" % format(int(round(x)), ",d").replace(",", " ")


def case(price, pace, mkt=0, dev=True):
    """Помесячные строки при заданных цене Pro и темпе продаж."""
    fix_was, d1, d2 = dict(cm.FIX), cm.DEV1_COST, cm.DEV2_COST
    cm.FIX = dict(cm.FIX)
    cm.FIX["mkt"] = mkt
    if not dev:
        cm.DEV1_COST = cm.DEV2_COST = 0
    p = dict(cm.SCEN["1 в месяц"])
    p["corp_price"], p["corp_per_month"] = price, pace
    _, rows = cm.run("1 в месяц", p)
    cm.FIX, cm.DEV1_COST, cm.DEV2_COST = fix_was, d1, d2
    return rows


def steady(rows, since=21):
    """Плюс УСТОЙЧИВЫЙ, а не разовый.

    Без этого условия двоичный поиск находит цену, при которой прибыль
    появляется ровно в 24-м месяце и больше нигде. Формально «вышли в плюс
    за 24 месяца», по существу — край, с которого сваливаешься от любого
    отклонения. Требуем плюс с 21-го месяца и до конца.
    """
    return all(x["net"] > 0 for x in rows if x["m"] >= since)


def min_price(pace, mkt=0, dev=True, lo=8000, hi=900000):
    if not steady(case(hi, pace, mkt, dev)):
        return None
    while hi - lo > 250:
        mid = (lo + hi) // 2
        if steady(case(mid, pace, mkt, dev)):
            hi = mid
        else:
            lo = mid
    return hi


def pace_needed(price, dev=True, limit=8.0):
    pace = 0.1
    while pace <= limit:
        if steady(case(price, pace, dev=dev)):
            return pace
        pace = round(pace + 0.1, 1)
    return None


print("=" * 78)
print("МИНИМАЛЬНАЯ ЦЕНА PRO, ПРИ КОТОРОЙ ВЫХОДИМ В ПЛЮС ЗА 24 МЕСЯЦА")
print("=" * 78)
print("Условие: прибыль положительна с 21-го месяца и до конца — устойчивый")
print("плюс, а не разовый выход в последнем месяце.")
print()
print("Платное продвижение убрано: по расчёту оно не окупается (LTV ÷ CAC =")
print("0,79), и держать его в «адекватном сценарии» значит закладывать")
print("заведомый убыток. Разработчик по лесенке 0 → 50 → 100 остаётся —")
print("это решение владельца, и именно оно определяет ответ.")
print()
print("  %-13s %13s %15s %11s" % ("темп Pro", "мин. цена", "клиентов к 24", "доля рынка"))
for pace in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    mp = min_price(pace)
    rows = case(mp, pace)
    print("  %-13s %13s %15.0f %10.0f%%"
          % ("%.1f/мес" % pace, money(mp), rows[-1]["corp"],
             rows[-1]["corp"] / ADDRESSABLE * 100))

print()
print("ЧТО ЗНАЧИТ «АДЕКВАТНЫЙ» — три условия, и каждое названо вслух:")
print("  • разработчик по лесенке остаётся: это решение владельца;")
print("  • платного продвижения нет: оно не окупается;")
print("  • темп 2 Pro в месяц — один договор в две недели. К 24-му месяцу это")
print("    36 клиентов, 9% от примерно 400 фирм в досягаемости. Работа, а не")
print("    удача, и не доля рынка, которой не бывает.")
print()
print("  ОТВЕТ: %s в год." % money(min_price(2.0)))

print()
print("-" * 78)
print("ЕСЛИ ОСТАВЛЯТЬ 45 000 ₽ — какой темп тогда нужен")
print("-" * 78)
for dev, label in ((True, "с разработчиком"), (False, "без разработчика")):
    p = pace_needed(45000, dev=dev)
    if p is None:
        print("  %-18s не хватает никакого разумного темпа" % label)
        continue
    rows = case(45000, p, dev=dev)
    print("  %-18s %.1f Pro в месяц -> %.0f клиентов к 24-му (%.0f%% рынка)"
          % (label, p, rows[-1]["corp"], rows[-1]["corp"] / ADDRESSABLE * 100))

print()
print("  НАСТОЯЩАЯ РАЗВИЛКА НЕ В ЦЕНЕ PRO, а в том, платим ли мы разработчика")
print("  из выручки подписки. Платим — цена должна быть около 55 тыс при темпе")
print("  2 в месяц. Не платим — 45 тыс хватает уже при 0,5 в месяц, то есть при")
print("  одном договоре раз в два месяца.")
