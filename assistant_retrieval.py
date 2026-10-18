# -*- coding: utf-8 -*-
"""Ассистент: поиск по базе и точные ответы — на сервере, а не в браузере.

ПОЧЕМУ ЭТОТ МОДУЛЬ ПОЯВИЛСЯ (1 сентября 2026). Партнёр владельца задал
ассистенту четыре вопроса и получил четыре неверных ответа:
  * «Много сделок у Orion?» — «в базе нет сделок с Orion» (в базе 15);
  * «Кто консультирует в сфере добычи угля?» — «сделок с углём нет» (9);
  * «Better Chance — какие сделки сопровождали?» — «в базе записей нет» (11);
  * «Какая самая крупная сделка?» — таймаут и ссылки на статьи «крупная
    сделка для ООО: нужно ли одобрение» из интернета.
Ни один из ответов не был враньём модели: ей передавали подборку сделок,
собранную В БРАУЗЕРЕ по словам ЗАГОЛОВКА (`relevantDeals` в index.html), а
консультанты, отрасли, имена компаний-сторон и темы в тот индекс не входили.
Не найдя слова «Orion» ни в одном заголовке, браузер отдавал сорок самых
свежих сделок — и модель честно сообщала, что в них Orion нет.

ЧТО ДЕЛАЕТ МОДУЛЬ. Держит индекс по всей видимой базе (заголовок, стороны,
предмет, отрасли, темы, консультанты, ключевые факты) и отвечает на вопрос
в два слоя:
  1. `route()` понимает, О ЧЁМ вопрос (фирма-консультант, компания, отрасль,
     «самая крупная», «сколько», тема вроде ухода иностранцев) и считает
     ТОЧНЫЙ ответ прямо по базе — числа, списки, ссылки. Это ответ, который
     верен без всякой модели и отдаётся пользователю, если модель молчит.
  2. Подборка сделок (не больше дюжины, компактно) плюс эта сводка уходят
     модели, чья работа — живой русский текст, а не арифметика по базе.
Правило простое: база отвечает на вопросы про базу, модель пишет прозу.

Зависимостей сверх стандартной библиотеки нет намеренно: модуль живёт в
веб-процессе на Timeweb, и лишний пакет — лишняя точка отказа при деплое.
Морфология — та же «общее начало ≥3 знаков и ≥60% длины короткого слова»,
что уже проверена в review.py и в поиске по ленте; копия здесь, а не импорт,
потому что review.py при импорте загружает все таблицы правок.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from deal_multiples import is_estimate, parse_rub_sum
from facts import PURCHASE_TYPES

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "static" / "data" / "deals_promoted.json"
INDEX_HTML = ROOT / "static" / "index.html"
SITE_MIN_YEAR = 2022
MAX_DEALS_FOR_MODEL = 12
MAX_LISTED = 6

# --------------------------------------------------------------------------
# Слова и формы
# --------------------------------------------------------------------------

STOP = set((
    "кто что какие какая какой каких какую где когда сколько много мало есть был была были быть "
    "про по об о в на с у из для и а но или же ли не нет да все всё это эта этот эти там тут "
    "расскажи покажи назови найди дай список какие-нибудь какой-нибудь какая-нибудь "
    "сделка сделки сделку сделок сделке сделкой компания компании компаний компанию фирма фирмы фирму "
    "год года году годы лет рынок рынка рынке российский российского российском россии россия "
    "ооо пао ао оао зао гк ук нко ип ltd llc inc plc group the and for of "
    "известно информация данные база базе базы компас компаса "
    # Вопросные и родовые слова: сами по себе ничего не ищут, а по общему
    # началу цепляют чужие имена («так» → «Такси», «столько» → «Столичных»,
    # «почему» → «Почта»). Со страницы компании «Почему так много покупает?»
    # без них становится вопросом о самой компании (2 сентября 2026).
    "почему зачем отчего как так тоже уже еще ещё очень столько такой такая такие "
    # «Какие сделки вели / совершили / провели?» — глагол вопроса ничего не
    # ищет, а по общему началу цепляет чужие имена: «вели» → «Великим» в
    # карточке «Русского молока» (3 октября 2026, вопрос со страницы Ситибанка).
    "вели вел вёл вела вело провели провел провёл провела совершили совершил совершила "
    "заключили заключил заключила участвовали участвовал участвовала делали делал делала "
    # Слова роли и просьбы уточнить — тоже не имена: «покупателя» цеплялось за
    # «Покупатель …» в сторонах чужой карточки, «детали» — за чужой заголовок.
    "покупатель покупателя покупателю покупателем покупатели продавец продавца продавцу продавцом продавцы "
    "уточни уточните уточнить детали деталь подробности подробнее расскажите объясни объясните "
    "последние последних последний последняя последнюю новые новых новая новый свежие недавние "
    # Слова вопроса о дате и этапе сделки — тоже не имена: «дата» по началу
    # в четыре знака проходила `_name_word_match` с «Датана» в заголовке
    # чужой карточки, и «А дата объявления?» после вопроса про Boxberry
    # отвечало про УльтимаТек (16 октября 2026). Раньше спасала случайность:
    # первой по очкам стояла карточка Rockwool со словом «объявила» в
    # прозе, а «датск» имени «дата» не называет; пересказ прозы это слово
    # убрал, и ничья по очкам отдала первое место «Датане».
    "дата даты дату датой датам датами датах число числа числу "
    "объявление объявления объявлению объявлении объявлено объявлена объявлен "
    "анонс анонса анонсе анонсировали анонсирована закрытие закрытия закрытии "
    # Глаголы сделки стоят в сотнях заголовков — как признак они ничего не
    # различают, а как шум подмешивают к точному попаданию чужие карточки
    # («Кто купил Ситибанк?» тянул за «купил» ещё четыре сделки).
    "купил купила купили купит купить покупает покупают покупка покупке покупку "
    "приобрел приобрела приобрели приобретает приобретение приобретения приобрёл приобрела "
    "продал продала продали продает продаёт продажа продаже продажу продать "
    "выкупил выкупила выкупит выкуп выкупа инвестировал инвестировала инвестирует инвестиции "
    "получил получила получит стал стала станет вошел вошла войдет вышел вышла закрыл закрыла "
    "сопровождал сопровождала сопровождали сопровождает консультировал консультировала "
    # Просьбы и глаголы вопроса (14 октября 2026): «Приведи пример сделки
    # MBO» узнавало по «пример» БЦ «Примиум», «встречались» тянуло случайные
    # карточки со словом «встреча».
    "приведи приведите пример примеры примера примеров покажите назовите перечисли перечислите "
    "встречались встречается встречаются бывают бывали прошли прошло прошел прошёл проходили"
).split())

# Родовые слова названий компаний: сами по себе не опознают компанию.
GENERIC_NAME_WORDS = set((
    "ооо ао пао зао оао нао гк ук зпиф группа группы групп компания компании компаний фирма холдинг корпорация фонд банк "
    "инвест инвестиции капитал capital partners group holding invest ltd llc inc plc the and of "
    "россия российский русский международный национальный первый новый"
).split())

# Родовые слова в названиях консультантов — именем фирмы не считаются.
ADVISOR_GENERIC = set((
    "партнер партнеры партнеров партнёры partners partner legal law lawyers юридическ юрист юристы "
    "консалтинг consulting консультант консультанты бюро адвокат адвокаты коллегия компания фирма "
    "групп группа group services сервис офис office капитал capital advisory advisors"
).split())

_SUFFIXES = sorted((
    "иями ями ами ого его ому ему ыми ими ах ях ам ям ов ев ей ой ый ий ая яя ое ее ую юю ие ые ых их ом ем "
    "а я о е и ы у ю ь й"
).split(), key=len, reverse=True)


def norm(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zа-я0-9]+", norm(text)) if t]


def stem(word: str) -> str:
    """Грубая основа: одно окончание из списка, остаток не короче четырёх
    знаков. Латиницу и короткие слова не трогаем — у «VK», «Orion», «Гош»
    окончаний нет, а резать их — значит терять имя."""
    if len(word) < 5 or not re.fullmatch(r"[а-я]+", word):
        return word
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


def same_word(a: str, b: str) -> bool:
    """Одно слово в разных падежах — та же граница, что в review.py."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 3:
        return False
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    short = min(len(a), len(b))
    return n >= 3 and n >= 0.6 * short


def name_match(a: str, b: str) -> bool:
    """Совпадение ИМЕНИ, а не обычного слова: `same_word` для имён слишком
    мягок — «иванов» ложился на «иван» (Иван Пешков) и на «иванян». Имя
    считается тем же, если основы равны или одна начинается с другой и
    общая часть не короче пяти знаков («ивановым» → «иванов»)."""
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 5 and long_.startswith(short)


def query_words(question: str) -> list[str]:
    """Значимые слова вопроса как есть, без обрезки окончаний — для сверки
    ИМЁН: основа «иванов» → «иван» ложится на «Иван Пешков», а само слово — нет."""
    out = []
    for t in tokens(question):
        if t in STOP or (len(t) < 2) or (len(t) < 3 and not re.fullmatch(r"[a-z0-9]+", t)):
            continue
        if t not in out:
            out.append(t)
    return out


def query_terms(question: str) -> list[str]:
    out = []
    for t in query_words(question):
        s = stem(t)
        if s not in out:
            out.append(s)
    return out


def year_in(text: str) -> int | None:
    m = re.search(r"\b(20[2-9]\d)\b", text or "")
    return int(m.group(1)) if m else None


Span = tuple  # (с какого года, по какой) — любой конец может быть None («с 2022 года»)

_NUM_WORDS = {"два": 2, "двух": 2, "три": 3, "трех": 3, "трёх": 3, "четыре": 4, "четырех": 4,
              "пять": 5, "пяти": 5, "2": 2, "3": 3, "4": 4, "5": 5}


def period_in(text: str, today_year: int | None = None) -> Span | None:
    """Период вопроса — диапазон лет, а не первый попавшийся год.

    «Какие компании купил Яндекс с 2022 года?» отвечало «у Яндекса нет
    сделок за 2022 год» (у него 20 сделок), «телеком за 2022–2024» — только
    2022-м, «IPO в 2024–2025» — только 2024-м (проверка на 100 вопросах,
    14 октября 2026). Понимаем: «2024–2025», «с 2022 по 2024», «2023 и 2024»,
    «с 2022 года», «после 2023», «до 2024», «в этом / прошлом году», «за
    последние два года»."""
    q = norm(text or "")
    if today_year is None:
        from datetime import date
        today_year = date.today().year
    years = [int(y) for y in re.findall(r"\b(20[2-9]\d|201\d)\b", q)]
    if len(set(years)) >= 2:
        return (min(years), max(years))
    if years:
        y = years[0]
        if re.search(rf"(?:\bс|\bсо|начиная\s+с|\bот|since)\s+{y}\b", q) or re.search(rf"\b{y}\s*(?:г\.?|года?)?\s*(?:и\s+(?:позже|далее|после)|по\s+(?:сей\s+день|сегодня|наст))", q):
            return (y, None)
        if re.search(rf"\bпосле\s+{y}\b", q):
            return (y + 1, None)
        if re.search(rf"\b(?:до|раньше|ранее)\s+{y}\b", q):
            return (None, y - 1)
        if re.search(rf"\bпо\s+{y}\b", q):
            return (None, y)
        return (y, y)
    if re.search(r"\b(?:в|за)\s+(?:этом|этот|текущем|текущий|нынешн\w*)\s+год", q) or "в этом году" in q:
        return (today_year, today_year)
    if re.search(r"\b(?:в|за)\s+(?:прошлом|прошлый|прошедшем|прошедший)\s+год", q):
        return (today_year - 1, today_year - 1)
    m = re.search(r"последни[ех]\s+(\w+)\s+(?:года|лет)", q)
    if m and m.group(1) in _NUM_WORDS:
        return (today_year - _NUM_WORDS[m.group(1)] + 1, None)
    if re.search(r"последни[йе]\s+год", q):
        return (today_year - 1, None)
    return None


def span_single(span: Span | None) -> int | None:
    """Один год — для старых мест, где период назывался одним числом."""
    return span[0] if span and span[0] is not None and span[0] == span[1] else None


def in_span(year: int, span: Span | None) -> bool:
    if not span:
        return True
    lo, hi = span
    return (lo is None or year >= lo) and (hi is None or year <= hi)


def period_text(span: Span | None) -> str:
    """« за 2025 год», « за 2022–2024 годы», « с 2022 года» — с ведущим пробелом."""
    if not span:
        return ""
    lo, hi = span
    if lo is not None and lo == hi:
        return f" за {lo} год"
    if lo is not None and hi is not None:
        return f" за {lo}–{hi} годы"
    if lo is not None:
        return f" с {lo} года"
    return f" по {hi} год включительно"


PLACEHOLDER = re.compile(
    r"^\s*(не\s+раскры[а-яё]*|публично\s+не\s+сообщал[а-яё]*|не\s+привлекал[а-яё]*|не\s+сообщал[а-яё]*|"
    r"нет\s+данных|—|-|n/?a|неизвестн[а-яё]*)?\s*\.?\s*$", re.I)


def has_fact(value: Any) -> bool:
    return bool(value) and not PLACEHOLDER.match(str(value))


# --------------------------------------------------------------------------
# Отрасли и темы: синонимы, по которым их узнаёт вопрос
# --------------------------------------------------------------------------

# Префиксы (без учёта регистра и ё). Короткие проверяются как целое слово —
# «ит» не должно узнаваться внутри «итог». ПОРЯДОК ВАЖЕН: узкие отрасли стоят
# раньше широких, и берётся первое совпадение — «добыча угля» должна давать
# «Уголь», а не «ГМК и добыча» (первая версия выбирала самый длинный префикс
# и отдавала общую отрасль). Ключи — точные подписи отраслей базы; те, что в
# базе не встретятся, отбрасываются при разборе вопроса.
INDUSTRY_HINTS: dict[str, list[str]] = {
    "Уголь": ["уголь", "угля", "углю", "углем", "угле", "угольн", "угледоб"],
    "Фармацевтика": ["фарм", "аптек", "лекарств"],
    "Страхование": ["страхов"],
    "Финтех": ["финтех", "fintech", "платежн", "эквайринг"],
    "Порты и инфраструктура": ["порт", "терминал", "инфраструктур"],
    "Производство тары": ["упаков", "тар"],
    "E-commerce": ["маркетплейс", "e-commerce", "ecommerce", "интернет-магазин"],
    "Телеком": ["телеком", "сотов", "мобильн", "оператор связи"],
    "Автопром": ["автопром", "автомобил", "автозавод", "дилер"],
    "Образование": ["образован", "школ", "университет", "edtech", "курс"],
    "Медиа": ["медиа", "издани", "телеканал", "кино", "музык"],
    "Гостиницы и туризм": ["гостиниц", "отел", "туризм", "турист", "курорт", "санатор"],
    "Развлечения": ["развлеч", "парк", "игров", "кинотеатр"],
    "Лесопром": ["лесопром", "лесн", "древес", "целлюлоз", "бумаж"],
    "ЖКХ и обращение с отходами": ["жкх", "отход", "мусор", "водоканал"],
    "Химия и удобрения": ["хими", "удобрен"],
    "Здравоохранение": ["клиник", "медицин", "здравоохран", "медцентр", "лаборатор"],
    "Рынок ценных бумаг": ["брокер", "ценных бумаг", "депозитар", "биржев"],
    "Управление активами": ["управляющ", "зпиф", "фонд", "управлени активами"],
    "Финансовые услуги": ["лизинг", "мфо", "микрофинанс", "финансов"],
    "Искусственный интеллект": ["нейросет", "искусственн", "ai-"],
    "Агро": ["агро", "сельхоз", "зерн", "ферм", "аграрн", "птицефабрик", "хозяйств"],
    "Пищепром и напитки": ["пищев", "пищепром", "напитк", "молочн", "мясн", "кондитер", "пивовар"],
    "Нефть и газ": ["нефт", "газ", "спг", "нефтегаз"],
    "Энергетика": ["энерг", "электро", "тэц", "генерац", "электростанц"],
    # Транспорт — раньше недвижимости: «сделки в логистике и складах» —
    # про логистику, а не про офисы (№40); «склад» без логистики остаётся
    # недвижимостью.
    "Транспорт и логистика": ["транспорт", "логист", "перевоз", "грузов", "авиа", "аэропорт", "аэродром"],
    "Строительство": ["строител", "застройщ", "подрядчик"],
    "Недвижимость": ["недвижим", "девелоп", "жк", "бизнес-центр", "офис", "склад", "трц", "земл", "участ", "здани"],
    "ГМК и добыча": ["золот", "метал", "руд", "добыч", "горн", "гмк", "месторожд", "никел"],
    "Машиностроение": ["машиностро", "завод", "станк", "оборудован", "приборостро"],
    "Ритейл": ["ритейл", "розниц", "магазин", "супермаркет", "торгов сет"],
    "Потребительские товары": ["потребител", "бренд", "одежд", "косметик", "ювелир", "обув"],
    "Банки": ["банк"],
    "ИТ и интернет": ["ит", "it", "айти", "интернет", "софт", "программ", "разработчик", "цифров", "онлайн", "платформ"],
    "Холдинги": ["холдинг"],
    "Профессиональные услуги": ["консалтинг", "аудит", "юридическ услуг"],
}

THEME_HINTS: dict[str, list[str]] = {
    "Уход иностранного владельца": ["иностран", "уход", "уш", "выход", "выш", "покин", "зарубеж", "нерезидент"],
    "Правкомиссия / указ президента": ["правкомисс", "правительствен", "указ", "президент"],
    "Национализация / иск Генпрокуратуры": ["национализ", "генпрокурат", "изъят", "в доход государства"],
    "Продажа с торгов": ["торг", "аукцион"],
    "Банкротство / долги": ["банкрот", "долг", "конкурсн"],
    "IPO / SPO": ["ipo", "spo", "размещен", "бирж"],
    "Венчур / раунд": ["венчур", "раунд", "стартап", "инвестор"],
    "Консолидация доли": ["консолидац", "довел", "увелич", "доведен"],
    "Создание СП": ["совместн", "сп"],
    "Искусственный интеллект": ["ии", "искусственн", "нейросет", "ai"],
}

# Слова, которые значат «ищу условие сделки», а не тему — ищем по тексту полей.
# Мультипликатор — число с «x» или названная пара «EV/EBITDA», «P/E»; само
# слово EBITDA («EBITDA выросла на 57%») мультипликатором не считается.
_MULT = (r"мультипликатор|ev\s*/\s*(?:ebitda|выручк|sales|s\b)|p\s*/\s*e\b|\d\s*[xх×](?![a-zа-яё])"
         r"|\d\s*[xх×]\s*(?:ebitda|выручк|прибыл)|\d\s+ebitda")

# Обратный выкуп — право продавца вернуть себе бизнес: «опцион на обратный
# выкуп» (Mercedes-Benz, Hyundai), «договор допускает обратный выкуп»
# (Michelin), «право выкупить активы обратно» (Faurecia), «вправе вернуть
# себе российский бизнес» («Автодом»). До второй проверки (№4) сюда входил
# любой опцион — 74 сделки, где четыре нужные тонули среди опционов на
# докупку доли.
_REVERSE = (r"обратн[а-яё]*\s+(?:выкуп|продаж|покупк)|выкуп[а-яё]*\s+(?:\S+\s+){0,3}обратно"
            r"|вернуть\s+(?:себе\s+)?(?:\S+\s+){0,2}(?:бизнес|актив|завод|компани|дол)|buy-?back\s+option|право\s+на\s+возврат")

TERM_HINTS: dict[str, str] = {
    "опцион": r"опцион",
    "обратн": _REVERSE,
    "earn-out": r"earn-?out|отложенн[а-яё]*\s+платеж|условн[а-яё]*\s+вознагражд",
    "earnout": r"earn-?out|отложенн[а-яё]*\s+платеж|условн[а-яё]*\s+вознагражд",
    "отложенн": r"earn-?out|отложенн[а-яё]*\s+платеж|условн[а-яё]*\s+вознагражд|рассрочк",
    "рассрочк": r"рассрочк|отложенн[а-яё]*\s+платеж",
    "эскроу": r"эскроу|escrow",
    "заверен": r"заверен",
    "неконкурен": r"неконкурен",
    # Мультипликаторы и оценка: «При каких мультипликаторах прошло IPO
    # B2B-РТС?» и «мультипликаторы в ИТ» (№14, 30, 34).
    "мультипликатор": _MULT,
    "ebitda": _MULT,
    "p/e": r"p\s*/\s*e\b",
    # Условия продажи уходящих иностранцев: дисконт и «добровольный взнос»
    # в бюджет по требованиям правкомиссии (№12).
    "дисконт": r"дисконт",
    "взнос": (r"взнос[а-яё]*\s+в\s+(?:федеральн[а-яё]*\s+)?бюджет|добровольн[а-яё]*\s+(?:взнос|отчислен|перечислен)"
              r"|перечисл[а-яё]*\s+(?:\S+\s+){0,4}в\s+бюджет|\d+\s*%[^.]{0,30}в\s+бюджет"),
    "mbo": r"\bmbo\b|выкуп[а-яё]*[^.]{0,40}менеджмент|менеджмент[а-яё]*[^.]{0,25}выкуп|management\s+buy",
    "менеджментом": r"\bmbo\b|выкуп[а-яё]*[^.]{0,40}менеджмент|менеджмент[а-яё]*[^.]{0,25}выкуп|management\s+buy",
    "lock-up": r"lock-?up|локап",
    "локап": r"lock-?up|локап",
}

# Как назвать условие человеку — по первому ключу, давшему выражение.
TERM_LABELS: dict[str, str] = {}
for _key, _label in (("опцион", "опцион"), ("обратн", "обратный выкуп"), ("earn-out", "отложенный платёж (earn-out)"),
                     ("рассрочк", "рассрочка"), ("эскроу", "эскроу"), ("заверен", "заверения"),
                     ("неконкурен", "запрет конкуренции"), ("мультипликатор", "мультипликаторы"),
                     ("ebitda", "мультипликаторы"), ("p/e", "мультипликатор P/E"), ("дисконт", "дисконт"),
                     ("взнос", "взнос в бюджет"), ("mbo", "выкуп менеджментом (MBO)"), ("lock-up", "lock-up")):
    TERM_LABELS.setdefault(TERM_HINTS[_key], _label)
TERM_LABELS.setdefault(TERM_HINTS["отложенн"], "отложенный платёж (earn-out)")


# --------------------------------------------------------------------------
# Индекс
# --------------------------------------------------------------------------

@dataclass
class Firm:
    id: str
    name: str
    rx: re.Pattern
    # Вид консультанта по каталогу сайта: "law" — вкладка юрфирм (FIRMS),
    # иначе — первая группа из INV_FIRMS («Банк», «Инвестиционный банк»,
    # «Консультант по недвижимости»…). Без него ассистент называл брокеров
    # IBC и Nikoliers юрфирмами (проверка на 100 вопросах, 14 октября 2026).
    kind: str = "law"

    @property
    def kind_label(self) -> str:
        return FIRM_KIND_LABELS.get(self.kind, self.kind.lower() if self.kind else "консультант")


FIRM_KIND_LABELS = {
    "law": "юрфирма", "Банк": "банк", "Инвестиционный банк": "инвестбанк",
    "Консультант по недвижимости": "консультант по недвижимости",
    "Инвестиционная компания": "инвестиционная компания", "Консалтинг": "консалтинговая компания",
    "Организатор торгов": "организатор торгов", "Институт развития": "институт развития",
}
# Кого считать в ответе на «какой инвестбанк / финансовый консультант»:
# банки и инвестиционные компании, но не брокеры по недвижимости и не
# организаторы торгов — у них другая работа, и в рейтинге банкиров они вводят
# в заблуждение (Nikoliers «самый частый финконсультант», вопрос №16).
INVEST_KINDS = {"Банк", "Инвестиционный банк", "Инвестиционная компания", "Консалтинг"}


@dataclass
class Doc:
    id: str
    title: str
    date: str
    year: int
    status: str
    type: str
    sum_text: str
    sum_rub: float | None
    estimate: bool
    industries: list[str]
    themes: list[str]
    buyer: str
    seller: str
    target: str
    asset: str
    advisors: list[str]
    advisor_roles: list[tuple[str, str]]
    facts: str
    strong: set[str] = field(default_factory=set)
    weak: set[str] = field(default_factory=set)
    raw: dict = field(default_factory=dict)
    blob: str = ""                  # весь текст карточки в нижнем регистре — для регионов

    @property
    def listing(self) -> bool:
        """Лот на торгах, который ещё не купили: на сайте (isListing) он не
        сделка и в счёт рейтингов и «Аналитики» не идёт."""
        return self.type == "Продажа с торгов" and self.status != "Закрыта"

    @property
    def price_rub(self) -> float | None:
        """Цена, допущенная к суммам «Аналитики» (facts.admitted.purchase_sums):
        названа сторонами и прочитана в источнике. Тот же отбор, что у
        countsAsPrice/priceRub в static/index.html, — чтобы средний размер
        сделки у ассистента и на странице считался по одним сделкам."""
        facts = self.raw.get("facts") or {}
        if not (facts.get("admitted") or {}).get("purchase_sums"):
            return None
        value = (facts.get("price") or {}).get("value_rub")
        return float(value) if value else None

    @property
    def top_price(self) -> float | None:
        """Цена сделки из списка «Крупнейшие покупки» на странице «Аналитика»
        (facts.admitted.top_purchases, countsAsTopPurchase в index.html): то
        же, что `price_rub`, но без обсуждаемых сделок. Ассистент называл
        крупнейшей сделкой с 2022 года выкуп «Полюсом» собственных акций, а
        в топ-5 ставил выставленный на продажу небоскрёб и допэмиссию —
        «Аналитика» таких сделок не показывает (вторая проверка, №13, 33, 57)."""
        facts = self.raw.get("facts") or {}
        if not (facts.get("admitted") or {}).get("top_purchases") or self.listing:
            return None
        value = (facts.get("price") or {}).get("value_rub")
        return float(value) if value else None

    @property
    def named_rub(self) -> float | None:
        """Цена, названная сторонами, в рублях (валюта — по курсу ЦБ на дату
        сделки) — даже если её ещё не сверили с источником. Без оценок,
        диапазонов, стартовых цен лотов и «не цен» (объём инвестиций в
        проект): смысл суммы — из facts.price.meaning, как `firmPrice` сайта."""
        price = (self.raw.get("facts") or {}).get("price") or {}
        meaning = price.get("meaning")
        if meaning == "disclosed" or (meaning == "foreign_currency" and price.get("fx_rate")):
            value = price.get("value_rub")
            return float(value) if value else None
        if meaning is None and self.sum_rub and not self.estimate:
            return self.sum_rub
        return None

    @property
    def purchase_like(self) -> bool:
        """Покупка по правилам допуска «Аналитики» (facts.admitted), кроме
        требований к самой цене: тип M&A или купленный лот торгов; не выкуп
        своих акций, не деньги в компанию (допэмиссия, раунд), не
        финансирование, не реорганизация, не передача внутри группы; сделка
        не сорвалась, не обсуждается и не лот, ещё выставленный на продажу."""
        if self.listing or self.type not in PURCHASE_TYPES:
            return False
        if self.status in ("Не состоялась", "Обсуждается"):
            return False
        nature = (self.raw.get("facts") or {}).get("nature") or {}
        return not any(nature.get(k) for k in NOT_PURCHASE_FLAGS)


# Те же признаки, что в facts.admitted('top_purchases'): что не покупка.
NOT_PURCHASE_FLAGS = ("cash_in", "financing", "reorganization", "own_shares", "intragroup")


@dataclass
class Index:
    docs: list[Doc]
    by_id: dict[str, Doc]
    companies: dict[str, dict]
    company_deals: dict[str, list[Doc]]
    firms: list[Firm]
    firm_deals: dict[str, list[Doc]]
    industries: list[str]
    df: Counter
    mtime: float
    company_sigs: dict[str, list[list[str]]] = field(default_factory=dict)
    common: set[str] = field(default_factory=set)


_LOCK = threading.Lock()
_INDEX: Index | None = None


def _js_regex_to_python(src: str) -> re.Pattern | None:
    try:
        return re.compile(src, re.I)
    except re.error:
        return None


def load_firms(html_path: Path = INDEX_HTML) -> list[Firm]:
    """Каталог консультантов живёт в index.html (массивы FIRMS/INV_FIRMS и
    регулярки FIRM_MATCH). Разбираем его регулярками, как уже делает
    pipeline/ingest/curated.py для кураторских сделок, — заводить второй
    каталог на сервере значило бы получить два расходящихся списка."""
    try:
        text = html_path.read_text(encoding="utf-8")
    except OSError:
        return []
    firms: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for which, block in re.findall(r"const (FIRMS|INV_FIRMS) = \[(.*?)\n\];", text, re.S):
        for m in re.finditer(r'\{id:"([^"]+)",\s*n:"([^"]+)"(?:,\s*g:\[([^\]]*)\])?', block):
            firms[m.group(1)] = m.group(2)
            groups = re.findall(r'"([^"]+)"', m.group(3) or "")
            kinds[m.group(1)] = "law" if which == "FIRMS" else (groups[0] if groups else "Консалтинг")
    matches: dict[str, re.Pattern] = {}
    m = re.search(r"const FIRM_MATCH = \{(.*?)\};", text, re.S)
    if m:
        for fid, src in re.findall(r"(\w+):/((?:\\/|[^/])+)/[a-z]*", m.group(1)):
            rx = _js_regex_to_python(src.replace("\\/", "/"))
            if rx:
                matches[fid] = rx
    out = []
    for fid, name in firms.items():
        rx = matches.get(fid)
        if rx is None:
            escaped = re.escape(name).replace(r"\ ", r"\s+")
            rx = re.compile(escaped, re.I)
        out.append(Firm(id=fid, name=name, rx=rx, kind=kinds.get(fid, "law")))
    return out


def _company_name(companies: dict, cid: str | None) -> str:
    if not cid:
        return ""
    c = companies.get(cid) or {}
    return c.get("name") or ""


def _advisors(deal: dict) -> tuple[list[str], list[tuple[str, str]]]:
    names, roles = [], []
    for row in (deal.get("law") or {}).get("adv") or []:
        if isinstance(row, (list, tuple)) and len(row) >= 2 and has_fact(row[1]):
            names.append(str(row[1]))
            roles.append((str(row[0] or ""), str(row[1])))
    fin = (deal.get("eco") or {}).get("finadv")
    if has_fact(fin):
        names.append(str(fin))
        roles.append(("Финансовый консультант", str(fin)))
    return names, roles


def _facts(deal: dict) -> str:
    eco, law = deal.get("eco") or {}, deal.get("law") or {}
    parts = [eco.get(k) for k in ("share", "val", "rationale", "context", "target_fin")]
    parts += [law.get(k) for k in ("struct", "appr", "terms")]
    parts.append(deal.get("extra"))
    return " ".join(str(p) for p in parts if has_fact(p))


# Другие имена, под которыми о компании спрашивают, а в базе её профиль
# назван иначе. «Сравни Ozon и Wildberries» отвечало «у Wildberries ни одной
# сделки» (вопрос №32): профиль называется «ООО „РВБ“ (Wildberries & Russ)», а
# компания узнаётся только по ВСЕМ значимым словам имени. Это слова поиска, а
# не правка базы: имя профиля остаётся тем, что записано в источниках.
#
# Разговорные имена (вторая проверка, №92: «Какие сделки были у Сбера?»
# уходило в поиск по словам и отдавало одну продажу Fortenova). Каждый ключ —
# профиль, у которого больше всего сделок под этим именем; дочки и структуры
# с собственными профилями («СберИнвест», «Т-Банк» и «Тинькофф») не
# склеиваются. Сокращения, совпадающие с обычными словами вопросов («ЦБ» в
# «реестр ЦБ», «Открытие»), сюда не берутся — по ним компания узнавалась бы
# в чужих вопросах; «Мосбиржа» — тоже: в «IPO на Мосбирже» биржа — площадка,
# а не сторона сделки.
COMPANY_ALIASES: dict[str, list[str]] = {
    "g549ab474": ["Wildberries", "Вайлдберриз", "Вайлдбериз", "Вайлдберис", "WB", "ВБ", "RWB", "РВБ"],
    "g28ff15bb": ["Сбер", "Sber", "Sberbank"],
    "gcafc31dc": ["VTB", "Банк ВТБ"],
    "yandex": ["Yandex"],
    "g4e694234": ["ВКонтакте"],
    "g2f93d858": ["Норникель", "Nornickel"],
    "gd685b926": ["Билайн", "Beeline"],
    "g8ec7e7bf": ["Российские железные дороги"],
    "ga3f64b72": ["ВЭБ", "Внешэкономбанк"],
    "gf1f56e08": ["ГПБ"],
    "ga2cfae5b": ["Альфабанк"],
    "gc2792a44": ["АФК"],
    "g889e2038": ["Центробанк", "ЦБ РФ"],
}

_CASED_WORD = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9-]*")


def _common_words(texts: list[str]) -> set[str]:
    """Обычные слова языка — по самой базе, а не по словарю из головы.

    Слово, которое в прозе карточек чаще пишется со строчной буквы, чем с
    заглавной в середине фразы, — обычное слово («продажи», «ресторанов»,
    «пример»), а не имя. По такому слову компания узнаётся только при
    признаке имени в самом вопросе (см. `_detect_company`). Имена брендов
    («Магнит», «Лента», «Точка») в прозе почти всегда с заглавной и сюда не
    попадают."""
    lower: Counter = Counter()
    upper: Counter = Counter()
    for text in texts:
        for m in _CASED_WORD.finditer(text or ""):
            word = m.group(0)
            if not re.match(r"[а-яё]", word, re.I):
                continue
            key = stem(norm(word))
            if word[0].islower():
                lower[key] += 1
            else:
                before = text[max(0, m.start() - 3):m.start()]
                if m.start() == 0 or re.search(r"[.!?]\s+$|[:;\n]\s*$", before):
                    continue        # начало фразы: заглавная ничего не значит
                upper[key] += 1
    return {w for w, n in lower.items() if n >= 3 and n >= 2 * upper.get(w, 0)}


def _build(data: dict, firms: list[Firm], mtime: float) -> Index:
    companies = data.get("companies") or {}
    match_keys = data.get("match_keys") or {}
    prose: list[str] = []
    docs: list[Doc] = []
    company_deals: dict[str, list[Doc]] = defaultdict(list)
    for deal in data.get("deals") or []:
        ds = str(deal.get("date") or "")
        if not ds[:4].isdigit() or int(ds[:4]) < SITE_MIN_YEAR:
            continue
        year = int(ds[:4])
        buyer = _company_name(companies, deal.get("buyer")) or (deal.get("buyer_name") or "")
        seller = _company_name(companies, deal.get("seller_id")) or (deal.get("seller") or "")
        target = _company_name(companies, deal.get("target") or deal.get("asset_id"))
        advisors, roles = _advisors(deal)
        inds = deal.get("industries") if isinstance(deal.get("industries"), list) and deal.get("industries") else [deal.get("ind")]
        inds = [i for i in inds if i]
        doc = Doc(
            id=str(deal["id"]), title=deal.get("title") or "", date=ds, year=year,
            status=deal.get("status") or "", type=deal.get("type") or "",
            sum_text=str(deal.get("sum") or ""), sum_rub=parse_rub_sum(deal.get("sum")),
            estimate=is_estimate(deal.get("sum")), industries=inds,
            themes=list(deal.get("themes") or []), buyer=buyer, seller=seller,
            target=target, asset=deal.get("asset") or "", advisors=advisors,
            advisor_roles=roles, facts=_facts(deal), raw=deal,
        )
        strong_src = " ".join([doc.title, doc.buyer, doc.seller, doc.target, doc.asset,
                               " ".join(inds), " ".join(doc.themes), " ".join(advisors), doc.type])
        for cid in (deal.get("buyer"), deal.get("seller_id"), deal.get("target"), deal.get("asset_id")):
            if cid and cid in companies:
                company_deals[cid].append(doc)
                strong_src += " " + " ".join(match_keys.get(cid) or [])
            if cid and cid in COMPANY_ALIASES:
                strong_src += " " + " ".join(COMPANY_ALIASES[cid])
        doc.strong = {stem(t) for t in tokens(strong_src) if t not in STOP and len(t) >= 2}
        doc.weak = {stem(t) for t in tokens(doc.facts) if t not in STOP and len(t) >= 3}
        doc.blob = norm(" ".join([doc.title, doc.buyer, doc.seller, doc.target, doc.asset, doc.facts]))
        prose.append(doc.facts)
        prose.append(doc.title)
        docs.append(doc)
    docs.sort(key=lambda d: d.date, reverse=True)
    firm_deals: dict[str, list[Doc]] = defaultdict(list)
    for doc in docs:
        for f in firms:
            if any(f.rx.search(a) for a in doc.advisors):
                firm_deals[f.id].append(doc)
    df: Counter = Counter()
    for doc in docs:
        for t in doc.strong:
            df[t] += 1
    industries = sorted({i for d in docs for i in d.industries})
    # Значимые слова имён — один раз при сборке, а не на каждый вопрос: сверка
    # вопроса с ~1800 профилями шла по 30 мс и прогон сотен вопросов тянулся минутами.
    company_sigs: dict[str, list[list[str]]] = {}
    for cid in company_deals:
        variants = [_significant(_company_name(companies, cid))]
        variants += [_significant(a) for a in COMPANY_ALIASES.get(cid, [])]
        variants = [v for v in variants if v and len(v) <= 4]
        if variants:
            company_sigs[cid] = variants
    return Index(docs=docs, by_id={d.id: d for d in docs}, companies=companies,
                 company_deals=dict(company_deals), firms=firms, firm_deals=dict(firm_deals),
                 industries=industries, df=df, mtime=mtime,
                 company_sigs=company_sigs, common=_common_words(prose))


def get_index(force: bool = False) -> Index:
    """Индекс перестраивается, когда файл базы на диске поменялся (деплой
    приносит новый JSON), — без перезапуска сервера и без кэша навсегда."""
    global _INDEX
    try:
        mtime = os.path.getmtime(DATA_PATH)
    except OSError:
        mtime = 0.0
    with _LOCK:
        if _INDEX is not None and not force and _INDEX.mtime == mtime:
            return _INDEX
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        _INDEX = _build(data, load_firms(), mtime)
        return _INDEX


# --------------------------------------------------------------------------
# Понимание вопроса
# --------------------------------------------------------------------------

@dataclass
class Intent:
    kind: str                       # advisor | company | compare | industry | largest | count | theme | term | recent | search | empty
    firm: Firm | None = None
    company_id: str | None = None
    industry: str | None = None
    theme: str | None = None
    term_rx: str | None = None
    year: int | None = None
    wants_advisors: bool = False
    terms: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)   # слова вопроса, по которым узнали компанию
    words: list[str] = field(default_factory=list)     # те же слова без обрезки окончаний
    company_ids: list[str] = field(default_factory=list)  # для сравнения: все узнанные компании
    days: int | None = None                            # «за последнюю неделю» — сколько дней назад
    # Условия, которые применяются ВСЕ, а не первое попавшееся (вопросы №3,
    # 25, 28, 29, 31, 40 проверки 14 октября 2026): период, темы, условия
    # сделки, статус, регион.
    span: Span | None = None
    themes: list[str] = field(default_factory=list)
    term_rxs: list[str] = field(default_factory=list)
    status: str | None = None                          # "closed" | "open" | "failed"
    region: str | None = None
    firms: list[Firm] = field(default_factory=list)    # «Сравни АЛРУД и ЕПАМ»
    rank: str | None = None                            # law | invest | advisors | industries | buyers
    wants_price: bool = False                          # «за сколько», «во сколько», «по какой цене»
    buyer_kind: str | None = None                      # "bank" — «банки-покупатели» (№80)
    role: str | None = None                            # "buyer" | "seller" — «что покупала S8 Capital» (№27);
                                                       # "object" — компанию продают («продажу Яндекса», №43)
    finance: bool = False                              # «какая выручка у ВкусВилла» — отчётность (№77)

    def __post_init__(self):
        if self.span is None and self.year:
            self.span = (self.year, self.year)
        if self.theme and not self.themes:
            self.themes = [self.theme]
        if self.term_rx and not self.term_rxs:
            self.term_rxs = [self.term_rx]


PREP_WORDS = re.compile(r"готовлюсь\s+к\s+(?:встрече|собеседованию)", re.I)
# «За сколько», «во сколько», «сколько стоит» — вопрос о ЦЕНЕ, а не о числе
# сделок: «Кто купил Ситибанк и за сколько?» уходило в «сколько всего сделок»
# и отвечало «такой сделки нет» (№47), «Во сколько Б1 оценила бизнес Russ?» —
# тоже (№24).
PRICE_WORDS = re.compile(
    r"за\s+сколько|во\s+сколько|сколько\s+(?:(?:может|могут|будет|бы)\s+)?(?:сто[ия]\w*|заплатил\w*|отдал\w*|выручил\w*)"
    r"|по\s+как(?:ой|ую)\s+цен|за\s+какую\s+(?:сумму|цену)|на\s+как(?:ую|ие)\s+сумм|как(?:ая|ой|ую)\s+(?:была\s+)?(?:цена|сумм|оценк)"
    r"|\bоцени\w*|\bоценк\w*|стоимост\w*|\bцен[аыеу]\b|мультипликатор"
    r"|сумм\w*\s+(?:известн|назван|раскрыт)|(?:известн|назван|раскрыт)\w*\s+сумм", re.I)
COUNT_STRICT = re.compile(r"сколько\s+(?:\w+\s+){0,2}сделок|сколько\s+(?:\w+\s+)?(?:было|прошло|закрыл\w*|состоял\w*)|число\s+сделок|количеств", re.I)
STATUS_FAILED = re.compile(r"не\s+состоял\w*|не\s+состоит\w*|сорвал\w*|сорва\w*|отмен\w*|не\s+закрыл\w*\s+и\s+не|провал\w*|расторг\w*|не\s+удал\w*", re.I)
STATUS_OPEN = re.compile(r"обсужда\w*|переговор\w*|не\s+закрыт\w*|ещ[её]\s+не\s+закрыт\w*|незакрыт\w*|в\s+процессе|не\s+завершен\w*|готовящ\w*", re.I)
STATUS_CLOSED = re.compile(r"закрыл\w*|закрыт(?!и)\w*|завершил\w*|завершен\w*|(?<!не\s)состоял\w*", re.I)
STATUS_LABELS = {"closed": "закрытые", "open": "ещё не закрытые (обсуждаются или ждут согласований)",
                 "failed": "не состоявшиеся"}
# Рейтинги по всей базе. Модель видит дюжину сделок, а не базу, и «какие
# юрфирмы самые активные» без счёта на сервере превращалось в «рейтинга нет»
# или в подсчёт по 12 случайным сделкам (№17, 58, 74, 75, 81).
RANK_WORDS = re.compile(
    r"сам\w*\s+активн|наиболее\s+активн|активне\w*|чаще\s+(?:всего|других|остальных)|больше\s+всего\s+сделок"
    r"|рейтинг|лидер\w*|\bтоп\b|топ[- ]?\d+|\bраст[уё]т|кто\s+(?:больше|чаще)\s+всех|самы\w*\s+(?:частые|популярн\w*)|по\s+числу\s+сделок"
    # «Как вырастить свой бизнес через покупки?» — модель отказывала как не
    # вопросу о сделках (№90); отвечаем теми, кто растёт покупками.
    r"|\bвыра(?:стить|щивать)\b.{0,40}\bчерез\s+(?:покупк|приобретени|поглощени|m&a|сделк)"
    r"|\bрост\w*\s+через\s+(?:покупк|приобретени|поглощени|m&a)", re.I)
RANK_SUBJECTS = (
    ("law", re.compile(r"юрфирм|юридическ\w*\s+(?:фирм|компани|консультант|бюро)|юрист|адвокат|law\s*firm", re.I)),
    ("invest", re.compile(r"инвестбанк|инвестиционн\w*\s+(?:банк|консультант)|финансов\w*\s+(?:консультант|советник)|банк\w*[- ]консультант|организатор", re.I)),
    ("advisors", re.compile(r"консультант|консультир|сопровожда|советник|консалтинг", re.I)),
    ("industries", re.compile(r"отрасл|сектор|индустри", re.I)),
    ("buyers", re.compile(r"покупател|покупа\w*|покупк|приобрета\w*|растут\s+через|скупа\w*", re.I)),
)
AVG_WORDS = re.compile(r"средн\w*\s+(?:размер|сумм|чек|стоимост|цен|сделк)|средн\w*\s+\w+\s+сделк|медиан|типичн\w*\s+(?:размер|сумм|сделк|чек)|в\s+среднем", re.I)
# Уточнение в диалоге: «а какие из них самые крупные?», «а за сколько?» —
# про сделки предыдущего ответа, а не про всю базу (№23).
FOLLOWUP_WORDS = re.compile(
    r"\bиз\s+(?:них|этих|тех|списка|перечисленн\w*)|\bсреди\s+(?:них|этих)|\bэтих\b|\bэти(?:ми)?\b|\bтам\b|\bу\s+них\b"
    r"|\bих\b|\bони\b|^\s*а\s+(?:за\s+сколько|во\s+сколько|сколько|как(?:ие|ая|ой|ую)|кто|когда|где|что)\b", re.I)

# Регионы — по тексту карточки: отдельного поля региона в базе нет.
REGION_HINTS: dict[str, str] = {
    "Татарстан": r"татарстан|казан[ьиеcь]|набережн\w*\s+челн|альметьевск|нижнекамск",
    "Башкортостан": r"башкорт|башкир|\bуф[аеы]\b",
    "Санкт-Петербург и Ленинградская область": r"петербург|\bспб\b|ленинградск",
    "Москва и Подмосковье": r"москв|московск|подмосков",
    "Новосибирская область": r"новосибирск",
    "Свердловская область": r"екатеринбург|свердловск",
    "Краснодарский край": r"краснодар|кубан|\bсочи\b|новороссийск",
    "Ростовская область": r"ростов\w*[- ]на[- ]дону|ростовск",
    "Нижегородская область": r"нижн\w*\s+новгород|нижегородск",
    "Пермский край": r"\bперм[ьиск]",
    "Самарская область": r"самар|тольятти",
    "Красноярский край": r"красноярск",
    "Якутия": r"якути|республик\w*\s+саха",
    "Дагестан": r"дагестан|махачкал",
    "Чечня": r"чечн|чеченск|грозн",
    "Крым": r"\bкрым|севастопол",
    "Калининградская область": r"калининград",
    "Приморский край": r"приморск\w*\s+кра|владивосток",
    "Хабаровский край": r"хабаровск",
    "Сахалин": r"\bсахалин(?:е|а|ом|ская|ской|скую)?\b",
    "Камчатка": r"камчат",
    "Мурманская область": r"мурманск",
    "Архангельская область": r"архангельск",
    "Тюменская область": r"тюмен",
    "ХМАО — Югра": r"\bхмао|югр[аые]|ханты",
    "ЯНАО": r"\bянао\b|\bямал(?:е|а|ом)?\b|ямало-ненец",
    "Кузбасс": r"кузбасс|кемеров",
    "Иркутская область": r"иркутск",
    "Омская область": r"\bомск",
    "Томская область": r"\bтомск",
    "Челябинская область": r"челябинск|магнитогорск",
    "Воронежская область": r"воронеж",
    "Тульская область": r"\bтул[аеьуы]\b|тульск",
    "Калужская область": r"калуг|калужск",
    "Ярославская область": r"ярослав",
    "Белгородская область": r"белгород",
    "Липецкая область": r"липецк",
    "Курская область": r"\bкурск",
    "Ставропольский край": r"ставропол",
    "Алтай": r"\bалта[йя]|барнаул",
    "Бурятия": r"бурят|улан-удэ",
    "Удмуртия": r"удмурт|ижевск",
    "Чувашия": r"чуваш|чебоксар",
    "Мордовия": r"мордов|саранск",
    "Оренбургская область": r"оренбург",
    "Саратовская область": r"саратов",
    "Волгоградская область": r"волгоград",
    "Астраханская область": r"астрахан",
    "Владимирская область": r"владимирск",
    "Тверская область": r"твер[ьис]",
    "Псковская область": r"псков",
    "Новгородская область": r"великий\s+новгород|новгородск",
    "Вологодская область": r"вологод|череповец",
    "Карелия": r"карели|петрозаводск",
    "Коми": r"\bкоми\b|сыктывкар",
}

ADVISOR_WORDS = re.compile(r"консультир|консультант|сопровожда|юрфирм|юридическ|инвестбанк|advis|law firm", re.I)
LARGEST_WORDS = re.compile(r"крупн|больш|дорог|максимальн|самая\s+больш|топ[- ]?\d*", re.I)
COUNT_WORDS = re.compile(r"сколько|как\s+много|число\s+сделок|количеств", re.I)
# «Что нового на рынке за последнюю неделю» уходило в компанию «Новосталь-М»:
# слово «нового» совпало с её именем по корню «новог». Маршрута «что свежего»
# не было вовсе, поэтому вопрос ловился первым, кто похож по буквам.
RECENT_WORDS = re.compile(r"что\s+нового|новые\s+сделки|свеж\w*\s+(?:сделк|новост)|что\s+появилось"
                          r"|последн\w*\s+(недел|дн|месяц)|за\s+(недел|месяц)"
                          r"|(?:на|за)\s+(?:эт\w+|текущ\w+|прошл\w+|минувш\w+)\s+(?:недел|месяц)", re.I)
# «Какие новости о сделках M&A вышли на этой неделе?» уходило в поиск по
# слову «вышли» (сделки «вышли из капитала» 2024–2025 годов), и модель в
# режиме «по интернету» писала, что новых сделок нет с апреля 2024 (№19
# третьей проверки). «Новости» без имени компании — то же «что нового».
NEWS_WORDS = re.compile(r"\bновост\w*|\bновенько\w*|\bсвежак\w*", re.I)
RECENT_MONTH = re.compile(r"месяц", re.I)
# «Сравни Сбербанк и ВТБ» находило только Сбербанк, вторую сторону теряло молча.
COMPARE_WORDS = re.compile(r"сравн|в\s+сравнении|против|или\s+лучше|кто\s+из\s+них|обе\s+компан", re.I)
# «Банки-покупатели», «какие банки покупали компании», «сделки, где
# покупатель — банк» (№80): условие на ПОКУПАТЕЛЯ, а не отрасль сделки.
# «Какие компании купили банки» сюда не попадает: там банк — предмет.
_BANK = r"(?<![а-яёa-z])банк\w*"
BANK_BUYER = re.compile(
    rf"{_BANK}[- ]покупател\w*|{_BANK}\s+(?:\w+\s+){{0,3}}?(?:покупа\w*|купил\w*|купят|приобрета\w*|приобр[её]л\w*"
    rf"|скупа\w*|выступа\w*\s+(?:в\s+рол\w+\s+)?покупател\w*)|покупател\w*\s*(?:[-—–:]\s*|(?:был\w*|явля\w*|выступа\w*)\s+)?{_BANK}",
    re.I)
# Отчётность компании (выручка, прибыль) — не сделки: ассистент её не видит,
# она на странице компании по данным ФНС. «Какая выручка у ВкусВилла за 2025
# год?» отвечало «нет сделок за 2025 год», и модель — «нет информации», не
# подсказав, где она есть (№77 третьей проверки).
FINANCE_WORDS = re.compile(r"выручк\w*|прибыл\w*|убыт(?:ок|к)\w*|\bebitda\b|отч[её]тност\w*|финансов\w*\s+(?:показател|результат|отч)", re.I)
# Роль компании в вопросе: «Что покупала S8 Capital?» — её покупки, а
# продажи отдельно и подписаны (№27). «Кто купил Ситибанк?» — роль у
# спрошенного «кто», а названная компания — предмет: роль не ставится.
ROLE_BUY = re.compile(r"\b(?:покупал\w*|купил\w*|покупает|покупают|покупк\w+|приобрета\w*|приобр[её]л\w*|скупа\w*)", re.I)
ROLE_SELL = re.compile(r"\b(?:продавал\w*|продал\w*|прода[её]т|продают|продаж\w*|избавил\w*|избавля\w*)", re.I)
ROLE_WHO = re.compile(r"\bкто\b|\bу\s+кого\b|\bкому\b|\bкого\b", re.I)


# «Кто консультировал продажу Яндекса консорциуму?», «кто купил Ситибанк»:
# названная компания — то, что продают, а не покупатель. Сделка, где Яндекс —
# предмет, стояла в списке компании пятнадцатой, за его покупками, и до модели
# не доходила; модель отвечала «ничего не нашёл» (№43 третьей проверки).
OBJECT_OF_DEAL = re.compile(
    r"(?:\bпродаж\w*|\bпокупк\w*|\bприобретени\w*|\bвыкуп\w*|\bпоглощени\w*|\bкто\s+(?:\w+\s+)?(?:купил\w*|"
    r"приобр[её]л\w*|покупа\w*|продал\w*|выкупил\w*))\s+(?:(?:доли|долей|акций|пакета|бизнеса|компании|актив\w*)\s+)?"
    r"«?([a-zа-я0-9][a-zа-я0-9.-]*)", re.I)


def _object_of_deal(question: str, matched: list[str]) -> bool:
    """Названная компания стоит сразу за «продажу / покупку / кто купил» и не в
    творительном падеже («покупку Яндексом» — Яндекс покупатель)."""
    for m in OBJECT_OF_DEAL.finditer(norm(question)):
        word = m.group(1)
        if re.search(r"(?:ом|ем|ём|ами|ями)$", word) and len(word) > 5:
            continue
        if any(word.startswith(t) or stem(word) == t or t.startswith(stem(word)) for t in matched if len(t) >= 2):
            return True
    return False


def _detect_role(question: str) -> str | None:
    if ROLE_WHO.search(question):
        return None
    buy, sell = bool(ROLE_BUY.search(question)), bool(ROLE_SELL.search(question))
    if buy and not sell:
        return "buyer"
    if sell and not buy:
        return "seller"
    return None


# Слова, которые начинаются с отраслевой подсказки, но отрасль не называют:
# «медианная сумма» читалась как отрасль «Медиа» и отвечала «в Медиа нет
# сделок с ценой» (№50 третьей проверки), «участвовал» — как «участок»
# (недвижимость), «тариф» — как «тара», «портфель» — как «порт».
HINT_FALSE_PREFIXES = ("медиан", "участв", "участник", "участи", "тариф", "тарел", "портфел",
                       "портрет", "портал", "газет")


def _hint_hit(token: str, hint: str) -> bool:
    """Слово вопроса — отраслевая подсказка: короткая (до трёх знаков) — целым
    словом, длинная — началом слова, кроме слов из HINT_FALSE_PREFIXES."""
    if len(hint) <= 3:
        return token == hint
    return token.startswith(hint) and not any(token.startswith(x) for x in HINT_FALSE_PREFIXES)


def _detect_industry(question: str, idx: Index) -> str | None:
    q_tokens = tokens(question)
    q_norm = " ".join(q_tokens)
    known = set(idx.industries)
    for ind, hints in INDUSTRY_HINTS.items():
        if ind not in known:
            continue
        for h in hints:
            hn = norm(h)
            if " " in hn:
                hit = hn in q_norm
            else:
                hit = any(_hint_hit(t, hn) for t in q_tokens)
            if hit:
                return ind
    return None


def _detect_theme(question: str) -> str | None:
    q = norm(question)
    q_tokens = tokens(question)
    # «уход/выход иностранцев» — самая частая тема, узнаём по двум признакам сразу.
    if re.search(r"иностран|зарубеж|нерезидент", q) and re.search(r"уход|уш|выход|выш|покин|продал", q):
        return "Уход иностранного владельца"
    if re.search(r"выходил[а-я]*\s+из\s+росси|уходил[а-я]*\s+из\s+росси|покидал[а-я]*\s+росси", q):
        return "Уход иностранного владельца"
    for theme, hints in THEME_HINTS.items():
        if theme == "Уход иностранного владельца":
            continue
        for h in hints:
            hn = norm(h)
            if len(hn) <= 3:
                if hn in q_tokens:
                    return theme
            elif any(t.startswith(hn) for t in q_tokens):
                return theme
    return None


def _detect_term(question: str) -> str | None:
    found = _detect_terms(question)
    return found[0] if found else None


def _detect_terms(question: str) -> list[str]:
    """Все условия сделки из вопроса: «с дисконтом и взносом в бюджет» — оба."""
    q = norm(question)
    out: list[str] = []
    for key, rx in TERM_HINTS.items():
        if key in q and rx not in out:
            out.append(rx)
    # «опцион на обратный выкуп» дал бы два выражения, одно из которых шире
    # другого: оставляем узкое, иначе «опцион» один отбирал бы лишнее.
    if r"опцион" in out and len(out) > 1 and any("обратн" in r for r in out):
        out.remove(r"опцион")
    return out


def _detect_themes(question: str) -> list[str]:
    """Все темы вопроса. «Сделки по уходу иностранцев через правкомиссию в
    2023 году» брало только уход и говорило, что правкомиссия ни у одной не
    упоминается (№3)."""
    first = _detect_theme(question)
    if not first:
        return []
    out = [first]
    q_tokens = tokens(question)
    for theme, hints in THEME_HINTS.items():
        if theme in out or theme == "Уход иностранного владельца":
            continue
        for h in hints:
            hn = norm(h)
            hit = (hn in q_tokens) if len(hn) <= 3 else any(t.startswith(hn) for t in q_tokens)
            if hit:
                out.append(theme)
                break
    return out


def _detect_status(question: str) -> str | None:
    q = norm(question)
    found = []
    if STATUS_FAILED.search(q):
        found.append("failed")
    if STATUS_OPEN.search(q):
        found.append("open")
    if any(not q[max(0, m.start() - 3):m.start()].endswith("не ") for m in STATUS_CLOSED.finditer(q)):
        found.append("closed")
    # «Какие закрыты, а какие ещё обсуждаются?» — человек просит разбивку по
    # этапам, а не один этап (№95 третьей проверки): фильтра нет.
    if len(found) > 1:
        return None
    return found[0] if found else None


def _status_ok(doc: Doc, status: str | None) -> bool:
    if not status:
        return True
    st = doc.status or ""
    if status == "closed":
        return st == "Закрыта"
    if status == "failed":
        return st == "Не состоялась"
    return bool(st) and st not in ("Закрыта", "Не состоялась")


def _detect_region(question: str) -> str | None:
    q = norm(question)
    for name, rx in REGION_HINTS.items():
        if re.search(rx, q):
            return name
    return None


def _detect_rank(question: str) -> str | None:
    if not RANK_WORDS.search(question):
        return None
    for kind, rx in RANK_SUBJECTS:
        if rx.search(question):
            return kind
    return None


def _detect_firms(question: str, idx: Index) -> list[Firm]:
    """Все фирмы-консультанты вопроса: «Сравни АЛРУД и ЕПАМ» узнавало одну
    ЕПАМ, а про АЛРУД (11 сделок) модель говорила «сделок нет» (№5)."""
    parts = [p for p in re.split(r"\s+(?:и|или|против|vs\.?)\s+|[,;:]", question) if p.strip()]
    if len(parts) < 2:
        return []
    out: list[Firm] = []
    for part in parts:
        f = _detect_firm(part, idx)
        if f and f.id not in {x.id for x in out}:
            out.append(f)
    return out


def _declension_match(a: str, b: str) -> bool:
    """Одно слово в разных падежах: общее начало от шести знаков и хвосты не
    длиннее трёх («никольская» / «никольскую»). Строже `same_word`: имя фирмы
    не должно ловиться на общем корне («групп», «мед»)."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 6 and len(a) - n <= 3 and len(b) - n <= 3


def _firm_deal_count(firm: Firm, idx: Index) -> int:
    """Сколько сделок базы фирма СОПРОВОЖДАЛА (а не участвовала в них)."""
    return sum(1 for doc in idx.docs if any(firm.rx.search(a) for a in doc.advisors))


def _detect_firm(question: str, idx: Index) -> Firm | None:
    hits = [f for f in idx.firms if f.rx.search(question)]
    if hits:
        return max(hits, key=lambda f: len(f.name))
    # Регулярки каталога знают именительный падеж («никольская»), а вопрос —
    # любой («Никольскую»): владелец 31 августа 2026 не нашёл фирму и получил
    # вместо неё компанию «Никольское». Сверяем значимые русские слова имени
    # фирмы со словами вопроса по общему началу.
    words = query_words(question)
    best: tuple[int, Firm] | None = None
    for f in idx.firms:
        # Родовые слова имени («Консалт», «Партнёры», «Групп») — не имя: по
        # ним «Никольской Консалтинг» узнавалась как «Б1 – Консалт».
        sig = [w for w in tokens(f.name)
               if len(w) >= 6 and re.fullmatch(r"[а-я]+", w) and not _generic_firm_word(w)]
        if not sig:
            continue
        if all(any(_declension_match(sw, w) for w in words) for sw in sig):
            score = sum(len(w) for w in sig)
            if best is None or score > best[0]:
                best = (score, f)
    return best[1] if best else None


_GENERIC_FIRM_ROOTS = ("консалт", "консульт", "партн", "групп", "юрид", "прав", "лигал", "адвокат", "бюро", "коллег", "компани")


def _generic_firm_word(word: str) -> bool:
    w = norm(word)
    return w in ADVISOR_GENERIC or any(w.startswith(r) for r in _GENERIC_FIRM_ROOTS)


def _significant(name: str) -> list[str]:
    """Значимые слова имени компании — то, по чему её узнают в вопросе.

    Порог в три знака отсекает служебные хвосты («.ру», «им.», «РФ») — но
    вместе с ними отсекал и сами имена длиной в два знака: у «VK», «X5 Group»,
    «S8 Capital», «1С» значимых слов не оставалось ВОВСЕ, и ни один вопрос не
    мог узнать эти компании — ни по-русски, ни латиницей (найдено 3 сентября
    2026 при просьбе владельца «Vk пусть находится буквами вк»). Поэтому
    двухзначные слова берутся ТОЛЬКО как запасной вариант — когда иначе список
    пуст. Добавлять их всегда нельзя: `_detect_company` требует совпадения
    ВСЕХ значимых слов, и «Учи.ру» с «ру» в списке перестала бы узнаваться по
    слову «учи».
    """
    keep = [stem(t) for t in tokens(name) if t not in GENERIC_NAME_WORDS and len(t) >= 3]
    if keep:
        return keep
    return [stem(t) for t in tokens(name) if t not in GENERIC_NAME_WORDS and len(t) >= 2]


RU2LAT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh",
          "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
          "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
          "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y",
          "ь": "", "э": "e", "ю": "yu", "я": "ya"}


def translit(word: str) -> str:
    """Кириллица и латиница — один ключ (та же таблица, что в static/index.html).

    Просьба владельца 3 сентября 2026: «VK пусть находится буквами вк (и другие
    компании тоже)». Имя компании в базе записано так, как её пишут источники
    («VK», «Ozon»), а спрашивают о ней с русской раскладки. Приводим обе стороны
    к латинице побуквенно: «вк» и «vk» дают один ключ. Сложившееся написание
    бренда, расходящееся с побуквенной транслитерацией («Яндекс» → «yandeks»
    против «Yandex»), это НЕ ловит и ловить не должно — такие имена в базе и так
    стоят по-русски, а список брендов-исключений был бы уже не механикой.
    """
    return "".join(RU2LAT.get(ch, ch) for ch in (word or "").lower().replace("ё", "е"))


def _name_word_match(name_stem: str, term: str) -> bool:
    """Слово вопроса называет слово ИМЕНИ (компании, стороны, заголовка).
    `same_word` здесь слишком мягок: у него общее начало в три знака, и
    «почему» ложилось на «Почта» (Почта Банк), «получил» — на «Полюс», «так»
    — на «Такси»; вопрос «Почему так много покупает?» со страницы «Яндекса»
    отвечал про Почта Банк (2 сентября 2026). Имя — не обычное слово: требуем
    общее начало от четырёх знаков (или равенство — для коротких «ВТБ»,
    «МТС»)."""
    if name_stem == term:
        return True
    # «вк» = «VK»: побуквенная транслитерация, не догадка о похожести
    if len(term) >= 2 and translit(name_stem) == translit(term):
        return True
    if not same_word(name_stem, term):
        return False
    # Латиница не склоняется: «Russ» — не «Russia Partners» (№24). Терпим
    # только опечатку в длинном имени (ниже).
    latin = bool(re.fullmatch(r"[a-z0-9&.-]+", name_stem) and re.fullmatch(r"[a-z0-9&.-]+", term))
    n = 0
    for x, y in zip(name_stem, term):
        if x != y:
            break
        n += 1
    if n < 4:
        return False
    # Общее начало — ещё не одно слово: «интерфакса» и «Интеррос» сходятся
    # в «интер», «ресторанов» и «Рестер» — в «рест», «Медси» и «Медскан» — в
    # «медс» (проверка на 100 вопросах, 14 октября 2026). Падеж меняет только
    # хвост: одно слово целиком начинается с другого. Опечатку в середине
    # длинного имени («wildberis») терпим, когда совпало от шести знаков, а
    # расхождение — пара букв в конце.
    if (name_stem.startswith(term) or term.startswith(name_stem)) and abs(len(name_stem) - len(term)) <= 2 \
            and not latin:
        return True
    return n >= 6 and len(name_stem) - n <= 4 and len(term) - n <= 3


def short_name_terms(question: str) -> list[str]:
    """Двухзначные слова вопроса с кириллицей — кандидаты на ИМЯ компании
    («вк», «1с»; чисто латинские «vk», «x5» проходят и так).

    `query_words` отбрасывает такие слова намеренно: по-русски двухбуквенное
    слово почти всегда предлог или частица, и в поиск по словам им попадать
    нечего. Но именно на них разбилось «Vk пусть находится буквами вк»
    (владелец, 3 сентября 2026): «вк» отсеивалось ещё до того, как дело
    доходило до сверки с именами компаний. Поэтому такие слова добавляются
    ТОЛЬКО в распознавание компании (там сверка идёт на полное равенство
    после транслитерации, см. _name_word_match) и не идут ни в поиск по
    словам, ни в веса терминов — иначе «за», «до», «от» стали бы значимыми
    словами вопроса.
    """
    return [t for t in tokens(question)
            if len(t) == 2 and t not in STOP and not re.fullmatch(r"[a-z0-9]+", t)]


# Слова, которые в вопросах встречаются часто, а в прозе карточек — редко,
# поэтому `_common_words` их не узнаёт: по ним компания тоже узнаётся только
# с признаком имени (кавычки, заглавная). Каждое — из живого провала:
# «пример» → БЦ «Примиум», «инвестбанк» → «Инвестиционная группа К1»,
# «Интерфакса» → «Интеррос», «свой» → «Свой», «среднего» → BGP (14 октября 2026).
STOP_MATCH = (
    "продаж", "продав", "пример", "ресторан", "кофейн", "инвестбанк", "интерфакс", "cbonds",
    "средн", "рейтинг", "активн", "растут", "растет", "юрфирм", "юрист", "лидер",
    "крупн", "больш", "дешев", "оценк", "оценил", "стоим", "мультипликатор", "услови",
    "бизнес", "отрасл", "сектор", "регион", "подписк", "выгруз",
)
# Короткие обычные слова — только целиком: префиксом «мир» стал бы «Мираторг».
STOP_MATCH_EXACT = {
    "свой", "своя", "свое", "свои", "своих", "сеть", "сети", "сетей", "цена", "цене", "цену", "цены",
    "сумма", "сумму", "суммы", "сумм", "рынок", "рынка", "рынке", "рынк", "мир", "мира", "город", "страна",
    "рост", "роста", "пример", "сделка", "сделки",
}


def _evident_words(question: str) -> set[str]:
    """Слова вопроса с признаком ИМЕНИ: в кавычках или с заглавной буквы не
    в начале фразы. «Какие сделки совершил фонд «Восход»?» называет фонд, а
    «кто покупал сети ресторанов» — никого. Первое слово фразы с заглавной —
    тоже признак, если это не слово вопроса из `STOP_MATCH` и не само
    отраслевое слово («Банки купили…», «Фармацевтика…»): «Самолет сделки»,
    «Апрель сделки» называют компании."""
    out: set[str] = set()
    q = question or ""
    for m in re.finditer(r"[«\"„“]([^»\"“”]{1,80})[»\"“”]", q):
        out.update(tokens(m.group(1)))
    for m in _CASED_WORD.finditer(q):
        word = m.group(0)
        if not word[0].isupper():
            continue
        before = q[:m.start()]
        parts = tokens(word)        # «Т-Технологии», «Сахалин-2», «М.Видео» — по частям
        if not before.strip() or re.search(r"[.!?]\s+$|[:\n]\s*$", before):
            out.update(t for t in parts if not _stop_match(t) and not _hint_word(t))
        else:
            out.update(parts)
    # Латиница с заглавной или с цифрой — имя и в начале фразы («Ozon», «X5»).
    for m in re.finditer(r"\b[A-Za-z][A-Za-z0-9&.-]*\b", q):
        w = m.group(0)
        if any(ch.isupper() for ch in w) or any(ch.isdigit() for ch in w):
            out.update(tokens(w))
    return {w for t in list(out) for w in (t, stem(t))}


def _hint_word(token: str) -> bool:
    """Само отраслевое или тематическое слово в падеже («банки», «фарме»), а
    не имя, которое с него начинается («Фармасинтез», «Авиапарк»)."""
    tn = norm(token)
    for hints in list(INDUSTRY_HINTS.values()) + list(THEME_HINTS.values()):
        for h in hints:
            hn = norm(h)
            if " " in hn:
                continue
            if tn == hn or (len(hn) > 3 and tn.startswith(hn) and len(tn) - len(hn) <= 2):
                return True
    return False


LEGAL_FORMS = {"ооо", "ао", "пао", "зао", "оао", "нао", "гк", "ук", "зпиф", "ltd", "llc", "inc", "plc", "мкпао"}


def _stop_match(term: str) -> bool:
    return term in STOP_MATCH_EXACT or any(term.startswith(p) for p in STOP_MATCH)


def _plain_word(term: str, idx: Index) -> bool:
    """Обычное слово языка, а не имя: по базе (`Index.common`) или по списку
    слов вопросов (`STOP_MATCH`)."""
    return (term in idx.common or stem(term) in idx.common or term in STOP_MATCH_EXACT
            or any(term.startswith(p) for p in STOP_MATCH))


def _detect_company(question: str, idx: Index, terms: list[str],
                    evident: set[str] | None = None) -> tuple[str, list[str]] | None:
    """Компания из вопроса — по значимым словам её имени. Возвращает id и те
    слова вопроса, по которым она узнана: `route` сверяет их с отраслевыми
    подсказками, иначе «сделки в фарме» узнавалось как ГК «Р-Фарм».

    Имя из ОДНОГО обычного слова («Продо», «Свой», «Звезда») узнаётся только
    когда в вопросе у этого слова есть признак имени — кавычки или заглавная
    не в начале фразы (`_evident_words`). Без этого «продажи» уводили вопрос
    про Ситибанк к компании «Продо», а «ресторанов» — к «Рестеру». Имя из
    нескольких слов, названное целиком, узнаётся и без признака."""
    if not terms:
        return None
    if evident is None:
        evident = _evident_words(question)
    q_tokens = set(tokens(question))
    q_stems = {stem(t) for t in q_tokens}
    sigs_by_company = idx.company_sigs or {
        cid: [_significant(c.get("name") or "")] for cid, c in idx.companies.items()}
    best: tuple[tuple, str, list[str]] | None = None
    for cid, variants in sigs_by_company.items():
        n_deals = len(idx.company_deals.get(cid) or [])
        if n_deals == 0:
            continue
        for vi, sig in enumerate(variants):
            if not sig or len(sig) > 4:
                continue
            pairs = [(s, t) for s in sig for t in terms if _name_word_match(s, t)]
            if len({s for s, _ in pairs}) < len(sig):
                continue
            matched_terms = [t for _, t in pairs]
            # Имя из нескольких слов названо целиком («Новый старт», «Русский
            # холод») — это имя, даже если каждое слово обычное.
            words_all = [w for w in tokens(_company_name(idx.companies, cid)) if w not in LEGAL_FORMS]
            full_name = len(words_all) >= 2 and all(
                any(w == t or stem(w) == stem(t) for t in q_tokens) for w in words_all)
            if len(sig) == 1 and all(_plain_word(t, idx) for t in matched_terms) \
                    and not any(t in evident or stem(t) in evident for t in matched_terms) \
                    and not full_name:
                continue
            exact = sum(1 for s, t in pairs if s == t or s == stem(t))
            name_tokens = [stem(w) for w in tokens(_company_name(idx.companies, cid)) if w not in LEGAL_FORMS]
            present = sum(1 for w in name_tokens if w in q_stems)
            missing = len(name_tokens) - present
            if vi > 0 and cid in COMPANY_ALIASES:
                # Названо другим именем профиля («Вайлдберриз» у ООО «РВБ»):
                # оно названо целиком, и при равенстве решает число сделок —
                # «сделки Вайлдберриз» про группу, а не про юрлицо с одной сделкой.
                present, missing = len(sig), 0
            # Больше значимых слов совпало — точнее; потом точное совпадение
            # слова, а не падежное; потом сколько слов полного имени есть в
            # вопросе («МТС Банк» — не «МТС»); при равенстве — у кого сделок больше.
            score = (len(sig), exact, present, -missing, n_deals)
            if best is None or score > best[0]:
                best = (score, cid, matched_terms)
    return (best[1], best[2]) if best else None


def _detect_companies(question: str, idx: Index, terms: list[str], limit: int = 3) -> list[str]:
    """Все компании, названные в вопросе, — для сравнения. `_detect_company`
    возвращает одну, самую уверенную, и «Сравни Сбербанк и ВТБ» теряло ВТБ
    молча. Здесь вопрос режется по союзам и каждая часть узнаётся отдельно:
    так обе стороны попадают в ответ, а порядок сохраняется тот, в котором
    их назвал человек."""
    parts = [p.strip() for p in re.split(r"\s+(?:и|или|против|vs\.?|c|с)\s+|[,;]", question) if p.strip()]
    found: list[str] = []
    evident = _evident_words(question)
    for part in parts:
        hit = _detect_company(part, idx, query_terms(part) + short_name_terms(part), evident)
        if hit and hit[0] not in found:
            found.append(hit[0])
        if len(found) >= limit:
            break
    return found


def _industry_covers(token: str) -> bool:
    tn = norm(token)
    for hints in INDUSTRY_HINTS.values():
        for h in hints:
            hn = norm(h)
            if " " in hn:
                continue
            if _hint_hit(tn, hn):
                return True
    return False


def _without_firm_name(question: str, firm: Firm) -> str:
    """Вопрос без слов, которыми названа фирма (по регулярке каталога и по
    самим словам имени в любом падеже)."""
    text = firm.rx.sub(" ", question)
    name_words = [w for w in tokens(firm.name) if len(w) >= 4]
    kept = [w for w in re.split(r"(\s+)", text)
            if not any(_declension_match(norm(w).strip("«»\"()"), nw) or norm(w).strip("«»\"()") == nw for nw in name_words)]
    return "".join(kept)


# ВОПРОС О САМОМ СЕРВИСЕ. 7 октября 2026 посетитель спросил «Чем мы
# можете ьыть полезны для меня» (опечатки — его), получил от модели отказ
# «могу помочь только информацией о сделках…» и пояснил кнопкой «нет»:
# «Пытаюсь понять пользу от сервиса». Владелец: «нужно чтобы пользователям
# полезно отвечало на вопрос, что может сервис, лаконично, что классного у
# нас есть». Ответ на такой вопрос не зависит ни от базы, ни от модели —
# поэтому он готовый, мгновенный и одинаковый (`about_answer`), а модель к
# нему не подключается. Признаки — только те, где подлежащее «вы / ты /
# сервис / Компас»: «чем полезна сделка для Сбербанка» сюда не попадает.
_SERVICE = r"(?:вы|ты|мы|вас|тебя|сервис\w*|компас\w*|ассистент\w*|бот\w*|сайт\w*|платформ\w*|проект\w*)"
ABOUT_WORDS = [re.compile(rx) for rx in (
    rf"\bчем\s+{_SERVICE}\b.{{0,40}}?\b(?:полез\w*|помо[чж]\w*|пригод\w*)",
    r"\bчем\s+(?:\w+\s+){0,3}?(?:полез\w*|помо[чж]\w*|пригод\w*)\s+(?:\w+\s+)?"
    r"(?:компас\w*|«компас»|сервис\w*|ассистент\w*|платформ\w*|бот|вы|ты)\b",
    r"\bчем\s+(?:вы|ты)\s+(?:занимаетесь|занимаешься)\b",
    r"^(?:а\s+)?что\s+(?:ты|вы)\s+(?:умеешь|умеете|можешь|можете)(?:\s+(?:делать|сделать|предложить))?\s*[?!.]*$",
    r"\bчто\s+(?:умеет|может)\s+(?:этот\s+)?(?:сервис|компас|ассистент|бот|сайт)\w*",
    r"\bчто\s+(?:это\s+)?за\s+(?:сервис|сайт|проект|платформ\w*|бот)\b",
    r"\bчто\s+такое\s+(?:«?компас»?|этот\s+(?:сервис|сайт))",
    r"\bпольз(?:а|у|ы)\s+(?:от|для)\s+(?:вас|тебя|сервиса|компаса|сайта|ассистента|меня)\b",
    r"^(?:а\s+)?(?:в\s+чем|какая)\s+(?:тут\s+|здесь\s+)?польза\s*[?!.]*$",
    r"\bкак\s+(?:тобой|вами|сервисом|компасом|сайтом|ассистентом)\s+пользоваться",
    # «Как пользоваться Компасом?» — отказ модели вместо рассказа о сервисе (№88).
    r"\bкак\s+(?:мне\s+)?(?:пользоваться|работать)\s+(?:с\s+)?(?:«?компас\w*»?|сервис\w*|сайт\w*|ассистент\w*"
    r"|платформ\w*|тобой|вами|этим\s+(?:сервисом|сайтом))",
    r"^(?:а\s+)?как\s+(?:этим\s+|здесь\s+|тут\s+)?пользоваться\s*[?!.]*$",
    r"\bрасскажи(?:те)?\s+(?:о|про)\s+(?:себе|сервисе|компасе|сайте|проекте|ваших\s+возможностях|свои\s+возможности)\b",
    r"\bвозможност\w*\s+(?:сервиса|компаса|ассистента|сайта|платформы)\b",
    r"^(?:а\s+)?(?:кто|что)\s+(?:ты|вы)(?:\s+такой|\s+такая|\s+такие|\s+такое)?\s*[?!.]*$",
    r"\b(?:зачем|для\s+чего)\s+(?:мне\s+)?(?:нужен\s+|нужна\s+)?(?:этот\s+|эта\s+)?(?:сервис|компас|сайт|ассистент|платформа)\b",
    r"^что\s+(?:здесь|тут)\s+(?:можно\s+(?:делать|найти|узнать)|есть)\s*[?!.]*$",
    r"^(?:привет\w*|здравствуй\w*|добрый\s+(?:день|вечер)|доброе\s+утро|hi|hello)[\s!.,)]*$",
)]


def about_service(question: str) -> bool:
    """Вопрос о самом «Компасе»: что умеет, чем полезен, как пользоваться."""
    q = re.sub(r"\s+", " ", norm(question)).strip()
    return bool(q) and any(rx.search(q) for rx in ABOUT_WORDS)


def about_answer(idx: Index | None = None) -> str:
    """Короткий рассказ о сервисе. Число сделок — из базы, вниз до сотен:
    лоты, выставленные на торги и не купленные, сделками не считаются (как
    в «Аналитике»). Примеры вопросов — кнопками под ответом
    (`FOLLOW_UPS.about` в static/index.html), не строкой текста."""
    idx = idx or get_index()
    n = sum(1 for d in idx.docs if not (d.type == "Продажа с торгов" and d.status != "Закрыта"))
    return "\n".join([
        f"«Компас» — база сделок M&A на российском рынке: больше {n // 100 * 100} сделок с 2022 года, "
        "у каждой — ссылки на источники.",
        "",
        "- **[Сделки](#/deals)** — кто купил, у кого, за сколько, на каком этапе и кто консультировал.",
        "- **[Компании](#/companies)** — все сделки компании и её финансы по данным ФНС, "
        "у банков — по данным Банка России.",
        "- **[Консультанты](#/advisors)** — какие сделки вели юрфирмы и инвестконсультанты.",
        "- **[Аналитика](#/analytics)** — рынок по годам и отраслям, крупнейшие сделки, мультипликаторы.",
        "- **Подписки** — уведомления о новых сделках компании или отрасли (в [личном кабинете](#/account)).",
        "- **Ассистент** — найдёт сделки по компании, отрасли или условию, сравнит компании, "
        "поможет подготовиться ко встрече или к собеседованию. Вы уже тут :)",
    ])


def _hint_covers(token: str, region: str | None) -> bool:
    """Слово вопроса уже прочитано как отрасль, тема или регион."""
    if _industry_covers(token):
        return True
    tn = norm(token)
    for hints in THEME_HINTS.values():
        for h in hints:
            hn = norm(h)
            if " " not in hn and ((tn == hn) if len(hn) <= 3 else tn.startswith(hn)):
                return True
    return bool(region and re.search(REGION_HINTS[region], tn))


def route(question: str, idx: Index | None = None) -> Intent:
    idx = idx or get_index()
    terms = query_terms(question)
    words = query_words(question)
    span = period_in(question)
    year = span_single(span)
    firm = _detect_firm(question, idx)
    # Слова из имени фирмы не должны читаться как отрасль: «Никольская
    # консалтинг» узнавалась фирмой, а «консалтинг» — отраслью, и список её
    # сделок фильтровался по отрасли до нуля (владелец 31 августа 2026:
    # «у Никольской вообще-то есть 2 сделки»).
    rank = _detect_rank(question)
    # «Какой инвестбанк чаще всего выступал ФИНАНСОВЫМ консультантом?» — слово
    # из предмета рейтинга не отрасль «Финансовые услуги» (№16).
    plain_q = question
    if rank in ("law", "invest", "advisors"):
        for kind, rx in RANK_SUBJECTS:
            if kind in ("law", "invest", "advisors"):
                plain_q = rx.sub(" ", plain_q)
    buyer_kind = "bank" if BANK_BUYER.search(question) else None
    if buyer_kind:
        # «банки» здесь — кто покупает, а не отрасль сделки
        plain_q = re.sub(_BANK, " ", plain_q, flags=re.I)
    industry = _detect_industry(_without_firm_name(plain_q, firm) if firm else plain_q, idx)
    themes = [t for t in _detect_themes(question) if t != industry]
    theme = themes[0] if themes else None
    term_rxs = _detect_terms(question)
    status = _detect_status(question)
    region = _detect_region(question)
    wants_adv = bool(ADVISOR_WORDS.search(question))
    wants_price = bool(PRICE_WORDS.search(question))
    finance = bool(FINANCE_WORDS.search(question))
    cond = dict(finance=finance, span=span, year=year, industry=industry, themes=themes, theme=theme, term_rxs=term_rxs,
                status=status, region=region, terms=terms, wants_price=wants_price, buyer_kind=buyer_kind,
                role=_detect_role(question))
    # Две фирмы в одном вопросе — обе («Сравни АЛРУД и ЕПАМ», №5).
    several_firms = _detect_firms(question, idx)
    if len(several_firms) >= 2:
        return Intent("compare_firms", firms=several_firms, firm=several_firms[0], **cond)
    # ИМЯ БЫВАЕТ И У КОНСУЛЬТАНТА, И У СТОРОНЫ СДЕЛОК. 22 сентября 2026 в
    # каталог консультантов добавили банки — Сбербанк, ВТБ, Газпромбанк,
    # Альфа-Банк: они действительно организуют размещения и консультируют.
    # Но покупают они куда чаще, чем консультируют: у Сбербанка 5 сделок как
    # у консультанта и 11 как у стороны. Вопрос «Сбербанк купил в 2025 году»
    # после добавления стал читаться как вопрос про консультанта — и вместо
    # покупок человек получал список сопровождённых сделок.
    #
    # Решает не список исключений, а счёт: если имя чаще называет СТОРОНУ,
    # чем консультанта, это вопрос про компанию — пока в самом вопросе не
    # спросили про сопровождение («кто консультировал», «юрфирма»).
    evident = _evident_words(question)
    found = _detect_company(question, idx, terms + short_name_terms(question), evident)
    if firm and not wants_adv:
        if found and len(idx.company_deals.get(found[0], ())) > _firm_deal_count(firm, idx):
            firm = None
    if firm:
        return Intent("advisor", firm=firm, wants_advisors=True, **cond)
    # «Что нового» — раньше всего: иначе слово «нового» узнаётся компанией
    # «Новосталь-М» по корню, и человек получает ответ не о том.
    company, matched = (found if found else (None, []))
    if company and matched and all(NEWS_WORDS.match(t) for t in matched):
        company = None                      # «Новости M&A» — не «Новосталь-М»
    news = False
    if NEWS_WORDS.search(question) and not company:
        # «Новости M&A» — что нового; «новости о Карпове» — поиск по имени.
        rest = [t for t in terms if not NEWS_WORDS.match(t)
                and not re.match(r"сделк|рынк|рынок|m&a|ma$|слияни|поглощени|вышл|появил|недел|месяц|свеж|последн", t)]
        news = not (rest and _search_is_specific(Intent("search", terms=rest), search(rest, idx), idx))
    if (RECENT_WORDS.search(question) or news) and not span:
        # Названная компания сужает свежие сделки до её сделок: «что нового у
        # Яндекса за неделю» — не лента всего рынка.
        recent_company = company if company and (len(set(matched)) >= 2 or any(
            t in evident or stem(t) in evident for t in matched)) else None
        return Intent("recent", days=30 if RECENT_MONTH.search(question) else 7,
                      industry=industry, terms=terms, company_id=recent_company)
    # Компанию узнали по слову, которое одновременно называет отрасль, тему
    # или регион («фарм», «банк», «агро»), и признака имени у него нет — это
    # вопрос про отрасль, а не про компанию. Имя из нескольких слов,
    # названное целиком («Московская биржа»), остаётся компанией.
    if company and matched and len(set(matched)) < 2 \
            and all(_hint_covers(t, region) for t in matched) \
            and not any(t in evident or stem(t) in evident for t in matched):
        company = None
    if buyer_kind and company and matched and all(re.match(r"банк", t) for t in matched):
        company = None
    if rank and not company:
        return Intent("rank", rank=rank, wants_advisors=rank in ("law", "invest", "advisors"), **cond)
    if COMPARE_WORDS.search(question):
        several = _detect_companies(question, idx, terms + short_name_terms(question))
        if len(several) >= 2:
            return Intent("compare", company_ids=several, **cond)
    if AVG_WORDS.search(question) and not company:
        return Intent("avg", **cond)
    if LARGEST_WORDS.search(question) and not wants_adv:
        return Intent("largest", company_id=company, matched=matched, **cond)
    is_count = bool(COUNT_WORDS.search(question)) and (bool(COUNT_STRICT.search(question)) or not wants_price)
    if is_count and not company:
        return Intent("count", **cond)
    if company:
        if not cond["role"] and _object_of_deal(question, matched):
            cond["role"] = "object"
        return Intent("company", company_id=company, wants_advisors=wants_adv, matched=matched, **cond)
    if term_rxs:
        return Intent("term", term_rx=term_rxs[0], **cond)
    if themes:
        return Intent("theme", **cond)
    # «Сколько может стоить пищевое производство?» — вопрос об уровне цен в
    # отрасли: средний и медианный размер сделки плюс сделки с ценой (№64).
    if wants_price and industry and not buyer_kind:
        return Intent("avg", **cond)
    if buyer_kind:
        return Intent("filter", wants_advisors=wants_adv, **cond)
    if industry:
        return Intent("industry", wants_advisors=wants_adv, **cond)
    if status or region:
        # «Когда закрылась сделка по Boxberry?» — про одну сделку, а не список
        # закрытых: слово статуса здесь вопрос о дате. Список — только когда
        # слова вопроса ни во что конкретное не попадают.
        rest = [t for t in terms if not (STATUS_FAILED.search(t) or STATUS_OPEN.search(t) or STATUS_CLOSED.search(t)
                                          or re.match(r"состо|закр|заверш|обсужд|сорв|отмен", t)
                                          or (region and re.search(REGION_HINTS[region], t)))]
        probe = Intent("search", terms=rest)
        if not (rest and _search_is_specific(probe, search(rest, idx), idx)):
            return Intent("filter", wants_advisors=wants_adv, **cond)
    if not terms:
        # Признаки вопроса нужны и пустому маршруту: со страницы компании «кто
        # консультировал сделки?» — это вопрос о консультантах этой компании.
        return Intent("empty", wants_advisors=wants_adv, **cond)
    return Intent("search", wants_advisors=wants_adv, words=words, **cond)


# --------------------------------------------------------------------------
# Поиск по словам (когда вопрос не про конкретную сущность)
# --------------------------------------------------------------------------

def _term_weight(term: str, idx: Index) -> float:
    """Вес слова вопроса: редкое в заголовках — отличительное, частое — фон."""
    total = max(1, len(idx.docs))
    n = sum(cnt for t, cnt in idx.df.items() if same_word(term, t))
    if n == 0:
        return 0.0
    if n <= 5:
        return 6.0
    if n <= 40:
        return 3.0
    if n <= 0.15 * total:
        return 1.0
    return 0.3


def search(terms: list[str], idx: Index, limit: int = MAX_DEALS_FOR_MODEL) -> list[Doc]:
    if not terms:
        return idx.docs[:limit]

    weights = {t: _term_weight(t, idx) for t in terms}
    scored = []
    for doc in idx.docs:
        score = 0.0
        for t in terms:
            w = weights[t]
            if not w:
                continue
            if any(same_word(t, s) for s in doc.strong):
                score += w
            elif any(same_word(t, s) for s in doc.weak):
                score += w * 0.4
        if score:
            scored.append((score, doc))
    if not scored:
        return []
    scored.sort(key=lambda x: (-x[0], x[1].date))
    # Точное попадание не должно тянуть за собой хвост из карточек, совпавших
    # одним фоновым словом: оставляем те, что набрали хотя бы половину от
    # лучшего результата (и не меньше одного веса «редкого» совпадения).
    top = scored[0][0]
    floor = max(1.0, top * 0.5)
    kept = [d for s, d in scored if s >= floor]
    return kept[:limit]


# --------------------------------------------------------------------------
# Точные ответы
# --------------------------------------------------------------------------

def _link(doc: Doc) -> str:
    return f"[{doc.title}](#/deal/{doc.id})"


def _fmt_date(ds: str) -> str:
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ds):
        y, m, d = ds.split("-")
        return f"{int(d)} {months[int(m) - 1]} {y}"
    if re.fullmatch(r"\d{4}-\d{2}", ds):
        y, m = ds.split("-")
        return f"{months[int(m) - 1]} {y}"
    return ds[:4]


def _date_phrase(doc: Doc) -> str:
    """Дата сделки словами — с оговоркой, если карточка датирована днём
    ПУБЛИКАЦИИ сообщения, а не самим закрытием (`date_basis == 'publication'`,
    Boxberry: Интерфакс 24 апреля 2025 сообщил о закрытии, точный день стороны
    не называли). Ответ «сделка закрыта 24 апреля» превращал бы дату новости
    в дату события (разбор рецензента, 6 сентября 2026)."""
    text = _fmt_date(doc.date)
    if doc.raw.get("date_basis") == "publication":
        return f"{text} (дата сообщения о закрытии; точный день закрытия не раскрывался)"
    return text


def _source_link(doc: Doc) -> str:
    """Первый внешний источник карточки — ссылкой рядом со сделкой. Экран
    ассистента обещает первоисточник в каждом ответе, а ответ «по базе» до
    5 сентября 2026 давал только ссылку на карточку «Компаса» (аудит перед
    бетой, вопрос про Boxberry). Ссылка на карточку и ссылка на источник —
    разные вещи, и читатель должен видеть обе."""
    for item in doc.raw.get("src") or []:
        if isinstance(item, list) and len(item) > 1 and str(item[1]).startswith("http"):
            label = str(item[0] or "источник").strip()
            return f" · [{label}]({item[1]})"
        if isinstance(item, str) and item.startswith("http"):
            return f" · [источник]({item})"
    return ""


def _line(doc: Doc) -> str:
    bits = [_fmt_date(doc.date)]
    if has_fact(doc.sum_text):
        bits.append(doc.sum_text)
    if doc.status:
        bits.append(doc.status.lower())
    return f"- {_link(doc)} — {', '.join(bits)}{_source_link(doc)}"


def _plural(n: int, one: str, few: str, many: str) -> str:
    a, b = n % 100, n % 10
    if 10 < a < 20:
        return many
    if 1 < b < 5:
        return few
    if b == 1:
        return one
    return many


def _filter(docs: list[Doc], year: Any = None, industry: str | None = None) -> list[Doc]:
    """Период (один год или диапазон `Span`) и отрасль. Отрасль совпадает и с
    темой того же имени: «Искусственный интеллект» в базе бывает и отраслью,
    и темой, и вопрос «венчур в ИИ» должен видеть обе (№25)."""
    span = (year, year) if isinstance(year, int) else year
    out = docs
    if span:
        out = [d for d in out if in_span(d.year, span)]
    if industry:
        out = [d for d in out if industry in d.industries or industry in d.themes]
    return out


VENTURE = "Венчур / раунд"


def _theme_ok(doc: Doc, theme: str) -> bool:
    """Тема вопроса у сделки. Тема с именем отрасли («Искусственный
    интеллект») засчитывается и по отрасли; «венчурные раунды» — это и тема
    «Венчур / раунд», и любая сделка типа «Инвестиция» (деньги в компанию):
    тема стоит у 19 сделок, а «венчурные раунды в ИИ» по базе — 8
    инвестиций в ИИ-компании, из которых тему несут две (вторая проверка, №25)."""
    if theme in doc.themes or theme in doc.industries:
        return True
    return theme == VENTURE and doc.type == "Инвестиция"


# Покупатель-банк (№80, «банки-покупатели»): «банк» в имени покупателя
# (Сбербанк Инвестиции, Газпромбанк-инвест — структуры банков) или банк без
# этого слова в имени (ВТБ, ПСБ) — в любой отрасли САМОЙ сделки. Отрасль
# «Банки» у сделки значит другое: что покупали банк. Отрасль профиля
# покупателя одна не годится: «Банки» стоят и у владельцев банков (Игорь Ким,
# Антон Пак, «АБ Холдинг»), а слово в скобках — у пояснения («структура
# совладельца банка «Хоум Кредит»»).
_BANK_NAME = re.compile(r"банк|bank", re.I)
_BANK_SHORT = re.compile(r"^(?:(?:ПАО|АО|Банк|Группа)\s+)?«?(?:ВТБ|ПСБ|МКБ|РНКБ|Тинькофф|ОТП)»?$", re.I)


def _buyer_is(doc: Doc, kind: str) -> bool:
    if kind != "bank":
        return True
    name = re.sub(r"\s*\([^)]*\)", "", doc.buyer or "").strip()
    return bool(name and (_BANK_NAME.search(name) or _BANK_SHORT.match(name)))


def _apply(intent: Intent, docs: list[Doc], industry: bool = True) -> list[Doc]:
    """ВСЕ условия вопроса разом: период, отрасль, темы, условия сделки,
    статус, регион. До 14 октября 2026 работало первое попавшееся условие, и
    «нефтегаз, которые обсуждаются» отдавало 12 последних сделок отрасли с
    заверением «список полон» (№29)."""
    out = _filter(docs, intent.span, intent.industry if industry else None)
    for th in intent.themes:
        out = [d for d in out if _theme_ok(d, th)]
    if intent.buyer_kind:
        out = [d for d in out if _buyer_is(d, intent.buyer_kind)]
    for rx in intent.term_rxs:
        r = re.compile(rx, re.I)
        out = [d for d in out if r.search(d.facts) or r.search(d.title)]
    if intent.status:
        out = [d for d in out if _status_ok(d, intent.status)]
    if intent.region:
        r = re.compile(REGION_HINTS[intent.region])
        out = [d for d in out if r.search(d.blob)]
    return out


def _scope_text(intent: Intent, industry: bool = True, period: bool = True) -> str:
    """Чем ограничена выборка — словами, с ведущим пробелом."""
    bits = []
    if intent.status:
        bits.append({"closed": "— только закрытые", "open": "— только ещё не закрытые",
                     "failed": "— только не состоявшиеся"}[intent.status])
    if period and intent.span:
        bits.append(period_text(intent.span).strip())
    if industry and intent.industry:
        bits.append(f"в отрасли «{intent.industry}»")
    if intent.themes:
        bits.append("по теме " + " и ".join(f"«{t}»" for t in intent.themes))
    if intent.term_rxs:
        labels = []
        for rx in intent.term_rxs:
            lab = TERM_LABELS.get(rx, "условие из вопроса")
            if lab not in labels:
                labels.append(lab)
        bits.append("с условием: " + ", ".join(labels))
    if intent.region:
        bits.append(f"с упоминанием региона «{intent.region}»")
    if intent.buyer_kind == "bank":
        bits.append("с покупателем-банком")
    return (" " + " ".join(bits)) if bits else ""


def _role_bucket(role: str) -> str | None:
    """Роль консультанта в карточке записана вольно («Юридический консультант
    покупателя (X5 Group)», «Продавец — ООО «Агрострой»»). Для ответа человеку
    нужна одна из нескольких понятных ролей, а не сырая строка."""
    r = norm(role)
    if not r:
        return None
    if "покупател" in r or "инвестор" in r or "приобретател" in r:
        return "консультант покупателя"
    if "продавц" in r or "продавец" in r:
        return "консультант продавца"
    if "эмитент" in r or "размещен" in r or "андеррайт" in r:
        return "консультант при размещении акций"
    if "финансов" in r:
        return "финансовый консультант"
    if "юридическ" in r or "консультант" in r:
        return "юридический консультант"
    return None


def _firm_counts(docs: list[Doc], idx: Index, kinds: set[str] | None = None) -> list[tuple[Firm, int]]:
    """Сколько сделок из `docs` сопровождала каждая фирма каталога — тем же
    правилом, что страница «Консультанты» (firmDeals в index.html: регулярка
    фирмы по консультантам и финконсультанту карточки)."""
    ids = {d.id for d in docs}
    out = []
    for f in idx.firms:
        if kinds is not None and f.kind not in kinds:
            continue
        n = sum(1 for d in idx.firm_deals.get(f.id) or [] if d.id in ids)
        if n:
            out.append((f, n))
    out.sort(key=lambda x: (-x[1], x[0].name.lower()))
    return out


def _advisor_stats(docs: list[Doc], idx: Index) -> list[tuple[str, int]]:
    """Какие фирмы названы консультантами в этих сделках — по каталогу, а не
    по сырому тексту: одна фирма пишется по-разному («Orion», «Orion Law»).
    Рядом с именем — кто это: юрфирма, банк, брокер по недвижимости; без
    пометки модель называла IBC и Nikoliers юрфирмами (№6)."""
    return [(f"{f.name} ({f.kind_label})", n) for f, n in _firm_counts(docs, idx)[:8]]


@dataclass
class Retrieval:
    intent: str
    answer: str | None          # точный ответ по базе (markdown) или None, если сказать нечего
    docs: list[Doc]             # что уходит модели
    subject: str | None = None  # о ком/о чём — для заголовка диалога
    # Вся выборка ответа, а не дюжина для модели: уточнение «а какие из них
    # самые крупные?» ищет внутри неё (см. `_refine`).
    pool: list[Doc] = field(default_factory=list)

    def deal_ids(self) -> list[str]:
        return [d.id for d in self.docs]


NOTE_ADVISORS = ("Считаются сделки, где фирма названа консультантом в открытых источниках; "
                 "фирмы раскрывают не все проекты.")
NOTE_SUMS = "Сумма известна не у всех сделок: цену в России раскрывают меньше чем в половине случаев."
NOTE_PARTIAL = ("Здесь показана часть списка; если в нём нет нужной сделки, это не значит, что её нет "
                "в «Компасе» — полный список по ссылке.")


def _answer_advisor(intent: Intent, idx: Index) -> Retrieval:
    firm = intent.firm
    docs = _apply(intent, idx.firm_deals.get(firm.id) or [])
    scope = _scope_text(intent)
    if not docs:
        text = (f"В «Компасе» пока нет сделок{scope}, где [{firm.name}](#/advisors/{firm.id}) названа "
                f"консультантом: фирма есть в каталоге, но её проекты в открытых источниках не встретились. "
                f"{NOTE_ADVISORS} Каталог фирмы: [{firm.name}](#/advisors/{firm.id}).")
        return Retrieval("advisor", text, [], firm.name)
    n = len(docs)
    inds = Counter(i for d in docs for i in d.industries).most_common(4)
    roles = Counter(b for d in docs for r, name in d.advisor_roles
                    if firm.rx.search(name) and (b := _role_bucket(r))).most_common(3)
    head = (f"Консультант [{firm.name}](#/advisors/{firm.id}) ({firm.kind_label}) в «Компасе»: {n} "
            f"{_plural(n, 'сделка', 'сделки', 'сделок')}{scope}.")
    lines = [head]
    if inds:
        lines.append("Отрасли: " + ", ".join(f"{i} ({c})" for i, c in inds) + ".")
    if roles:
        lines.append("Чаще всего в роли: " + ", ".join(f"{r.lower()} ({c})" for r, c in roles) + ".")
    lines.append("Последние:")
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED} — все на [странице фирмы](#/advisors/{firm.id}).")
    lines.append(NOTE_ADVISORS)
    return Retrieval("advisor", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], firm.name, pool=docs)


def _answer_compare_firms(intent: Intent, idx: Index) -> Retrieval:
    """Две-три фирмы рядом: сколько сделок, отрасли, последние сделки."""
    blocks: list[str] = []
    docs: list[Doc] = []
    for firm in intent.firms:
        own = _apply(intent, idx.firm_deals.get(firm.id) or [])
        link = f"[{firm.name}](#/advisors/{firm.id})"
        if not own:
            blocks.append(f"**{link}** ({firm.kind_label}) — в «Компасе» нет сделок{_scope_text(intent)}, "
                          "где фирма названа консультантом.")
            continue
        n = len(own)
        inds = Counter(i for d in own for i in d.industries).most_common(3)
        block = [f"**{link}** ({firm.kind_label}) — {n} {_plural(n, 'сделка', 'сделки', 'сделок')}{_scope_text(intent)}"
                 + (f"; отрасли: {', '.join(f'{i} ({c})' for i, c in inds)}" if inds else "") + ". Последние:"]
        block += [_line(d) for d in own[:4]]
        if n > 4:
            block.append(f"…и ещё {n - 4} — на [странице фирмы](#/advisors/{firm.id}).")
        blocks.append("\n".join(block))
        docs += own[:6]
    names = " и ".join(f.name for f in intent.firms)
    lines = [f"{names} — рядом по сделкам в «Компасе»:"] + blocks + [NOTE_ADVISORS]
    return Retrieval("advisor", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], names)


def _company_pool(intent: Intent, idx: Index) -> list[Doc]:
    docs = idx.company_deals.get(intent.company_id) or []
    docs = _filter(docs, intent.span, None)
    if intent.status:
        docs = [d for d in docs if _status_ok(d, intent.status)]
    return sorted(docs, key=lambda d: d.date, reverse=True)


def _answer_company(intent: Intent, idx: Index) -> Retrieval:
    cid = intent.company_id
    name = _company_name(idx.companies, cid)
    docs = _company_pool(intent, idx)
    scope = _scope_text(intent, industry=False)
    # Тема, названная в самом имени («Венчурный фонд «Восход»»), — это имя,
    # а не условие отбора (№26).
    name_norm = norm(name)
    themes = [th for th in intent.themes
              if not any(len(h) > 3 and norm(h) in name_norm for h in THEME_HINTS.get(th, []))]
    scope = _scope_text(Intent("filter", span=intent.span, status=intent.status), industry=False)
    if themes or intent.term_rxs or intent.region:
        # Тема и условие сужают список компании, но не до пустого.
        narrowed = _apply(Intent("filter", themes=themes, term_rxs=intent.term_rxs, region=intent.region), docs)
        if narrowed:
            docs = narrowed
        scope = _scope_text(Intent("filter", span=intent.span, status=intent.status,
                                   themes=themes if narrowed else [],
                                   term_rxs=intent.term_rxs if narrowed else []), industry=False)
    fin = ("Выручку и прибыль ассистент не видит: отчётность по данным ФНС — на "
           f"[странице компании](#/companies/{cid}), если она там есть." if intent.finance else "")
    if not docs:
        text = f"У компании [{name}](#/companies/{cid}) в «Компасе» нет сделок" + scope + "."
        return Retrieval("company", (fin + "\n" + text) if fin else text, [], name)
    n = len(docs)
    # «Сделка Яндекса с Uber» — вопрос про одну сделку компании, а не про
    # весь список: слова вопроса сверх имени компании отбирают подходящие.
    name_stems = [stem(t) for t in tokens(name)]
    extra = [t for t in intent.terms
             if t not in intent.matched and not t.isdigit() and not any(same_word(t, s) for s in name_stems)
             and not _plain_word(t, idx)]
    picked = [d for d in docs if extra and any(
        any(_name_word_match(s, t) for s in d.strong) or any(same_word(t, s) for s in d.weak) for t in extra)]
    if n == 1:
        single = _answer_deal(docs[0])
        total = len(_company_pool(intent, idx))
        tail = (f"Это единственная сделка компании [{name}](#/companies/{cid}) в «Компасе»{period_text(intent.span)}."
                if total == 1 else f"Всего у компании [{name}](#/companies/{cid}) в «Компасе» {total} "
                f"{_plural(total, 'сделка', 'сделки', 'сделок')}{period_text(intent.span)}.")
        return Retrieval("company", single.answer + "\n" + tail, docs, name, pool=docs)
    if intent.role == "object":
        words = [t for t in intent.terms if t not in intent.matched and not t.isdigit()
                 and not any(same_word(t, s) for s in name_stems)]
        own = _object_answer(intent, idx, cid, name, docs, words, scope)
        if own:
            return own
    elif intent.role and not (picked and len(picked) < n):
        own = _role_answer(intent, idx, cid, name, docs, scope)
        if own:
            return own
    if picked and len(picked) < n:
        k = len(picked)
        if k == 1:
            # Одна конкретная сделка компании — сводка с этапами и источником,
            # а не строка списка: «Когда Яндекс приобрёл Boxberry?» спрашивает
            # про даты, и они лежат в этапах (аудит, раунд 2).
            single = _answer_deal(picked[0])
            tail = (f"Всего у компании [{name}](#/companies/{cid}) в «Компасе» {n} "
                    f"{_plural(n, 'сделка', 'сделки', 'сделок')}{scope}.")
            rest = [d for d in docs if d not in picked]
            return Retrieval("company", single.answer + "\n" + tail, (picked + rest)[:MAX_DEALS_FOR_MODEL], name,
                             pool=picked + rest)
        lines = [f"По вопросу {'подходит' if k == 1 else 'подходят'} {k} "
                 f"{_plural(k, 'сделка', 'сделки', 'сделок')} компании [{name}](#/companies/{cid}):"]
        lines += [_role_line(d, cid) for d in picked[:MAX_LISTED]]
        if k > MAX_LISTED:
            lines.append(f"…и ещё {k - MAX_LISTED}.")
        lines.append(f"Всего у компании в «Компасе» {n} {_plural(n, 'сделка', 'сделки', 'сделок')}"
                     + scope + f" — на [странице компании](#/companies/{cid}).")
        rest = [d for d in docs if d not in picked]
        docs = picked + rest
    else:
        lines = [f"Компания [{name}](#/companies/{cid}) в «Компасе»: {n} {_plural(n, 'сделка', 'сделки', 'сделок')}"
                 + scope + _roles_text(docs, cid) + ":"]
        lines += [_role_line(d, cid) for d in docs[:MAX_LISTED]]
        if n > MAX_LISTED:
            lines.append(f"…и ещё {n - MAX_LISTED} — на [странице компании](#/companies/{cid}).")
    if n > 2:
        st = Counter((d.status or "без статуса").lower() for d in docs)
        lines.append("По этапам: " + ", ".join(f"{k} — {v}" for k, v in st.most_common()) + ". "
                     f"Сумма названа у {sum(1 for d in docs if has_fact(d.sum_text))} из {n}.")
    if intent.wants_advisors:
        stats = _advisor_stats(docs, idx)
        if stats:
            lines.append("Консультанты, названные в этих сделках: " + ", ".join(f"{f} ({c})" for f, c in stats) + ".")
        else:
            lines.append("Консультанты в этих сделках публично не назывались.")
    if intent.wants_price:
        priced = [d for d in docs if has_fact(d.sum_text)]
        if priced:
            lines.append("Суммы: " + "; ".join(f"{d.title} — {d.sum_text}" for d in priced[:MAX_LISTED]) + ".")
    if fin:
        lines.insert(0, fin)
    return Retrieval("company", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], name, pool=docs)


ROLE_WORDS = {"buyer": ("покупатель", "Покупки", "покупок"), "seller": ("продавец", "Продажи", "продаж")}


def _roles_text(docs: list[Doc], cid: str) -> str:
    """« (покупатель — 6, продавец — 2)» — по ссылкам карточек."""
    cnt = Counter(_role(d, cid) or "участник" for d in docs)
    order = ("покупатель", "продавец", "предмет сделки", "участник")
    bits = [f"{r} — {cnt[r]}" for r in order if cnt.get(r)]
    return f" ({', '.join(bits)})" if bits and bits != [f"участник — {len(docs)}"] else ""


def _object_answer(intent: Intent, idx: Index, cid: str, name: str, docs: list[Doc], extra: list[str],
                   scope: str) -> Retrieval | None:
    """«Кто консультировал продажу Яндекса консорциуму?» — сделки, где
    компания продавец или предмет, первыми; среди них — где есть другие
    слова вопроса («консорциум»), даже обычные. Одна такая — сводка по ней."""
    sold = [d for d in docs if _role(d, cid) in ("предмет сделки", "продавец")]
    if not sold:
        return None

    def hits(d: Doc) -> int:
        text = norm(d.title + " " + " ".join([d.buyer, d.seller, d.target, d.asset]))
        words = set(tokens(text))
        return sum(1 for t in extra if len(t) >= 4 and any(w.startswith(t[:max(5, len(t) - 2)]) for w in words))

    best = max(hits(d) for d in sold)
    top = [d for d in sold if best and hits(d) == best]
    # предмет — раньше продавца: «продажа Яндекса» — это продажа самого Яндекса
    sold.sort(key=lambda d: (-hits(d), _role(d, cid) != "предмет сделки"))
    rest = [d for d in docs if d not in sold]
    n = len(docs)
    total = (f"Всего у компании [{name}](#/companies/{cid}) в «Компасе» {n} "
             f"{_plural(n, 'сделка', 'сделки', 'сделок')}{scope}.")
    if len(top) == 1:
        single = _answer_deal(top[0])
        others = [d for d in sold if d is not top[0]]
        tail = [total]
        if others:
            tail.insert(0, "Другие сделки, где компанию продавали или она продавала свой бизнес: "
                        + "; ".join(_link(d) for d in others[:4]) + ("…" if len(others) > 4 else "") + ".")
        ordered = [top[0]] + others + rest
        return Retrieval("company", single.answer + "\n" + "\n".join(tail), ordered[:MAX_DEALS_FOR_MODEL], name,
                         pool=ordered)
    k = len(sold)
    shown = top if top and len(top) < k else sold
    if shown is top:
        lines = [f"По вопросу подходят {len(top)} из {k} сделок, где [{name}](#/companies/{cid}) — "
                 f"предмет сделки или продавец{scope}:"]
    else:
        lines = [f"Сделки, где [{name}](#/companies/{cid}) — предмет сделки или продавец{scope}: {k}:"]
    lines += [_role_line(d, cid) for d in shown[:MAX_LISTED]]
    if len(shown) > MAX_LISTED:
        lines.append(f"…и ещё {len(shown) - MAX_LISTED}.")
    if intent.wants_advisors:
        stats = _advisor_stats(sold, idx)
        lines.append("Консультанты, названные в этих сделках: " + ", ".join(f"{f} ({c})" for f, c in stats) + "."
                     if stats else "Консультанты в этих сделках публично не назывались.")
    lines.append(total)
    ordered = sold + rest
    return Retrieval("company", "\n".join(lines), ordered[:MAX_DEALS_FOR_MODEL], name, pool=ordered)


def _role_answer(intent: Intent, idx: Index, cid: str, name: str, docs: list[Doc], scope: str) -> Retrieval | None:
    """«Что покупала S8 Capital?» — покупки компании, а её продажи отдельно и
    подписаны как продажи. До второй проверки на 100 вопросах все восемь
    сделок шли одним списком, и модель записала в покупки две продажи
    «Кордианта» и завода Bosch «Севергрупп» (№27)."""
    want = ROLE_WORDS[intent.role][0]
    other_key = "seller" if intent.role == "buyer" else "buyer"
    mine = [d for d in docs if _role(d, cid) == want]
    other = [d for d in docs if _role(d, cid) == ROLE_WORDS[other_key][0]]
    rest = [d for d in docs if d not in mine and d not in other]
    link = f"[{name}](#/companies/{cid})"
    n = len(docs)
    total = f"Всего у компании в «Компасе» {n} {_plural(n, 'сделка', 'сделки', 'сделок')}{scope} — на [странице компании](#/companies/{cid})."
    if not mine:
        lines = [f"Сделок, где {link} — {want}{scope}, в «Компасе» нет. "
                 f"Сделки компании в других ролях — {n}" + _roles_text(docs, cid) + ":"]
        lines += [_role_line(d, cid) for d in docs[:MAX_LISTED]]
        if n > MAX_LISTED:
            lines.append(f"…и ещё {n - MAX_LISTED} — на [странице компании](#/companies/{cid}).")
        return Retrieval("company", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], name, pool=docs)
    k = len(mine)
    lines = [f"{ROLE_WORDS[intent.role][1]} компании {link} в «Компасе»{scope}: {k} "
             f"{_plural(k, 'сделка', 'сделки', 'сделок')}, где компания — {want}:"]
    lines += [_role_line(d, cid) for d in mine[:MAX_LISTED]]
    if k > MAX_LISTED:
        lines.append(f"…и ещё {k - MAX_LISTED}.")
    if other:
        o_word = ROLE_WORDS[other_key]
        lines.append(f"Отдельно — {o_word[1].lower()} (компания — {o_word[0]}), {len(other)}:")
        lines += [_role_line(d, cid) for d in other[:3]]
        if len(other) > 3:
            lines.append(f"…и ещё {len(other) - 3}.")
    if rest:
        lines.append(f"Ещё {len(rest)} {_plural(len(rest), 'сделка', 'сделки', 'сделок')}, где компания — предмет сделки "
                     "или участник: " + "; ".join(_link(d) for d in rest[:3]) + ("…" if len(rest) > 3 else "") + ".")
    lines.append(total)
    if intent.wants_price:
        priced = [d for d in mine if has_fact(d.sum_text)]
        if priced:
            lines.append("Суммы: " + "; ".join(f"{d.title} — {d.sum_text}" for d in priced[:MAX_LISTED]) + ".")
    ordered = mine + other + rest
    return Retrieval("company", "\n".join(lines), ordered[:MAX_DEALS_FOR_MODEL], name, pool=ordered)


def _list_answer(kind: str, intent: Intent, idx: Index, pool: list[Doc], head: str,
                 link: str | None, subject: str | None) -> Retrieval:
    n = len(pool)
    lines = [head]
    if not intent.span or intent.span[0] != intent.span[1]:
        by_year = Counter(d.year for d in pool)
        if len(by_year) > 1:
            lines.append("По годам: " + ", ".join(f"{y} — {c}" for y, c in sorted(by_year.items())) + ".")
    if intent.wants_advisors:
        stats = _advisor_stats(pool, idx)
        named = sum(1 for d in pool if d.advisors)
        if stats:
            lines.append(f"Консультанты названы у {named} из них. Чаще других: "
                         + ", ".join(f"{f} ({c})" for f, c in stats) + ".")
        else:
            lines.append("Ни у одной из этих сделок консультанты публично не назывались.")
        lines.append(NOTE_ADVISORS)
    if intent.buyer_kind == "bank":
        buyers = Counter(d.buyer for d in pool if d.buyer).most_common(8)
        if buyers:
            lines.append("Банки-покупатели: " + ", ".join(f"{b} — {c}" for b, c in buyers)
                         + (" и другие." if len({d.buyer for d in pool}) > 8 else "."))
    if intent.wants_price:
        lines += _price_lines(pool, intent)
    # Лоты, выставленные на торги и ещё не купленные, на сайте не сделки. В
    # недвижимости их больше половины свежих карточек, и «сделки в девелопменте
    # в 2026 году» показывали шесть лотов подряд (№79 третьей проверки):
    # первыми — сделки, лоты — следом и с пометкой.
    lots = [d for d in pool if d.listing]
    if lots and len(lots) < n and "Продажа с торгов" not in intent.themes:
        lines.append(f"Из них {len(lots)} — объекты, выставленные на торги и ещё не проданные; "
                     "они идут после сделок.")
        pool = [d for d in pool if not d.listing] + lots
    lines.append("Последние сделки:" if n > MAX_LISTED else "Сделки:")
    lines += [_line(d) for d in pool[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED}" + (f" — {link}." if link else "."))
    return Retrieval(kind, "\n".join(lines), pool[:MAX_DEALS_FOR_MODEL], subject, pool=pool)


def _answer_industry(intent: Intent, idx: Index) -> Retrieval:
    ind = intent.industry
    docs = _apply(intent, idx.docs)
    scope = _scope_text(intent, industry=False)
    if not docs:
        return Retrieval("industry", f"В отрасли «{ind}» в базе пока нет сделок{scope}.", [], ind)
    n = len(docs)
    head = (f"В отрасли [{ind}](#/industry/{ind}) в базе «Компаса» {n} "
            f"{_plural(n, 'сделка', 'сделки', 'сделок')}{scope}.")
    return _list_answer("industry", intent, idx, docs, head, f"на [странице отрасли](#/industry/{ind})", ind)


def _is_offering(doc: Doc) -> bool:
    """Само размещение акций (IPO, SPO, pre-IPO раунд), а не покупка, рядом
    с которой упомянуто чьё-то IPO."""
    return doc.type == "IPO" or bool(re.search(r"\bipo\b|\bspo\b|размещени", norm(doc.title)))


def _offering_lines(pool: list[Doc]) -> list[str]:
    """Суммы у IPO — объём размещения, а не цена сделки. «Какие IPO прошли
    и на какие суммы?» отвечало ценой покупки ЦОДа Ростелекомом (26,3 млрд ₽)
    как «самой крупной» (вторая проверка, №18): у IPO нет цены, названной
    сторонами, и `_price_lines` видела только посторонние покупки."""
    offers = [d for d in pool if _is_offering(d)]
    others = len(pool) - len(offers)
    if not offers:
        return [f"Самих размещений акций среди этих {len(pool)} сделок нет."]
    named = sorted([d for d in offers if has_fact(d.sum_text)], key=lambda d: -(d.sum_rub or 0))
    out = [f"Размещений акций (IPO, SPO, pre-IPO) среди них — {len(offers)}; объём размещения назван у {len(named)}"
           + (":" if named else ".")]
    out += [f"- {_link(d)} — {d.sum_text}, {_fmt_date(d.date)}" for d in named[:MAX_LISTED]]
    if len(named) > MAX_LISTED:
        out.append(f"…и ещё {len(named) - MAX_LISTED} с названным объёмом.")
    if others:
        out.append(f"Остальные {others} {_plural(others, 'сделка', 'сделки', 'сделок')} темы — покупки и инвестиции, "
                   "связанные с размещением; их суммы — не объём размещения.")
    return out


def _price_lines(pool: list[Doc], intent: Intent | None = None) -> list[str]:
    """Что известно о ценах выборки — посчитано здесь, а не моделью."""
    if intent is not None and "IPO / SPO" in intent.themes:
        return _offering_lines(pool)
    with_sum = [d for d in pool if d.sum_rub]
    est = [d for d in with_sum if d.estimate]
    priced = [d for d in pool if d.price_rub]
    if not with_sum:
        return [f"Сумма не названа ни у одной из этих {len(pool)} {_plural(len(pool), 'сделки', 'сделок', 'сделок')}."]
    out = [f"Сумма в рублях есть у {len(with_sum)} из {len(pool)}"
           + (f" (у {len(est)} из них — оценка экспертов, а не цена сторон)" if est else "") + "."]
    if priced:
        vals = sorted(d.price_rub for d in priced)
        out.append(f"По ценам, которые назвали стороны ({len(priced)} {_plural(len(priced), 'сделка', 'сделки', 'сделок')}): "
                   f"в сумме {_fmt_rub(sum(vals))}, медиана {_fmt_rub(_median(vals))}, "
                   f"самая крупная — {_fmt_rub(vals[-1])}.")
    return out


NOTE_LARGEST = ("Как в списке «Крупнейшие покупки» на странице [Аналитика](#/analytics), сюда не входят "
                "обсуждаемые сделки и объекты, только выставленные на продажу, выкуп компанией собственных "
                "акций, деньги в компанию (допэмиссии, раунды), финансирование и оценки экспертов.")


def _role(doc: Doc, cid: str | None) -> str | None:
    """Кем компания была в сделке — по ссылкам карточки, а не по имени."""
    raw = doc.raw or {}
    if not cid:
        return None
    if raw.get("buyer") == cid:
        return "покупатель"
    if raw.get("seller_id") == cid:
        return "продавец"
    if cid in (raw.get("target"), raw.get("asset_id")):
        return "предмет сделки"
    return None


def _role_line(doc: Doc, cid: str | None) -> str:
    """Строка списка с ролью компании: «… — 27 декабря 2022, 340 млрд ₽,
    закрыта (компания — покупатель)»."""
    line = _line(doc)
    role = _role(doc, cid)
    if role and cid:
        line = line.replace(_source_link(doc), "") + f" (компания — {role}){_source_link(doc)}"
    return line


def _answer_largest(intent: Intent, idx: Index) -> Retrieval:
    """Крупнейшие сделки — тем же отбором, что «Крупнейшие покупки» на
    странице «Аналитика» (facts.admitted.top_purchases): покупка, цена
    названа сторонами и сверена с источником, сделка не обсуждается и не лот
    на торгах. До второй проверки на 100 вопросах (октябрь 2026) список
    строился по любой сумме в рублях, и крупнейшей сделкой с 2022 года
    выходил выкуп «Полюсом» собственных акций, а в топ-10 2025 года стояли
    выставленный на продажу небоскрёб, допэмиссия и «объём инвестиций в
    проект» (№13, 33, 57). Если сверенных цен в выборке мало — следом идут
    такие же покупки с ценой, которую стороны назвали, но мы ещё не сверили,
    отдельным блоком и с этой пометкой."""
    cid = intent.company_id
    base = _company_pool(intent, idx) if cid else idx.docs
    pool = _apply(intent, base, industry=not cid)
    who = _company_name(idx.companies, cid) if cid else None
    top_n = 10 if re.search(r"\b10\b|десят", " ".join(intent.terms)) else 5
    top = sorted([d for d in pool if d.top_price], key=lambda d: -(d.top_price or 0))
    rest = sorted([d for d in pool if not d.top_price and d.purchase_like and d.named_rub],
                  key=lambda d: -(d.named_rub or 0))
    scope = _scope_text(intent, industry=not cid).strip()
    if who:
        scope = (f"компании [{who}](#/companies/{cid}) " + scope).strip()
    n_pool = len(pool)
    total = (f"Всего в выборке {n_pool} {_plural(n_pool, 'сделка', 'сделки', 'сделок')}; "
             f"цена, названная сторонами и сверенная с источником, — у {len(top)}"
             + (f", названная, но ещё не сверенная, — у {len(rest)}" if rest else "") + ".")
    if not top and not rest:
        est = sorted([d for d in pool if d.purchase_like and d.sum_rub and d.estimate], key=lambda d: -(d.sum_rub or 0))
        lines = [f"В выборке{(' ' + scope) if scope else ''} нет покупок с ценой, которую назвали стороны, — "
                 "сравнить по размеру не по чему."]
        if est:
            lines.append("Есть только оценки экспертов (это не цена сделки):")
            lines += [_role_line(d, cid) for d in est[:3]]
        lines += [total, NOTE_LARGEST]
        return Retrieval("largest", "\n".join(lines), est[:MAX_DEALS_FOR_MODEL], who, pool=est)
    head = f"Крупнейшие покупки {scope}" if scope else "Крупнейшие покупки в базе «Компаса»"
    lines = [head + " — по цене, которую назвали стороны и которую мы сверили с источником:" if top
             else head + ": сверенных с источником цен в этой выборке нет; по цене, которую назвали стороны:"]
    shown = top[:top_n]
    lines += [_role_line(d, cid) for d in shown]
    extra: list[Doc] = []
    if top and len(top) < top_n and rest:
        extra = rest[:top_n - len(top)]
        lines.append("Ещё покупки с ценой, которую назвали стороны, но мы её пока не сверили с источником "
                     "(в «Аналитику» они пока не входят):")
    elif not top:
        extra = rest[:top_n]
    lines += [_role_line(d, cid) for d in extra]
    lines.append(total)
    lines.append(NOTE_LARGEST + " " + NOTE_SUMS)
    ordered = shown + extra
    return Retrieval("largest", "\n".join(lines), ordered[:MAX_DEALS_FOR_MODEL], who, pool=top + rest)


def _answer_recent(intent: Intent, idx: Index) -> Retrieval:
    """Что появилось в базе за последние дни.

    Дата берётся из поля «добавлено», а не из даты сделки: человек спрашивает
    «что нового», то есть что появилось у НАС, — сделка может быть и прошлого
    года, а в «Компас» приехать вчера. Ровно так же устроена лента на сайте.
    """
    from datetime import date, timedelta
    days = intent.days or 7
    edge = (date.today() - timedelta(days=days)).isoformat()
    pool = [d for d in idx.docs if str((d.raw or {}).get("added") or "") >= edge]
    if intent.industry:
        pool = [d for d in pool if intent.industry in d.industries]
    scope = f" в отрасли «{intent.industry}»" if intent.industry else ""
    if intent.company_id:
        own = set(id(d) for d in idx.company_deals.get(intent.company_id) or [])
        pool = [d for d in pool if id(d) in own]
        cid = intent.company_id
        scope = f" у компании [{_company_name(idx.companies, cid)}](#/companies/{cid})"
    pool.sort(key=lambda d: str((d.raw or {}).get("added") or ""), reverse=True)
    period = "последнюю неделю" if days <= 7 else "последний месяц"
    if not pool:
        return Retrieval("recent", f"За {period}{scope} в «Компасе» новых сделок не появилось.", [], None)
    n = len(pool)
    lines = [f"За {period}{scope} в «Компасе» появилось {n} "
             f"{_plural(n, 'сделка', 'сделки', 'сделок')}:"]
    lines += [_line(d) for d in pool[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(f"Ещё {n - MAX_LISTED} — в [ленте сделок](#/deals).")
    return Retrieval("recent", "\n".join(lines), pool[:MAX_DEALS_FOR_MODEL], None, pool=pool)


def _answer_compare(intent: Intent, idx: Index) -> Retrieval:
    """Две-три компании рядом: сколько сделок, в каких ролях, последняя.

    Оценок «кто лучше» здесь нет и быть не может — мы показываем числа, а
    вывод делает читатель (то же правило, что и на экране сравнения).
    """
    blocks: list[str] = []
    docs: list[Doc] = []
    period = period_text(intent.span)
    for cid in intent.company_ids:
        name = _company_name(idx.companies, cid)
        own = _filter(idx.company_deals.get(cid) or [], intent.span, None)
        own = sorted(own, key=lambda d: d.date, reverse=True)
        if not own:
            blocks.append(f"**[{name}](#/companies/{cid})** — сделок в «Компасе» нет{period}.")
            continue
        n = len(own)
        head = (f"**[{name}](#/companies/{cid})** — {n} "
                f"{_plural(n, 'сделка', 'сделки', 'сделок')}{period}" + _roles_text(own, cid) + ".")
        block = [head, "Последняя: " + _role_line(own[0], cid).lstrip("- ")]
        if 1 < n <= 3:
            # Немного сделок — все: из двух сделок Ozon модель называла одну (№32).
            block.append(("Другая: " if n == 2 else "Другие: ") + "; ".join(_link(d) for d in own[1:]) + ".")
        # Крупнейшая — по цене, которую назвали стороны, среди состоявшихся
        # покупок и продаж (без обсуждаемых, выкупа своих акций,
        # финансирования); роль компании — рядом. До второй проверки ответ
        # давал только последнюю сделку, и модель сама выбирала «крупнейшую»
        # из дюжины карточек — с ошибкой в сумме и в роли (№21, ВТБ и Сбербанк).
        priced = sorted([d for d in own if d.purchase_like and d.named_rub], key=lambda d: -(d.named_rub or 0))
        if priced:
            big = priced[0]
            block.append(f"Крупнейшая по цене, названной сторонами ({_fmt_rub(big.named_rub)}): "
                         + _role_line(big, cid).lstrip("- "))
        else:
            block.append("Сделок с ценой, которую назвали стороны, у компании нет.")
        blocks.append("\n".join(block))
        docs += ([priced[0]] if priced else []) + [d for d in own[:4] if not priced or d is not priced[0]]
    if not blocks:
        return Retrieval("compare", None, [], None)
    names = " и ".join(_company_name(idx.companies, c) for c in intent.company_ids)
    lines = [f"{names} — рядом по тому, что есть в «Компасе»:"] + blocks
    # Во сколько раз больше — готовой цифрой: модель писала «в 10 раз» при
    # 14 сделках против 2 (№32 третьей проверки).
    counts = [(c, len(_filter(idx.company_deals.get(c) or [], intent.span, None))) for c in intent.company_ids]
    if len(counts) == 2 and all(k for _, k in counts) and counts[0][1] != counts[1][1]:
        (a, ka), (b, kb) = sorted(counts, key=lambda x: -x[1])
        ratio = ka / kb
        times = (f"{round(ratio)}" if abs(ratio - round(ratio)) < 0.05 else f"{ratio:.1f}".replace(".", ","))
        word = "раза" if times in ("2", "3", "4") or "," in times else "раз"
        lines.append(f"Сделок у {_company_name(idx.companies, a)} больше: {ka} против {kb} — в {times} {word}.")
    lines.append("Сравнение строится по сделкам, которые мы нашли в открытых источниках; "
                 "оно не полно и не является оценкой компаний. "
                 "Показатели отчётности — на [экране сравнения](#/compare).")
    return Retrieval("compare", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], names)


NOTE_SITE = "Это сделки, показанные на сайте (с 2022 года), а не вся статистика рынка."


def _answer_count(intent: Intent, idx: Index) -> Retrieval:
    pool = _apply(intent, idx.docs)
    n = len(pool)
    what = _scope_text(intent).strip()
    lines = [f"В базе «Компаса» {n} {_plural(n, 'сделка', 'сделки', 'сделок')} {what}.".replace(" .", ".")]
    if pool:
        by_year = Counter(d.year for d in pool)
        if not span_single(intent.span) and len(by_year) > 1:
            lines.append("По годам: " + ", ".join(f"{y} — {c}" for y, c in sorted(by_year.items())) + ".")
        if intent.wants_price:
            lines += _price_lines(pool, intent)
        lines.append("Последние:")
        lines += [_line(d) for d in pool[:MAX_LISTED]]
    if intent.span and intent.span[0] is not None and intent.span[0] < SITE_MIN_YEAR:
        lines.append(f"Сделки до {SITE_MIN_YEAR} года «Компас» не собирает: база начинается с {SITE_MIN_YEAR} года.")
    lines.append(NOTE_SITE)
    return Retrieval("count", "\n".join(lines), pool[:MAX_DEALS_FOR_MODEL], None, pool=pool)


def _answer_theme(intent: Intent, idx: Index) -> Retrieval:
    docs = _apply(intent, idx.docs)
    theme = intent.themes[0]
    rest = Intent("filter", span=intent.span, industry=intent.industry, themes=intent.themes[1:],
                  term_rxs=intent.term_rxs, status=intent.status, region=intent.region)
    scope = _scope_text(rest)
    if not docs:
        return Retrieval("theme", f"По теме «{theme}» сделок{scope} в базе пока нет.", [], theme)
    n = len(docs)
    head = (f"По теме [{theme}](#/theme/{theme}) в базе «Компаса» {n} "
            f"{_plural(n, 'сделка', 'сделки', 'сделок')}{scope}.")
    if VENTURE in intent.themes:
        head += " Сюда входят и все инвестиции в компании (деньги в компанию за долю)."
    if "IPO / SPO" in intent.themes:
        # Сами размещения — первыми: про них и спрашивают.
        docs = [d for d in docs if _is_offering(d)] + [d for d in docs if not _is_offering(d)]
    return _list_answer("theme", intent, idx, docs, head, f"[все по теме](#/theme/{theme})", theme)


def _excerpt(doc: Doc, rx: re.Pattern, width: int = 220) -> str:
    """Фраза карточки, где названо условие, — чтобы человек видел само
    условие («earn-out до 500 млн ₽»), а не только название сделки."""
    for text in (doc.facts, doc.title):
        m = rx.search(text or "")
        if not m:
            continue
        start = max(text.rfind(". ", 0, m.start()) + 2, m.start() - width // 2, 0)
        end = text.find(". ", m.end())
        end = len(text) if end < 0 else end + 1
        piece = text[start:min(end, start + width)].strip()
        return piece + ("…" if start + width < end else "")
    return ""


_FOREIGN_EXIT = re.compile(r"российск\w*\s+(?:бизнес|актив|завод|подразделен|дочк)|в\s+росси", re.I)
_NEGATED = re.compile(r"\bне\s+(?:предусм\w*|предполаг\w*|был\w*|име\w*|содерж\w*|включ\w*|оговар\w*)|\bнет\b|отсутств\w*|\bбез\s+(?:прав|опцион)", re.I)


def _sentences(doc: Doc, rx: re.Pattern) -> list[str]:
    """Фразы карточки, где названо условие."""
    return [sent for sent in re.split(r"(?<=[.;!?])\s+", doc.facts or "") if rx.search(sent)]


def _affirmed(doc: Doc, rx: re.Pattern) -> bool:
    """Условие названо хотя бы в одной фразе без отрицания рядом."""
    return any(not _NEGATED.search(sent) for sent in _sentences(doc, rx))


def _topic_pick(intent: Intent, pool: list[Doc]) -> list[Doc]:
    """Слова вопроса сверх условия — о чём сделки: «мультипликаторы в сделках
    с ресторанами и кофейнями» — не все 66 сделок с мультипликаторами, а
    рестораны и кофейни (№34). Сверка — по заголовку и сторонам: проза
    карточки упоминает слишком многое. Ничего не нашлось — весь список."""
    keys = list(TERM_HINTS)
    topic = [t for t in intent.terms
             if len(t) >= 4 and not t.isdigit() and not any(k.startswith(t) or t.startswith(k[:5]) for k in keys)
             and not _hint_covers(t, intent.region)]
    if not topic:
        return pool
    picked = [d for d in pool if any(any(same_word(t, s) for s in d.strong) for t in topic)]
    return picked or pool


def _answer_term(intent: Intent, idx: Index) -> Retrieval:
    docs = _apply(intent, idx.docs)
    rx_title = re.compile(intent.term_rxs[-1], re.I) if intent.term_rxs else None
    docs = _topic_pick(intent, docs)
    # Условие прямо в заголовке («MBO ПАО ВымпелКом», «management buy-out») —
    # первым: это сделка именно такого вида, а не упоминание в прозе. Дальше —
    # где во фразе с условием стоят и другие слова вопроса: «опцион на
    # обратный выкуп» у Hyundai и Mercedes-Benz выше «права выкупа обратно»
    # без слова «опцион» (№4).
    if rx_title:
        words = [t for t in intent.terms if len(t) >= 4 and not t.isdigit()]
        # «Обратный выкуп банка не предусмотрен… опционов в сделке нет»
        # (Ситибанк) — условие названо, чтобы сказать, что его НЕТ.
        docs = [d for d in docs if rx_title.search(d.title) or _affirmed(d, rx_title)]

        def closeness(d: Doc) -> int:
            best = max((sum(1 for t in words if t in norm(sent)) for sent in _sentences(d, rx_title)
                        if not _NEGATED.search(sent)), default=0)
            # Состоявшаяся сделка и уход иностранного владельца — где такое
            # условие и записано в договор (опцион продавца вернуть бизнес).
            return best + (d.status == "Закрыта") + bool(_FOREIGN_EXIT.search(d.title)
                                                          or "Уход иностранного владельца" in d.themes)
        docs = sorted(docs, key=lambda d: (0 if rx_title.search(d.title) else 1, -closeness(d)))
    scope = _scope_text(intent)
    if not docs:
        return Retrieval("term", f"Сделок{scope} в «Компасе» пока не нашлось.", [], None)
    n = len(docs)
    rx = re.compile(intent.term_rxs[-1], re.I)
    lines = [f"Сделок{scope} в «Компасе» — {n}. "
             + ("Сначала те, где условие названо ближе всего к словам вопроса:" if n > MAX_LISTED else "Все:")]
    for d in docs[:MAX_LISTED]:
        lines.append(_line(d))
        ex = _excerpt(d, rx)
        if ex:
            lines.append(f"  «{ex}»")
    if n > MAX_LISTED:
        lines.append(f"…и ещё {n - MAX_LISTED}.")
    return Retrieval("term", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], None, pool=docs)


def _answer_filter(intent: Intent, idx: Index) -> Retrieval:
    """Статус, регион, период — без отрасли и темы («Какие сделки не
    состоялись в 2025 году?», №31; «сделки в Татарстане», №69)."""
    docs = _apply(intent, idx.docs)
    scope = _scope_text(intent)
    if not docs:
        return Retrieval("filter", f"Сделок{scope} в «Компасе» пока нет.", [], None)
    n = len(docs)
    head = f"В базе «Компаса» {n} {_plural(n, 'сделка', 'сделки', 'сделок')}{scope}."
    return _list_answer("filter", intent, idx, docs, head, "в [ленте сделок](#/deals)", None)


def _fmt_rub(value: float) -> str:
    """Рубли словами для человека: «8,9 млрд ₽», «450 млн ₽», «1,2 трлн ₽»."""
    if value >= 1e12:
        return f"{value / 1e12:.1f} трлн ₽".replace(".", ",")
    if value >= 1e9:
        v = value / 1e9
        return (f"{v:.1f}" if v < 100 else f"{v:.0f}").replace(".", ",") + " млрд ₽"
    if value >= 1e6:
        return f"{value / 1e6:.0f} млн ₽"
    return f"{value:,.0f} ₽".replace(",", " ")


def _median(vals: list[float]) -> float:
    vals = sorted(vals)
    k = len(vals)
    return vals[k // 2] if k % 2 else (vals[k // 2 - 1] + vals[k // 2]) / 2


def _answer_avg(intent: Intent, idx: Index) -> Retrieval:
    """Средний и медианный размер сделки — посчитан здесь, а не моделью.

    «Какой средний размер сделки в агро?» модель считала «на глаз» по
    дюжине карточек и получала 16,5 млрд ₽ (№20). Считаем по тем же
    сделкам, что суммы на странице «Аналитика»: цена названа сторонами и
    прочитана в источнике (facts.admitted.purchase_sums), лоты торгов — не
    сделки. Медиана рядом со средним: несколько мегасделок тянут среднее
    вверх, и «типичная» сделка видна по медиане."""
    pool = [d for d in _apply(intent, idx.docs) if not d.listing]
    priced = sorted([d for d in pool if d.price_rub], key=lambda d: -(d.price_rub or 0))
    scope = _scope_text(intent)
    if not priced:
        return Retrieval("avg", f"Сделок{scope} с ценой, названной сторонами, в «Компасе» нет — "
                         "средний размер посчитать не по чему.", pool[:MAX_DEALS_FOR_MODEL], None, pool=pool)
    vals = [d.price_rub for d in priced]
    n = len(vals)
    mean, med = sum(vals) / n, _median(vals)
    lines = [f"Размер сделки{scope} по базе «Компаса»: среднее — {_fmt_rub(mean)}, "
             f"медиана — {_fmt_rub(med)} (половина сделок дешевле, половина дороже).",
             f"Посчитано по {n} {_plural(n, 'сделке', 'сделкам', 'сделкам')} с ценой, названной сторонами, "
             f"из {len(pool)}; от {_fmt_rub(vals[-1])} до {_fmt_rub(vals[0])}."]
    if n >= 3 and mean > 2 * med:
        lines.append("Среднее заметно выше медианы: его тянут вверх несколько крупных сделок.")
    if n < 5:
        lines.append("Сделок с ценой мало, поэтому цифры — ориентир, а не статистика рынка.")
    lines.append("Крупнейшие из них:")
    lines += [_line(d) for d in priced[:5]]
    # Сделки с оценкой и мультипликаторами — модели первыми: на вопрос
    # «сколько может стоить пищевое производство» они отвечают по существу.
    mult = re.compile(TERM_HINTS["мультипликатор"], re.I)
    with_mult = [d for d in pool if mult.search(d.facts)]
    if with_mult:
        lines.append(f"Мультипликаторы названы у {len(with_mult)} "
                     f"{_plural(len(with_mult), 'сделки', 'сделок', 'сделок')} этой выборки, например:")
        for d in with_mult[:3]:
            lines.append(_line(d))
            ex = _excerpt(d, mult)
            if ex:
                lines.append(f"  «{ex}»")
    lines.append(NOTE_SUMS)
    docs = with_mult[:4] + [d for d in priced if d not in with_mult[:4]]
    return Retrieval("avg", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], None, pool=pool)


def _answer_rank(intent: Intent, idx: Index) -> Retrieval:
    """Рейтинги по всей базе: консультанты, отрасли, покупатели.

    Считаем так же, как сайт: лоты торгов, которые ещё не куплены, — не
    сделки (isListing); юрфирмы — вкладка «Юридические» каталога (FIRMS),
    как «Лига консультантов» на странице «Аналитика»; отрасли — по всем
    отраслям сделки; покупатели — по профилю покупателя."""
    pool = [d for d in _apply(intent, idx.docs) if not d.listing]
    scope = _scope_text(intent)
    single = span_single(intent.span)
    prev_pool = None
    if single:
        prev_intent = Intent("filter", span=(single - 1, single - 1), industry=intent.industry,
                             themes=intent.themes, term_rxs=intent.term_rxs, status=intent.status,
                             region=intent.region)
        prev_pool = [d for d in _apply(prev_intent, idx.docs) if not d.listing]
    kind = intent.rank
    lines: list[str] = []
    docs: list[Doc] = []
    if kind in ("law", "invest", "advisors"):
        kinds = {"law": {"law"}, "invest": INVEST_KINDS, "advisors": None}[kind]
        rows = _firm_counts(pool, idx, kinds)
        prev = dict((f.id, n) for f, n in _firm_counts(prev_pool, idx, kinds)) if prev_pool is not None else {}
        title = {"law": "Юрфирмы", "invest": "Банки и инвестиционные консультанты",
                 "advisors": "Консультанты"}[kind]
        if not rows:
            return Retrieval("rank", f"{title}{scope}: ни в одной сделке «Компаса» не названы.", [], title)
        lines.append(f"{title} по числу сделок{scope} в «Компасе»:")
        for i, (f, n) in enumerate(rows[:10], 1):
            extra = f" ({f.kind_label})" if kind != "law" else ""
            was = f"; за {single - 1} — {prev.get(f.id, 0)}" if single else ""
            lines.append(f"{i}. [{f.name}](#/advisors/{f.id}){extra} — {n} "
                         f"{_plural(n, 'сделка', 'сделки', 'сделок')}{was}")
            docs += [d for d in idx.firm_deals.get(f.id) or [] if d in pool][:2]
        if kind == "invest":
            lines.append("Консультанты по недвижимости (IBC Real Estate, Nikoliers, CORE.XP) и организаторы "
                         "торгов в этот список не входят.")
        lines.append(f"Всего сделок в выборке — {len(pool)}, консультант назван у "
                     f"{sum(1 for d in pool if d.advisors)}. {NOTE_ADVISORS} "
                     "Тот же счёт — на странице [Консультанты](#/advisors).")
        subject = title
    elif kind == "industries":
        cnt = Counter(i for d in pool for i in dict.fromkeys(d.industries) if i and i != "Не определена")
        if not cnt:
            return Retrieval("rank", f"Сделок{scope} в «Компасе» нет.", [], None)
        prev = Counter(i for d in prev_pool or [] for i in dict.fromkeys(d.industries)) if prev_pool is not None else None
        lines.append(f"Отрасли по числу сделок{scope} в «Компасе» (всего сделок — {len(pool)}; "
                     "у сделки бывает несколько отраслей):")
        for i, (ind, n) in enumerate(cnt.most_common(10), 1):
            was = f"; за {single - 1} — {prev.get(ind, 0)}" if prev is not None else ""
            lines.append(f"{i}. [{ind}](#/industry/{ind}) — {n} {_plural(n, 'сделка', 'сделки', 'сделок')}{was}")
        lines.append("Подробнее по отраслям и годам — на странице [Аналитика](#/analytics).")
        docs = []
        subject = "Отрасли"
    else:  # buyers
        cnt = Counter(d.raw.get("buyer") for d in pool if d.raw.get("buyer") in idx.companies)
        rows = [(cid, n) for cid, n in cnt.most_common() if n >= 2][:10]
        if not rows:
            return Retrieval("rank", f"Компаний с двумя и больше покупками{scope} в «Компасе» нет.", [], None)
        if intent.buyer_kind == "bank":
            lines.append(f"Банки — самые активные покупатели{_scope_text(replace(intent, buyer_kind=None))} "
                         "в «Компасе», по числу сделок, где банк — покупатель:")
        else:
            lines.append(f"Самые активные покупатели{scope} в «Компасе» — по числу сделок, где компания покупатель:")
        for i, (cid, n) in enumerate(rows, 1):
            name = _company_name(idx.companies, cid)
            own = [d for d in pool if d.raw.get("buyer") == cid]
            inds = Counter(x for d in own for x in d.industries).most_common(2)
            lines.append(f"{i}. [{name}](#/companies/{cid}) — {n} {_plural(n, 'покупка', 'покупки', 'покупок')}"
                         + (f" ({', '.join(x for x, _ in inds)})" if inds else ""))
            docs += own[:2]
        lines.append("Считаются сделки, где покупатель назван в открытых источниках; "
                     "список серийных покупателей — на странице [Аналитика](#/analytics).")
        subject = "Покупатели"
    return Retrieval("rank", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], subject, pool=docs)


def _short_advisor(raw: str) -> str:
    """Имя консультанта из сырой строки карточки: до тире-пояснения и до
    скобки, не длиннее 60 знаков — на экран уходит имя, а не абзац."""
    name = re.split(r"\s+[—–-]\s+|\s*\(", raw, maxsplit=1)[0].strip(" ;,")
    return (name[:57] + "…") if len(name) > 60 else name


SIZE_WORDS = ("средн", "мал", "мелк", "небольш", "крупн")


def _answer_advisors_overall(intent: Intent, idx: Index) -> Retrieval:
    """«Кто сопровождает продажи…», «какие консультанты работают с…» без
    имени фирмы и без отрасли — счёт консультантов по всем сделкам (с
    условиями вопроса), а не одна случайная сделка по слову вопроса. Слово
    «продажа» — консультанты стороны продавца, «покупка» — покупателя."""
    pool = [d for d in _apply(intent, idx.docs) if not d.listing]
    side = {"seller": "консультант продавца", "buyer": "консультант покупателя"}.get(intent.role or "")
    rows = []
    for f in idx.firms:
        own = [d for d in idx.firm_deals.get(f.id) or [] if d in pool and (
            side is None or any(f.rx.search(name) and _role_bucket(r) == side for r, name in d.advisor_roles))]
        if own:
            rows.append((f, own))
    rows.sort(key=lambda x: (-len(x[1]), x[0].name.lower()))
    scope = _scope_text(intent)
    who = f" на стороне {'продавца' if intent.role == 'seller' else 'покупателя'}" if side else ""
    lines = []
    if any(t.startswith(SIZE_WORDS) for t in intent.terms):
        lines.append("Размер бизнеса («средний», «малый») в карточках не размечен, поэтому считаем по всем сделкам.")
    if not rows:
        lines.append(f"Консультанты{who}{scope} ни в одной сделке «Компаса» не названы. {NOTE_ADVISORS}")
        return Retrieval("rank", "\n".join(lines), [], None)
    named = sum(1 for d in pool if d.advisors)
    lines.append(f"Консультанты{who} по числу сделок{scope} в «Компасе» (всего сделок в выборке — {len(pool)}, "
                 f"консультант назван у {named}; фирм — {len(rows)}):")
    docs: list[Doc] = []
    for i, (f, own) in enumerate(rows[:10], 1):
        lines.append(f"{i}. [{f.name}](#/advisors/{f.id}) ({f.kind_label}) — {len(own)} "
                     f"{_plural(len(own), 'сделка', 'сделки', 'сделок')}")
        docs += [d for d in own[:2] if d not in docs]
    lines.append(NOTE_ADVISORS + " Тот же счёт — на странице [Консультанты](#/advisors).")
    return Retrieval("rank", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], "Консультанты", pool=docs)


def _answer_search(intent: Intent, idx: Index) -> Retrieval:
    # Спросили про консультанта, которого нет в каталоге, — ищем его имя в
    # самих карточках: там названы и фирмы вне каталога. Родовые слова
    # («партнёры», legal, консалтинг) именем не считаются — иначе «Иванов и
    # партнёры» находил бы всех «…и партнёры» базы.
    if intent.wants_advisors and intent.terms:
        # Обычные слова вопроса («среднего», «бизнеса», «продажу») — не имя
        # фирмы: «Какие консультанты сопровождают продажу среднего бизнеса?»
        # находило по «среднего» одну сделку с BGP Capital (вторая проверка, №65).
        name_terms = [t for t in (intent.words or intent.terms)
                      if len(t) >= 4 and t not in ADVISOR_GENERIC and stem(t) not in ADVISOR_GENERIC
                      and not _plain_word(t, idx) and not _stop_match(t) and not _hint_covers(t, intent.region)
                      and not ADVISOR_WORDS.search(t)]
        if not name_terms:
            return _answer_advisors_overall(intent, idx)
        hits = [d for d in idx.docs
                if any(any(name_match(t, w) for w in tokens(a)) for t in name_terms for a in d.advisors)] if name_terms else []
        hits = _filter(hits, intent.span, intent.industry)
        if hits:
            names = Counter(_short_advisor(a) for d in hits for a in d.advisors
                            if any(any(name_match(t, w) for w in tokens(a)) for t in name_terms))
            n = len(hits)
            who = ", ".join(f"«{a}»" for a, _ in names.most_common(3))
            lines = [f"Консультант с таким именем ({who}) назван в {n} "
                     f"{_plural(n, 'сделке', 'сделках', 'сделках')}:"]
            lines += [_line(d) for d in hits[:MAX_LISTED]]
            if n > MAX_LISTED:
                lines.append(f"…и ещё {n - MAX_LISTED}.")
            lines.append(NOTE_ADVISORS)
            return Retrieval("advisor", "\n".join(lines), hits[:MAX_DEALS_FOR_MODEL], who)
        if name_terms:
            close = [f for f in idx.firms if any(name_match(t, w) for t in name_terms for w in tokens(f.name))]
            tail = (" Похожие по названию в каталоге: "
                    + ", ".join(f"[{f.name}](#/advisors/{f.id})" for f in close[:3]) + ".") if close else ""
            return Retrieval("advisor",
                             "В базе «Компаса» такой консультант не назван ни в одной сделке, и в каталоге "
                             "консультантов его нет." + tail + " " + NOTE_ADVISORS, [], None)
    docs = search(intent.terms, idx, limit=len(idx.docs))
    if intent.span:
        by_year = [d for d in docs if in_span(d.year, intent.span)]
        docs = by_year or docs
    if not docs:
        return Retrieval("search", None, [], None)
    # Попали во что-то конкретное («Когда Яндекс приобрёл Boxberry?») —
    # отвечаем сводкой этой сделки с этапами и источником, остальное списком.
    if _search_is_specific(intent, docs, idx):
        return _answer_deal(docs[0], docs[1:])
    n = len(docs)
    # Сколько нашлось всего — словами: без этого модель писала «это все» под
    # шестью строками из двадцати (вторая проверка).
    lines = [f"Похожих по словам вопроса сделок в базе — {n}"
             + (f"; первые {MAX_LISTED}:" if n > MAX_LISTED else ":")]
    lines += [_line(d) for d in docs[:MAX_LISTED]]
    if n > MAX_LISTED:
        lines.append(NOTE_PARTIAL)
    return Retrieval("search", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], None, pool=docs)


def _events(doc: Doc) -> list[str]:
    """Этапы сделки с датами («16 апреля 2025 — объявлено о сделке»). Аудит,
    раунд 2 (6 сентября 2026): ассистент отвечал «дата анонса не указана»,
    хотя на карточке Boxberry этап 16 апреля стоял — этапы просто не
    попадали ни в сводку, ни в карточку для модели."""
    out = []
    for ev in doc.raw.get("events") or []:
        if not isinstance(ev, dict):
            continue
        date, title = str(ev.get("date") or ""), str(ev.get("title") or ev.get("kind") or "").strip()
        if not re.fullmatch(r"\d{4}(-\d{2}-\d{2})?", date) or not title:
            continue
        # Карточка датирована днём ПУБЛИКАЦИИ сообщения о закрытии — этап
        # закрытия с той же датой обязан говорить то же, а не «сделка завершена
        # 24 апреля» (см. _date_phrase).
        if doc.raw.get("date_basis") == "publication" and ev.get("kind") == "closed" and date == doc.date:
            out.append(f"{_fmt_date(date)} — опубликовано сообщение о закрытии сделки")
            continue
        out.append(f"{_fmt_date(date)} — {title[0].lower() + title[1:]}")
    return out


def _answer_deal(doc: Doc, more: list[Doc] | None = None) -> Retrieval:
    """Сводка одной сделки — для вопроса с её страницы или для поиска по
    словам, который попал в конкретную сделку (тогда `more` — остальные
    найденные, коротким списком следом)."""
    bits = [_date_phrase(doc)]
    if doc.status:
        bits.append(doc.status.lower())
    lines = [f"Сделка {_link(doc)} — {', '.join(bits)}.{_source_link(doc)}"]
    events = _events(doc)
    if events:
        lines.append("Этапы: " + "; ".join(events) + ".")
    parties = []
    if doc.buyer:
        parties.append(f"покупатель — {doc.buyer}")
    if doc.seller:
        parties.append(f"продавец — {doc.seller}")
    if doc.target or doc.asset:
        parties.append(f"предмет — {doc.target or doc.asset}")
    if parties:
        lines.append("Стороны: " + "; ".join(parties) + ".")
    lines.append(f"Сумма: {doc.sum_text}." if has_fact(doc.sum_text) else "Сумму сделки не раскрывали.")
    # Оценка, мультипликаторы и условия — в точный ответ целиком: «Какие
    # условия были у продажи Ситибанка?», «При каких мультипликаторах прошло
    # IPO B2B-РТС?» (№11, 30).
    eco, law = doc.raw.get("eco") or {}, doc.raw.get("law") or {}
    if has_fact(eco.get("val")):
        lines.append(f"Оценка: {_clip(eco['val'], 400)}")
    if has_fact(law.get("terms")):
        lines.append(f"Условия: {_clip(law['terms'], 400)}")
    if doc.advisor_roles:
        lines.append("Консультанты: " + ", ".join(f"{n} ({r.lower()})" if r else n
                                                 for r, n in doc.advisor_roles[:4]) + ".")
    else:
        lines.append("Консультанты в открытых источниках не назывались.")
    docs = [doc]
    if more:
        rest = [d for d in more if d.id != doc.id]
        if rest:
            lines.append(f"Ещё похожих по словам вопроса сделок — {len(rest)}"
                         + (f"; первые {MAX_LISTED}:" if len(rest) > MAX_LISTED else ":"))
            lines += [_line(d) for d in rest[:MAX_LISTED]]
            docs += rest[:MAX_DEALS_FOR_MODEL - 1]
    return Retrieval("deal", "\n".join(lines), docs, doc.title)


def _answer_entity(context_type: str | None, context_id: str | None, intent: Intent, idx: Index) -> Retrieval | None:
    """Ответ о сущности страницы, с которой задан вопрос, — когда сам вопрос
    её не называет. «Что известно?» или «Кто консультировал сделки?» на
    странице «Яндекса» до 2 сентября 2026 давали пустой быстрый ответ (все
    слова вопроса — стоп-слова), и посетитель ждал модель 30–40 секунд, хотя
    точная сводка по компании считается за миллисекунды."""
    if not context_type or not context_id:
        return None
    if context_type == "company" and context_id in idx.companies:
        return _answer_company(Intent("company", company_id=context_id, span=intent.span, status=intent.status,
                                      wants_advisors=intent.wants_advisors, terms=intent.terms,
                                      themes=intent.themes, term_rxs=intent.term_rxs, region=intent.region,
                                      wants_price=intent.wants_price, role=intent.role), idx)
    if context_type == "advisor":
        firm = next((f for f in idx.firms if f.id == context_id), None)
        if firm:
            return _answer_advisor(Intent("advisor", firm=firm, span=intent.span, status=intent.status,
                                          terms=intent.terms), idx)
    if context_type == "industry" and context_id in idx.industries:
        return _answer_industry(Intent("industry", industry=context_id, span=intent.span, status=intent.status,
                                       wants_advisors=intent.wants_advisors, terms=intent.terms), idx)
    if context_type == "deal":
        doc = idx.by_id.get(context_id)
        if doc:
            return _answer_deal(doc)
    return None


# Вопрос называет страницу, с которой задан, а не другое имя: «какие сделки
# КОМПАНИИ закрыты» на странице «Яндекса» уходил в поиск по словам «закрыты»
# и «сумма» и перечислял сделки Qiwi, «Открытия», KFC (№95 третьей проверки);
# «какие сделки Сбербанка вела ЭТА ФИРМА» на странице Orion давал все сделки
# Сбербанка вместо двух, где консультировал Orion (№73).
PAGE_REF = re.compile(
    r"\b(?:эт(?:а|ой|у|ою|им|их|ими)|данн\w+)\s+(?:компани\w*|фирм\w*|организаци\w*|отрасл\w*|консультант\w*)"
    r"|\bкомпани(?:я|и|ю|ей)\b|\bфирм(?:а|ы|у|ой)\b|\bу\s+не[её]\b|\bу\s+него\b|\bе[её]\s+сделк\w*|\bего\s+сделк\w*"
    r"|\bв\s+этой\s+отрасли\b", re.I)
FIRM_PAGE_REF = re.compile(r"\bфирм\w*|\bконсультант\w*|\bвел[аио]?\b|\bсопровожда\w*|\bконсультир\w*", re.I)
PAGE_KINDS = ("search", "filter", "count", "theme", "term")


def _answer_firm_company(firm: Firm, cid: str, intent: Intent, idx: Index) -> Retrieval | None:
    """Сделки компании, где консультантом была фирма страницы: «Какие сделки
    Сбербанка вела эта фирма и сколько они длились?» на странице Orion."""
    own = idx.company_deals.get(cid) or []
    both = [d for d in _apply(intent, idx.firm_deals.get(firm.id) or [], industry=False) if d in own]
    if not both:
        return None
    both.sort(key=lambda d: d.date, reverse=True)
    name = _company_name(idx.companies, cid)
    k = len(both)
    lines = [f"Сделки компании [{name}](#/companies/{cid}), где консультантом была "
             f"[{firm.name}](#/advisors/{firm.id}) ({firm.kind_label}){_scope_text(intent, industry=False)}: {k}."]
    for d in both[:MAX_LISTED]:
        lines.append(_role_line(d, cid))
        events = _events(d)
        if events:
            lines.append("  Этапы: " + "; ".join(events) + ".")
        roles = [r for r, n in d.advisor_roles if firm.rx.search(n)]
        if roles and roles[0]:
            lines.append(f"  Роль фирмы: {roles[0].lower()}.")
    n = len(own)
    lines.append(f"Всего у компании в «Компасе» {n} {_plural(n, 'сделка', 'сделки', 'сделок')} — "
                 f"на [странице компании](#/companies/{cid}).")
    rest = sorted([d for d in own if d not in both], key=lambda d: d.date, reverse=True)
    return Retrieval("company", "\n".join(lines), (both + rest)[:MAX_DEALS_FOR_MODEL], name, pool=both)


def _page_answer(question: str, context_type: str | None, context_id: str | None, intent: Intent,
                 idx: Index) -> Retrieval | None:
    """Вопрос, который ссылается на страницу («компании», «эта фирма»), а
    другого имени не называет, — ответ о сущности страницы с условиями
    вопроса (статус, год, тема, цена)."""
    if not context_type or not context_id:
        return None
    if context_type == "advisor" and intent.kind == "company" and intent.company_id \
            and FIRM_PAGE_REF.search(question):
        firm = next((f for f in idx.firms if f.id == context_id), None)
        if firm:
            return _answer_firm_company(firm, intent.company_id, intent, idx)
    if intent.kind in PAGE_KINDS and not intent.company_id and not intent.firm and PAGE_REF.search(question) \
            and context_type in ("company", "advisor", "industry"):
        terms = [t for t in intent.terms if not re.match(r"состо|закр|заверш|обсужд|сорв|отмен|сделк|компан|фирм", t)]
        own_intent = Intent("empty", span=intent.span, status=intent.status, wants_advisors=intent.wants_advisors,
                            terms=terms, themes=intent.themes, term_rxs=intent.term_rxs, region=intent.region,
                            wants_price=intent.wants_price, role=intent.role)
        return _answer_entity(context_type, context_id, own_intent, idx)
    return None


# «Какие (ещё) сделки вели?» — про сделки сторон, а «что известно о сделке?» —
# про саму сделку: слово «сделки» в STOP и до терминов не доходит, поэтому
# читается сам текст вопроса, и только во множественном смысле.
PARTIES_DEALS_WORDS = re.compile(
    r"какие\s+(?:ещё\s+|еще\s+|другие\s+)?сделки|(?:ещё|еще|другие|прочие)\s+сделки|"
    r"сделки\s+(?:вел|совершал|провод|заключал|были|делал)", re.I)


def _answer_deal_parties(deal_id: str | None, year: Any, idx: Index) -> Retrieval | None:
    """Сделки сторон той сделки, со страницы которой задан вопрос.

    «Какие сделки вели в 2026 году?» на карточке Ситибанка (владелец,
    3 октября 2026) никого не называет: поиск по словам «сделки» и «вели»
    попадал в случайную карточку, и модель честно отвечала «нет». Человек же
    спрашивает о покупателе, продавце и предмете сделки, которую читает, —
    отвечаем их сделками, за названный год или за всё время."""
    doc = idx.by_id.get(deal_id or "")
    if not doc:
        return None
    raw = doc.raw or {}
    seen: set[str] = set()
    lines: list[str] = []
    docs: list[Doc] = []
    period = period_text((year, year) if isinstance(year, int) else year)
    for key, role in (("buyer", "покупатель"), ("seller_id", "продавец"),
                      ("target", "предмет сделки"), ("asset_id", "предмет сделки")):
        cid = raw.get(key)
        if not cid or cid in seen or cid not in idx.companies:
            continue
        seen.add(cid)
        name = _company_name(idx.companies, cid)
        own = sorted(_filter(idx.company_deals.get(cid) or [], year, None), key=lambda d: d.date, reverse=True)
        if not own:
            lines.append(f"У компании [{name}](#/companies/{cid}) ({role}) сделок{period} в «Компасе» нет.")
            continue
        n = len(own)
        lines.append(f"[{name}](#/companies/{cid}) ({role}) — {n} {_plural(n, 'сделка', 'сделки', 'сделок')}{period}:")
        lines += [_line(d) for d in own[:MAX_LISTED]]
        if n > MAX_LISTED:
            lines.append(f"…и ещё {n - MAX_LISTED} — на [странице компании](#/companies/{cid}).")
        docs += [d for d in own if d not in docs]
    if not seen:
        return None
    head = f"Сделки сторон этой сделки{period} по базе «Компаса»:"
    ordered = [doc] + [d for d in docs if d.id != doc.id]
    return Retrieval("deal", "\n".join([head] + lines), ordered[:MAX_DEALS_FOR_MODEL], doc.title)


def _search_is_specific(intent: Intent, docs: list[Doc], idx: Index) -> bool:
    """Поиск по словам попал во что-то конкретное: хотя бы одно отличительное
    (редкое) слово вопроса стоит в заголовке или сторонах первой найденной
    сделки. «Кто купил Ситибанк?» — да; «какие последние сделки?» — нет,
    это фоновые слова, и со страницы сущности такой вопрос про неё."""
    if not docs:
        return False
    top = docs[0]
    return any(len(t) >= 4 and _term_weight(t, idx) >= 3.0 and any(_name_word_match(s, t) for s in top.strong)
               for t in intent.terms)


def _scoped(context_type: str | None, context_id: str | None, idx: Index) -> list[Doc] | None:
    """Вопрос, заданный со страницы сделки/компании/фирмы/отрасли, — про неё."""
    if not context_type or not context_id:
        return None
    if context_type == "deal":
        d = idx.by_id.get(context_id)
        return [d] if d else None
    if context_type == "company":
        docs = idx.company_deals.get(context_id) or []
        return sorted(docs, key=lambda d: d.date, reverse=True)[:MAX_DEALS_FOR_MODEL] or None
    if context_type == "advisor":
        return (idx.firm_deals.get(context_id) or [])[:MAX_DEALS_FOR_MODEL] or None
    if context_type == "industry":
        return [d for d in idx.docs if context_id in d.industries][:MAX_DEALS_FOR_MODEL] or None
    return None


def _refine(question: str, intent: Intent, prev: Retrieval, pool: list[Doc], idx: Index) -> Retrieval | None:
    """Уточнение внутри сделок предыдущего ответа: «самые крупные», «за
    сколько», «сколько из них», «из них в 2025 году», «какие закрылись».
    None — уточнение ничего не сузило и слов сверх него нет: тогда вопрос
    ищется обычным порядком."""
    cond = Intent("filter", span=intent.span, industry=intent.industry, themes=intent.themes,
                  term_rxs=intent.term_rxs, status=intent.status, region=intent.region)
    base = _apply(cond, pool)
    scope = _scope_text(cond)
    n0 = len(pool)
    sub = f" ({prev.subject})" if prev.subject else ""
    head = f"Из {n0} {_plural(n0, 'сделки', 'сделок', 'сделок')} предыдущего ответа{sub}"
    lines: list[str]
    if not base:
        return Retrieval(prev.intent, head + f" ни одна не подходит под условие{scope}.", pool[:MAX_DEALS_FOR_MODEL],
                         prev.subject, pool=pool)
    if LARGEST_WORDS.search(question) or intent.kind == "largest":
        with_sum = sorted([d for d in base if d.sum_rub], key=lambda d: -(d.sum_rub or 0))
        if not with_sum:
            lines = [head + f"{scope} ни у одной не названа сумма в рублях — сравнить их по размеру нельзя:"]
            lines += [_line(d) for d in base[:MAX_LISTED]]
            docs = base
        else:
            named = [d for d in with_sum if not d.estimate]
            est = [d for d in with_sum if d.estimate]
            lines = [head + f"{scope} самые крупные по названной цене:" if named
                     else head + f"{scope} сумма известна только по оценкам экспертов (цену стороны не называли):"]
            lines += [_line(d) for d in named[:MAX_LISTED]]
            if est and named:
                lines.append("По оценкам экспертов (не подтверждённая цена):")
            lines += [_line(d) for d in est[:3 if named else MAX_LISTED]]
            rest = [d for d in base if d not in with_sum]
            lines.append(f"Сумма названа у {len(with_sum)} из {len(base)}"
                         + (f"; без суммы: {', '.join(d.title for d in rest[:3])}" if rest else "") + ".")
            docs = with_sum + rest
        return Retrieval("largest", "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], prev.subject, pool=docs)
    if intent.wants_price:
        priced = [d for d in base if has_fact(d.sum_text)]
        rest = [d for d in base if d not in priced]
        lines = [head + f"{scope} сумма названа у {len(priced)}:"] if priced else \
                [head + f"{scope} ни у одной сумма публично не называлась."]
        lines += [_line(d) for d in priced[:MAX_LISTED]]
        if rest and priced:
            lines.append("Без названной суммы: " + "; ".join(_link(d) for d in rest[:4]) + ".")
        docs = priced + rest
        return Retrieval(prev.intent, "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], prev.subject, pool=docs)
    has_cond = bool(cond.span or cond.industry or cond.themes or cond.term_rxs or cond.status or cond.region)
    if COUNT_WORDS.search(question) or len(base) < n0 or has_cond:
        k = len(base)
        cond_text = scope.replace("— только ", "").strip()
        under = f" под условие «{cond_text}»" if cond_text else ""
        lines = [head + f"{under} подходят {k}:" if len(base) < n0
                 else head + f"{under} подходят все {k}:" if has_cond else head + f": {k}."]
        lines += [_line(d) for d in base[:MAX_LISTED]]
        if k > MAX_LISTED:
            lines.append(f"…и ещё {k - MAX_LISTED}.")
        return Retrieval(prev.intent, "\n".join(lines), base[:MAX_DEALS_FOR_MODEL], prev.subject, pool=base)
    extra = [t for t in intent.terms if not t.isdigit() and not _plain_word(t, idx) and len(t) >= 3]
    picked = [d for d in base if extra and any(
        any(_name_word_match(s, t) for s in d.strong) or any(same_word(t, s) for s in d.weak) for t in extra)]
    if picked:
        lines = [head + " к вопросу подходят:"] + [_line(d) for d in picked[:MAX_LISTED]]
        docs = picked + [d for d in base if d not in picked]
        return Retrieval(prev.intent, "\n".join(lines), docs[:MAX_DEALS_FOR_MODEL], prev.subject, pool=docs)
    return None


def retrieve(question: str, context_type: str | None = None, context_id: str | None = None,
             idx: Index | None = None, previous: str | None = None) -> Retrieval:
    """`previous` — предыдущая реплика посетителя в том же диалоге. Уточняющий
    вопрос («перепроверь», «а дата объявления?») сам по себе никого не
    называет, и поиск по нему пуст — тогда он читается вместе с предыдущим
    вопросом. Аудит, раунд 2 (6 сентября 2026): на «перепроверь» ассистент
    отвечал «в Компасе нет сделки Яндекс — Boxberry», сославшись на неё
    репликой раньше, — поиск шёл только по текущей фразе."""
    idx = idx or get_index()
    # Сайт шлёт context_type="general", когда вопрос задан не со страницы
    # сущности (главная, экран ассистента). Это то же, что «контекста нет»:
    # условие `not context_type` его не узнавало, и одно слово «сделки»
    # отвечало «ничего не нашёл» (№91 третьей проверки).
    if context_type in (None, "", "general") or not context_id:
        context_type, context_id = None, None
    # ПОДГОТОВКА К ВСТРЕЧЕ ИЛИ СОБЕСЕДОВАНИЮ — всегда про сущность страницы.
    # 5 октября 2026 подготовка к встрече со Сбербанком ушла в маршрут
    # «консультант»: в заготовке было слово «консультантами», Сбербанк есть и
    # в каталоге консультантов, и модель получила сделки, где банк был
    # советником, а не стороной. Слова, которыми человек рассказывает о себе
    # («я юрист», «я инвестбанкир»), тем более не должны уводить маршрут.
    if context_type in ("company", "advisor") and context_id and PREP_WORDS.search(question):
        own = _answer_entity(context_type, context_id, Intent("empty", wants_advisors=True), idx)
        if own:
            return own
    intent = route(question, idx)
    # Уточнение к прошлому ответу («а какие из них самые крупные?», «а за
    # сколько?») ищется сначала внутри его сделок: до 14 октября 2026 слово
    # «крупные» запускало поиск крупнейших по всей базе, и ответ «у
    # Альфа-Банка нет сделок за 2026 год» противоречил предыдущему (№23).
    if previous and FOLLOWUP_WORDS.search(question) \
            and intent.kind not in ("company", "advisor", "compare", "compare_firms"):
        prev = retrieve(previous, context_type, context_id, idx)
        pool = prev.pool or prev.docs
        if pool:
            refined = _refine(question, intent, prev, pool, idx)
            if refined:
                return refined
    if previous and intent.kind in ("empty", "search"):
        # Слабый вопрос: никого не называет, а поиск по его словам не попал ни
        # во что конкретное («а дата объявления?» находит по слову «дата»
        # случайные сделки — это не попадание).
        weak = intent.kind == "empty" or not _search_is_specific(intent, search(intent.terms, idx), idx)
        if weak:
            # Сначала предыдущий вопрос сам по себе: слова уточнения («дата»,
            # «объявления») только размывают отбор внутри найденной компании.
            for text in (previous, f"{previous} {question}"):
                again = retrieve(text, context_type, context_id, idx)
                if again.answer or again.docs:
                    return again
    handlers = {
        "advisor": _answer_advisor, "company": _answer_company, "industry": _answer_industry,
        "largest": _answer_largest, "count": _answer_count, "theme": _answer_theme,
        "term": _answer_term, "search": _answer_search,
        "recent": _answer_recent, "compare": _answer_compare,
        "compare_firms": _answer_compare_firms, "filter": _answer_filter,
        "rank": _answer_rank, "avg": _answer_avg,
    }
    # Со страницы сделки «какие сделки …?» или вопрос с годом — про стороны
    # этой сделки, а не про неё саму (см. _answer_deal_parties).
    about_parties = context_type == "deal" and (bool(intent.span) or bool(PARTIES_DEALS_WORDS.search(question)))
    if intent.kind == "empty" and not context_type and not context_id and re.search(r"сделк", norm(question)):
        # Одно слово «сделки» — показываем, что появилось за месяц, а не
        # «ничего не найдено» (№91).
        return _answer_recent(Intent("recent", days=30), idx)
    page = _page_answer(question, context_type, context_id, intent, idx)
    if page:
        return page
    if intent.kind == "empty":
        if about_parties:
            own = _answer_deal_parties(context_id, intent.span, idx)
            if own:
                return own
        own = _answer_entity(context_type, context_id, intent, idx)
        if own:
            return own
        scoped = _scoped(context_type, context_id, idx)
        return Retrieval("empty", None, scoped or [], None)
    result = handlers[intent.kind](intent, idx)
    # Со страницы сущности вопрос почти всегда про неё: если поиск по словам
    # не попал ни во что конкретное, быстрый ответ — сводка по самой
    # сущности, а модели уходят её сделки первыми. Конкретное попадание
    # («Кто купил Ситибанк?» со страницы «Яндекса») остаётся ответом на
    # заданный вопрос — сделки страницы лишь добавляются к нему.
    if intent.kind == "search":
        if about_parties and not _search_is_specific(intent, result.docs, idx):
            own = _answer_deal_parties(context_id, intent.span, idx)
            if own:
                return own
        own = _answer_entity(context_type, context_id, intent, idx)
        if own and own.answer and result.intent == "search" and not _search_is_specific(intent, result.docs, idx):
            merged = own.docs + [d for d in result.docs if d not in own.docs]
            return Retrieval(own.intent, own.answer, merged[:MAX_DEALS_FOR_MODEL], own.subject)
        scoped = _scoped(context_type, context_id, idx)
        if scoped:
            # Найденное — первым: сводка говорит о нём; сделки страницы — контекст для модели.
            merged = result.docs + [d for d in scoped if d not in result.docs]
            result = Retrieval(result.intent, result.answer, merged[:MAX_DEALS_FOR_MODEL], result.subject)
    return result


# --------------------------------------------------------------------------
# Компактная карточка для модели
# --------------------------------------------------------------------------

_MULT_RX = re.compile(TERM_HINTS["мультипликатор"], re.I)


def _clip(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _sentences_with(text: str, rx: re.Pattern, limit: int) -> str:
    out = []
    for sent in re.split(r"(?<=[.;])\s+", text or ""):
        if rx.search(sent) and sent not in out:
            out.append(sent)
    return _clip(" ".join(out), limit) if out else ""


def compact(doc: Doc, facts_chars: int = 320) -> dict[str, Any]:
    """Карточка сделки для модели. Цифры — отдельными полями и целиком.

    До 14 октября 2026 всё описание сделки резалось до 320 знаков одной
    строкой, и оценка с мультипликаторами (они шли третьими) до модели не
    доходила: «мультипликаторы IPO B2B-РТС не раскрывались» при «P/E
    5,4–5,7x, EV/EBITDA 3,9–4,1x» в базе (№14, 30), «у Wink — „Смотрешки“
    отложенных платежей нет» при earn-out до 500 млн ₽ (№7). Теперь оценка
    (`val`), условия (`terms`), доля и фразы с мультипликаторами идут своими
    полями, а урезается только проза (мотивы, контекст, структура)."""
    eco, law = doc.raw.get("eco") or {}, doc.raw.get("law") or {}
    out: dict[str, Any] = {"id": doc.id, "title": doc.title, "date": doc.date}
    if doc.status:
        out["status"] = doc.status
    if has_fact(doc.sum_text):
        out["sum"] = doc.sum_text
    if doc.industries:
        out["industry"] = ", ".join(doc.industries)
    if doc.buyer:
        out["buyer"] = doc.buyer
    if doc.seller:
        out["seller"] = doc.seller
    if doc.target or doc.asset:
        out["subject"] = doc.target or doc.asset
    if doc.advisor_roles:
        out["advisors"] = [f"{r}: {n}" if r else n for r, n in doc.advisor_roles][:4]
    events = _events(doc)
    if events:
        out["events"] = events[:5]
    if has_fact(eco.get("share")):
        out["stake"] = _clip(eco["share"], 260)
    if has_fact(eco.get("val")):
        out["valuation"] = _clip(eco["val"], 700)
    if has_fact(law.get("terms")):
        out["terms"] = _clip(law["terms"], 600)
    if "valuation" not in out or not _MULT_RX.search(out["valuation"]):
        mult = _sentences_with(" ".join(str(x) for x in (eco.get("target_fin"), doc.raw.get("extra")) if has_fact(x)),
                               _MULT_RX, 400)
        if mult:
            out["multiples"] = mult
    prose = []
    for key in ("rationale", "context"):
        if has_fact(eco.get(key)):
            prose.append(str(eco[key]))
    for key in ("appr", "struct"):
        if has_fact(law.get(key)):
            prose.append(str(law[key]))
    if prose:
        out["facts"] = _clip(" ".join(prose), facts_chars)
    return out


def context_for_model(ret: Retrieval) -> str:
    cards = [compact(d) for d in ret.docs[:MAX_DEALS_FOR_MODEL]]
    return json.dumps(cards, ensure_ascii=False)


def suggestions(idx: Index | None = None) -> list[str]:
    """Примеры вопросов для экрана ассистента — из данных, а не из головы:
    у каждого примера гарантированно есть ответ по базе."""
    idx = idx or get_index()
    out: list[str] = []
    # Первой подсказкой стоял вопрос про самую активную фирму каталога («Какие
    # сделки сопровождала VERBA LEGAL?») — партнёр 3 сентября 2026 попросил
    # убрать: имя одного консультанта в подсказке для всех читается как его
    # реклама. Вместо фирмы — самая заполненная отрасль: у неё, как и у фирмы,
    # гарантированно есть ответ по базе (маршрут «industry»), а никого
    # конкретного она не выделяет. Имена фирм в подсказках теперь запрещены
    # тестом (test_assistant_retrieval.py).
    by_industry: dict[str, int] = {}
    for d in idx.docs:
        for ind in d.industries:
            if ind and ind != "Не определена":
                by_industry[ind] = by_industry.get(ind, 0) + 1
    if by_industry:
        top_ind = max(by_industry.items(), key=lambda kv: kv[1])[0]
        out.append(f"Какие сделки были в отрасли «{top_ind}»?")
    years = sorted({d.year for d in idx.docs}, reverse=True)
    if years:
        y = years[1] if len(years) > 1 else years[0]
        out.append(f"Самые крупные сделки {y} года")
    top_company = max(idx.company_deals.items(), key=lambda kv: len(kv[1]), default=None)
    if top_company:
        name = _company_name(idx.companies, top_company[0])
        if name:
            # Имя не склоняем — «у компании «Яндекс»» верно при любом названии.
            # Форму собственности и внешние кавычки снимаем: «у компании
            # «АО «ДОМ.РФ»»» читалось как канцелярит с двойными кавычками.
            short = re.sub(r"^(?:ПАО|АО|ООО|ЗАО|ОАО|НАО|ГК|МКПАО)\s+", "", name).strip()
            if short.startswith("«") and short.endswith("»") and short.count("«") == 1:
                short = short[1:-1]
            quoted = short if ("«" in short or "»" in short) else f"«{short}»"
            out.append(f"Какие сделки были у компании {quoted}?")
    if any("Уход иностранного владельца" in d.themes for d in idx.docs):
        out.append("Кто из иностранных владельцев уходил из России?")
    return out[:4]
