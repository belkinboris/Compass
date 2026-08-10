# -*- coding: utf-8 -*-
"""Приток, шаг 5: проверка карточки чтением — и перенос найденного в поля.

ЗАЧЕМ ЭТОТ ШАГ ВООБЩЕ ПОЯВИЛСЯ. Правила разбора слепы ровно к тому, чего в них
не написали, и слепы молча. За два дня так нашлись: `рудник`, совпадающий
внутри слова «сотрудники»; `\\bкуп…`, не видящий слова «покупает»; действие,
названное существительным («закрыла сделку по покупке»). Каждый раз замер
выглядел законченным, и каждый раз дефект находился не проверкой кода, а
чтением живых данных. Перечислить такие ошибки заранее нельзя — их можно
только вычитывать.

Поэтому после `promote.py` карточку читает человек (в рутине — модель) и
сверяет КАЖДОЕ поле с текстом источника. Замер первого прогона: из 13 карточек,
которые приток добавил сам, поправить было что у 9. Самое опасное найденное —
не пустые поля, а МОЛЧАЛИВО НЕВЕРНЫЕ: у «Дом.РФ» датой стояло 3 августа, хотя
в источнике «сделка была закрыта 4 мая»; у Visa стоял статус «Закрыта», хотя
в источнике «объявила о приобретении», а сумма — «составит».

ГРАНИЦА, КОТОРАЯ ДЕЛАЕТ ЭТО БЕЗОПАСНЫМ. Читающий не «формулирует» и не
«уточняет» — он ПЕРЕНОСИТ. Каждая правка несёт с собой дословную цитату из
источника, и скрипт механически проверяет, что записываемое значение из этой
цитаты выводимо:
  * имя стороны, предмет, сумма — нормализованная подстрока цитаты;
  * дата — день и месяц названы в цитате прописью, год не меняется (менять год
    значит утверждать новое, а не уточнять известное);
  * отрасль — либо слово нашего же словаря стоит в цитате, либо в цитате стоит
    имя компании, у профиля которой в базе эта отрасль;
  * статус — в цитате есть слово, которым этот статус подтверждается.
Плюс, пока сырьё за день лежит на диске, цитата сверяется с НАСТОЯЩИМ текстом
источника, а не только с таблицей. Соврать в таблице так, чтобы скрипт этого
не заметил, нельзя — можно только не заметить дефект.

ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ АВТОМАТИЧЕСКОГО ПРАВИЛА. Тем же, чем «прочитать» от
«угадать». Падежный поиск профиля отрасли (имя с точностью до окончания) как
АВТОМАТИЧЕСКОЕ правило измерен на 1541 карточке и отвергнут: +42 попадания и
+43 ошибки. Здесь он допустим — но только как подтверждение решения, которое
читающий уже принял по тексту, и только на одну карточку, а не на всю базу.

Запуск:
    python3 pipeline/ingest/review.py            # сухой прогон
    python3 pipeline/ingest/review.py --write    # записать
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import draft as drafter                                   # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
RAW = os.path.join(ROOT, 'data', 'inbox', 'raw')
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

MONTHS = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
          'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11,
          'декабря': 12}

# Слово, которым подтверждается статус. Список закрытый: статус — единственное
# поле, которое не цитируется дословно, поэтому обоснование должно быть
# перечислимым, а не «на усмотрение».
#
# «не будет» и «отозв» добавлены при дочитывании gdde6bef5 (Whoosh/«МТС
# Юрент»): карточка стояла «Закрыта», хотя ФАС не согласовала объединение,
# Whoosh отозвал ходатайство, а президент АФК «Система» прямо заявил
# «объединения Whoosh и «Юрент» не будет» — ни одно старое слово списка
# («не состоял», «отказал», «прекращен», «отменен») не встречалось в
# источниках дословно, хотя сделка сорвалась максимально однозначно.
STATUS_WORDS = {
    'Обсуждается': ('переговор', 'рассматрива', 'обсужда', 'изучает', 'намерен', 'планирует'),
    'Подписана': ('объявил', 'подписал', 'заключил', 'договорил', 'соглашени'),
    'Согласование получено': ('одобрил', 'согласовал', 'разрешил', 'предписани'),
    'Закрыта': ('закрыл', 'заверш', 'купил', 'приобрел', 'приобрёл', 'продал',
                'выкупил', 'привлек', 'привлёк', 'стал владельцем', 'перешл', 'перешёл'),
    'Не состоялась': ('не состоял', 'отказал', 'прекращен', 'отменен', 'отменён',
                       'не будет', 'отозв'),
}

# ТИП СДЕЛКИ РЕШАЕТ, ЧТО НАПИСАНО В ПЛАШКЕ СТОРОН, И ПОТОМУ ЕГО НАДО УМЕТЬ
# ПРАВИТЬ. У «Инвестиции» покупатель называется «Инвестор» — и карточка «Флит
# Лизинг» купил 100% долей «МБ РУС Финанс» показывала владельцу «Инвестор»
# вместо «Покупатель», потому что классификатор притока поставил ей
# «Инвестицию». Наполнять линзы у карточки с неверным типом бессмысленно:
# каркас важнее содержимого.
TYPE_WORDS = {
    'M&A': ('100%', 'контрол', 'долей', 'доли', 'акци', 'купил', 'приобрел',
            'приобрёл', 'продал', 'выкупил', 'поглощен', 'присоедин',
            'стало владельцем', 'стал владельцем'),
    'Инвестиция': ('инвестиц', 'раунд', 'вложил', 'миноритарн', 'профинансир',
                   'вошёл в капитал', 'вошел в капитал'),
    'IPO': ('ipo', 'размещени', 'листинг', 'вышл', 'бирж'),
    'Продажа с торгов': ('торг', 'аукцион', 'приватизац', 'банкрот'),
    'Финансирование · структурная сделка': ('кредит', 'заём', 'заем', 'облигац',
                                            'секьюритизац', 'финансирован'),
}

# ---------------------------------------------------------------------------
# Правки к gd057d2c1 (Visa/BioCatch) и g4a10e7a2 (Smallest.ai) сняты вместе с
# самими карточками: 5 августа владелец решил не держать в базе сделки без
# российской стороны, и обе удалены `pipeline/remove_out_of_scope_deals.py`.
# Правка к карточке, которой нет, — это отказ на каждом прогоне.
#
# ТАБЛИЦА ПРАВОК. Прогон 5 августа 2026: 13 карточек, которые приток добавил
# сам, прочитаны против текста источника. `quote` — дословный кусок источника,
# `why` — что именно правило не увидело и почему.
def load_fixes():
    """Собрать правки из всех файлов `fixes/*.py`, в порядке имён.

    Порядок важен: `main()` читает состояние карточки ОДИН раз в начале
    прогона и сверяет каждую запись с ним, поэтому две записи на одно поле
    одной карточки по-прежнему запрещены — теперь ещё и между файлами.
    Проверку держит `test_no_duplicate_fix_for_one_field`.
    """
    import importlib
    import pkgutil
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixes')
    out = []
    for mod in sorted(m.name for m in pkgutil.iter_modules([folder])):
        out.extend(importlib.import_module('fixes.%s' % mod).FIXES)
    return out


# ТАБЛИЦА ПРАВОК ЛЕЖИТ В `fixes/`, ПО ФАЙЛУ НА ПАРТИЮ. Причин две, и вторая
# важнее первой: (1) одна общая таблица росла на ~3 тыс. знаков с каждой
# прочитанной карточки и на дистанции дочитывания всей базы перестала бы
# помещаться в контекст; (2) пока таблица одна, два потока, читающие РАЗНЫЕ
# партии, конфликтуют в git на каждом коммите. Своя партия — свой файл, и
# дочитывание можно вести в несколько сессий одновременно.
#
# `quote` — дословный кусок источника, `why` — что именно правило не увидело.
FIXES = load_fixes()


def flat(s):
    return re.sub(r'[^\wа-яё]+', '', str(s or ''), flags=re.I).lower()


def industries():
    html = open(INDEX, encoding='utf-8').read()
    raw = re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
    return {x.strip().strip('"') for x in raw.split(',') if x.strip()}


def source_texts():
    """Настоящие тексты источников за все дни, что ещё лежат на диске."""
    texts = []
    for folder, load in ((RAW, 'jsonl'), (TRIAGE, 'json')):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            try:
                if load == 'jsonl' and name.endswith('.jsonl'):
                    for line in open(path, encoding='utf-8'):
                        rec = json.loads(line)
                        texts.append(' '.join(str(rec.get(k) or '') for k in ('title', 'summary')))
                elif load == 'json' and name.endswith('.json'):
                    for rec in json.load(open(path, encoding='utf-8')).get('items', []):
                        texts.append(' '.join(str(rec.get(k) or '') for k in ('title', 'summary')))
            except (ValueError, OSError):
                continue
    return [re.sub(r'\s+', ' ', t) for t in texts if t.strip()]


def quote_is_real(quote, texts):
    """Цитата обязана дословно лежать в тексте источника — пока он есть на диске."""
    needle = flat(quote)
    return any(needle in flat(t) for t in texts)


def date_is_supported(old, new, quote):
    """Дату можно уточнить внутри известного года, но не перенести в другой.

    Менять год — значит утверждать новое; тот же порог, что у
    `fix_placeholder_dates.py`. День и месяц обязаны быть названы в цитате
    прописью («закрыта 4 мая»), иначе это не перенос, а догадка.
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(new or '')):
        return 'новая дата не в формате ГГГГ-ММ-ДД'
    if str(old or '')[:4] != new[:4]:
        return 'год не совпадает: уточнять день можно, переносить год — нет'
    day, month = int(new[8:10]), int(new[5:7])
    for word, num in MONTHS.items():
        if num == month and re.search(r'(?<!\d)%d\s+%s' % (day, word), quote, re.I):
            return None
    return 'в цитате нет «%d %s»' % (day, [w for w, n in MONTHS.items() if n == month][0])


def sum_is_supported(new, quote):
    """Сумма — сборка из чисел цитаты по нашему формату, а не дословный кусок.

    «370–430 млн ₽ (по оценке)» не лежит дословно в «могла составить от
    370 млн до 430 млн руб.» — мешают «от…до» и знак рубля, — но каждое ЧИСЛО
    и единица обязаны лежать. Проверяем: все числа нового значения стоят в
    цитате отдельными числами; единица названа (полные «миллиона»/«миллиарда»
    считаются); валюта в цитате названа; пометка «(по оценке)» стоит
    тогда и ТОЛЬКО тогда, когда цитата сама говорит об оценке («оценивает»,
    «могла составить», «по оценке») — записать оценку как факт нельзя, как и
    факт как оценку.

    Валюта — только значком (правило CLAUDE.md): ₽ ПОСЛЕ числа, $ и € ПЕРЕД
    числом — 156 карточек базы уже несут суммы в долларах, и правило обязано
    подтверждать их, а не только рублёвую запись."""
    m = re.match(r'^(?:([$€])\s*)?(\d[\d\s,.]*?)(?:\s*[–—-]\s*(\d[\d\s,.]*?))?\s*'
                 r'(млн|млрд)(?:\s*(₽))?(\s*\(по оценке\))?$', str(new or ''))
    if not m or not (m.group(1) or m.group(5)):
        return ('формат суммы не разобран: ожидается «N[–M] млн|млрд ₽ '
                '[(по оценке)]» или «$/€N[–M] млн|млрд [(по оценке)]»')
    if m.group(1) and m.group(5):
        return 'сумма не может нести знак валюты дважды'
    for num in filter(None, (m.group(2), m.group(3))):
        if not re.search(r'(?<![\d,.])%s(?![\d])' % re.escape(num.strip()), quote):
            return 'числа «%s» нет в цитате' % num.strip()
    unit_rx = {'млн': r'млн|миллион', 'млрд': r'млрд|миллиард'}[m.group(4)]
    if not re.search(unit_rx, quote, re.I):
        return 'в цитате нет «%s»' % m.group(4)
    currency_rx = {'₽': r'руб|₽', '$': r'\$|доллар', '€': r'€|евро'}[m.group(5) or m.group(1)]
    if not re.search(currency_rx, quote, re.I):
        return 'в цитате нет валюты «%s»' % (m.group(5) or m.group(1))
    estimate = bool(re.search(r'оцен|мог(?:ла|ло)?\s+состав', quote, re.I))
    if m.group(6) and not estimate:
        return 'пометка «(по оценке)» не подтверждена цитатой'
    if not m.group(6) and estimate:
        return 'цитата говорит об оценке — нужна пометка «(по оценке)»'
    return None


def _same_word(a, b):
    """Одно слово с точностью до окончания: общее начало ≥3 знаков и ≥60%
    длины короткого. Порог не выдуман — это тот же критерий, которым
    `extract_seller` подтверждает имя в косвенном падеже. «Вера» и «Вета» им
    НЕ склеиваются: общее начало «Ве» — два знака."""
    a, b = a.lower(), b.lower()
    if a == b:
        return True
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n >= 3 and n >= 0.6 * min(len(a), len(b))


def name_is_supported(new, quote):
    """Имя стороны — дословно ИЛИ слово в слово с точностью до окончаний.

    Строгая подстрока не работает на русских падежах: «Александра Лютикова»
    (как надо писать на экране) не встречается в тексте «„Интел-руал"
    принадлежала … Александре Лютиковой и Айбеку Баймахану» — там дательный.
    Отменять проверку нельзя, её МОЖНО ЗАМЕНИТЬ более слабой, но всё ещё
    механической (урок CLAUDE.md «инвариант можно заменить, но не отменить»):
    каждое слово результата обязано лечь на слово цитаты, отличаясь только
    окончанием. Правило проверено на себе — чужое имя его не проходит."""
    words = [w for w in re.split(r'[^\wа-яё]+', str(new), flags=re.I) if w]
    quote_words = [w for w in re.split(r'[^\wа-яё]+', str(quote), flags=re.I) if w]
    if not words:
        return 'пустое имя'
    for w in words:
        if not any(_same_word(w, q) for q in quote_words):
            return 'слова «%s» нет в цитате даже с точностью до окончания' % w
    return name_is_nominative(new)


def name_is_nominative(new):
    """Имя стороны обязано стоять В ИМЕНИТЕЛЬНОМ падеже.

    ЗАЧЕМ ОТДЕЛЬНАЯ ПРОВЕРКА. Послабление на падеж выше — «каждое слово ложится
    на слово цитаты с точностью до окончания» — задумано, чтобы РАЗРЕШИТЬ
    «Александра Лютикова» при цитате «принадлежала … Александре Лютиковой».
    Но оно симметрично: ту же проверку проходит и сама цитатная форма. Так в
    базу попали «Виктору Маршеву» (дательный от «принадлежащее») и «Автодома»
    (родительный после «у»), и владелец нашёл второе в очереди 9 августа.
    Дословность падеж не различает — значит, за форму имени должно отвечать
    отдельное правило, а не внимательность пишущего.

    Судим по ПЕРВОМУ слову и только если оно кириллическое, длиннее трёх букв
    и не аббревиатура: «Freedom Тимура Турлова» — это Freedom, чей владелец
    Турлов, и родительный там на своём месте. Порог «нет именительного-
    конкурента со score не ниже 0,3 от лучшего» — тот же, что в casing.py: без
    него признак не видит «Автодома» (именительный мн. числа со score 0,024).
    """
    try:
        from casing import _morph, _nominative_rival
    except ImportError:                       # pymorphy не установлен — не мешаем
        return None
    text = str(new or '').strip().lstrip('«»"“”„(')
    if not text:
        return None
    word = re.split(r'[\s,(]+', text)[0].strip('«»"“”„()')
    if not re.match(r'^[А-Яа-яЁё-]{4,}$', word) or word.isupper():
        return None
    parses = _morph.parse(word)
    best = max(parses, key=lambda p: p.score)
    if best.tag.case in (None, 'nomn'):
        return None
    if 'Name' in best.tag:
        # ЛИЧНОЕ ИМЯ — ОСОБЫЙ СЛУЧАЙ, И ПОРОГ ПО ВЕРОЯТНОСТИ ЗДЕСЬ ВРЁТ.
        # «Александра» — это и родительный от «Александр» (score 0,764), и
        # именительный женского имени «Александра» (0,083); вероятности
        # отражают частоту в корпусе, а не то, о ком речь в этой карточке.
        # Поэтому для имён достаточно ЛЮБОГО именительного разбора, каким бы
        # редким он ни был. «Виктору» и «Сергея» именительного не дают вовсе —
        # их правило по-прежнему ловит.
        if any(p.tag.case == 'nomn' for p in parses):
            return None
    elif any(p.tag.case == 'nomn' and p.score >= best.score * 0.3 for p in parses):
        # Только порог по вероятности. `_nominative_rival` из casing.py здесь
        # НЕ подходит: он дополнительно щадит слово, у которого именительный
        # даёт ту же лемму, — и «Автодома» (родительный ед. против
        # именительного мн. одного и того же «автодом») проходил бы мимо.
        return None
    return ('имя стороны в косвенном падеже («%s», %s) — на экран оно пойдёт '
            'как есть; поставьте именительный' % (word, best.tag.case))


def industry_is_supported(new, quote, companies, inds):
    """Отрасль — либо слово нашего словаря, либо профиль компании из цитаты."""
    if new not in inds:
        return 'отрасли %r нет в списке INDUSTRIES' % new
    if drafter.industry_by_words(quote) == new:
        return None
    # Профиль компании: имя ищется с падежным окончанием. Как АВТОМАТИЧЕСКОЕ
    # правило это измерено и отвергнуто (+42 попадания, +43 ошибки на 1541
    # карточке); здесь оно лишь подтверждает решение, уже принятое по тексту.
    for comp in companies.values():
        core = re.sub(r'^(ООО|АО|ПАО|ЗАО|ГК|МКООО)\s+', '', str(comp.get('name') or '')).strip('«» "')
        if len(core) < 5 or comp.get('ind') != new:
            continue
        stem = core[:-1]
        if re.search(r'(?<![\wа-яё])%s[а-яё]{0,3}(?![\wа-яё])' % re.escape(stem), quote, re.I):
            return None
    return 'ни слово словаря, ни профиль компании из цитаты не дают «%s»' % new


def source_urls():
    """Адреса, которые приток действительно забирал: приложить можно только их."""
    urls = set()
    if os.path.isdir(RAW):
        for name in sorted(os.listdir(RAW)):
            if not name.endswith('.jsonl'):
                continue
            for line in open(os.path.join(RAW, name), encoding='utf-8'):
                try:
                    url = json.loads(line).get('url')
                except ValueError:
                    continue
                if url:
                    urls.add(str(url))
    return urls


def get_field(card, field):
    """Поле карточки, включая вложенные ('eco.val', 'law.appr').

    Экономика и право лежат объектами eco/law, а факты из статей чаще всего
    относятся именно к ним: дисконт — в «Оценку», лицензию OFAC — в
    «Согласования». Точка в имени поля — путь внутрь объекта."""
    obj = card
    for part in str(field).split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def set_field(card, field, value):
    parts = str(field).split('.')
    obj = card
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def already_applied(fix, card):
    """Правка уже в базе — прогон должен быть идемпотентным, а не падать."""
    if fix['field'] == 'src':
        return any(len(s) > 1 and s[1] == fix['new'][1] for s in card.get('src') or [])
    return get_field(card, fix['field']) == fix['new']


def check(fix, card, texts, companies, inds, urls=frozenset()):
    """Список причин, по которым правку принимать НЕЛЬЗЯ."""
    bad = []
    field, new, quote = fix['field'], fix['new'], fix['quote']
    if field == 'src':
        # ВТОРОЙ ИСТОЧНИК — НЕ УКРАШЕНИЕ. Об одной сделке пишут несколько
        # изданий, и факт нередко есть только у одного: материал упаковки
        # «Полекса» назван у mergers.ru и не назван у «Коммерсанта». Приложить
        # можно только адрес, который приток РЕАЛЬНО забирал, — иначе ссылка
        # берётся из головы, а это ровно то, чего мы избегаем.
        if not (isinstance(new, list) and len(new) == 2 and str(new[1]).startswith('http')):
            bad.append('источник должен быть парой [имя, http-адрес]')
        elif urls and new[1] not in urls:
            bad.append('такого адреса нет среди забранных источником записей')
        if texts and not quote_is_real(quote, texts):
            bad.append('цитаты нет в тексте источника')
        return bad
    if get_field(card, field) != fix['old']:
        bad.append('поле уже другое: в базе %r, ожидали %r' % (get_field(card, field), fix['old']))
    if texts and not quote_is_real(quote, texts):
        bad.append('цитаты нет в тексте источника')
    if field == 'date':
        problem = date_is_supported(fix['old'], new, quote)
        if problem:
            bad.append(problem)
    elif field == 'ind':
        problem = industry_is_supported(new, quote, companies, inds)
        if problem:
            bad.append(problem)
    elif field == 'status':
        if new not in STATUS_WORDS:
            bad.append('неизвестный статус %r' % new)
        elif not any(w in quote.lower() for w in STATUS_WORDS[new]):
            bad.append('в цитате нет слова, подтверждающего статус «%s»' % new)
    elif field == 'type':
        if new not in TYPE_WORDS:
            bad.append('неизвестный тип сделки %r — их ровно пять' % new)
        elif not any(w in quote.lower() for w in TYPE_WORDS[new]):
            bad.append('в цитате нет слова, подтверждающего тип «%s»' % new)
    elif field == 'sum' and new is not None:
        problem = sum_is_supported(new, quote)
        if problem:
            bad.append(problem)
    elif new is not None:
        # Имя, предмет, сумма — только перенос, дословно.
        if flat(new) not in flat(quote):
            # У имён сторон есть послабление на падеж — и только у них:
            # предмет и прочий текст обязаны лежать дословно, иначе
            # «переформулировал» станет неотличимо от «перенёс».
            if field in ('seller', 'buyer_name') and not name_is_supported(new, quote):
                pass
            else:
                bad.append('значение не лежит в цитате дословно')
    return bad


def _self_check():
    """Правила проверяются на себе — иначе они молча пропустят выдумку."""
    # Дословность: подмена одного слова правило НЕ проходит.
    q = 'Продавцом актива выступала сеть сервисных офисов Business Club.'
    assert flat('Business Club') in flat(q)
    assert flat('Business Centre') not in flat(q)
    # Дата: день и месяц обязаны быть в цитате, год менять нельзя.
    assert date_is_supported('2026-08-03', '2026-05-04', 'сделка была закрыта 4 мая') is None
    assert date_is_supported('2026-08-03', '2026-05-05', 'сделка была закрыта 4 мая')
    assert date_is_supported('2026-08-03', '2025-05-04', 'сделка была закрыта 4 мая')
    # Статус: слово-подтверждение обязательно.
    assert any(w in 'visa объявила о приобретении' for w in STATUS_WORDS['Подписана'])
    assert not any(w in 'visa объявила о приобретении' for w in STATUS_WORDS['Не состоялась'])
    # Имя стороны в косвенном падеже: своё проходит, чужое — нет.
    q_names = ('До нынешней смены собственника «Интел-руал» принадлежала гражданам '
               'Казахстана Александре Лютиковой и Айбеку Баймахану.')
    assert name_is_supported('Александра Лютикова и Айбек Баймахан', q_names) is None
    assert name_is_supported('Иван Петров', q_names)          # чужое имя целиком
    assert name_is_supported('Александра Петрова', q_names)   # подменена половина
    assert not _same_word('Вера', 'Вета')                     # короткие не склеиваются
    # Падеж имени: цитатная форма НЕ проходит, именительная проходит.
    q_marshev = ('Ранее сетью управляло ООО "Сибнефтепродукт", принадлежащее '
                 'Виктору Маршеву.')
    assert name_is_supported('Виктору Маршеву', q_marshev)     # дательный — отказ
    assert name_is_supported('Виктор Маршев', q_marshev) is None
    q_avtodom = 'приобрел у «Автодома» 100% долей ООО «МБ РУС Финанс»'
    assert name_is_supported('«Автодома»', q_avtodom)          # родительный — отказ
    assert name_is_supported('«Автодом»', q_avtodom) is None
    # Латиница впереди — родительный после неё законен и правилом не трогается.
    assert name_is_nominative('Freedom Тимура Турлова') is None
    assert name_is_nominative('Банк России') is None
    # Сумма: числа и единица обязаны лежать в цитате, оценка — быть помеченной.
    q_est = 'стоимость актива могла составить от 370 млн до 430 млн руб. без учета обременений'
    assert sum_is_supported('370–430 млн ₽ (по оценке)', q_est) is None
    assert sum_is_supported('500 млн ₽ (по оценке)', q_est)      # чужое число
    assert sum_is_supported('370–430 млн ₽', q_est)              # оценка без пометки
    assert sum_is_supported('370–430 млрд ₽ (по оценке)', q_est)  # чужая единица
    q_fact = 'Дачу Строгановых в Москве продали за 552,6 миллиона рублей'
    assert sum_is_supported('552,6 млн ₽', q_fact) is None
    assert sum_is_supported('552,6 млн ₽ (по оценке)', q_fact)   # факт как оценка
    assert sum_is_supported('7–8 млрд ₽ (по оценке)',
                            'стоимость сделки оценивает в 7–8 млрд руб.') is None


def stamp_reviewed(card, day=None):
    """Отметка «карточку читали против источника» — даже если правок не нашлось.

    Без неё «не читали» и «читали, добавить нечего» выглядят на карточке
    одинаково (оба — прочерки в eco/law), и пропуск шага чтения незаметен,
    пока источник не откроет человек: ровно так владелец 8 августа нашёл
    карточку NexTouch/«Квант» с пустыми линзами при 326 КБ текста в кэше.
    С отметкой очередь «что ещё не прочитано» — это запрос по базе, а не
    ручная проверка. Идемпотентна: уже стоящую дату не переписывает, чтобы
    повторный прогон не выдавал старое чтение за свежее."""
    if not card.get('reviewed'):
        card['reviewed'] = day or datetime.now(timezone.utc).date().isoformat()
        return True
    return False


def stamp_deep_researched(card, day=None):
    """Отметка «карточку довели до стандарта января-июня 2026», отдельная от
    `reviewed`. Владелец 10 августа: не гнаться за числом источников, а
    исследовать по карточке всё, что вообще есть в интернете, пока не
    исчерпано честно. Это НЕ синоним `reviewed` — та ставится на ЛЮБУЮ
    правку, эта только по явному заявлению читающего (`--mark-deep`), потому
    что «прочитал источник» и «обыскал вопрос со всех сторон» — разная
    планка, и первое не должно тихо сходить за второе. Идемпотентна, как и
    `stamp_reviewed`."""
    if not card.get('deep_researched'):
        card['deep_researched'] = day or datetime.now(timezone.utc).date().isoformat()
        return True
    return False


def main(write=False, mark_read=(), mark_deep=()):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    # Черновики предпросмотра проверяются тем же механизмом, что и карточки
    # базы: читающий правит их ДО того, как владелец увидит проект поста, —
    # чтобы на модерацию приходил уже вычитанный черновик.
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    cards = {d['id']: d for d in data['deals']}
    cards.update({c['id']: c for c in pending['cards']})
    inds, texts = industries(), source_texts()
    print('Правок в таблице: %d | текстов источников на диске: %d'
          % (len(FIXES), len(texts)))
    if not texts:
        print('ВНИМАНИЕ: сырья на диске нет — цитаты сверить не с чем, проверяется')
        print('только состояние полей. Это ослабленная проверка, а не полная.')

    urls = source_urls()
    ok, refused, done = [], [], 0
    for fix in FIXES:
        card = cards.get(fix['id'])
        if not card:
            refused.append((fix, ['карточки %s нет в базе' % fix['id']]))
            continue
        if already_applied(fix, card):
            done += 1
            continue
        bad = check(fix, card, texts, data['companies'], inds, urls)
        (refused if bad else ok).append((fix, bad))

    if done:
        print('  уже применено раньше: %d' % done)
    for fix, _ in ok:
        print('  ПРАВИМ   %s %-11s %r -> %r' % (fix['id'], fix['field'],
                                                str(fix['old'])[:34], str(fix['new'])[:40]))
        print('           %s' % fix['why'])
    for fix, bad in refused:
        print('  ОТКАЗ    %s %-11s %s' % (fix['id'], fix['field'], '; '.join(bad)))

    # Карточки, прочитанные БЕЗ правок (--mark-read): честный случай «читал,
    # добавить нечего» — источник беден, а не шаг пропущен. Требует, чтобы
    # карточка существовала: опечатка в id не должна молча съесть отметку.
    to_mark = []
    for cid in mark_read:
        if cid not in cards:
            refused.append((dict(id=cid, field='reviewed'),
                            ['карточки %s нет ни в базе, ни в предпросмотре' % cid]))
        else:
            to_mark.append(cid)

    # --mark-deep: явное заявление «эту карточку исследовал по стандарту
    # 2026 года целиком, а не только сверил одно поле» — отдельная планка от
    # mark_read, см. stamp_deep_researched.
    to_mark_deep = []
    for cid in mark_deep:
        if cid not in cards:
            refused.append((dict(id=cid, field='deep_researched'),
                            ['карточки %s нет ни в базе, ни в предпросмотре' % cid]))
        else:
            to_mark_deep.append(cid)

    print('\nпринято %d, отклонено %d' % (len(ok), len(refused)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1 if refused else 0
    if refused:
        print('Есть отклонённые правки — не пишем НИЧЕГО: таблицу надо починить целиком.')
        return 1

    for fix, _ in ok:
        card = cards[fix['id']]
        if fix['field'] == 'src':
            card.setdefault('src', []).append(list(fix['new']))
            continue
        assert get_field(card, fix['field']) == fix['old'], 'состояние поля изменилось'
        set_field(card, fix['field'], fix['new'])
        # Свидетельство о стороне обязано указывать на то, что теперь в поле,
        # иначе на карточке останется ссылка на снятое значение.
        role = {'buyer_name': 'buyer', 'asset': 'target', 'seller': 'seller'}.get(fix['field'])
        if role and card.get('party_evidence'):
            if fix['new'] is None:
                card['party_evidence'].pop(role, None)
            else:
                url = next((s[1] for s in card.get('src') or []
                            if len(s) > 1 and str(s[1]).startswith('http')), None)
                card['party_evidence'][role] = [{'value': fix['new'], 'field': fix['field'],
                                                 'method': 'human_review', 'url': url}]
            if not card['party_evidence']:
                card.pop('party_evidence')

    # Отметка прочтения: и на карточки с правками (включая применённые в
    # прошлых прогонах — их читали, просто штампа тогда ещё не было), и на
    # прочитанные без правок (--mark-read).
    stamped = 0
    for cid in {f['id'] for f in FIXES if f['id'] in cards} | set(to_mark):
        if stamp_reviewed(cards[cid]):
            stamped += 1

    stamped_deep = 0
    for cid in to_mark_deep:
        if stamp_deep_researched(cards[cid]):
            stamped_deep += 1

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if pending['cards']:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d правок, %d отметок прочтения, %d отметок глубокого '
          'исследования в %s'
          % (len(ok), stamped, stamped_deep, os.path.relpath(DATA, ROOT)))
    return 0


if __name__ == '__main__':
    _args = sys.argv[1:]
    _flags = ('--write', '--mark-read', '--mark-deep')
    _ids = [a for a in _args if a not in _flags]
    sys.exit(main(write='--write' in _args,
                  mark_read=_ids if '--mark-read' in _args else (),
                  mark_deep=_ids if '--mark-deep' in _args else ()))
