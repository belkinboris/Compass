# -*- coding: utf-8 -*-
"""Форма 0409806 «Бухгалтерский баланс (публикуемая форма)» — готовые,
официально опубликованные банком «Активы» и «Собственные средства», прямо
со страницы ЦБ. Найдено 23 августа 2026 в ответ на вопрос владельца
(«с чем сравнивали»): наш собственный расчёт по сырым счетам формы 101
(`cbr_account_types.py`) даёт ВАЛОВУЮ величину и устойчиво завышает
«Активы» на 3-11% относительно того, что банк и сам ЦБ называют этим
словом (независимая сверка — TAdviser/МСФО, а надо было сверяться с самим
ЦБ). SOAP-метод той же формы (`GetF806Xml`/`GetF806Data`) — тупик, отдаёт
только шапку строк без единого числа (проверено 18 августа). Но у формы
806 есть ВТОРОЙ канал — обычная веб-страница ЦБ, и она отдаёт числа:
https://www.cbr.ru/banking_sector/credit/coinfo/f806/?dt=YYYYMM&regnum=NNNN
(`dt` — год и месяц ПЕРВОГО ДНЯ отчётного квартала: «1.04.2026» → `202604`;
`regnum` — тот же регистрационный номер банка, что и у `cbr_client.py`).

ЭТО РЕШЕНИЕ ВОПРОСА, А НЕ ОБХОД. Форма 101 остаётся полезной для формы 102
(прибыли/убытки помесячно — `cbr_client.py`, уже проверено), но для «Активы»/
«Капитал» на сайт идёт ИМЕННО эта форма — она чистая (за вычетом резервов),
её же видит любой человек на сайте ЦБ, спорить не с чем.

СТРАНИЦА — ОБЫЧНЫЙ HTML, БЕЗ JS-РЕНДЕРА: таблица с классом `data`, строки
`<tr><td>номер</td><td>название</td><td>примечание</td><td class="right">
<nobr>значение за отчётный период</nobr></td><td class="right"><nobr>
значение за предыдущий год</nobr></td></tr>`. Оба числа — тыс. руб.
Строки «Всего активов» (раздел I) и «Всего источников собственных средств»
(раздел III) — то, что нужно; остальные строки (детализация статей) не
разбираются, за ними не гонимся.

ЗАПРОШЕННЫЙ КВАРТАЛ МОЖЕТ БЫТЬ ЕЩЁ НЕ ОПУБЛИКОВАН. Проверено 23 августа
2026: `dt=202607` (квартал, начавшийся 1 июля 2026) на эту дату отдаёт
страницу с теми же названиями строк, но ПУСТЫМИ значениями (`<nobr></nobr>`)
— банк квартал ещё не отчитался, это НЕ ошибка запроса. `dt` с заведомо
некорректным месяцем (например, «13») отдаёт страницу вовсе без таблицы
данных. Оба случая — `parse_balance()` возвращает `None`, а не бросает
исключение; `latest_available()` откатывается на квартал назад и пробует
снова, пока не найдёт данные или не исчерпает лимит попыток.

ЕДИНИЦЫ. Страница отдаёт тыс. руб — `F806Balance.assets_rub`/`equity_rub`
уже переведены в рубли (`× 1000`), тот же формат, что `assets_rub`/
`equity_rub` у `fns_client.py` (JS `fnsMoney()` ждёт именно рубли, не
тысячи).

ПОЛНАЯ ТАБЛИЦА (Этап 8, П2-8) — просьба обоих партнёров живьём после
показа сводных плиток: «Нужен бухгалтерский баланс. ОСВ, отчёт о
финансовых результатах и тд не надо… Баланс это небольшой документ.
Активы и пассивы, 1-2 странички». `parse_full_table()` разбирает ВСЕ
строки разделов I–III (Активы / Пассивы / Источники собственных средств)
— именно то, что бухгалтерски и называется балансом (Актив = Пассив +
Капитал). Раздел IV «Внебалансовые обязательства» на той же странице —
уже не баланс в этом смысле (гарантии, условные обязательства), и явно
не входит в «1-2 странички» — сознательно не разбирается. `_ROW_RE`
(сводка) и парсер полной таблицы читают одну и ту же разметку, просто
полная таблица не фильтрует по названию строки.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import httpx

BASE_URL = "https://www.cbr.ru/banking_sector/credit/coinfo/f806/"
QUARTER_START_MONTHS = (1, 4, 7, 10)

_TITLE_RE = re.compile(r"публикуемая форма\)\s*на\s*(\d{1,2})\.(\d{1,2})\.(\d{4})")
_LEGAL_NAME_RE = re.compile(r'coinfo_item_text[^>]*>([^<]*)</div>')
_ROW_RE = re.compile(
    r'<td>[\d.]+</td>\s*<td>(?P<name>[^<]*)</td>\s*<td>(?P<note>[^<]*)</td>\s*'
    r'<td class="right"><nobr>(?P<v1>[\d\xa0 ]*)</nobr></td>\s*'
    r'<td class="right"><nobr>(?P<v2>[\d\xa0 ]*)</nobr></td>',
    re.S,
)

ASSETS_ROW = "Всего активов"
EQUITY_ROW = "Всего источников собственных средств"

BALANCE_SECTIONS = ("I. Активы", "II. Пассивы", "III. Источники собственных средств")

_ROW_BLOCK_RE = re.compile(r'<tr[^>]*>(?P<body>.*?)</tr>', re.S)
_SECTION_CELL_RE = re.compile(r'<td colspan="5">\s*<strong>(?P<title>[^<]*)</strong>\s*</td>', re.S)
_DETAIL_CELL_RE = re.compile(
    r'<td>(?P<num>[^<]*)</td>\s*<td>(?P<name>[^<]*)</td>\s*<td>(?P<note>[^<]*)</td>\s*'
    r'<td class="right"><nobr>(?P<v1>[-\d\xa0 ]*)</nobr></td>\s*'
    r'<td class="right"><nobr>(?P<v2>[-\d\xa0 ]*)</nobr></td>',
    re.S,
)


class F806Error(RuntimeError):
    pass


@dataclass(frozen=True)
class F806Balance:
    regnum: int
    as_of: date                     # первый день отчётного квартала
    assets_rub: int
    assets_rub_prior_year: int | None
    equity_rub: int
    equity_rub_prior_year: int | None
    legal_name: str | None          # полное юридическое имя со страницы ЦБ, для подписи


def _parse_number(raw: str) -> int | None:
    cleaned = raw.replace("\xa0", "").replace(" ", "").strip()
    return int(cleaned) if cleaned else None


def _quarter_start_on_or_before(d: date) -> date:
    month = max(m for m in QUARTER_START_MONTHS if m <= d.month)
    return date(d.year, month, 1)


def _step_back_one_quarter(d: date) -> date:
    idx = QUARTER_START_MONTHS.index(d.month)
    if idx == 0:
        return date(d.year - 1, QUARTER_START_MONTHS[-1], 1)
    return date(d.year, QUARTER_START_MONTHS[idx - 1], 1)


def fetch_page(regnum: int, on_date: date, client: httpx.Client) -> str:
    resp = client.get(BASE_URL, params={"dt": f"{on_date.year:04d}{on_date.month:02d}", "regnum": regnum},
                       timeout=20.0)
    resp.raise_for_status()
    return resp.text


def parse_balance(html: str, regnum: int) -> F806Balance | None:
    """`None` — квартал не опубликован (пустые значения) или страница не
    похожа на форму 806 вовсе (например, некорректная дата в запросе).
    НЕ бросает исключение на эти случаи — это ожидаемый, частый исход
    (см. докстроку модуля), а не ошибка."""
    title_m = _TITLE_RE.search(html)
    if not title_m:
        return None
    day, month, year = (int(x) for x in title_m.groups())
    as_of = date(year, month, day)

    rows: dict[str, tuple[int | None, int | None]] = {}
    for m in _ROW_RE.finditer(html):
        name = m.group("name").strip()
        if name in (ASSETS_ROW, EQUITY_ROW):
            rows[name] = (_parse_number(m.group("v1")), _parse_number(m.group("v2")))

    assets = rows.get(ASSETS_ROW)
    equity = rows.get(EQUITY_ROW)
    if not assets or assets[0] is None or not equity or equity[0] is None:
        return None

    name_m = _LEGAL_NAME_RE.search(html)
    legal_name = name_m.group(1).strip() if name_m else None

    return F806Balance(
        regnum=regnum,
        as_of=as_of,
        assets_rub=assets[0] * 1000,
        assets_rub_prior_year=assets[1] * 1000 if assets[1] is not None else None,
        equity_rub=equity[0] * 1000,
        equity_rub_prior_year=equity[1] * 1000 if equity[1] is not None else None,
        legal_name=legal_name,
    )


def parse_full_table(html: str) -> dict | None:
    """Полный бухгалтерский баланс (разделы I-III) — строки «подпись |
    значение», не только два итога. `None` — тот же честный исход, что и
    у `parse_balance()`: квартал не опубликован или страница не форма 806.

    Возвращает {"as_of": date, "legal_name": str|None, "sections": [
    {"title": str, "rows": [{"num": str, "name": str, "note": str,
    "period_rub": int|None, "prior_year_rub": int|None}, ...]}, ...]}
    — только для секций из BALANCE_SECTIONS, в порядке появления на
    странице; раздел IV (внебалансовые обязательства) не включён (см.
    докстроку модуля)."""
    title_m = _TITLE_RE.search(html)
    if not title_m:
        return None
    day, month, year = (int(x) for x in title_m.groups())
    as_of = date(year, month, day)

    sections: list[dict] = []
    current: dict | None = None
    any_value = False
    for block in _ROW_BLOCK_RE.finditer(html):
        body = block.group("body")
        section_m = _SECTION_CELL_RE.search(body)
        if section_m:
            title = section_m.group("title").strip()
            current = {"title": title, "rows": []} if title in BALANCE_SECTIONS else None
            if current is not None:
                sections.append(current)
            continue
        if current is None:
            continue
        detail_m = _DETAIL_CELL_RE.search(body)
        if not detail_m:
            continue
        period = _parse_number(detail_m.group("v1"))
        prior = _parse_number(detail_m.group("v2"))
        if period is not None or prior is not None:
            any_value = True
        current["rows"].append({
            "num": detail_m.group("num").strip(),
            "name": detail_m.group("name").strip(),
            "note": detail_m.group("note").strip(),
            "period_rub": period * 1000 if period is not None else None,
            "prior_year_rub": prior * 1000 if prior is not None else None,
        })

    if not any_value:
        return None

    name_m = _LEGAL_NAME_RE.search(html)
    legal_name = name_m.group(1).strip() if name_m else None
    return {"as_of": as_of, "legal_name": legal_name, "sections": sections}


def find_latest_page(regnum: int, client: httpx.Client, *, today: date, max_quarters_back: int = 6) -> str | None:
    """Сырой HTML последнего ОПУБЛИКОВАННОГО квартала (та же логика отката,
    что раньше жила только внутри `latest_available()`) — вынесена отдельно,
    чтобы `latest_available()` и `latest_full_table()` разбирали ОДНУ и ту же
    страницу вместо двух отдельных сетевых запросов на банк."""
    on_date = _quarter_start_on_or_before(today)
    for _ in range(max_quarters_back):
        html = fetch_page(regnum, on_date, client)
        if parse_balance(html, regnum) is not None:
            return html
        on_date = _step_back_one_quarter(on_date)
    return None


def latest_available(regnum: int, client: httpx.Client, *, today: date, max_quarters_back: int = 6) -> F806Balance | None:
    """Идёт от последнего НАЧАВШЕГОСЯ квартала назад, пока не найдёт
    опубликованные данные (первый квартал почти всегда ещё не опубликован
    — банкам даётся время на отчётность) или не исчерпает попытки."""
    html = find_latest_page(regnum, client, today=today, max_quarters_back=max_quarters_back)
    return parse_balance(html, regnum) if html is not None else None


def latest_full_table(regnum: int, client: httpx.Client, *, today: date, max_quarters_back: int = 6) -> dict | None:
    """Полная таблица (см. `parse_full_table()`) для того же последнего
    опубликованного квартала, что вернул бы `latest_available()`."""
    html = find_latest_page(regnum, client, today=today, max_quarters_back=max_quarters_back)
    return parse_full_table(html) if html is not None else None
