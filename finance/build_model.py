# -*- coding: utf-8 -*-
"""Финансовая модель «Компаса» на 24 месяца — Excel с живыми формулами.

Один сценарий, все числа названы владельцем или измерены:
  • One — 990 ₽ в месяц, для человека;
  • Pro — 49 900 ₽ в год, для команды; два новых договора в месяц;
  • ООО на АУСН; разработчик лесенкой 0 → 50 → 100 тыс ₽ в месяц.

Почему один сценарий, а не три. Раньше колонки разводили темп продаж Pro
(0,5 / 1 / 2 в месяц), и владелец справедливо заметил, что три ряда почти
одинаковых чисел ничего не решают на этом этапе. Чувствительность к темпу и
цене считает `finance/scenarios.py` — отдельно, одной таблицей.

Все входные данные лежат на листе «Допущения» и больше нигде: меняете жёлтую
клетку — пересчитывается всё. Ни одно число в таблицах не вбито руками.
Тот же счёт повторён обычным кодом в `finance/check_model.py`, а
`test_finance_model.py` сверяет книгу с ним клетка за клеткой.

Ставки налогов проверены по источникам 23 сентября 2026 (список — на листе
«Налоги и риски»):
  • АУСН «доходы минус расходы» — 20%, минимальный налог 3% от доходов,
    считается за каждый месяц отдельно;
  • страховые взносы на АУСН — тариф 0%; остаётся взнос на травматизм
    2 959 ₽ в год;
  • НДС на АУСН нет до предела режима в 60 млн ₽ дохода;
  • токены Yandex AI Studio (gpt-oss-120b) — 0,3 ₽ за 1000, вход и выход.

    python3 finance/build_model.py
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "finance" / "Компас_финмодель_24м.xlsx"
MONTHS = 24
START = dt.date(2026, 10, 1)
CALC = "По месяцам"

INK = "1C2B25"
ACCENT = "0F5132"
WARN = "9C3B1B"

H1 = Font(name="Calibri", size=14, bold=True, color=ACCENT)
H2 = Font(name="Calibri", size=11, bold=True, color=INK)
BOLD = Font(name="Calibri", size=11, bold=True)
NORM = Font(name="Calibri", size=11)
SMALL = Font(name="Calibri", size=9, color="6B6B6B")
RED = Font(name="Calibri", size=11, bold=True, color=WARN)
GOOD = Font(name="Calibri", size=11, bold=True, color=ACCENT)
FILL_IN = PatternFill("solid", fgColor="FFF3CD")      # поля для ввода
FILL_HEAD = PatternFill("solid", fgColor="E7EFEA")
RUB = '# ##0 ₽;[Red]-# ##0 ₽'
RUB0 = '# ##0;[Red]-# ##0'
PCT = '0.0%'
NUM1 = '0.0'
NUM2 = '0.00'


def month_name(i: int) -> str:
    m = START.month - 1 + i
    y = START.year + m // 12
    names = ["янв", "фев", "мар", "апр", "май", "июн",
             "июл", "авг", "сен", "окт", "ноя", "дек"]
    return "%s %d" % (names[m % 12], y)


def put(ws, row, col, value, font=NORM, fmt=None, fill=None, wrap=False):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if wrap:
        c.alignment = Alignment(wrap_text=True, vertical="top")
    return c


def bullets(ws, r, texts, last_col, height=40, font=NORM):
    for t in texts:
        put(ws, r, 1, "•", NORM)
        put(ws, r, 2, t, font, wrap=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=last_col)
        ws.row_dimensions[r].height = height
        r += 1
    return r


# ---------------------------------------------------------------- допущения
def sheet_assumptions(wb):
    ws = wb.create_sheet("Допущения")
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 90

    r = 1
    put(ws, r, 1, "Допущения модели", H1); r += 1
    put(ws, r, 1, "Жёлтые клетки можно менять — всё остальное в книге считается от них.", SMALL); r += 1
    put(ws, r, 1, "«Ваш счёт» и «ваше решение» — названо вами. «Уточнить» — моя оценка, "
                  "её надо заменить фактом.", SMALL); r += 2

    def block(title):
        nonlocal r
        for c in range(1, 4):
            ws.cell(row=r, column=c).fill = FILL_HEAD
        put(ws, r, 1, title, H2, fill=FILL_HEAD)
        r += 1

    def row(name, value, note, fmt):
        nonlocal r
        put(ws, r, 1, name, NORM, wrap=True)
        put(ws, r, 2, value, BOLD, fmt=fmt, fill=FILL_IN)
        put(ws, r, 3, note, SMALL, wrap=True)
        ws.row_dimensions[r].height = 30
        r += 1
        return r - 1

    ref = {}
    block("Тариф One — для человека")
    ref["price_m"] = row("One, ₽ в месяц", 990, "Ваше решение.", RUB)
    ref["price_y"] = row("One, ₽ в год", 9900,
        "Десять месяцев по цене двенадцати. Годовая оплата ценна тем, что даёт деньги вперёд.", RUB)
    ref["share_y"] = row("Доля годовых подписок к 24-му месяцу", 0.22,
        "Растёт от нуля: сначала люди платят помесячно, пока не убедились.", PCT)
    ref["churn"] = row("Отток в месяц", 0.10,
        "Сколько платящих уходит каждый месяц. 10% — это около 10 месяцев жизни подписки. "
        "Не измерено: проверять с третьего месяца продаж. Самое важное число модели.", PCT)
    ref["refund"] = row("Доля годовых подписок, по которым просят возврат", 0.05,
        "Человек вправе отказаться в любой момент и вернуть деньги за неиспользованный срок "
        "(ст. 32 закона о защите прав потребителей). С помесячной подписки возвращать нечего, "
        "поэтому считаются только годовые: доля отказов × половина срока.", PCT)

    block("Откуда берутся подписчики")
    ref["ceiling"] = row("Сколько человек в России вообще может это купить", 25000,
        "Ядро ≈3 400: сотрудники 286 консультантов из нашей же базы (по 5 человек), "
        "корпоративное развитие 700 покупателей (по 2), фонды и оценщики. Остальное — "
        "аналитики, журналисты, преподаватели, студенты, частные инвесторы. "
        "Самое зыбкое число модели.", RUB0)
    ref["pay_share"] = row("Какая доля из них может платить", 0.035,
        "Верхняя граница: больше платящих, чем столько, модель не допускает.", PCT)
    ref["reg_org0"] = row("Бесплатных регистраций в месяц на старте", 25,
        "Факт закрытого теста — 16 аккаунтов за 7 недель, по заявке и без продвижения. "
        "Без двери на входе берём 25.", RUB0)
    ref["reg_growth"] = row("Рост бесплатных регистраций в месяц", 0.10,
        "Канал, пересылки, поиск. Рост замедляется по мере того, как рынок заполняется.", PCT)
    ref["cpr"] = row("Цена одной регистрации из рекламы, ₽", 800,
        "Посев в отраслевом канале: 10–50 тыс ₽ за размещение, 20–60 регистраций. "
        "Измерить первым же посевом.", RUB)
    ref["conv"] = row("Доля зарегистрировавшихся, которые начинают платить", 0.07,
        "Не измерено. Для бесплатной регистрации с платной подпиской обычно 3–10%.", PCT)
    ref["conv_lag"] = row("Через сколько месяцев после регистрации начинают платить", 2,
        "Человек смотрит, возвращается, ждёт повода.", RUB0)

    block("Тариф Pro — для команды")
    ref["corp_price"] = row("Pro, ₽ в год", 49900,
        "Ваше решение. Рядом на рынке: Контур.Фокус базовый — от 31 тыс ₽ в год, "
        "Seldon.Basis — от 54 тыс, СПАРК «Корпоратив» — около 200 тыс.", RUB)
    ref["corp_per_month"] = row("Новых Pro в месяц", 2,
        "Один договор в две недели. Продаж Pro ещё не было — число проверяется первыми "
        "разговорами с клиентами, а не расчётом.", NUM1)
    ref["corp_start"] = row("Месяц, когда приходит первый Pro", 4,
        "Раньше не получится: нужны оферта для юрлиц, счёт и акты.", RUB0)
    ref["corp_churn"] = row("Доля Pro, которые не продлевают договор через год", 0.20,
        "Каждый пятый.", PCT)
    ref["corp_var"] = row("Обслуживание одного Pro, ₽ в месяц", 400,
        "Ассистент для команды из трёх человек (60 вопросов по 1 ₽), выгрузки, ответы на вопросы.",
        RUB)

    block("Ассистент на сайте")
    ref["ai_q"] = row("Вопросов в месяц, включённых в One", 12,
        "Ограничение нужно не ради экономии, а чтобы один человек или скрипт не задал тысячу "
        "вопросов за счёт остальных.", RUB0)
    ref["ai_cost_q"] = row("Цена одного вопроса, ₽", 1.0,
        "Измерено на 50 вопросах из живой базы: в среднем 1,04 ₽ (обычный вопрос 0,80–1,12 ₽, "
        "с поиском в интернете 1,19–1,67 ₽).", RUB)

    block("Постоянные расходы, ₽ в месяц — ваши счета")
    ref["timeweb"] = row("Хостинг Timeweb", 5300, "Ваш счёт. Сервер сайта и база.", RUB)
    ref["ycloud"] = row("Yandex.Cloud", 7000,
        "Ваш счёт. Облако и ассистент при нынешнем числе пользователей; рост вместе с "
        "подписчиками считается отдельно.", RUB)
    ref["claude_sub"] = row("Claude", 20000,
        "Ваш счёт. Инструмент разработки. Ассистент на сайте работает на модели Яндекса, "
        "его расход — в строке выше.", RUB)
    ref["office"] = row("Аренда офиса", 1908, "Ваш счёт: 22 900 ₽ в год.", RUB)

    block("Постоянные расходы, ₽ в месяц — оценки, уточнить")
    ref["fns"] = row("API-ФНС", 8000, "Финансы компаний. Уточнить по счёту.", RUB)
    ref["kassa"] = row("Онлайн-касса", 2500,
        "При оплате от человека нужен чек. Обычно его выбивает платёжный сервис — "
        "уточнить в договоре.", RUB)
    ref["acc"] = row("Бухгалтерия", 7000,
        "На АУСН учёт простой: налог считает налоговая по выписке банка. Уточнить у бухгалтера.",
        RUB)
    ref["legal"] = row("Юрист и патентный поверенный", 10000,
        "Товарный знак, оферта, политика персональных данных. Уточнить.", RUB)
    ref["mkt"] = row("Платная реклама", 30000,
        "Небольшой бюджет, чтобы измерить цену регистрации. При нынешних допущениях реклама "
        "себя не окупает (см. «Экономика клиента»).", RUB)
    ref["misc"] = row("Прочее", 8000, "Связь, сервисы, банк. Уточнить.", RUB)

    block("Команда")
    ref["gd_salary"] = row("Зарплата гендиректора, ₽ в месяц", 0,
        "Ваше решение: не платим. Взносов за гендиректора на АУСН нет в любом случае.", RUB)
    ref["team_cost"] = row("Остальная команда на подряде, ₽ в месяц", 0,
        "Самозанятые и ИП: акт и чек на каждую выплату.", RUB)
    ref["dev_free"] = row("Первые месяцы без разработчика", 3, "Ваше решение.", RUB0)
    ref["dev1_cost"] = row("Разработчик, ₽ в месяц — первый этап", 50000,
        "Ваше решение. Подряд с самозанятым или ИП, без взносов (риск — на листе "
        "«Налоги и риски»).", RUB)
    ref["dev1_until"] = row("Первый этап — по какой месяц включительно", 12,
        "Месяцы с 4-го по 12-й.", RUB0)
    ref["dev2_cost"] = row("Разработчик, ₽ в месяц — с 13-го месяца", 100000, "Ваше решение.", RUB)

    block("Налоги и платежи")
    ref["usn"] = row("Ставка АУСН «доходы минус расходы»", 0.20, "", PCT)
    ref["usn_min"] = row("Минимальный налог, % от дохода за месяц", 0.03,
        "Платится, если прибыли нет или она мала. На АУСН считается за каждый месяц отдельно.",
        PCT)
    ref["vat_limit"] = row("Доход в год, до которого нет НДС", 60000000,
        "Это и есть предел АУСН: выше него режим уже не работает.", RUB)
    ref["vat_rate"] = row("Ставка НДС выше предела", 0.05, "За 24 месяца не достигается.", PCT)
    ref["injury"] = row("Взнос на травматизм, ₽ в год", 2959,
        "Единственный обязательный взнос на АУСН, 247 ₽ в месяц.", RUB)
    ref["ins_rate"] = row("Тариф взносов, если подрядчика признают работником", 0.30,
        "В расчёте месяцев не участвует — нужен для оценки риска на листе «Налоги и риски».", PCT)
    ref["acq"] = row("Комиссия за приём платежей", 0.030,
        "Оплата картой. Через СБП — 0,4–0,7%.", PCT)

    block("Старт")
    ref["cash0"] = row("Деньги на старте, ₽", 500000,
        "Уточнить: от этого числа зависит, в каком месяце кончатся деньги.", RUB)
    ref["paid0"] = row("Платящих на старте", 0, "Сейчас доступ бесплатный, по заявке.", RUB0)
    return ws, ref


# ------------------------------------------------------------ экономика клиента
def sheet_unit(wb, ref, calc_rows):
    """Сходится ли ОДИН подписчик и ОДИН договор Pro — до всякого роста."""
    ws = wb.create_sheet("Экономика клиента")
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 84

    r = 1
    put(ws, r, 1, "Экономика одного клиента", H1); r += 1
    put(ws, r, 1, "Здесь нет роста — только один подписчик или один договор и деньги вокруг "
                  "него. Если здесь не сходится, рост не поможет.", SMALL); r += 2

    rows = {}
    A = lambda key: "Допущения!$B$%d" % ref[key]        # noqa: E731
    R = lambda key: "$B$%d" % rows[key]                 # noqa: E731

    def sec(title):
        nonlocal r
        for c in range(1, 4):
            ws.cell(row=r, column=c).fill = FILL_HEAD
        put(ws, r, 1, title, H2, fill=FILL_HEAD)
        r += 1

    def line(key, name, formula, note="", fmt=RUB, font=NORM):
        nonlocal r
        put(ws, r, 1, name, font, wrap=True)
        put(ws, r, 2, formula, font, fmt=fmt)
        put(ws, r, 3, note, SMALL, wrap=True)
        ws.row_dimensions[r].height = 30
        rows[key] = r
        r += 1

    sec("Подписчик One")
    line("arpu", "Средний платёж в месяц",
         "=%s*(1-%s)+%s/12*%s" % (A("price_m"), A("share_y"), A("price_y"), A("share_y")),
         "Помесячные и годовые вперемешку; годовая засчитывается по 1/12 в месяц.")
    line("acq", "минус комиссия за платёж", "=-%s*%s" % (R("arpu"), A("acq")))
    line("ref", "минус возвраты", "=-%s*%s*%s/2" % (R("arpu"), A("share_y"), A("refund")),
         "Только с годовых подписок и только за неиспользованный срок.")
    line("var", "минус ассистент", "=-%s*%s" % (A("ai_q"), A("ai_cost_q")),
         "Включённые вопросы × измеренная цена вопроса.")
    line("contrib", "ВКЛАД ОДНОГО ПОДПИСЧИКА В МЕСЯЦ",
         "=%s+%s+%s+%s" % (R("arpu"), R("acq"), R("ref"), R("var")),
         "Столько он приносит на покрытие постоянных расходов.", RUB, BOLD)
    line("ltv", "Принесёт за всю жизнь подписки (LTV)", "=%s/%s" % (R("contrib"), A("churn")),
         "Вклад в месяц, делённый на отток.")
    line("cac", "Стоит привести одного платящего через рекламу (CAC)",
         "=%s/%s" % (A("cpr"), A("conv")),
         "Цена регистрации, делённая на долю тех, кто начинает платить.")
    line("ratio", "LTV ÷ CAC", "=%s/%s" % (R("ltv"), R("cac")),
         "Ниже 1 — реклама сжигает деньги: подписчик приносит меньше, чем стоил. "
         "У здоровой подписки 3 и выше.", NUM2, BOLD)
    line("cpr_max", "Цена регистрации, при которой реклама окупается втрое",
         "=%s*%s/3" % (R("ltv"), A("conv")),
         "Задача маркетингу одним числом: приводить людей дешевле этого.", RUB, RED)

    sec("Договор Pro")
    line("corp_m", "Платит в месяц", "=%s/12" % A("corp_price"),
         "Годовой договор, разложенный на месяцы. Деньгами приходит сразу за год.")
    line("corp_c", "минус обслуживание", "=-%s" % A("corp_var"))
    line("corp_contrib", "ВКЛАД ОДНОГО ДОГОВОРА В МЕСЯЦ", "=%s+%s" % (R("corp_m"), R("corp_c")),
         "", RUB, BOLD)
    line("corp_eq", "Один Pro = столько подписчиков One",
         "=ROUND(%s/%s,1)" % (R("corp_contrib"), R("contrib")),
         "Pro здесь не рычаг, а второй ручеёк той же ширины: чтобы он решал, нужен поток "
         "договоров, а не пара крупных клиентов.", NUM1, GOOD)

    sec("Порог безубыточности")
    fixed = "+".join(A(k) for k in ("timeweb", "ycloud", "claude_sub", "office", "fns", "kassa",
                                    "acc", "legal", "misc", "mkt", "gd_salary", "team_cost"))
    line("fixed", "Постоянные расходы в месяц", "=%s+%s/12" % (fixed, A("injury")),
         "Всё, что платится независимо от числа клиентов, без разработчика.")
    line("be", "Нужно подписчиков One, если нет Pro", "=ROUNDUP(%s/%s,0)" % (R("fixed"), R("contrib")),
         "", RUB0, GOOD)
    line("be_corp", "Нужно договоров Pro, если нет One",
         "=ROUNDUP(%s/%s,0)" % (R("fixed"), R("corp_contrib")),
         "Любая настоящая смесь лежит между этими двумя числами.", RUB0, GOOD)
    line("be_dev1", "  подписчиков One с разработчиком за 50 тыс ₽",
         "=ROUNDUP((%s+%s)/%s,0)" % (R("fixed"), A("dev1_cost"), R("contrib")), "", RUB0)
    line("be_dev2", "  подписчиков One с разработчиком за 100 тыс ₽",
         "=ROUNDUP((%s+%s)/%s,0)" % (R("fixed"), A("dev2_cost"), R("contrib")),
         "Разница с первой строкой — цена разработчика, выраженная в подписчиках.", RUB0, RED)
    line("be_month", "Месяц выхода в прибыль",
         "=IFERROR(MATCH(TRUE,INDEX('%s'!$B$%d:$%s$%d>0,0),0),\"за 24 месяца не выходим\")"
         % (CALC, calc_rows["net"], get_column_letter(1 + MONTHS), calc_rows["net"]),
         "Первый месяц с чистой прибылью, из помесячного расчёта.", RUB0, BOLD)
    return ws, rows


# ------------------------------------------------------------------ расчёт
def sheet_calc(wb, ref):
    """Помесячный расчёт: воронка, выручка, расходы, налоги, деньги."""
    ws = wb.create_sheet(CALC)
    ws.column_dimensions["A"].width = 44
    ws.freeze_panes = "B4"
    for i in range(MONTHS):
        ws.column_dimensions[get_column_letter(2 + i)].width = 12

    A = lambda key: "Допущения!$B$%d" % ref[key]        # noqa: E731
    col = lambda i: get_column_letter(2 + i)            # noqa: E731

    r = 1
    put(ws, r, 1, "Расчёт по месяцам", H1); r += 1
    put(ws, r, 1, "Каждая клетка — формула от листа «Допущения».", SMALL); r += 1
    put(ws, r, 1, "Месяц", BOLD, fill=FILL_HEAD)
    for i in range(MONTHS):
        put(ws, r, 2 + i, month_name(i), BOLD, fill=FILL_HEAD)
    r += 1

    def line(name, formula, fmt=RUB, font=NORM, note=None):
        nonlocal r
        put(ws, r, 1, name, font)
        for i in range(MONTHS):
            put(ws, r, 2 + i, formula(i), font, fmt=fmt)
        if note:
            put(ws, r, 2 + MONTHS, note, SMALL, wrap=True)
        r += 1
        return r - 1

    def fill(row, formula, fmt):
        for i in range(MONTHS):
            ws.cell(row=row, column=2 + i, value=formula(i)).number_format = fmt

    def sec(title):
        nonlocal r
        for c in range(1, 2 + MONTHS):
            ws.cell(row=r, column=c).fill = FILL_HEAD
        put(ws, r, 1, title, H2, fill=FILL_HEAD)
        r += 1

    sec("Регистрации и подписчики One")
    org = line("Бесплатных регистраций", lambda i: "=%s*(1+%s)^%d"
               % (A("reg_org0"), A("reg_growth"), i), RUB0)
    paid_reg = line("Регистраций из рекламы", lambda i: "=%s/%s" % (A("mkt"), A("cpr")), RUB0,
                    note="Бюджет рекламы, делённый на цену регистрации.")
    reg = line("Регистраций за месяц", lambda i: "", RUB0,
               note="Рост замедляется по мере заполнения рынка: множитель «какая доля ещё не "
                    "зарегистрирована».")
    seen = line("Зарегистрировано всего", lambda i: "", RUB0)
    fill(reg, lambda i: "=ROUND((%s%d+%s%d)*%s,0)" % (
        col(i), org, col(i), paid_reg,
        ("MAX(0,1-%s%d/%s)" % (col(i - 1), seen, A("ceiling"))) if i else "1"), RUB0)
    fill(seen, lambda i: ("=%s%d" % (col(i), reg)) if i == 0
         else "=%s%d+%s%d" % (col(i - 1), seen, col(i), reg), RUB0)
    new = line("Новых платящих",
               # Проверка «столбец левее начала таблицы» обязана стоять ДО INDEX:
               # INDEX(диапазон;1;0) не ошибка, а «вся строка», и в скалярном месте
               # молча отдаёт ТЕКУЩИЙ столбец — регистрации этого же месяца без
               # задержки (найдено сверкой книги с двойником 22 сентября 2026).
               lambda i: "=IF(COLUMN()-1-%s<1,0,IFERROR(ROUND(INDEX($B$%d:$%s$%d,1,COLUMN()-1-%s)*%s,0),0))"
                         % (A("conv_lag"), reg, col(MONTHS - 1), reg, A("conv_lag"), A("conv")), RUB0,
               note="Регистрация превращается в оплату с задержкой из допущений.")
    paid = line("Платящих на конец месяца", lambda i: "", RUB0,
                note="Годовые подписки не уходят помесячно: их доля растёт и гасит отток.")
    fill(paid, lambda i: "=MIN(%s,%s*%s)" % (
        ("%s+%s%d" % (A("paid0"), col(i), new)) if i == 0 else
        ("%s%d*(1-%s*(1-%s*%d/%d))+%s%d" % (col(i - 1), paid, A("churn"), A("share_y"),
                                           i, MONTHS, col(i), new)),
        A("ceiling"), A("pay_share")), RUB0)

    sec("Договоры Pro")
    corp_new = line("Новых Pro", lambda i: "=IF(%d<%s,0,%s)"
                    % (i + 1, A("corp_start"), A("corp_per_month")), NUM1)
    corp = line("Pro на конец месяца", lambda i: "", NUM1,
                note="Дробь — это средний поток: за год не продлевает пятая часть.")
    fill(corp, lambda i: ("=%s%d" % (col(i), corp_new)) if i == 0 else
         "=%s%d*(1-%s/12)+%s%d" % (col(i - 1), corp, A("corp_churn"), col(i), corp_new), NUM1)

    sec("Выручка")
    share = lambda i: "%s*%d/%d" % (A("share_y"), i, MONTHS)   # noqa: E731
    rev_b2c = line("Выручка от One", lambda i: "=%s%d*(%s*(1-%s)+%s/12*%s)"
                   % (col(i), paid, A("price_m"), share(i), A("price_y"), share(i)),
                   note="Годовая подписка засчитывается по 1/12 в месяц.")
    corp_rev = line("Выручка от Pro", lambda i: "=%s%d*%s/12" % (col(i), corp, A("corp_price")),
                    note="Годовой договор засчитывается по 1/12 в месяц.")
    rev = line("Выручка всего", lambda i: "=%s%d+%s%d" % (col(i), rev_b2c, col(i), corp_rev),
               RUB, BOLD)
    year_sold = line("  из неё годовых подписок One продано, ₽",
                     lambda i: "=%s%d*%s*%s" % (col(i), new, share(i), A("price_y")),
                     note="Деньги за год вперёд. Только с них возможен возврат.")
    cash_in = line("Поступило денег",
                   lambda i: "=%s%d+%s%d-%s%d*%s*%s/12+%s%d*%s"
                             % (col(i), rev_b2c, col(i), year_sold, col(i), new, share(i),
                                A("price_y"), col(i), corp_new, A("corp_price")),
                   note="Годовые подписчики и компании платят сразу за год.")

    sec("Расходы")
    first = line("Хостинг Timeweb", lambda i: "=%s" % A("timeweb"))
    line("Yandex.Cloud и ассистент", lambda i: "=%s+%s%d*%s*%s"
         % (A("ycloud"), col(i), paid, A("ai_q"), A("ai_cost_q")),
         note="Постоянный счёт плюс вопросы подписчиков: подписчики × вопросы × цена вопроса.")
    line("Claude", lambda i: "=%s" % A("claude_sub"))
    line("API-ФНС", lambda i: "=%s" % A("fns"))
    line("Онлайн-касса", lambda i: "=%s" % A("kassa"))
    line("Бухгалтерия", lambda i: "=%s" % A("acc"))
    line("Аренда офиса", lambda i: "=%s" % A("office"))
    line("Обслуживание Pro", lambda i: "=%s%d*%s" % (col(i), corp, A("corp_var")))
    line("Юрист и товарный знак", lambda i: "=%s" % A("legal"))
    line("Платная реклама", lambda i: "=%s" % A("mkt"))
    line("Прочее", lambda i: "=%s" % A("misc"))
    line("Комиссия за платежи", lambda i: "=%s%d*%s" % (col(i), cash_in, A("acq")))
    line("Возвраты по годовым подпискам", lambda i: "=%s%d*%s/2" % (col(i), year_sold, A("refund")))
    line("Зарплата гендиректора", lambda i: "=%s" % A("gd_salary"))
    line("Команда на подряде", lambda i: "=%s" % A("team_cost"))
    line("Разработчик", lambda i: "=IF(%d<=%s,0,IF(%d<=%s,%s,%s))"
         % (i + 1, A("dev_free"), i + 1, A("dev1_until"), A("dev1_cost"), A("dev2_cost")),
         note="Три месяца без разработчика, девять по 50 тыс, дальше по 100 тыс.")
    last = line("Взнос на травматизм", lambda i: "=%s/12" % A("injury"))
    costs = line("Расходы всего", lambda i: "=SUM(%s%d:%s%d)" % (col(i), first, col(i), last),
                 RUB, BOLD)

    sec("Налоги")
    rev_ytd = line("Доход с начала календарного года",
                   lambda i: "=SUM($%s$%d:%s%d)" % (col(0 if i < 3 else 3), rev, col(i), rev),
                   note="Старт в октябре, поэтому первый календарный год — три месяца.")
    vat = line("НДС", lambda i: "=IF(%s%d>%s,%s%d*%s,0)"
               % (col(i), rev_ytd, A("vat_limit"), col(i), rev, A("vat_rate")),
               note="Нули здесь — нормально: на АУСН НДС нет до 60 млн ₽ в год.")
    usn = line("Налог АУСН", lambda i: "=MAX((%s%d-%s%d-%s%d)*%s,%s%d*%s)"
               % (col(i), rev, col(i), costs, col(i), vat, A("usn"), col(i), rev, A("usn_min")),
               note="Большее из двух: 20% с прибыли или 3% с дохода за этот месяц.")
    taxes = line("Налоги всего", lambda i: "=%s%d+%s%d" % (col(i), vat, col(i), usn), RUB, BOLD)

    sec("Итог")
    net = line("Чистая прибыль", lambda i: "=%s%d-%s%d-%s%d"
               % (col(i), rev, col(i), costs, col(i), taxes), RUB, BOLD)
    flow = line("Денежный поток", lambda i: "=%s%d-%s%d-%s%d"
                % (col(i), cash_in, col(i), costs, col(i), taxes), RUB, BOLD)
    cash = line("Деньги на конец месяца", lambda i: "", RUB, BOLD,
                note="Месяц, когда число уходит в минус, — тот, к которому нужны деньги.")
    fill(cash, lambda i: ("=%s+%s%d" % (A("cash0"), col(i), flow)) if i == 0
         else "=%s%d+%s%d" % (col(i - 1), cash, col(i), flow), RUB)
    ws.column_dimensions[get_column_letter(2 + MONTHS)].width = 60
    return ws, {"reg": reg, "paid": paid, "corp": corp, "corp_rev": corp_rev, "rev": rev,
                "costs": costs, "taxes": taxes, "net": net, "cash": cash}


# ---------------------------------------------------------- налоги и риски
def sheet_tax_risk(wb, ref):
    ws = wb.create_sheet("Налоги и риски")
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 80
    A = lambda key: "Допущения!$B$%d" % ref[key]        # noqa: E731

    r = 1
    put(ws, r, 1, "Налоги и риски", H1); r += 2

    put(ws, r, 1, "Почему ООО на АУСН", H2); r += 1
    r = bullets(ws, r, (
        "Страховые взносы на АУСН — 0%. Остаётся только взнос на травматизм, 2 959 ₽ в год. "
        "На обычной УСН за гендиректора без зарплаты пришлось бы платить 8 128 ₽ в месяц: "
        "с 2026 года взносы с руководителя считаются от МРОТ, даже если зарплаты нет.",
        "Плата за это — ставка 20% с прибыли вместо 15% и минимальный налог 3% от дохода "
        "вместо 1%, причём считается он за каждый месяц отдельно: убыточный месяц нельзя "
        "перекрыть прибыльным.",
        "Пока мы в убытке, АУСН выгоднее обычной УСН при выручке до 4,73 млн ₽ в год; когда "
        "выйдем в прибыль — при прибыли до 1,89 млн ₽ в год. Выше — выгоднее перейти на УСН "
        "с начала следующего года.",
        "НДС на АУСН нет до 60 млн ₽ дохода в год. На обычной УСН освобождение кончается на "
        "20 млн ₽.",
    ), 3, 46)
    r += 1

    put(ws, r, 1, "Что нужно соблюдать, чтобы остаться на АУСН", H2); r += 1
    r = bullets(ws, r, (
        "Доход до 60 млн ₽ в год и не больше 5 человек. Спросить бухгалтера, считаются ли "
        "подрядчики, в том числе разработчик.",
        "Счета только в банках из списка ФНС, выплаты только безналом, другие режимы "
        "совмещать нельзя, доля участника-юрлица — не больше 25%.",
        "Деловую причину выбора режима лучше записать заранее: переход только ради нулевых "
        "взносов налоговая может оспорить.",
        "Гендиректор без зарплаты при живой выручке — частый повод для вопросов банка.",
    ), 3, 36)
    r += 1

    put(ws, r, 1, "Разработчик на подряде: риск", H2); r += 1
    put(ws, r, 1, "Подряд без взносов — законно и обычно. Но одинаковая сумма каждый месяц и "
                  "единственный заказчик — признаки, по которым налоговая может признать "
                  "отношения трудовыми. Снимает риск договор на конкретный результат, акт с "
                  "перечнем сделанного на каждую сдачу и чек самозанятого на каждую выплату. "
                  "Если подрядчик был нашим сотрудником в последние два года, самозанятым для "
                  "нас он быть не может.", NORM, wrap=True)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    ws.row_dimensions[r].height = 76; r += 1
    paid_out = "(%s*9+%s*12)" % (A("dev1_cost"), A("dev2_cost"))
    for name, formula, note in (
        ("Выплачено разработчику за 24 месяца", "=%s" % paid_out,
         "Девять месяцев по первой ставке и двенадцать по второй."),
        ("Взносы, если признают работником", "=%s*%s" % (paid_out, A("ins_rate")),
         "30% со всех выплат задним числом."),
        ("Штраф 20%", "=%s*%s*0.2" % (paid_out, A("ins_rate")), "П. 1 ст. 122 НК РФ."),
        ("Итого при худшем исходе", "=%s*%s*1.2" % (paid_out, A("ins_rate")), "Плюс пени."),
    ):
        put(ws, r, 1, name, NORM); put(ws, r, 2, formula, RED, fmt=RUB)
        put(ws, r, 3, note, SMALL, wrap=True); r += 1
    r += 1

    put(ws, r, 1, "Что добавляет продажа людям", H2); r += 1
    r = bullets(ws, r, (
        "Чек на каждый платёж (54-ФЗ). Обычно его выбивает платёжный сервис — проверить в "
        "договоре; иначе нужна облачная касса.",
        "Возврат: человек вправе отказаться в любой момент и получить деньги за "
        "неиспользованный срок, и оферта этого не отменит. Оформление доступа лицензией на "
        "базу данных может сузить возврат — вопрос юристу.",
        "Персональные данные: уведомление Роскомнадзора, политика обработки и отдельное "
        "согласие на рассылку.",
        "Реклама в каналах маркируется, и о ней отчитываются. Если это делает площадка — "
        "только по письменному поручению.",
        "Товарный знак: пока он не зарегистрирован, название может занять кто угодно. "
        "Регистрация идёт около года.",
    ), 3, 36)
    r += 1

    put(ws, r, 1, "Источники ставок (проверено 23 сентября 2026)", H2); r += 1
    for t in ("ФЗ от 25.02.2022 № 17-ФЗ — АУСН: ставка 20%, минимальный налог 3% за месяц, "
              "нулевой тариф взносов, пределы 60 млн ₽ и 5 человек",
              "ФЗ от 28.11.2025 № 425-ФЗ — взносы с руководителя от МРОТ (п. 1 ст. 421 НК РФ)",
              "взнос на травматизм для АУСН на 2026 год — 2 959 ₽ в год",
              "ст. 32 Закона РФ «О защите прав потребителей» — отказ от услуги и возврат",
              "54-ФЗ — касса при расчётах с людьми",
              "Yandex AI Studio — 0,3 ₽ за 1000 токенов (gpt-oss-120b)"):
        put(ws, r, 1, "— " + t, SMALL); r += 1
    return ws


# ------------------------------------------------------------------ итоги
def sheet_summary(wb, calc, unit):
    ws = wb.create_sheet("Итоги", 0)
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 72
    last = get_column_letter(1 + MONTHS)
    m12 = get_column_letter(1 + 12)
    C = "'%s'!" % CALC
    U = "'Экономика клиента'!"

    r = 1
    put(ws, r, 1, "«Компас» — финансовая модель на 24 месяца", H1); r += 1
    put(ws, r, 1, "Октябрь 2026 — сентябрь 2028. One — 990 ₽ в месяц, Pro — 49 900 ₽ в год, "
                  "два новых договора Pro в месяц. ООО на АУСН.", SMALL); r += 2

    def sec(title):
        nonlocal r
        for c in range(1, 4):
            ws.cell(row=r, column=c).fill = FILL_HEAD
        put(ws, r, 1, title, H2, fill=FILL_HEAD)
        r += 1

    def row(name, formula, note="", fmt=RUB, font=NORM):
        nonlocal r
        put(ws, r, 1, name, font, wrap=True)
        put(ws, r, 2, formula, font, fmt=fmt)
        put(ws, r, 3, note, SMALL, wrap=True)
        ws.row_dimensions[r].height = 28
        r += 1

    k = calc
    sec("Главное")
    row("Месяц выхода в прибыль", "=%sB%d" % (U, unit["be_month"]),
        "Первый месяц с чистой прибылью.", RUB0, BOLD)
    row("Месяц, когда кончаются стартовые деньги",
        "=IFERROR(MATCH(TRUE,INDEX(%s$B$%d:$%s$%d<0,0),0),\"не кончаются\")"
        % (C, k["cash"], last, k["cash"]), "", RUB0, BOLD)
    row("Сколько денег нужно сверх стартовых",
        "=MAX(0,-MIN(%sB%d:%s%d))" % (C, k["cash"], last, k["cash"]),
        "Самая глубокая точка минуса.", RUB, RED)

    sec("За два года")
    row("Платящих One через 12 месяцев", "=%s%s%d" % (C, m12, k["paid"]), "", RUB0)
    row("Платящих One через 24 месяца", "=%s%s%d" % (C, last, k["paid"]), "", RUB0)
    row("Договоров Pro через 24 месяца", "=%s%s%d" % (C, last, k["corp"]), "", NUM1)
    row("Выручка за 24 месяца", "=SUM(%sB%d:%s%d)" % (C, k["rev"], last, k["rev"]), "", RUB, BOLD)
    row("  из неё от Pro", "=SUM(%sB%d:%s%d)" % (C, k["corp_rev"], last, k["corp_rev"]))
    row("Расходы за 24 месяца", "=SUM(%sB%d:%s%d)" % (C, k["costs"], last, k["costs"]))
    row("Налоги за 24 месяца", "=SUM(%sB%d:%s%d)" % (C, k["taxes"], last, k["taxes"]))
    row("Чистая прибыль за 24 месяца", "=SUM(%sB%d:%s%d)" % (C, k["net"], last, k["net"]),
        "", RUB, BOLD)

    sec("Один клиент")
    row("Вклад одного подписчика One в месяц", "=%sB%d" % (U, unit["contrib"]))
    row("Вклад одного договора Pro в месяц", "=%sB%d" % (U, unit["corp_contrib"]))
    row("Один Pro = столько подписчиков One", "=%sB%d" % (U, unit["corp_eq"]), "", NUM1, GOOD)
    row("LTV ÷ CAC", "=%sB%d" % (U, unit["ratio"]),
        "Ниже 1 — реклама не окупается.", NUM2, BOLD)
    row("Порог: подписчиков One без Pro", "=%sB%d" % (U, unit["be"]),
        "Без разработчика.", RUB0, GOOD)
    row("Порог: договоров Pro без One", "=%sB%d" % (U, unit["be_corp"]),
        "Без разработчика.", RUB0, GOOD)

    r += 1
    put(ws, r, 1, "Как читать", H2); r += 1
    bullets(ws, r, (
        "Меняйте только жёлтые клетки на листе «Допущения» — всё остальное пересчитается.",
        "Результат решают три числа: отток подписчиков, темп договоров Pro и зарплата "
        "разработчика. Все три — на листе «Допущения».",
        "Числа с пометкой «уточнить» — оценки, а не счета. Их стоит заменить в первую очередь.",
        "Лист «Налоги и риски» стоит прочитать целиком: там то, что не видно в числах.",
    ), 3, 30)
    return ws


# ------------------------------------------------------------------ пересчёт
def recalculate(path: Path) -> bool:
    """Пересчитать книгу LibreOffice и сохранить значения рядом с формулами.

    Зачем это обязательно. openpyxl пишет формулы, но не кладёт рядом
    результат. Excel на компьютере пересчитает при открытии, а просмотрщик на
    телефоне показывает то, что лежит в файле, — пустоту, которая рисуется
    нулями (22 сентября 2026 владелец увидел с телефона страницу нулей).

    Нужен пакет libreoffice-calc: без него даже пустая книга не открывается, и
    ошибка выглядит как «source file could not be loaded», а не как «нет Calc».
    """
    if not shutil.which("soffice"):
        print("! LibreOffice не найден — книга остаётся без посчитанных значений.")
        print("  На телефоне она покажет нули. Поставьте libreoffice-calc и соберите заново.")
        return False
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = tmp / "m.xlsx"
        shutil.copy(path, src)
        out = subprocess.run(
            ["soffice", "--headless", "-env:UserInstallation=file://%s/profile" % tmp,
             "--convert-to", "xlsx", str(src), "--outdir", str(tmp / "out")],
            capture_output=True, text=True, timeout=600)
        done = tmp / "out" / "m.xlsx"
        if not done.exists():
            print("! Пересчёт не удался: %s" % (out.stderr.strip()[:200] or "файл не появился"))
            print("  Чаще всего это значит, что стоит libreoffice-core без libreoffice-calc.")
            return False
        shutil.copy(done, path)
    return True


def main():
    wb = Workbook()
    wb.remove(wb.active)
    _, ref = sheet_assumptions(wb)
    _, calc = sheet_calc(wb, ref)
    _, unit = sheet_unit(wb, ref, calc)
    sheet_tax_risk(wb, ref)
    sheet_summary(wb, calc, unit)
    order = ["Итоги", "Экономика клиента", "Допущения", CALC, "Налоги и риски"]
    wb._sheets = [wb[n] for n in order]
    wb.save(OUT)
    ok = recalculate(OUT)
    print("Записано: %s" % OUT)
    print("Листов: %s" % ", ".join(order))
    print("Значения посчитаны: %s" % ("да" if ok else "НЕТ — см. предупреждение выше"))
    if ok:
        print("Сверить с двойником: python3 -m pytest test_finance_model.py -q")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
