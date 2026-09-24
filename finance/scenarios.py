# -*- coding: utf-8 -*-
"""Насколько результат модели держится за темп продаж Pro и его цену.

Книга `Компас_финмодель_24м.xlsx` считает один сценарий: два договора Pro в
месяц по 49 900 ₽. Здесь — то, чего в книге нет: минимальная цена Pro, при
которой модель успевает в плюс до 24-го месяца, для разных темпов продаж.

Два ответа рядом: «по букве» (прибыль в 24-м месяце) и «со страховкой»
(прибыль три последних месяца подряд) — один месяц над нулём ещё не
прибыльность. Платная реклама здесь выключена: по расчёту она не окупается.

    python3 finance/scenarios.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_model as cm          # noqa: E402

# Фирм в досягаемости: 286 консультантов названы в наших же сделках, плюс
# фонды, оценщики и корпоративное развитие покупателей. Число грубое и нужно
# для одного: видеть, не требует ли темп доли рынка, которой не бывает.
ADDRESSABLE = 400


def case(price, pace, dev=True):
    p = dict(cm.P, corp_price=price, corp_per_month=pace)
    return cm.run(p, dict(cm.FIX, mkt=0), *((None, None) if dev else (0, 0)))


def last_run(rows):
    """Сколько месяцев подряд в конце прибыль положительна."""
    n = 0
    for x in reversed(rows):
        if x["net"] <= 0:
            break
        n += 1
    return n


def min_price(pace, need, dev=True, lo=8000, hi=900000):
    ok = lambda pr: last_run(case(pr, pace, dev)) >= need   # noqa: E731
    if not ok(hi):
        return None
    while hi - lo > 250:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def pace_needed(price, need, dev=True, limit=8.0):
    pace = 0.1
    while pace <= limit:
        if last_run(case(price, pace, dev)) >= need:
            return pace
        pace = round(pace + 0.1, 1)
    return None


def main():
    print("МИНИМАЛЬНАЯ ЦЕНА PRO, ЧТОБЫ УСПЕТЬ В ПЛЮС ДО 24-ГО МЕСЯЦА")
    print("(разработчик по лесенке 0 → 50 → 100, без платной рекламы)")
    print()
    print("  %-10s %14s %16s %16s" % ("темп Pro", "по букве", "со страховкой", "клиентов к 24-му"))
    for pace in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        rows = case(49900, pace)
        print("  %-10s %14s %16s %9.0f (%.0f%%)"
              % ("%.1f/мес" % pace, cm.money(min_price(pace, 1)), cm.money(min_price(pace, 3)),
                 rows[-1]["corp"], rows[-1]["corp"] / ADDRESSABLE * 100))

    print()
    print("ЦЕНА 49 900 ₽ — КАКОЙ ТЕМП НУЖЕН")
    for need, label in ((1, "по букве"), (3, "со страховкой")):
        for dev, dlabel in ((True, "с разработчиком"), (False, "без разработчика")):
            p = pace_needed(49900, need, dev)
            print("  %-14s %-18s %.1f Pro в месяц" % (label, dlabel, p))


if __name__ == "__main__":
    main()
