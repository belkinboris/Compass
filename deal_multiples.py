# -*- coding: utf-8 -*-
"""Мультипликаторы сделок (EV/Выручка) — Этап 16, П1.

ПОЧЕМУ ЭТОТ МОДУЛЬ СУЩЕСТВУЕТ. Пилот (`pipeline/measure_deal_multiples_pilot.py`,
Этап 15) показал: сырое сопоставление «сумма сделки / выручка цели» без
фильтров даёт мультипликаторы до 4336x — не редкие сделки, а несопоставимые
величины (IPO/допэмиссия вместо продажи компании, доля вместо 100%, выручка
управляющей компании-СПВ вместо операционного бизнеса). Здесь та же методика,
что доказала себя в пилоте, перенесена в код, КОТОРЫЙ РЕАЛЬНО ПОКАЗЫВАЕТСЯ
ПОСЕТИТЕЛЮ, — и поэтому обвешана тестами на каждую найденную ловушку, а не
только на happy path.

ЧТО СЧИТАЕТСЯ «ЧИСТОЙ» СДЕЛКОЙ ДЛЯ МУЛЬТИПЛИКАТОРА:
  * `type == "M&A"` И названы ОБЕ стороны (покупатель и продавец) — тип
    сам по себе ненадёжен: у допэмиссий и SPO он тоже стоит «M&A» (см.
    CLAUDE.md, «Тип сделки определяет не только ярлык, но и какие роли
    существуют»), но у cash-in сделки структурно нет продавца — деньги
    идут в компанию, а не от одного акционера другому. Требование «обе
    стороны названы» отсеивает Segezha-допэмиссию и SPO «Эталона» ещё на
    текстовом фильтре, до всякого обращения к БФО.
  * сумма сделки — число В РУБЛЯХ (не $/€: курс на момент старой сделки
    сегодняшним пересчётом молча искажается, см. CLAUDE.md «Число может
    быть верным фактом и совсем не той величиной»).
  * сумма НЕ помечена «(по оценке)» — оценка не то же самое, что цена.
  * доля предмета сделки УСТАНОВЛЕНА и не меньше 95%: названа цифрой
    («100% акций») или словами о покупке целиком («целиком», «полностью»,
    «единственным владельцем»). Неизвестная доля — не допуск: до 6 сентября
    2026 карточка без процента считалась «потенциально 100%», и это молча
    превращало «нет распознанного 30%» в «куплено целиком» (замечание
    аудита, раунд 2). Теперь неизвестность оставляет сделку в базе, но не
    в мультипликаторе — пока чтение источника не запишет долю явно.
  * сумма — ЦЕНА, НАЗВАННАЯ СТОРОНАМИ (`sum_basis` == 'disclosed'): не
    оценка, не диапазон, не «более/не менее», не стартовая цена торгов, не
    объём допэмиссии. Смысл суммы выводится из её текста (`sum_basis()`), а
    карточка может нести явное поле `sum_basis`, которое сильнее разбора —
    для случаев, где по тексту не видно, что число не цена (иск о
    компенсации, оценка всей компании при IPO).
  * предмет — один профиль-компания, а не лот из нескольких юрлиц
    (`lot`): отчётность одного юрлица не описывает весь купленный периметр.
  * цель сделки — не банк (РСБУ банков не сопоставим с обычной выручкой,
    см. блок «По данным Банка России») и с подтверждённым по ИНН профилем
    (fns_registry.py, decision=confirmed).
  * выручка цели взята ЗА ГОД, ближайший к году сделки СВЕРХУ ВНИЗ не
    больше чем на один год (последний отчётный год перед закрытием —
    стандартная практика в M&A, а разрыв 2+ года почти всегда значит, что
    более свежей отчётности просто нет, и старое число может не отражать
    компанию на момент сделки).
  * итоговый мультипликатор — в разумных границах 0,1–15. Шире — почти
    всегда означает, что выручка взята не у того юридического лица (лот,
    управляющая компания-прослойка вместо операционного бизнеса), а не
    редкую сделку: см. находки пилота (g5eb6ff22 — 4336x, revenue
    юрлица-прослойки 17 млн ₽ при сумме сделки 75 млрд ₽).

Ничего из отброшенного не считается неверным фактом — это фильтр
СОПОСТАВИМОСТИ, а не оценка качества карточки: сделка без чистого
мультипликатора просто не участвует в статистике, её данные не трогаются.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select

MIN_MULTIPLE = 0.1
MAX_MULTIPLE = 15.0
MIN_STAKE_PERCENT = 95.0
# Отчётность — за последний ПОЛНЫЙ год до сделки (разрыв 1), на крайний
# случай — за позапрошлый (разрыв 2: отчёт за прошлый год ещё не сдан).
# Тот же год, что и сделка, не годится: на дату сделки его результата не
# существует (аудит 5 сентября 2026: цену февраля 2025 делили на выручку
# за весь 2025 год).
MIN_YEAR_GAP = 1
MAX_YEAR_GAP = 2
MIN_YEAR = 2022
MIN_INDUSTRY_SAMPLE = 3

UNIT_MULT = {'тыс': 1e3, 'млн': 1e6, 'млрд': 1e9, 'трлн': 1e12}

_RUB_AMOUNT = re.compile(
    r'(?P<n1>\d[\d\s\xa0]*(?:[.,]\d+)?)'
    r'(?:\s*[–—-]\s*(?P<n2>\d[\d\s\xa0]*(?:[.,]\d+)?))?'
    r'\s*(?P<unit>тыс|млн|млрд|трлн)\.?\s*₽',
    re.I)
_STAKE_PCT = re.compile(r'(\d{1,3}(?:[.,]\d+)?)\s*%')
# Процент, который НЕ доля: «на 30% выше», «дисконт 20%», «выросла на 15%»,
# «ставка 12%» — рядом с ним стоит слово о сравнении величин, а не о
# пакете. Замер по золотой выборке 6 сентября 2026: у «Камы» (куплено
# 100%) `eco.share` говорил «на 30% превышает стоимость», и наименьший
# процент (30) выбрасывал сделку как покупку меньшей доли.
_NOT_A_STAKE = re.compile(
    r'(?:(?:^|[^а-яё])(?:на|в|до|с|со|от)\s+(?:\d{1,3}(?:[.,]\d+)?)\s*%\s*(?:выше|ниже|больше|меньше|дороже|дешевле|превыша|уступа))'
    r'|(?:(?:\d{1,3}(?:[.,]\d+)?)\s*%\s*(?:выше|ниже|больше|меньше|дороже|дешевле|превыша|дисконт|скидк|годовых|ставк))'
    r'|(?:(?:дисконт|скидк|ставк|рост|снижен|падени|выросл|упал|сократил|увеличил)[а-яё]*\s+(?:на\s+|в\s+|до\s+)?(?:\d{1,3}(?:[.,]\d+)?)\s*%)',
    re.I)
# Не твёрдая цена: оценка, «около»/«~»/«до», сумма одного этапа или один из
# вариантов («или EV…»), допэмиссия, «без учёта долга», неофициальные и
# предварительные цифры (аудит 5 сентября 2026: «~100 млн ₽ (или EV ~1 млрд
# ₽)» и «400 млн ₽ (первый этап)» проходили как цена и давали ×0,55 и ×9,28).
_RANGE = re.compile(r'\d\s*(?:тыс|млн|млрд|трлн)?\.?\s*[–—-]\s*\d', re.I)
_LOWER_BOUND = re.compile(r'(?:^|[^а-яё])(?:более|свыше|не\s+менее|как\s+минимум|минимум|от)\s*\d', re.I)
_AUCTION_START = re.compile(r'стартов|начальн|по\s+стартовой', re.I)
_ESTIMATE = re.compile(
    r'оценк|оценив|~|≈|около|^\s*до\s|не\s+более|\bили\b|этап|допэмисс|без\s+уч[её]т'
    r'|неофициальн|предварит|ожида|по\s+данным|по\s+одним|списан|запрашива|ориентировочн',
    re.I)
_FOREIGN = re.compile(r'[$€£¥]|\b(?:USD|EUR|долл|евро)', re.I)
_UNDISCLOSED = re.compile(r'^\s*(?:—|-|не\s+раскрыт[а-яё]*|публично\s+не\s+сообщал[а-яё]*|нет\s+данных)?\s*\.?\s*$', re.I)

# Смысл суммы — закрытый список. Порядок важен: явное поле карточки сильнее
# разбора текста, «не цена» сильнее «оценки», оценка сильнее «раскрыто».
SUM_BASES = ('disclosed', 'estimate', 'range', 'lower_bound', 'auction_start',
             'foreign_currency', 'not_a_price', 'valuation', 'raise', 'undisclosed', 'unparsed')
SUM_BASIS_LABELS = {
    'disclosed': 'цена, названная сторонами',
    'estimate': 'оценка (эксперты, СМИ, «около»)',
    'range': 'диапазон',
    'lower_bound': 'нижняя граница («более», «не менее»)',
    'auction_start': 'стартовая цена торгов',
    'foreign_currency': 'сумма в валюте',
    'not_a_price': 'число не является ценой сделки',
    'valuation': 'оценка всей компании, не цена пакета',
    'raise': 'объём привлечения (допэмиссия, раунд, размещение)',
    'undisclosed': 'не раскрыта',
    'unparsed': 'не разобрана',
}


def sum_basis(deal: dict[str, Any]) -> str:
    """Что означает число в `sum` — единственное место, где это решается
    (клиентская копия — `sumBasis` в static/index.html, правила те же).

    До 6 сентября 2026 смысл суммы нигде не хранился и не вычислялся: топ
    «Аналитики» и мультипликаторы читали `sum` как цену, если в строке не
    было слова «оценк». Так в «покупки» попали 320 млрд ₽ структурной сделки
    под залог и допэмиссия Segezha, а в мультипликаторы — стартовая цена
    торгов и «более 200 млрд ₽» (аудит, раунды 1 и 2). Явное поле карточки
    `sum_basis` сильнее разбора текста — им рутина или человек помечают
    то, чего по тексту не видно (компенсация по иску, оценка всей компании)."""
    explicit = deal.get('sum_basis')
    if explicit in SUM_BASES:
        return explicit
    text = str(deal.get('sum') or '')
    if _UNDISCLOSED.match(text):
        return 'undisclosed'
    if _FOREIGN.search(text) and '₽' not in text:
        return 'foreign_currency'
    if _AUCTION_START.search(text):
        return 'auction_start'
    if _RANGE.search(text):
        return 'range'
    if _ESTIMATE.search(text):
        return 'estimate'
    if _LOWER_BOUND.search(text):
        return 'lower_bound'
    if '₽' not in text:
        return 'foreign_currency' if _FOREIGN.search(text) else 'unparsed'
    if not _RUB_AMOUNT.search(text):
        return 'unparsed'  # «несколько млрд ₽ (точно не указана)» — рубли есть, числа нет
    return 'disclosed'


def parse_rub_sum(text: str | None) -> float | None:
    """Число в рублях из строки суммы, или None, если это не ₽-сумма.

    Диапазон («36–45 млн ₽») усредняется — известное огрубление (см. урок
    «Диапазон при разборе может схлопнуться в одну цифру»), но для оценки
    порядка величины мультипликатора этого достаточно; сама карточка
    диапазон не теряет, он остаётся в `sum` как есть."""
    if not text:
        return None
    m = _RUB_AMOUNT.search(text)
    if not m:
        return None
    def num(s: str) -> float:
        return float(s.replace(' ', '').replace('\xa0', '').replace(',', '.'))
    n1 = num(m.group('n1'))
    n2 = num(m.group('n2')) if m.group('n2') else None
    mult = UNIT_MULT[m.group('unit').lower()]
    lo = n1 * mult
    hi = (n2 * mult) if n2 is not None else lo
    return (lo + hi) / 2


def is_estimate(text: str | None) -> bool:
    """Не твёрдая цена: оценка, диапазон, нижняя граница, стартовая цена
    торгов. Обёртка над `sum_basis` для строки без карточки."""
    if not text:
        return False
    return sum_basis({'sum': text}) in ('estimate', 'range', 'lower_bound', 'auction_start')


def stake_percent(deal: dict[str, Any]) -> float | None:
    """Доля предмета сделки в процентах, если она названа в тексте.

    None значит «доля не названа» — в контексте этого модуля такую сделку
    ТРЕТИРУЕМ как потенциально 100% (это стандартное умолчание для сделок
    смены контроля без явно указанной меньшей доли), а не отбрасываем;
    отбрасываются только сделки, где доля НАЗВАНА и она меньше порога."""
    # Заголовок — тоже место, где названа доля («Ростех приобрел 25% в …»,
    # «Софтлайн купил 51% К2-9b»): у 24 из 83 кандидатов (замер 5 сентября
    # 2026) доля стояла ТОЛЬКО в заголовке, и сумму за пакет делили на
    # выручку всей компании.
    # Берётся НАИМЕНЬШАЯ из названных долей по всем трём полям, а не
    # наибольшая: «консолидировали 100%, выкупив 30%» и «приобрёл 49%,
    # партнёр сохранил 51%» — покупка 30% и 49%, а не 100% и 51%. До 6 сентября
    # 2026 брался max по первому полю с процентами, и Guess (30%) с
    # БФТ/«Полиматика» (49%) проходили порог 95% (аудит, раунд 2). Меньшая
    # доля из текста — не обязательно купленная, но ошибка здесь в
    # безопасную сторону: сделка выпадает из выборки, а не искажает её.
    nums = []
    for text in (deal.get('eco', {}).get('share'), deal.get('asset'), deal.get('title')):
        if not text:
            continue
        cleaned = _NOT_A_STAKE.sub(' ', str(text))
        nums += [float(x.replace(',', '.')) for x in _STAKE_PCT.findall(cleaned)]
    plausible = [n for n in nums if 1 <= n <= 100]
    return min(plausible) if plausible else None


# Покупка целиком, названная словами, а не процентом: «купил компанию
# целиком», «выкупил полностью», «стал единственным владельцем».
_FULL_WORDS = re.compile(
    r'целиком|полностью|единственн[а-яё]*\s+(?:владельц|собственник|акционер)|весь\s+бизнес|вс[ея]\s+(?:акци|дол)',
    re.I)


def stake_established(deal: dict[str, Any]) -> float | None:
    """Доля, которую карточка НАЗЫВАЕТ: процент (наименьший из названных)
    или слова о покупке целиком (100). None — доля не установлена, и это
    не допуск (правило владельца, 6 сентября 2026: неизвестность не
    превращается в предположение «куплено 100%»)."""
    pct = stake_percent(deal)
    if pct is not None:
        return pct
    for text in (deal.get('eco', {}).get('share'), deal.get('asset'), deal.get('title')):
        if text and _FULL_WORDS.search(str(text)):
            return 100.0
    return None


def year_of(deal: dict[str, Any]) -> int | None:
    ds = str(deal.get('date') or '')
    return int(ds[:4]) if ds[:4].isdigit() else None


def target_of(deal: dict[str, Any]) -> str | None:
    return deal.get('target') or deal.get('asset_id')


@dataclass
class MultipleCandidate:
    """Сделка, прошедшая ТЕКСТОВЫЕ фильтры (без обращения к БФО) —
    промежуточный шаг перед докачкой выручки цели из базы."""
    deal_id: str
    title: str
    target_id: str
    year: int
    sum_rub: float
    stake_percent: float | None


EXCLUSION_LABELS = {
    'type': 'не покупка компании (IPO, инвестиция, финансирование)',
    'parties': 'не названы обе стороны',
    'year': 'сделка раньше 2022 года',
    'target': 'предмет не привязан к профилю компании',
    'target_lot': 'предмет — лот из нескольких юрлиц',
    'target_bank': 'предмет — банк',
    'target_unconfirmed': 'у предмета не подтверждён ИНН',
    'status': 'сделка не состоялась',
    'sum_basis': 'сумма — не цена, названная сторонами',
    'share_unknown': 'доля не установлена',
    'share_below': 'куплена доля меньше 95%',
    'sum_unparsed': 'сумма не разобрана',
}


def admission(d: dict[str, Any], confirmed_ids: set[str], bank_ids: set[str],
              lot_ids: set[str] | None = None) -> tuple[MultipleCandidate | None, str | None]:
    """Одна сделка: либо кандидат, либо причина отказа (ключ EXCLUSION_LABELS).
    Причины видны в ответе `/api/analytics/multiples` — чтобы «почему этой
    сделки нет в мультипликаторах» отвечалось цифрой, а не догадкой."""
    if d.get('type') != 'M&A':
        return None, 'type'
    has_buyer = bool(d.get('buyer') or d.get('buyer_name'))
    has_seller = bool(d.get('seller') or d.get('seller_id'))
    if not (has_buyer and has_seller):
        return None, 'parties'
    yr = year_of(d)
    if not yr or yr < MIN_YEAR:
        return None, 'year'
    target = target_of(d)
    if not target:
        return None, 'target'
    if lot_ids and target in lot_ids:
        return None, 'target_lot'
    if target in bank_ids:
        return None, 'target_bank'
    if target not in confirmed_ids:
        return None, 'target_unconfirmed'
    if d.get('status') == 'Не состоялась':
        return None, 'status'
    if sum_basis(d) != 'disclosed':
        return None, 'sum_basis'
    stake = stake_established(d)
    if stake is None:
        return None, 'share_unknown'
    if stake < MIN_STAKE_PERCENT:
        return None, 'share_below'
    sum_rub = parse_rub_sum(d.get('sum'))
    if not sum_rub or sum_rub <= 0:
        return None, 'sum_unparsed'
    return MultipleCandidate(
        deal_id=d.get('id') or '', title=d.get('title') or d.get('id') or '', target_id=target,
        year=yr, sum_rub=sum_rub, stake_percent=stake), None


def find_candidates(deals: dict[str, dict[str, Any]], confirmed_ids: set[str],
                     bank_ids: set[str], lot_ids: set[str] | None = None) -> list[MultipleCandidate]:
    """Кандидаты по ТЕКСТУ карточки — без обращения к БФО (та часть фильтра,
    которую можно применить без единого запроса к базе)."""
    out = []
    for deal_id, d in deals.items():
        cand, _ = admission(dict(d, id=deal_id), confirmed_ids, bank_ids, lot_ids)
        if cand:
            out.append(cand)
    return out


def exclusion_counts(deals: dict[str, dict[str, Any]], confirmed_ids: set[str],
                     bank_ids: set[str], lot_ids: set[str] | None = None) -> dict[str, int]:
    """Сколько сделок M&A с 2022 года не дошли до мультипликатора и почему —
    считается только по тем, у кого есть покупатель и продавец: остальное
    не сделки этого класса."""
    counts: dict[str, int] = {}
    for deal_id, d in deals.items():
        cand, reason = admission(dict(d, id=deal_id), confirmed_ids, bank_ids, lot_ids)
        if reason in ('type', 'parties', 'year'):
            continue
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return counts


@dataclass
class DealMultiple:
    deal_id: str
    title: str
    target_id: str
    target_name: str | None
    year: int
    sum_rub: float
    revenue_rub: float
    revenue_year: int
    multiple: float


def _sanity_checked_multiple(sum_rub: float, metric_rub: float | None,
                              metric_year: int | None, deal_year: int) -> float | None:
    """Общая граница для ЛЮБОГО мультипликатора «сумма сделки / показатель
    отчётности» — вынесена, чтобы пороги (MIN/MAX_MULTIPLE, MAX_YEAR_GAP)
    не жили в двух копиях для выручки и для операционной прибыли."""
    if metric_rub is None or metric_year is None or metric_rub <= 0:
        return None
    if not (MIN_YEAR_GAP <= deal_year - metric_year <= MAX_YEAR_GAP):
        return None
    multiple = sum_rub / metric_rub
    if not (MIN_MULTIPLE <= multiple <= MAX_MULTIPLE):
        return None
    return round(multiple, 2)


def multiple_for_candidate(cand: MultipleCandidate, revenue_rub: float | None,
                            revenue_year: int | None, target_name: str | None
                            ) -> DealMultiple | None:
    """Санитарная проверка одного кандидата с уже докачанной выручкой.

    Отдельная от `find_candidates` функция специально: текстовый фильтр не
    требует БД и тестируется без фикстур, а этот шаг — единственное место,
    трогающее реальное число выручки, и его легче всего проверить на
    придуманных значениях (см. test_deal_multiples.py)."""
    multiple = _sanity_checked_multiple(cand.sum_rub, revenue_rub, revenue_year, cand.year)
    if multiple is None:
        return None
    return DealMultiple(
        deal_id=cand.deal_id, title=cand.title, target_id=cand.target_id,
        target_name=target_name, year=cand.year, sum_rub=cand.sum_rub,
        revenue_rub=revenue_rub, revenue_year=revenue_year, multiple=multiple)


@dataclass
class OpProfitMultiple:
    """Второй мультипликатор — сумма сделки к прибыли от продаж
    (операционной прибыли), а не к выручке. Ближайший к EV/EBITDA
    показатель, который вообще есть в официальной отчётности: амортизация
    отдельной строкой в ней не раскрывается, настоящую EBITDA из неё не
    собрать (см. `methodology_operating_profit` в `compute_market_multiples`
    — то же честное объяснение уходит и на экран)."""
    deal_id: str
    title: str
    target_id: str
    target_name: str | None
    year: int
    sum_rub: float
    operating_profit_rub: float
    operating_profit_year: int
    multiple: float


def multiple_for_candidate_op(cand: MultipleCandidate, operating_profit_rub: float | None,
                               operating_profit_year: int | None, target_name: str | None
                               ) -> OpProfitMultiple | None:
    """То же самое, что `multiple_for_candidate`, только знаменатель —
    операционная прибыль, а не выручка. Операционный убыток (или его
    отсутствие в отчётности) означает, что мультипликатор просто не
    считается — это честная пустота, а не ноль."""
    multiple = _sanity_checked_multiple(cand.sum_rub, operating_profit_rub,
                                         operating_profit_year, cand.year)
    if multiple is None:
        return None
    return OpProfitMultiple(
        deal_id=cand.deal_id, title=cand.title, target_id=cand.target_id,
        target_name=target_name, year=cand.year, sum_rub=cand.sum_rub,
        operating_profit_rub=operating_profit_rub, operating_profit_year=operating_profit_year,
        multiple=multiple)


def industry_medians(rows: list[DealMultiple], industry_of: dict[str, str]
                      ) -> list[dict[str, Any]]:
    """Медиана по отраслям с >=MIN_INDUSTRY_SAMPLE наблюдениями — меньше
    трёх сделок медианой не подписываем (см. CLAUDE.md, «У числа на экране
    два свойства: величина и множество» — знаменатель обязан быть честным,
    а на выборке в одну-две сделки медиана выглядит точнее, чем есть)."""
    by_ind: dict[str, list[float]] = {}
    for r in rows:
        ind = industry_of.get(r.target_id) or 'Не определена'
        by_ind.setdefault(ind, []).append(r.multiple)
    out = []
    for ind, mults in by_ind.items():
        if len(mults) < MIN_INDUSTRY_SAMPLE:
            continue
        s = sorted(mults)
        n = len(s)
        median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        out.append({'industry': ind, 'count': n, 'median': round(median, 2),
                     'min': round(s[0], 2), 'max': round(s[-1], 2)})
    out.sort(key=lambda x: -x['count'])
    return out


def overall_median(rows: list[DealMultiple]) -> float | None:
    if not rows:
        return None
    s = sorted(r.multiple for r in rows)
    n = len(s)
    return round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 2)


def compute_market_multiples(db, deals: dict[str, dict[str, Any]],
                              registry: dict[str, dict], get_company_profile,
                              lot_ids: set[str] | None = None) -> dict[str, Any]:
    """Полный расчёт для эндпоинта /api/analytics/multiples — единственная
    функция здесь, которая трогает БД; всё остальное в модуле — чистые
    функции над словарями, проверяемые без фикстур базы."""
    from db.models import FinancialReport, LegalEntity, LegalEntityMatchStatus

    confirmed_ids = {cid for cid, row in registry.items() if row['decision'] == 'confirmed'}
    bank_ids = {cid for cid, row in registry.items() if row['decision'] == 'bank'}
    # Лоты приходят готовым множеством от вызывающего кода: get_company_profile
    # перечитывает весь справочник на каждый вызов (0,1 с), и перебор тысячи
    # предметов сделок через него занимал две минуты на запрос (6 сентября 2026).
    lot_ids = set(lot_ids or ())
    candidates = find_candidates(deals, confirmed_ids, bank_ids, lot_ids)
    excluded = exclusion_counts(deals, confirmed_ids, bank_ids, lot_ids)

    rows: list[DealMultiple] = []
    op_rows: list[OpProfitMultiple] = []
    industry_of: dict[str, str] = {}
    # Отрасль — из самой сделки, а не из профиля компании: у профиля ключ
    # называется `industry` (а здесь читали `ind`), и все двадцать сделок
    # уезжали в «Не определена» одной строкой — партнёр увидел это на
    # экране 31 августа 2026. У сделки отрасль есть всегда.
    deal_industry = {did: (deal.get('ind') or '') for did, deal in deals.items()}
    for cand in candidates:
        entity = db.scalar(select(LegalEntity).where(
            LegalEntity.company_id == cand.target_id,
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
        ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id))
        if not entity:
            continue
        report = db.scalar(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id,
            FinancialReport.year < cand.year,
            FinancialReport.revenue_rub.is_not(None),
        ).order_by(FinancialReport.year.desc()))
        if not report:
            continue
        dm = multiple_for_candidate(cand, float(report.revenue_rub), report.year, entity.legal_name)
        if dm:
            rows.append(dm)
        # Та же строка отчётности уже несёт операционную прибыль — второй
        # запрос к БД не нужен, только своя санитарная проверка (операционный
        # убыток и `None` отсеиваются внутри `multiple_for_candidate_op`).
        op_profit = report.operating_profit_rub
        op_dm = multiple_for_candidate_op(
            cand, float(op_profit) if op_profit is not None else None,
            report.year, entity.legal_name)
        if op_dm:
            op_rows.append(op_dm)
        if dm or op_dm:
            ind = deal_industry.get(cand.deal_id) or ''
            if not ind or ind == 'Не определена':
                profile = get_company_profile(cand.target_id)
                ind = (profile or {}).get('industry') or ind
            if ind:
                industry_of[cand.target_id] = ind

    rows.sort(key=lambda r: r.year, reverse=True)
    op_rows.sort(key=lambda r: r.year, reverse=True)
    return {
        'candidates_total': len(candidates),
        'clean_total': len(rows),
        'median': overall_median(rows),
        'industries': industry_medians(rows, industry_of),
        # Почему сделки не попали в мультипликатор — по причинам, с подписями
        # для экрана; «доля не установлена» здесь самая частая, и это
        # очередь на чтение, а не дефект расчёта.
        'excluded': [{'reason': k, 'label': EXCLUSION_LABELS[k], 'count': v}
                     for k, v in sorted(excluded.items(), key=lambda kv: -kv[1])],
        'no_report': len(candidates) - len(rows),
        'deals': [{
            'id': r.deal_id, 'title': r.title, 'year': r.year,
            'target_id': r.target_id, 'target_name': r.target_name,
            'sum_rub': r.sum_rub, 'revenue_rub': r.revenue_rub,
            'revenue_year': r.revenue_year, 'multiple': r.multiple,
        } for r in rows],
        'methodology': (
            'Мультипликатор показывает, во сколько годовых выручек обошлась '
            'компания покупателю. Считаем его только там, где сравнение честное: '
            'в карточке прямо сказано, что компания куплена целиком (доля 95% и '
            'выше; если доля не названа, сделка в расчёт не идёт), цену назвали '
            'сами стороны и в рублях (оценки, диапазоны, стартовые цены торгов и '
            '«более…» не в счёт), а выручка взята из отчётности '
            'за последний полный год до сделки (или за позапрошлый, если прошлогодний ещё не сдан). Значения вне разумных границ не '
            'показываем: почти всегда это значит, что отчётность нашлась не у того '
            'юрлица, а не что сделка настолько необычная. В цену сделки иногда '
            'входит и принятый на себя долг компании — тогда мультипликатор '
            'получается чуть выше, чем по цене одних только акций.'
        ),
        'operating_profit': {
            'clean_total': len(op_rows),
            'median': overall_median(op_rows),
            'industries': industry_medians(op_rows, industry_of),
            'deals': [{
                'id': r.deal_id, 'title': r.title, 'year': r.year,
                'target_id': r.target_id, 'target_name': r.target_name,
                'sum_rub': r.sum_rub, 'operating_profit_rub': r.operating_profit_rub,
                'operating_profit_year': r.operating_profit_year, 'multiple': r.multiple,
            } for r in op_rows],
            'methodology': (
                'В M&A обычно сравнивают цену сделки с EBITDA (прибылью до вычета '
                'процентов, налогов и амортизации) — это точнее выручки, потому что '
                'учитывает, сколько компания реально зарабатывает. Но официальная '
                'отчётность, на которую мы опираемся, амортизацию отдельной строкой '
                'не показывает, и собрать из неё настоящую EBITDA нельзя. Прибыль от '
                'продаж (операционная прибыль) — ближайшая доступная замена: та же '
                'прибыль, но с учётом амортизации, поэтому мультипликатор обычно '
                'получается немного выше настоящего EV/EBITDA. Условия отбора сделок '
                'и границы — те же, что и у мультипликатора по выручке.'
            ),
        },
    }
