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


def last_run(rows):
    """Сколько месяцев ПОДРЯД в конце прибыль положительна.

    Срок владелец назвал сам: успеть ДО 24-го месяца, а не выйти в плюс к
    какой-то более ранней дате. Поэтому никакого дедлайна раньше 24-го здесь
    нет — считается только длина завершающей череды прибыльных месяцев.

    Зачем вообще её считать, а не просто смотреть на 24-й месяц. Двоичный
    поиск по цене охотно находит величину, при которой прибыль появляется
    ровно в последнем месяце и больше нигде. Формально условие выполнено,
    по существу это шум: один месяц над нулём — не прибыльность. Поэтому
    ниже считаются ДВА ответа: по букве (плюс в 24-м) и со страховкой
    (плюс последние три месяца), и видно, во сколько страховка обходится.
    """
    n = 0
    for x in reversed(rows):
        if x["net"] > 0:
            n += 1
        else:
            break
    return n


def first_of_run(rows):
    n = last_run(rows)
    return rows[-n]["m"] if n else None


def min_price(pace, need_months=1, mkt=0, dev=True, lo=8000, hi=900000):
    ok = lambda pr: last_run(case(pr, pace, mkt, dev)) >= need_months   # noqa: E731
    if not ok(hi):
        return None
    while hi - lo > 250:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


def pace_needed(price, need_months=1, dev=True, limit=8.0):
    pace = 0.1
    while pace <= limit:
        if last_run(case(price, pace, dev=dev)) >= need_months:
            return pace
        pace = round(pace + 0.1, 1)
    return None


print("=" * 78)
print("МИНИМАЛЬНАЯ ЦЕНА PRO, ПРИ КОТОРОЙ УСПЕВАЕМ В ПЛЮС ДО 24-ГО МЕСЯЦА")
print("=" * 78)
print("Срок — «успеть до 24-го», как и сказано: более раннего дедлайна нет.")
print("Считаются два ответа рядом:")
print("  A — по букве: прибыль положительна в 24-м месяце;")
print("  B — со страховкой: положительна последние ТРИ месяца. Один месяц над")
print("      нулём — это ещё не прибыльность, и цена страховки видна тут же.")
print()
print("Платное продвижение убрано: по расчёту оно не окупается (LTV ÷ CAC =")
print("0,79). Разработчик по лесенке 0 → 50 → 100 остаётся — это решение")
print("владельца, и именно оно определяет ответ.")
print()
print("  %-11s %14s %8s %14s %8s %13s"
      % ("темп Pro", "A: мин. цена", "месяц", "B: мин. цена", "месяц", "клиентов к 24"))
for pace in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    a, b = min_price(pace, 1), min_price(pace, 3)
    ra, rb = case(a, pace), case(b, pace)
    print("  %-11s %14s %8s %14s %8s %9.0f (%.0f%%)"
          % ("%.1f/мес" % pace, money(a), "%d-й" % first_of_run(ra),
             money(b), "%d-й" % first_of_run(rb),
             ra[-1]["corp"], ra[-1]["corp"] / ADDRESSABLE * 100))

print()
print("ЧТО Я СЧИТАЮ АДЕКВАТНЫМ ТЕМПОМ: 2 Pro в месяц — один договор в две")
print("недели. К 24-му месяцу это 36 клиентов, 9% от примерно 400 фирм в")
print("досягаемости: работа, а не удача, и не доля рынка, которой не бывает.")
print()
print("  ОТВЕТ ПО БУКВЕ:      %s в год." % money(min_price(2.0, 1)))
print("  ОТВЕТ СО СТРАХОВКОЙ: %s в год." % money(min_price(2.0, 3)))

print()
print("-" * 78)
print("ВАША ЦЕНА 49 900 ₽ — проходит ли")
print("-" * 78)
for need, label in ((1, "по букве"), (3, "со страховкой")):
    for dev, dlabel in ((True, "с разработчиком"), (False, "без разработчика")):
        p = pace_needed(49900, need, dev=dev)
        if p is None:
            print("  %-14s %-18s не хватает никакого разумного темпа" % (label, dlabel))
            continue
        rows = case(49900, p, dev=dev)
        print("  %-14s %-18s нужно %.1f Pro/мес -> %.0f клиентов (%.0f%% рынка), плюс с %d-го"
              % (label, dlabel, p, rows[-1]["corp"],
                 rows[-1]["corp"] / ADDRESSABLE * 100, first_of_run(rows)))

print()
_a2, _b2 = min_price(2.0, 1), min_price(2.0, 3)
_pb = pace_needed(49900, 3)
print("  49 900 ₽ ПРОХОДЯТ при темпе 2 договора в месяц: минимальная цена при")
print("  этом темпе — %s, то есть у вашей цены есть небольшой запас." % money(_a2))
print("  Со страховкой на три месяца нужен темп %.1f в месяц или цена %s." % (_pb, money(_b2)))
print()
print("  И то же, что было видно раньше: без разработчика 49 900 ₽ хватает")
print("  при темпе %.1f–%.1f договора в месяц. Решается не цена Pro, а то,"
      % (pace_needed(49900, 1, dev=False), pace_needed(49900, 3, dev=False)))
print("  платим ли мы разработчика из выручки подписки.")
