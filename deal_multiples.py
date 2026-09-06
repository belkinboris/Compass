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
  * доля, ПРИОБРЕТАЕМАЯ В ЭТОЙ СДЕЛКЕ, установлена и не меньше 95%. Первый
    источник — явное поле карточки `stake_acquired` (число процентов,
    пишется через review.py с цитатой). Второй — текст карточки, но только
    процент, стоящий рядом со словом о приобретении («приобрёл 49%»,
    «продало 100% акций», «выкупив оставшиеся 75%»); процент рядом со
    словом о результате или истории («консолидировала 100%», «довела долю
    до 51%», «ранее владел 30%», «сохранил 51%») — не покупка. Если таких
    процентов в карточке НЕСКОЛЬКО РАЗНЫХ (несколько этапов, доли
    участников консорциума) — доля не установлена. Слова о покупке целиком
    («купил целиком», «стал единственным владельцем») — 100%.
    Неизвестная доля — не допуск: до 6 сентября 2026 карточка без процента
    считалась «потенциально 100%», днём позже её заменил «наименьший из
    названных процентов» — и рецензент верно заметил, что наименьший
    процент не обязан относиться к купленному пакету (прежняя доля
    покупателя, доля одного участника консорциума, первый этап). Неизвестное
    остаётся в базе и в очереди на чтение, но не в статистике.
  * сумма ДОПУЩЕНА к расчёту. Два разных признака: КАК раскрыта сумма
    (`sum_basis()`: цена, названная сторонами; диапазон; оценка; нижняя
    граница; стартовая цена торгов; валюта; объём привлечения; не цена) и
    ДОПУСКАЕТСЯ ЛИ она к конкретному расчёту (`ADMITTED_SUM_BASES`). Сегодня
    допущена только цена, названная сторонами. Диапазон — не «оценка»:
    стороны тоже раскрывают пределы цены (условное вознаграждение,
    корректировки) — но пока не решено, какое число из диапазона брать,
    он к медиане не допускается; данные при этом не переписываются, у
    карточки `sum` остаётся как есть. Явное поле `sum_basis` сильнее
    разбора — для чисел, у которых по тексту не видно, что это не цена
    (иск о компенсации, оценка всей компании при IPO).
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
SUM_BASES = ('disclosed', 'reported', 'estimate', 'range', 'lower_bound', 'auction_start',
             'foreign_currency', 'not_a_price', 'valuation', 'raise', 'undisclosed', 'unparsed')
# Смысл ДАТЫ карточки — тоже закрытый список и тоже явное поле (`date_basis`):
# дата закрытия, подписания, объявления, ПУБЛИКАЦИИ сообщения, записи в
# реестре. Дата публикации — не дата перехода долей (урок «Дата новости — не
# дата сделки»); поле говорит читателю и ассистенту, чем является число.
DATE_BASES = ('closing', 'signing', 'announcement', 'publication', 'registry')
DATE_BASIS_LABELS = {
    'closing': 'дата закрытия сделки',
    'signing': 'дата подписания',
    'announcement': 'дата объявления',
    'publication': 'дата сообщения источника',
    'registry': 'дата записи в реестре',
}

# К КАКИМ расчётам сумма допускается — отдельно от того, КАК она раскрыта.
# Расширять список (например, диапазоном) можно только вместе с решением,
# какое число из него идёт в расчёт, — это методология, не разбор текста.
ADMITTED_SUM_BASES = ('disclosed',)
SUM_BASIS_LABELS = {
    'disclosed': 'цена, названная сторонами',
    # Число есть, но назвали его анонимные «источники» издания, а не стороны,
    # отчётность или реестр (третий разбор рецензента: Ozon/«О23» — один
    # читатель видел «по данным источников РБК», другой — пересказ как факт).
    # В расчёты не допускается: требование «цену назвали стороны» не выполнено.
    'reported': 'сумма по данным источников СМИ, сторонами не подтверждена',
    'estimate': 'оценка (эксперты, СМИ, «около»)',
    'range': 'диапазон (пределы цены или оценка — способ расчёта не определён)',
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
    (клиент с 6 сентября 2026 копии не держит: читает facts.price.meaning).

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
    # «2,5 тыс. ₽ (номинальная цена по решению суда)» — число есть, цены нет;
    # нашлось третьим уровнем проверки (facts.number_checks: порядок величины).
    if re.search(r'номинальн|заявлено как объём инвестиц|не цена', text, re.I):
        return 'not_a_price'
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


# Контекст процента: рядом со словом о ПРИОБРЕТЕНИИ — купленная доля; рядом
# со словом о РЕЗУЛЬТАТЕ (консолидировала, довела до, сохранил, принадлежит)
# или об ИСТОРИИ (ранее, тогда, в 2020 году) — нет. Слово ищется и ДО
# процента («приобрёл 25%»), и ПОСЛЕ него, до конца предложения («100% акций
# АО «КИВИ» переданы Fusion Factor»): в русском глагол часто стоит за
# дополнением.
_ACQ_WORDS = re.compile(
    r'приобр|купи|купл|покуп|выкуп|прода[её]?[тжлн]|продаж|получи|перешл|переход|переда|переоформ|уступ|взыска'
    r'|выстав|на\s+торг|на\s+аукцион|лот\s+включа|в\s+периметр|предмет(?:ом)?\s+сделки|речь\s+ид[её]т\s+о'
    r'|стал[аио]?\s+(?:владельц|собственник)|оставшиес|оставшихся', re.I)
# Только глагольные формы: причастия «принадлежавших X», «владевшего 60%»
# определяют, ЧЬИ акции куплены, а не кто владеет ими теперь.
_RESULT_WORDS = re.compile(
    r'консолидир|довел|довед|увеличи|нарасти|сохрани|принадлеж(?!ащ|авш)|владе(?!льц|вш)|контролир|составля|состави'
    r'|наход|остаётся|остается|остал[аи]сь|(?:^|[^а-яё])до\s*$', re.I)
_HISTORY_WORDS = re.compile(r'ранее|прежде|до этого|тогда|в\s+20\d\d\s+год|c\s+20\d\d|с\s+20\d\d', re.I)
# Слово, возвращающее из истории к этой сделке: «ранее владел 30%, теперь
# приобрёл 70%» — 70 про сделку, хотя стоит после «ранее».
_PRESENT_WORDS = re.compile(r'теперь|сейчас|на этот раз|в рамках (?:этой |данной |новой |нынешней )?сделки'
                            r'|по (?:итогам|результатам) сделки|в результате сделки', re.I)
# Скобки — пояснение, а не часть фразы: «(ранее холдинг IDF Eurasia) купила
# 100%», «(которая полностью вышла из капитала)». Скобка, в которой стоит
# только процент («Doğan Holding (50%)»), остаётся — это число о доле.
_PARENS = re.compile(r'\((?!\s*\d{1,3}(?:[.,]\d+)?\s*%[^()]{0,25}\))[^()]*\)')
# Окно после процента — до конца ПРОСТОГО предложения: запятая, двоеточие и
# тире открывают новую часть («довела долю до 51%, приобретя 36%» — глагол
# за запятой относится к 36, а не к 51).
_SENTENCE_END = re.compile(r'[.;,:]\s|[.;,:]$|\s[—–]\s')


def _window_verdict(before: str, after: str) -> bool:
    """Считать ли процент купленной долей по словам до и после него."""
    acq = [x.end() for x in _ACQ_WORDS.finditer(before)]
    res = [x.end() for x in _RESULT_WORDS.finditer(before)]
    hist = [x.end() for x in _HISTORY_WORDS.finditer(before)]
    present = [x.end() for x in _PRESENT_WORDS.finditer(before)]
    if hist and not (present and max(present) > max(hist)):
        return False  # история этой доли: «ранее владел 30%», «в 2021 году купил 20%»
    if acq:
        # результат названнее покупки: «выкупив …, довела долю до 51%»
        return not (res and max(res) > max(acq))
    # глагол после дополнения: «100% акций переданы X», «100% долей перешли к Y»
    acq_after = _ACQ_WORDS.search(after)
    stop_after = min([m.start() for m in (_RESULT_WORDS.search(after), _HISTORY_WORDS.search(after)) if m],
                     default=None)
    if acq_after and (stop_after is None or acq_after.start() < stop_after):
        return True
    return False


def _split_windows(cleaned: str, pos: int) -> tuple[str, str]:
    before = cleaned[max(0, pos - 70):pos]
    # окно — от последней сильной границы (точка, точка с запятой), чтобы
    # «продал 100% акций. Ранее владел 30%» не смешивались
    cut = max(before.rfind('. '), before.rfind('; '))
    if cut >= 0:
        before = before[cut + 2:]
    after = cleaned[pos:pos + 90]
    m = _SENTENCE_END.search(after)
    if m:
        after = after[:m.start()]
    return before, after


def _percents(text: str | None):
    if not text:
        return
    cleaned = _NOT_A_STAKE.sub(' ', _PARENS.sub(' ', str(text)))
    for m in _STAKE_PCT.finditer(cleaned):
        value = float(m.group(1).replace(',', '.'))
        if 1 <= value <= 100:
            yield value, m, cleaned


def acquired_percents(text: str | None) -> list[float]:
    """Проценты, которые текст называет КУПЛЕННОЙ долей, по порядку."""
    out = []
    for value, m, cleaned in _percents(text):
        before, after = _split_windows(cleaned, m.start())
        if _window_verdict(before, after[m.end() - m.start():]):
            out.append(value)
    return out


# Поле «Предмет / доля» (`eco.share`) и `asset` называют ПРЕДМЕТ сделки: процент
# в начале такого поля — купленная доля по смыслу самого поля, глагол ему не
# нужен («100% долей ООО «Флоктори»», «Предмет — 100% акций АО «Ильинская
# больница»»). Замер 6 сентября 2026: без этого правила 195 покупок с
# установленной долей теряли её, почти все — ровно такой формы. Не считается,
# если сразу за процентом идёт слово о текущем владении («99,9% находятся на
# балансе ООО «Агроинвест»») — это структура собственности, а не предмет.
_SUBJECT_HEAD = re.compile(
    r'^\s*(?:предмет(?:\s+сделки)?\s*[—–:-]\s*|лот\s*[—–:-]\s*)?(\d{1,3}(?:[.,]\d+)?)\s*%', re.I)


def subject_percents(text: str | None) -> list[float]:
    """Проценты купленной доли в поле, описывающем предмет сделки: тот, что
    стоит в начале поля (если за ним нет слова о владении), плюс те, что
    названы в контексте покупки."""
    out = acquired_percents(text)
    if not text:
        return out
    cleaned = _PARENS.sub(' ', str(text))
    m = _SUBJECT_HEAD.search(cleaned)
    if m:
        value = float(m.group(1).replace(',', '.'))
        _, after = _split_windows(cleaned, m.start(1))
        after = after[m.end() - m.start(1):]
        blocked = _RESULT_WORDS.search(after) or _HISTORY_WORDS.search(after)
        if 1 <= value <= 100 and not blocked and not any(abs(value - x) < 0.05 for x in out):
            out.insert(0, value)
    return out


def stake_percent(deal: dict[str, Any]) -> float | None:
    """Единственная доля, которую текст называет КУПЛЕННОЙ в этой сделке.

    Читаются `eco.share`, `asset` и заголовок: у 24 из 83 кандидатов (замер
    5 сентября 2026) доля стояла ТОЛЬКО в заголовке, и сумму за пакет делили
    на выручку всей компании. Процент засчитывается, если ближе всего к нему
    стоит слово о приобретении, а не о результате («довела долю до 51%,
    приобретя 36%» → 36) и не об истории («ранее владел 30%, теперь приобрёл
    70%» → 70). Если таких процентов несколько и они разные (этапы, участники
    консорциума) — доля не установлена: None.

    История правила. До 6 сентября 2026 брался max по первому полю с
    процентами — Guess (30%) и БФТ/«Полиматика» (49%) проходили порог 95%
    (аудит, раунд 2). Затем — НАИМЕНЬШИЙ из названных: ошибка в безопасную
    сторону, но рецензент прав, что она ошибка: у консолидации «консолидировала
    100%, выкупив 30%» наименьший верен, у «ранее владел 30%, купил 70%» —
    нет, а у «первый этап — 68%» наименьший вообще про этап, а не про сделку.
    Поэтому теперь — контекст покупки, а не арифметика по всем процентам."""
    distinct: list[float] = []
    def add(value: float) -> None:
        if not any(abs(value - x) < 0.05 for x in distinct):
            distinct.append(value)
    for value in acquired_percents(deal.get('title')):
        add(value)
    for text in (deal.get('eco', {}).get('share'), deal.get('asset')):
        for value in subject_percents(text):
            add(value)
    if len(distinct) == 1:
        return distinct[0]
    return None  # ни одного процента о покупке — или несколько разных (этапы, участники, история)


# Покупка целиком, названная словами, а не процентом: «купил компанию
# целиком», «выкупил полностью», «стал единственным владельцем». Голое
# «полностью» не годится: «АФК «Система» полностью вышла из капитала» — про
# продавца («Элемент», 6 сентября 2026).
_FULL_WORDS = re.compile(
    r'(?:купи|купл|выкуп|приобр)[а-яё]*\s+(?:[а-яё«»"\w-]+\s+){0,2}?(?:целиком|полностью)'
    r'|(?:целиком|полностью)\s+(?:выкуп|куп|приобр)'
    r'|(?<!прежде )(?<!ранее )(?<!был )(?<!была )(?<!было )(?<!были )единственн[а-яё]*\s+(?:владельц|собственник|акционер|участник)'
    r'|весь\s+бизнес|вс[ея]\s+(?:акци|дол)|всех\s+(?:акци|дол)',
    re.I)


def stake_established(deal: dict[str, Any]) -> float | None:
    """Доля, приобретаемая в этой сделке: явное поле `stake_acquired`, иначе
    единственный процент в контексте покупки (`stake_percent`), иначе — когда
    процентов о покупке нет вовсе — слова о покупке целиком (100). None — не
    установлена, и это не допуск (правило владельца, 6 сентября 2026:
    неизвестность не превращается в предположение «куплено 100%»)."""
    explicit = deal.get('stake_acquired')
    if isinstance(explicit, (int, float)) and 0 < float(explicit) <= 100:
        return float(explicit)
    pct = stake_percent(deal)
    if pct is not None:
        return pct
    texts = (deal.get('title'), deal.get('eco', {}).get('share'), deal.get('asset'))
    if any(acquired_percents(t) for t in texts) or any(subject_percents(t) for t in texts[1:]):
        return None  # проценты о покупке есть, но разные — слова «целиком» их не разрешают
    for text in texts:
        if text and _FULL_WORDS.search(str(text)):
            return 100.0
    return None


def year_of(deal: dict[str, Any]) -> int | None:
    ds = str(deal.get('date') or '')
    return int(ds[:4]) if ds[:4].isdigit() else None


def multiple_year(deal: dict[str, Any]) -> tuple[int | None, str]:
    """Год сделки для мультипликатора и его основание. Подтверждённая двумя
    чтениями дата закрытия (или записи в реестре) сильнее даты карточки:
    у «ВымпелКома» карточка датирована подписанием 24.11.2022, закрытие —
    9.10.2023, и делить цену на выручку 2021 года было бы неверно (третий
    разбор рецензента). Основание возвращается наружу: от года зависит
    знаменатель, и API обязан сказать, откуда год."""
    f = (deal.get('facts') or {}).get('date') or {}
    if f.get('basis') == 'verified' and f.get('meaning') in ('closing', 'registry') and str(f.get('value') or '')[:4].isdigit():
        return int(str(f['value'])[:4]), 'подтверждённая дата закрытия' if f['meaning'] == 'closing' else 'подтверждённая дата записи в реестре'
    return year_of(deal), 'дата карточки'


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
    if sum_basis(d) not in ADMITTED_SUM_BASES:
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

    import facts as facts_layer

    confirmed_ids = {cid for cid, row in registry.items() if row['decision'] == 'confirmed'}
    bank_ids = {cid for cid, row in registry.items() if row['decision'] == 'bank'}
    # Лоты приходят готовым множеством от вызывающего кода: get_company_profile
    # перечитывает весь справочник на каждый вызов (0,1 с), и перебор тысячи
    # предметов сделок через него занимал две минуты на запрос (6 сентября 2026).
    lot_ids = set(lot_ids or ())
    # Кандидаты по ТЕКСТУ (правила — предложение): сколько сделок проходят
    # правила и ждут чтения. В расчёт идут только сделки, у которых все
    # текстовые факты ПОДТВЕРЖДЕНЫ двумя чтениями (facts.admitted.multiple_text).
    text_candidates = find_candidates(deals, confirmed_ids, bank_ids, lot_ids)
    candidates = []
    facts_reasons: dict[str, int] = {}
    verified_meta: dict[str, dict[str, Any]] = {}
    for deal_id, d in deals.items():
        f = d.get('facts') or {}
        ok, reason = facts_layer.admitted(dict(d, id=deal_id), 'multiple_text') if f else (False, 'no_facts')
        if ok:
            price, stake = f['price'], f['stake']
            year, year_basis = multiple_year(d)
            candidates.append(MultipleCandidate(
                deal_id=deal_id, title=d.get('title') or deal_id, target_id=target_of(d) or '',
                year=year or 0, sum_rub=float(price['value_rub']), stake_percent=stake.get('value')))
            scope = price.get('scope')
            numerator = ('цена за 100% акций' if scope == 'equity'
                         else f"цена за пакет {stake.get('value')}%" if scope == 'package'
                         else 'цена с учётом долга (EV)')
            verified_meta[deal_id] = {
                'stake': stake.get('value'), 'price_scope': scope, 'year_basis': year_basis,
                'formula': f'{numerator} ÷ показатель купленной компании за последний полный год до сделки',
                'verified_by': price.get('verified_by'), 'price_quote': price.get('quote'),
                'price_source': price.get('source'), 'checks': facts_layer.number_checks(d),
                'perimeter_report': (f.get('target') or {}).get('perimeter_report'),
            }
        elif reason not in ('not_control_change', 'before_site_year', 'no_facts'):
            facts_reasons[reason] = facts_reasons.get(reason, 0) + 1
    excluded = facts_reasons

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
        # Периметр подтверждался читателями ПО КОНКРЕТНОМУ отчёту (ИНН, год,
        # выручка); если сейчас в знаменателе другой отчёт — восстановленный,
        # другого года — это уже не проверенная сделка: карточка не менялась,
        # а знаменатель изменился (третий разбор рецензента).
        seen = verified_meta[cand.deal_id].get('perimeter_report') or {}
        if seen and (str(seen.get('inn')) != str(entity.inn) or int(seen.get('year') or 0) != int(report.year)
                     or abs(float(seen.get('revenue_rub') or 0) - float(report.revenue_rub)) > 0.01 * float(report.revenue_rub)):
            verified_meta[cand.deal_id]['checks'].append('report_changed')
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
    verified_ids = {c.deal_id for c in candidates}
    return {
        # сколько сделок проходят правила по тексту (предложение правил) …
        'candidates_total': len(text_candidates),
        # … и сколько из них ждут подтверждения чтением
        'awaiting_reading': len([c for c in text_candidates if c.deal_id not in verified_ids]),
        'verified_total': len(candidates),
        'clean_total': len(rows),
        'median': overall_median(rows),
        'industries': industry_medians(rows, industry_of),
        # Почему сделки не попали в мультипликатор — по причинам из слоя
        # фактов (facts.REASON_LABELS), с подписями для экрана.
        'excluded': [{'reason': k, 'label': facts_layer.REASON_LABELS.get(k, k), 'count': v}
                     for k, v in sorted(excluded.items(), key=lambda kv: -kv[1])],
        'no_report': len(candidates) - len(rows),
        'deals': [dict({
            'id': r.deal_id, 'title': r.title, 'year': r.year,
            'target_id': r.target_id, 'target_name': r.target_name,
            'sum_rub': r.sum_rub, 'revenue_rub': r.revenue_rub,
            'revenue_year': r.revenue_year, 'multiple': r.multiple,
        }, **verified_meta.get(r.deal_id, {})) for r in rows],
        'methodology': (
            'Что здесь считается: цена сделки ÷ выручка купленной компании за последний '
            'полный год до сделки (или за позапрошлый, если прошлогодний отчёт ещё не сдан). '
            'Цена — за 100% акций, если так подтверждено чтением; за пакет — тогда это '
            'указано у сделки; долг компании в цену не входит, если у сделки не сказано '
            '«с учётом долга». Показываются только сделки, у которых доля (95% и выше), '
            'цена и юрлицо подтверждены двумя независимыми чтениями источников с '
            'цитатами, а отчётность относится именно к купленному юрлицу. Год сделки — '
            'подтверждённая дата закрытия, если она прочитана, иначе дата карточки; '
            'основание года указано у каждой сделки. Значения вне границ 0,1–15 не '
            'показываем: почти всегда это значит, что отчётность нашлась не у того '
            'юрлица. Это не EV/EBITDA и не его замена — другой числитель и другой '
            'знаменатель.'
        ),
        'operating_profit': {
            'clean_total': len(op_rows),
            'median': overall_median(op_rows),
            'industries': industry_medians(op_rows, industry_of),
            'deals': [dict({
                'id': r.deal_id, 'title': r.title, 'year': r.year,
                'target_id': r.target_id, 'target_name': r.target_name,
                'sum_rub': r.sum_rub, 'operating_profit_rub': r.operating_profit_rub,
                'operating_profit_year': r.operating_profit_year, 'multiple': r.multiple,
            }, **verified_meta.get(r.deal_id, {})) for r in op_rows],
            'methodology': (
                'Что здесь считается: цена сделки ÷ прибыль от продаж купленной компании '
                '(строка 2200 отчёта о финансовых результатах) за последний полный год до '
                'сделки. Цена — за 100% акций или за пакет, как подтверждено чтением; долг '
                'в цену не входит, если не сказано «с учётом долга». Это не EV/EBITDA: '
                'прибыль от продаж считается после амортизации, а цена акций — без долга, '
                'поэтому сравнивать с рыночными EV/EBITDA нельзя. Показываются только '
                'сделки с подтверждёнными двумя чтениями долей, ценой и юрлицом; '
                'операционный убыток или его отсутствие — честная пустота, не ноль.'
            ),
        },
    }
