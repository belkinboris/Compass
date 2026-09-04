# -*- coding: utf-8 -*-
"""Публикация в Telegram: один пост на сделку, обновление — правкой поста.

ЗАЧЕМ. Об одной сделке пишут пять изданий за два дня. Пять постов об одном и
том же — это спам, поэтому правило простое: одна сделка — один пост. Появился
новый факт (сумма, сторона, консультант) — тот же пост редактируется, а внизу
появляется строка «⟳ Обновлено: …». Уведомление о правке приходит НЕ всегда:
только когда изменилось то, ради чего пост читают.

ЧТО СЧИТАЕТСЯ ЗНАЧИМЫМ (`SIGNIFICANT`). Сумма, покупатель, продавец, предмет,
статус сделки и консультанты. Появление такого факта — повод для короткого
уведомления ответом на пост. Всё остальное (уточнение формулировки, ещё один
источник, отрасль) правит пост молча. Отдельно оговорено закрытие сделки:
переход статуса в «Закрыта» — событие, а не переформулировка, и о нём
уведомляем.

ПОЧЕМУ НЕ НОВЫЙ ПОСТ НА КАЖДОЕ ОБНОВЛЕНИЕ. Лента должна оставаться списком
сделок, а не списком новостей: юрист ищет «что было со сделкой X», а не «что
писали в среду». Пост со сделкой — это её карточка в телеграме, и она живёт
столько же, сколько карточка на сайте.

ЧТО ЭТОТ МОДУЛЬ НЕ ДЕЛАЕТ. Он ничего не отправляет: отправка — отдельный шаг,
которому нужен токен бота и который живёт там, где есть сеть. Здесь только
текст, разбор изменений и решение «уведомлять или нет» — всё это чистые
функции, и потому проверяются тестами без сети.

Запуск (пример поста по случайной карточке базы):
    python3 pipeline/publish/format_post.py --sample
"""
import json
import os
import re
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# `_same_word` (падежный компаратор — общее начало ≥3 знаков и ≥60% короткого
# слова) уже написан и проверен на себе в review.py — не дублируем его здесь.
# format_post.py остаётся импортируемым и напрямую (`python3 …/format_post.py
# --sample`), и как модуль изнутри send_telegram.py — поэтому сам добавляет
# путь до pipeline/ingest, а не полагается на то, что это уже сделал вызывающий.
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_INGEST = os.path.join(ROOT, 'pipeline', 'ingest')
if _INGEST not in sys.path:
    sys.path.insert(0, _INGEST)
from review import _same_word  # noqa: E402
# Адрес витрины, который уходит в ссылки телеграм-поста. Домен был вписан
# в код числом — и не тот: сайт живёт на projectcompass.ru, а посты вели бы
# читателя на kompas.deals. Берём из переменной окружения `APP_BASE_URL` (той
# же, что уже используется для ссылок из писем), а вписанное значение — лишь
# запасное на случай, если переменная не задана.
SITE = (os.environ.get('APP_BASE_URL') or 'https://projectcompass.ru').rstrip('/')

SIGNIFICANT = ('sum', 'buyer', 'buyer_name', 'seller', 'target', 'asset', 'status', 'advisers', 'events')

PLACEHOLDER = re.compile(
    r'^\s*(?:[—-]|н/д|нет\s+данных|не\s+раскры[а-яё]*|не\s+привлекал[а-яё]*'
    r'|(?:публично|официально)\s+не\s+[а-яё]+)\s*\.?\s*$', re.I)


def has(value):
    v = re.sub(r'\s+', ' ', str(value or '')).strip()
    return bool(v) and not PLACEHOLDER.match(v)


def _plural(n, one, few, many):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def esc(text):
    return (str(text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ЭТАП 9 (реакция партнёров на пост «Алор брокер»): «Он пишет в предмет кусок
# фразы из заголовка… смысла писать стороны и предмет тогда нет вообще».
# Строка стороны/предмета печатается, только если несёт хотя бы одно значащее
# слово, которого в заголовке (и в уже напечатанной части поста) нет ДАЖЕ С
# ТОЧНОСТЬЮ ДО ОКОНЧАНИЯ — иначе она дословный или падежный повтор заголовка,
# и такая строка честнее не показывать вовсе, чем показать как факт.
#
# Строгая substring-проверка здесь не годится: «неназванную» (заголовок) и
# «неназванная» (предмет) — разные строки по символам, но одно и то же слово.
# Замер по базе (24 августа 2026, substring-приближение) — 91 карточка из 207
# с `asset` и 461 сторона из 968 текстом дословно повторяют заголовок; после
# перехода на пословный компаратор с падежным допуском число НЕ падает — оно
# растёт (см. `pipeline/publish/measure_headline_echo.py`), потому что
# substring недосчитывал падежные пары.
_WORD_RE = re.compile(r'[a-zA-Zа-яёА-ЯЁ0-9]+', re.I)

# Служебные слова НЕ считаются «новизной» сами по себе (частый предлог/союз,
# совпавший с заголовком случайно, не делает строку содержательной) — но их
# отсутствие в заголовке тоже не подтверждает новизну. Список — стандартный
# для русского языка, не наш собственный домен.
_STOPWORDS_RU = frozenset("""
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли
если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без
будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой
совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех
никогда можно при наконец два об другой хоть после над больше тот через эти
нас про всего них какая много разве три эту моя впрочем хорошо свою этой перед
иногда лучше чуть том нельзя такой им более всегда конечно всю между
""".split())


def _significant_words(text):
    """Слова длиннее одной буквы, кроме стоп-слов, в нижнем регистре."""
    return [w.lower() for w in _WORD_RE.findall(str(text or ''))
            if len(w) > 1 and w.lower() not in _STOPWORDS_RU]


def has_novelty(candidate, reference):
    """Есть ли в `candidate` хотя бы одно значащее слово, которого нет в
    `reference` даже с точностью до окончания (`_same_word`)? Пустой
    `candidate` — не новизна."""
    cand_words = _significant_words(candidate)
    if not cand_words:
        return False
    ref_words = _significant_words(reference)
    return any(not any(_same_word(cw, rw) for rw in ref_words) for cw in cand_words)


def names_party_upfront(name, detail, limit=60):
    """Деталь ДОСЛОВНО называет сторону, и имя стоит в начале фразы, а не в
    её хвосте. Тогда имя перед тире — второй такой же повтор, и его не печатаем.

    Строже, чем `has_novelty`, НАМЕРЕННО, и это измерено. Для «Предмета» мягкой
    проверки по основам слов хватает, а для имени СТОРОНЫ она опасна дважды
    (замер 4 сентября 2026 по всем 1589 карточкам; мягкое правило меняло 65
    строк «Покупатель», из них ломало 48):

    * «Займер» ложится основой на «займы», «Газпром нефть» — на «Нефтяная
      компания группы «Газпром»»: имени в детали НЕТ, а мягкая проверка
      считает его повтором. Убери имя — и читатель не узнает покупателя вовсе
      (38 строк; ровно дефект Pridex/Multispace, 25 августа: строка обязана
      нести имя). Поэтому сверка ДОСЛОВНАЯ, а не по основам.
    * Имя в детали есть, но в хвосте чужой фразы: «Московская сеть клиник
      DocMed привлекла 200 млн ₽ от инвестиционного фонда «ТилТех Капитал»».
      Подлежащее там — цель, а не покупатель, и строка без имени впереди
      читалась бы как «покупатель — DocMed» (10 строк). Поэтому имя обязано
      стоять В НАЧАЛЕ детали.
    """
    n, d = _flat_for_match(name), _flat_for_match(detail)
    if not n or not d:
        return False
    pos = d.find(n)
    return 0 <= pos <= limit


def _flat_for_match(text):
    """Нижний регистр, единые кавычки, схлопнутые пробелы — для ДОСЛОВНОГО
    сравнения имени с текстом (кавычки в базе разнобойные: «Афкап», "Афкап")."""
    t = re.sub(r'<[^>]+>', ' ', str(text or '')).lower().replace('\u0451', '\u0435')
    t = re.sub(r'[\u00ab\u00bb"\u201c\u201d\u201e\u2018\u2019\']', '"', t)
    return re.sub(r'\s+', ' ', t).strip()


def _sentences(text):
    """Разбить на предложения тем же признаком, что и везде в проекте:
    «точка/!/? + пробел + заглавная» — надёжнее списка сокращений (CLAUDE.md:
    «18,8 млрд руб.», «Fortum Russia B.V.» ошибаются в безопасную сторону,
    список сокращений — нет)."""
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not text:
        return []
    parts = re.split(r'(?<=[.!?])\s+(?=[А-ЯЁA-Z])', text)
    return [p.strip() for p in parts if has(p)]


# Предложение о ТОМ, КАК НОВОСТЬ СТАЛА ИЗВЕСТНА, — не факт о сделке и не
# пояснение стороны. Найдено владельцем 30 августа на живом посте
# Транснефть/Газпромбанк (g60f99ba6): «Покупатель: «Транснефть» — О покупке
# ... сообщила в финансовой отчетности по МСФО...» — предложение объясняет,
# кто и где СООБЩИЛ, а не кто покупатель. Оно ещё и выиграло приоритет
# «имя в кавычках» в _pick_novel_sentences — имя стояло в кавычках именно
# в мета-предложении. Замер по всем 1575 карточкам: с этим детектором
# срабатывание ровно одно (эта карточка), ложных ноль. Детектор нарочно
# требует ДВУХ признаков сразу — глагол сообщения И канал раскрытия:
# «Компания сообщила, что покупка усилит её позиции» (глагол без канала) —
# это содержание, его фильтровать нельзя.
_REPORTING_VERB = re.compile(
    r'(сообщил\w*|сообщается|говорится|стало известно|следует из|указано в'
    r'|пишет|пишут|со ссылкой на|по информации|передает|передаёт)', re.I)
_DISCLOSURE_CHANNEL = re.compile(
    r'(отчетност|отчётност|отчете|отчёте|пресс-релиз|сообщени'
    r'|на сайте|издани|СМИ|раскрыти|релиз)', re.I)


def _is_reporting_meta(sentence):
    return bool(_REPORTING_VERB.search(sentence) and _DISCLOSURE_CHANNEL.search(sentence))


def _pick_novel_sentences(text, reference, limit=2, max_chars=280, drop=None):
    """Дословные предложения из `text`, каждое — с новизной к постоянно
    расширяющемуся `reference` (уже выбранные предложения тоже входят в
    референс — второе предложение не должно повторять первое). Не сочиняем
    ничего нового, только выбираем ГОТОВЫЕ предложения карточки.
    `drop` — необязательный предикат-отсев кандидатов: НЕ глобальный фильтр,
    а инструмент вызывающего. Мета-фильтр раскрытия нарочно не встроен сюда
    безусловно: в детали «Предмета» предложение «выручка выросла, следует из
    отчетности» несёт факт вместе с атрибуцией, и терять его нельзя — а вот
    пояснению СТОРОНЫ (см. _party_detail) такое предложение не годится никогда.

    Предложение с именем в кавычках («ООО «Счастливая работа»») идёт
    первым кандидатом — оно почти всегда точнее называет предмет/сторону,
    чем соседнее предложение без имени (пример находки на карточке-образце
    HeadHunter/Happy Job, `gebead2e8`: первое по порядку предложение
    `eco.target_fin` — список учредителей, второе — точное юрлицо; без
    этого приоритета в пост уходил бы список фамилий вместо имени
    компании). Порядок остальных предложений не трогаем — это выбор МЕЖДУ
    готовыми предложениями, а не переписывание текста."""
    sentences = [s for s in _sentences(text) if not (drop and drop(s))]
    ordered = sorted(sentences, key=lambda s: 0 if '«' in s else 1)
    picked, total, ref = [], 0, reference
    for s in ordered:
        if len(picked) >= limit:
            break
        if total + len(s) > max_chars:
            continue          # это предложение не влезло — пробуем следующее, не сдаёмся
        if has_novelty(s, ref):
            picked.append(s)
            total += len(s) + 1
            ref = ref + ' ' + s
    # Сохранить порядок исходного текста среди отобранных — сортировка выше
    # была только для ВЫБОРА, не для итоговой последовательности.
    picked_set = set(picked)
    return [s for s in sentences if s in picked_set]


def party_names(deal, companies):
    """Стороны так, как их видит читатель: имя из профиля либо имя текстом."""
    def name(ref, text):
        if ref and companies.get(ref):
            return companies[ref]['name']
        return text if has(text) else None
    seller = name(deal.get('seller_id'), deal.get('seller'))
    buyer = name(deal.get('buyer'), deal.get('buyer_name'))
    asset = name(deal.get('target'), deal.get('asset'))
    if not asset and deal.get('asset_id') and companies.get(deal['asset_id']):
        asset = companies[deal['asset_id']]['name']
    return seller, asset, buyer


def needs_review_before_post(deal):
    """П2-9: карточка идёт на дочитывание ПЕРЕД первым постом, если на момент
    отправки у неё нет ни одного смыслового поля сверх заголовка — ВСЕ поля
    `eco`/`law` пусты или заглушки, `extra` пуст, консультантов нет — и её ещё
    не читали (`reviewed` не стоит). Так вышла карточка «Алор брокер» 24
    августа: источник (Frank Media) был живой, но карточка ушла постом со
    всеми пустыми линзами, потому что шаг чтения её просто не коснулся.

    НЕ новый тормоз E9: пустая, но УЖЕ прочитанная карточка (источник честно
    пуст — `reviewed` стоит) публикуется как есть. Различие «не читали» и
    «читали, добавить нечего» уже записано уроком CLAUDE.md; это же правило
    здесь, только гейт стоит перед ПОСТОМ, а не перед оценкой заполненности.

    Сама читка — не дело этой функции: она сетевая и требует модели (тот же
    `review.py`-путь, что дневной обыск G7), а `format_post`/`send_telegram`
    обязаны оставаться чистыми и проверяемыми без сети. Функция только решает,
    ПОРА ли читать, — вызывающий (рутина публикации) решает, ЧТО с этим
    делать."""
    if deal.get('reviewed'):
        return False
    if has(deal.get('extra')):
        return False
    eco = deal.get('eco') or {}
    law = deal.get('law') or {}
    fields = (eco.get('sum'), eco.get('share'), eco.get('val'), eco.get('target_fin'),
              eco.get('fin'), eco.get('finadv'), eco.get('rationale'), eco.get('context'),
              law.get('struct'), law.get('appr'), law.get('terms'))
    if any(has(v) for v in fields):
        return False
    adv = law.get('adv') or []
    if any(has(a[1]) for a in adv if isinstance(a, (list, tuple)) and len(a) > 1):
        return False
    return True


def _adviser_key(name):
    """Ключ, по которому две записи считаются ОДНОЙ фирмой. Точного совпадения
    строк мало: владелец 31 августа 2026 увидел на карточке «два раза АЛРУД»
    (кириллицей и латиницей из двух прогонов обогащения), а в посте — «Aspring
    Capital» и «Aspring Capital (инвестиционный банк)». Скобочное уточнение и
    правовая форма к имени не относятся; латиницу и кириллицу сводит только
    список пар из каталога сайта, поэтому здесь — то, что можно сделать без
    него: имя без скобок, без правовой формы и без регистра."""
    t = re.sub(r'\s*\([^)]*\)', ' ', str(name or ''))
    t = re.sub(r'\b(ооо|оао|зао|пао|ао|мка|ак|адвокатское\s+бюро|юридическая\s+фирма|'
               r'группа\s+компаний|llc|ltd|inc|llp|group)\b', ' ', t, flags=re.I)
    t = re.sub(r'[«»"\'`,.]', ' ', t)
    return ' '.join(t.lower().split())


def advisers(deal):
    out = []
    for row in ((deal.get('law') or {}).get('adv') or []):
        if isinstance(row, (list, tuple)) and len(row) > 1 and has(row[1]):
            out.append(str(row[1]).strip())
    fin = (deal.get('eco') or {}).get('finadv')
    if has(fin):
        out += [x.strip().split('—')[0].strip() for x in str(fin).split(';') if x.strip()]
    seen, uniq = set(), []
    for a in out:
        key = _adviser_key(a)
        if key and key not in seen:
            seen.add(key)
            # Из двух записей одной фирмы оставляем более короткую подпись:
            # «Aspring Capital» читается лучше, чем «Aspring Capital
            # (инвестиционный банк)», а роль и так видна на карточке.
            uniq.append(a)
    return uniq


MONTHS_OF = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
             'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')


def fmt_day(raw):
    """«2026-08-06» -> «6 августа 2026». Пусто — если даты нет или она неполная."""
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', str(raw or ''))
    if not m:
        return ''
    of = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
          'августа', 'сентября', 'октября', 'ноября', 'декабря')
    month = int(m.group(2))
    if not 1 <= month <= 12:
        return ''
    return '%d %s %s' % (int(m.group(3)), of[month - 1], m.group(1))


def fmt_month(raw):
    """«2026-06-26» -> «июнь 2026», «2024» -> «2024 год». Пусто — если неясно."""
    raw = str(raw or '')
    if re.fullmatch(r'\d{4}', raw):
        return '%s год' % raw
    m = re.fullmatch(r'(\d{4})-(\d{2})-\d{2}', raw)
    if not m:
        return ''
    month = int(m.group(2))
    return '%s %s' % (MONTHS_OF[month - 1], m.group(1)) if 1 <= month <= 12 else m.group(1)


# Сколько дней сделка считается свежей новостью. Дальше пост читается не как
# объявление о сделке, а как сообщение о новых сведениях по известной сделке.
FRESH_DAYS = 30


def deal_age_days(deal, today=None):
    """Сколько дней сделке. None — если дату разобрать нельзя (год без дня)."""
    raw = str(deal.get('date') or '')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
        return None
    try:
        made = datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None
    return ((today or date.today()) - made).days


def _ru1(x):
    """0.5 -> «0,5» — русская десятичная запятая, не точка."""
    return ('%.1f' % x).replace('.', ',')


def _fmt_rub(value):
    v = float(value)
    sign = '−' if v < 0 else ''
    v = abs(v)
    if v >= 1e9:
        return '%s%s млрд ₽' % (sign, _ru1(v / 1e9))
    if v >= 1e6:
        return '%s%s млн ₽' % (sign, _ru1(v / 1e6))
    if v >= 1e3:
        return '%s%d тыс. ₽' % (sign, round(v / 1e3))
    return '%s%d ₽' % (sign, round(v))


def _yoy(new, old):
    """«(+18,6% г/г)» — только если известен и новый, и прошлогодний год:
    без прошлого года «относительно чего» не с чем сравнивать, а не сравнивать
    честнее, чем придумывать базу."""
    if new is None or old is None or float(old) == 0:
        return ''
    pct = (float(new) - float(old)) / abs(float(old)) * 100
    sign = '+' if pct >= 0 else '−'
    return ' (%s%s%% г/г)' % (sign, _ru1(abs(pct)))


def fin_summary(bo_rows):
    """(год, «Выручка N ₽ (+X% г/г) · Чистая прибыль M ₽») по ПОСЛЕДНЕМУ году
    из `bo_rows` (результат `fns_client.normalize_bo()`), где известна выручка
    или чистая прибыль — `None`, если данных нет вовсе. Чистая, без сети:
    сам факт живого запроса к ФНС — забота вызывающего (П7-9), а не этой
    функции, иначе render() перестал бы быть тестируемым без сети."""
    rows = [r for r in (bo_rows or [])
            if r.get('revenue_rub') is not None or r.get('net_profit_rub') is not None]
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r['year'])
    latest = rows[-1]
    prior = next((r for r in rows[:-1] if r['year'] == latest['year'] - 1), None)
    parts = []
    if latest.get('revenue_rub') is not None:
        parts.append('Выручка %s%s' % (_fmt_rub(latest['revenue_rub']),
                                        _yoy(latest.get('revenue_rub'), prior.get('revenue_rub') if prior else None)))
    if latest.get('net_profit_rub') is not None:
        parts.append('Чистая прибыль %s%s' % (_fmt_rub(latest['net_profit_rub']),
                                               _yoy(latest.get('net_profit_rub'), prior.get('net_profit_rub') if prior else None)))
    if not parts:
        return None
    return latest['year'], ' · '.join(parts)


def _subject_detail(deal, companies, reference, limit=2, max_chars=260):
    """Дословные предложения о ПРЕДМЕТЕ сделки — точное юрлицо/доля и род
    занятий — с новизной к `reference` (заголовок + уже показанное имя).

    ИСТОЧНИКИ, В ПОРЯДКЕ ПРИОРИТЕТА: `eco.share` («Предмет / доля» —
    CLAUDE.md уже фиксирует это назначение поля), иначе `extra` (тот же
    факт часто дублируется туда, когда `eco` не разобран); `eco.target_fin`
    («Финансы предмета») — добавлен НЕ по букве брифа, а по факту разбора
    карточки-образца (HeadHunter/Happy Job, `gebead2e8`): там `eco.share`
    пуст, а точное юрлицо («ООО «Счастливая работа»») и учредители лежат
    именно в `target_fin`, первым предложением; профиль цели (`desc`) —
    когда предмет связан со своим профилем компании."""
    eco = deal.get('eco') or {}
    sources = []
    if has(eco.get('share')):
        sources.append(eco['share'])
    elif has(deal.get('extra')):
        sources.append(deal['extra'])
    if has(eco.get('target_fin')):
        sources.append(eco['target_fin'])
    target_id = deal.get('target')
    if target_id and companies.get(target_id) and has(companies[target_id].get('desc')):
        sources.append(companies[target_id]['desc'])

    picked, ref = [], reference
    for src in sources:
        if len(picked) >= limit:
            break
        budget = max_chars - sum(len(s) for s in picked)
        if budget <= 0:
            break
        new = _pick_novel_sentences(src, ref, limit=limit - len(picked), max_chars=budget)
        if new:
            picked += new
            ref = ref + ' ' + ' '.join(new)
    return picked


def _join_subject_sentences(parts):
    """Склеивает куски `_subject_detail()` в одну строку. Найдено 30 августа
    на «Транснефть»/Газпромбанк (g60f99ba6): `eco.share` — короткая фраза без
    точки на конце («7,52% голосующих ценных бумаг»), а не предложение; при
    двух источниках (`eco.share` + профиль цели) `' '.join(picked)` склеивал
    её с описанием банка встык, без знака препинания — «...ценных бумаг
    Опорный банк газовой отрасли: ...» читалось как один сломанный кусок
    текста. Кусок без конечной пунктуации получает точку перед склейкой со
    следующим — тем же приёмом, каким уже оформлена пара «Покупатель: X —
    деталь» (там сторону от детали отделяет тире, здесь между двумя
    ДЕТАЛЯМИ ставится точка, потому что тире здесь означало бы другую пару
    «сторона — деталь», которой у _subject_detail() вообще нет)."""
    out = []
    for i, part in enumerate(parts):
        part = part.strip()
        if i < len(parts) - 1 and part and not re.search(r'[.!?…»"\)]$', part):
            part += '.'
        out.append(part)
    return ' '.join(out)


# Правовые формы и родовые слова не идентифицируют сторону: требовать их
# присутствия в предложении-пояснении бессмысленно («Группа» есть в сотнях
# предложений). Если после их отсева от имени ничего не осталось, проверка
# «предложение называет сторону» отключается — лучше старое поведение, чем
# невыполнимое требование.
_GENERIC_NAME_WORDS = {'ооо', 'ао', 'пао', 'зао', 'оао', 'нао', 'гк', 'ук',
                       'зпиф', 'группа', 'группы', 'компания', 'компании',
                       'холдинг', 'корпорация', 'фонд', 'банк',
                       # Дескрипторы из длинных имён: «объединённая компания
                       # Wildberries и Russ» — слово «объединённая» пословный
                       # компаратор матчил с «объект» (общее начало «объе»),
                       # и предложение о здании сходило за пояснение стороны.
                       'объединенная', 'объединённая', 'венчурный', 'управляющая'}


def _mentions_party(sentence, party_name):
    """Предложение претендует на роль пояснения стороны, только если называет
    её: хотя бы одно значащее слово имени лежит в предложении (с точностью до
    окончаний — тот же пословный компаратор, что и везде)."""
    name_words = [w for w in re.findall(r'[А-Яа-яЁёA-Za-z0-9]+', party_name or '')
                  if len(w) >= 3 and w.lower().replace('ё', 'е') not in _GENERIC_NAME_WORDS]
    if not name_words:
        return True
    sent_words = re.findall(r'[А-Яа-яЁёA-Za-z0-9]+', sentence)
    return any(any(_same_word(nw, sw) for sw in sent_words) for nw in name_words)


def _party_detail(deal, companies, ref_field_id, eco_field, reference, limit=1, max_chars=200):
    """Одно дословное предложение о СТОРОНЕ (обычно — покупателе): профиль
    компании (`desc`), иначе поле `eco`, названное в `eco_field` (для
    покупателя это `context` — по образцу той же карточки: `eco.context`
    описывает hh.ru, не цель).

    НАЙДЕНО ВЛАДЕЛЬЦЕМ 30 августа (Транснефть/Газпромбанк, g60f99ba6): пост
    вышел со строкой «Покупатель: «Транснефть» — О покупке ... сообщила в
    финансовой отчетности по МСФО...» — предложение из `eco.context` объясняло,
    кто и где СООБЩИЛ о сделке, а не кто покупатель. Причина двойная: (1)
    `eco.context` не обязан описывать сторону — это эвристика по одной
    карточке-образцу, и здесь все шесть предложений контекста были о механике
    сделки; (2) приоритет «имя в кавычках» вытолкнул наверх именно
    мета-предложение — имя стороны стояло в кавычках внутри него. Поэтому для
    context-фолбэка два отсева: предложение обязано НАЗЫВАТЬ сторону
    (_mentions_party) и не быть мета-предложением о раскрытии
    (_is_reporting_meta). Для `desc` профиля ни то ни другое не требуется:
    описание компании по построению о ней и без глаголов сообщения.

    Замер по всем 1575 карточкам: жалоба владельца на ОДИН пост вскрыла
    системный класс — правки меняют 93 поста (6%), и почти во всех старая
    строка клеила к имени покупателя предложение о ЦЕЛИ, ПРОДАВЦЕ или истории
    актива («Покупатель: Иван Тырышкин — PPF Group получила 318 млн евро
    убытка»). Примерно у половины строка честно сжимается до имени или
    исчезает (имя и так в заголовке), у 12 пояснение заменяется на
    предложение, называющее саму сторону. Осознанный размен: предложение,
    описывающее покупателя БЕЗ его имени («Фонд основан в 2010 году...»),
    теперь тоже отсеется — механически его не отличить от описания цели, а
    неверная строка в посте дороже отсутствующей (CLAUDE.md: «Ошибка дороже
    молчания»)."""
    eco = deal.get('eco') or {}
    company_id = deal.get(ref_field_id)
    if company_id and companies.get(company_id) and has(companies[company_id].get('desc')):
        picked = _pick_novel_sentences(companies[company_id]['desc'], reference,
                                       limit=limit, max_chars=max_chars)
        if picked:
            return ' '.join(picked)
    if eco_field and has(eco.get(eco_field)):
        party_name = _party_name_for(deal, companies, ref_field_id)
        drop = lambda s: _is_reporting_meta(s) or not _mentions_party(s, party_name)
        picked = _pick_novel_sentences(eco[eco_field], reference,
                                       limit=limit, max_chars=max_chars, drop=drop)
        if picked:
            return ' '.join(picked)
    return None


def _party_name_for(deal, companies, ref_field_id):
    """Имя стороны так, как его выбирает party_names, — для проверки
    «предложение называет сторону»."""
    if ref_field_id == 'buyer':
        company_id = deal.get('buyer')
        if company_id and companies.get(company_id):
            return companies[company_id]['name']
        return deal.get('buyer_name') or ''
    company_id = deal.get(ref_field_id)
    if company_id and companies.get(company_id):
        return companies[company_id]['name']
    return ''


def is_fresh(deal, today=None):
    """Свежая сделка — обычный пост. Старая — «новое о сделке».

    ЗАЧЕМ. Правило публикации смотрело, видел ли карточку КАНАЛ, а не что
    нового узнали МЫ. Из-за этого 4 августа в канал ушли посты о сделках 26
    июня, 15 июня и 1 марта 2025 года — каждый читался как объявление о свежей
    сделке, хотя поводом было дописанное обогащением поле. Читателю канала
    нужны новости, а не выдача архива за новость.

    Дата, у которой известен только год, свежей не считается: если мы не знаем
    даже месяца, объявлять сделку сегодняшней нельзя.
    """
    age = deal_age_days(deal, today)
    return age is not None and age <= FRESH_DAYS


def render(deal, companies, updates=(), today=None, fin=None):
    """Текст поста (HTML для Telegram). Пустых строк-заглушек в посте нет.

    ЭТАП 9 — реакция партнёров на пост «Алор брокер»: «он пишет в предмет
    кусок фразы из заголовка… смысла писать стороны и предмет тогда нет
    вообще». Формула переписана по образцу их же примера («M&A новости»,
    HeadHunter/Happy Job) — предмет и покупатель получают суть (юрлицо,
    доля, чем занимается, финпоказатели), а не голое имя, но КАЖДАЯ строка
    печатается только с новизной к заголовку и к уже показанному тексту —
    иначе она дословный или падежный повтор, который партнёры и назвали
    бесполезным.

    `fin` — предвычисленные финансовые строки сторон ({'target': (год,
    текст), 'buyer': (год, текст)} из `fin_summary()`) — ЖИВОЙ запрос к ФНС
    делает вызывающий (`send_telegram.main()`, П7-9), не эта функция:
    render() остаётся чистой и проверяется тестами без сети, как и раньше.
    """
    seller, asset, buyer = party_names(deal, companies)
    fin = fin or {}
    lines = []
    if not is_fresh(deal, today):
        # Старая сделка: сначала честно говорим, что это не свежая новость, и
        # называем ЕЁ дату — иначе читатель примет архив за сегодняшний рынок.
        #
        # ЗАГОЛОВОК ЗАВИСИТ ОТ ТОГО, ЕСТЬ ЛИ ЧТО СКАЗАТЬ. 7 августа в канал ушёл
        # пост «Новое о сделке · май 2026» про «Обсидиан», в котором ничего
        # нового не сообщалось, — владелец справедливо спросил, что же в ней
        # новое. Ответ: ничего, просто карточка впервые дошла до канала.
        # Обещать новизну там, где её нет, нельзя; но и молчать о том, почему
        # сделка мая всплыла в августе, тоже — поэтому называем дату появления
        # карточки в базе, это проверяемый факт (поле `added`).
        when = fmt_month(deal.get('date'))
        if updates:
            lines.append('🗂 <b>Новое о сделке</b>%s' % (' · %s' % esc(when) if when else ''))
            lines.append('Что стало известно: %s' % esc(', '.join(updates)))
        else:
            lines.append('🗂 <b>Сделка из базы</b>%s' % (' · %s' % esc(when) if when else ''))
            added = fmt_day(deal.get('added'))
            lines.append('Публикуем впервые%s.'
                         % (' — карточка появилась в «Компасе» %s' % esc(added) if added else ''))
        lines.append('')
    title = str(deal.get('title') or '')
    lines.append('<b>%s</b>' % esc(title))

    # Новизна считается против ЗАГОЛОВКА и против уже напечатанной части
    # поста — вторая строка не должна повторять то, что сказала первая,
    # даже если само по себе слово в заголовке не встречалось.
    reference = title

    def emit(text):
        nonlocal reference
        lines.append(text)
        reference = reference + ' ' + re.sub(r'<[^>]+>', '', text)

    # ПРЕДМЕТ — с сутью (юрлицо/доля, чем занимается), не голое имя-повтор
    # заголовка. Финстрока цели — сразу под ним, отдельной строкой (П7-9).
    asset_novel = bool(asset) and has_novelty(asset, reference)
    detail = _join_subject_sentences(_subject_detail(deal, companies, reference + (' ' + asset if asset else '')))
    # Деталь сама называет предмет — имя перед тире не повторяем. Найдено
    # владельцем 2 сентября на посте о госпакете Шереметьево: «Предмет:
    # Международный аэропорт Шереметьево (МАШ) — Госпакет Международного
    # аэропорта Шереметьево (МАШ) — на конец января…» — одно и то же дважды,
    # потому что новизна детали считалась против имени (в ней есть «госпакет»
    # и «30%»), а новизна имени против детали — нет.
    if asset_novel and detail and not has_novelty(asset, detail):
        asset_novel = False
    if asset_novel and detail:
        subject = 'Предмет: %s — %s' % (esc(asset), esc(detail))
    elif asset_novel:
        subject = 'Предмет: %s' % esc(asset)
    elif detail:
        subject = 'Предмет: %s' % esc(detail)
    else:
        subject = None
    target_fin = fin.get('target')
    if subject or target_fin:
        lines.append('')
        if subject:
            emit(subject)
        if target_fin:
            # «Финансы цели» звучало как внутренний термин («финансы чего?» —
            # спросил партнёр 31 августа); по-русски — чья это отчётность.
            emit('Финансы покупаемой компании, %s год: %s' % (target_fin[0], esc(target_fin[1])))

    facts = []
    if has(deal.get('sum')):
        facts.append('Сумма: %s' % esc(deal['sum']))
    elif PLACEHOLDER.match(str(deal.get('sum') or '')):
        # Карточка ПРЯМО утверждает, что сумма не раскрыта, — честный факт,
        # не пустота (партнёры сами хвалили именно такую строку у конкурента).
        # `sum=None`, наоборот, значит «мы не нашли», а не «стороны скрыли» —
        # молчание там честнее любой формулировки.
        facts.append('Сумма: не раскрывается')
    if has(deal.get('status')):
        status_line = 'Статус: %s' % esc(deal['status'])
        if deal['status'] == 'Закрыта':
            when = fmt_month(deal.get('date'))
            if when:
                status_line += ' · %s' % esc(when)
        facts.append(status_line)
    if has(deal.get('ind')):
        facts.append('Отрасль: %s' % esc(deal['ind']))
    if facts:
        lines.append('')
        for f in facts:
            emit(f)

    # ПОКУПАТЕЛЬ — тоже с сутью (профиль компании либо `eco.context`, где эта
    # сторона обычно и описывается), плюс его собственная финстрока (П7-9).
    # НАЙДЕНО ВЛАДЕЛЬЦЕМ 25 августа (Pridex/Multispace, ge283bafc): без
    # проверки на пустой `buyer` строка «Покупатель: …» печаталась из ОДНОЙ
    # детали (eco.context), когда имени стороны не было вовсе, — читатель
    # видел «Покупатель: В периметр сделки вошли четыре объекта…», хотя это
    # предложение вообще не о покупателе. Деталь без имени не идентифицирует
    # сторону — строка обязана нести хотя бы имя.
    buyer_novel = bool(buyer) and has_novelty(buyer, reference)
    buyer_detail = _party_detail(deal, companies, 'buyer', 'context',
                                  reference + ' ' + buyer) if buyer else None
    if buyer and buyer_detail and names_party_upfront(buyer, buyer_detail):
        # Деталь сама называет покупателя в начале фразы — имя перед тире было
        # бы вторым таким же. Владелец 4 сентября 2026 на живом посте о ТЦ
        # «Город Косино» (gddb34475): «Покупатель: ООО «Афкап» — Новым
        # владельцем компании стало ООО «Афкап» Агиля Мохнатова…» — «повторение
        # странное». Тот же дефект и та же починка, что у «Предмета» выше
        # (2 сентября, госпакет Шереметьево), только здесь проверка строже —
        # см. докстроку names_party_upfront: имя из строки при этом НЕ
        # пропадает, оно остаётся внутри самой детали.
        buyer_line = 'Покупатель: %s' % esc(buyer_detail)
    elif buyer and (buyer_novel or buyer_detail):
        buyer_line = 'Покупатель: %s' % esc(buyer)
        if buyer_detail:
            buyer_line += ' — %s' % esc(buyer_detail)
    else:
        buyer_line = None
    buyer_fin = fin.get('buyer')
    if buyer_line or buyer_fin:
        lines.append('')
        if buyer_line:
            emit(buyer_line)
        if buyer_fin:
            emit('Финансы покупателя, %s год: %s' % (buyer_fin[0], esc(buyer_fin[1])))

    # ПРОДАВЕЦ — только имя, только с новизной (брифом не обещана суть, чтобы
    # не раздувать пост: покупатель и предмет для читателя важнее).
    if seller and has_novelty(seller, reference):
        lines.append('')
        emit('Продавец: %s' % esc(seller))

    # ЗАЧЕМ — одно предложение из `eco.rationale`, если оно ещё не сказано.
    rationale = (deal.get('eco') or {}).get('rationale')
    why = _pick_novel_sentences(rationale, reference, limit=1, max_chars=200) if has(rationale) else []
    if why:
        lines.append('')
        emit('Зачем: %s' % esc(' '.join(why)))

    adv = advisers(deal)
    if adv:
        lines.append('')
        lines.append('Консультанты: %s' % esc(', '.join(adv[:6])))

    # ССЫЛКИ НА ПЛАТФОРМУ — НЕ В ТЕКСТЕ, А КНОПКАМИ ПОД ПОСТОМ (`lens_links`,
    # `render_buttons`). Владелец 2 сентября 2026: «кнопки экономист/юрист
    # красивые со стрелочками, но нивелируют ценность перехода на карточку
    # сделки — надо элегантное решение, а не просто убрать стрелки». Три
    # текстовые ссылки подряд конкурировали друг с другом, и две узкие
    # (линзы) выигрывали у главной у самой широкой по смыслу. В настоящей
    # клавиатуре Telegram иерархия видна глазами: карточка — отдельная
    # широкая кнопка первым рядом, линзы — узкие вторым. Текст поста при
    # этом заканчивается фактом (источником), а не столбиком ссылок.
    src = [s for s in (deal.get('src') or []) if len(s) > 1 and str(s[1]).startswith('http')]
    if src:
        lines.append('')
        lines.append('Источник: <a href="%s">%s</a>' % (esc(src[0][1]), esc(src[0][0])))
        if len(src) > 1:
            # «Ещё источников: 2» — пустая строка: непонятно, где они и
            # зачем о них знать (замечание владельца 3 сентября 2026).
            # Говорим то же самое, но так, чтобы читателю было куда пойти.
            more = len(src) - 1
            lines.append('Ещё %d %s — в карточке сделки'
                         % (more, _plural(more, 'источник', 'источника', 'источников')))

    # «⟳ Обновлено» — для ПРАВКИ уже опубликованного поста. У старой сделки то
    # же самое уже сказано шапкой «Новое о сделке», и повторять незачем.
    if updates and is_fresh(deal, today):
        lines.append('')
        lines.append('⟳ Обновлено: %s' % esc(', '.join(updates)))

    # Хештег — из названия отрасли и типа как есть: регистр не трогаем, иначе
    # «#ИТиинтернет» превращается в нечитаемое «#итиинтернет».
    tag = lambda s: '#' + re.sub(r'[^\wА-Яа-яЁё]+', '', str(s or ''))
    tags = [tag(deal.get('ind'))]
    if has(deal.get('type')):
        tags.append(tag(str(deal['type']).split('·')[0]))
    lines.append('')
    lines.append(' '.join(t for t in tags if len(t) > 1))
    return '\n'.join(lines)


def lens_links(deal):
    """Какие линзы карточки стоит открывать прямой ссылкой: [(подпись, lens)].

    Условие то же, что было у текстовых ссылок: линза предлагается, только
    если там правда что-то есть, — иначе читатель жмёт «Юрист» и попадает на
    пустую вкладку. Вынесено в отдельную функцию, потому что теперь этим
    пользуются двое: клавиатура поста и её текстовый предпросмотр в консоли."""
    eco, law = (deal.get('eco') or {}), (deal.get('law') or {})
    out = []
    if (has(deal.get('sum')) or has(deal.get('status')) or has(deal.get('ind'))
            or has(eco.get('share')) or has(eco.get('rationale')) or has(eco.get('val'))
            or has(eco.get('target_fin')) or has(eco.get('finadv'))):
        out.append(('Экономист', 'eco'))
    if (advisers(deal) or has(law.get('struct')) or has(law.get('appr'))
            or has(law.get('terms'))):
        out.append(('Юрист', 'law'))
    return out


_OWN_LINK_LINE = re.compile(
    r'^\s*(?:→\s*)?<a href="%s/#/deal/[^"]*">[^<]*</a>\s*$' % re.escape(SITE))


def strip_platform_links(text):
    """Убрать из готового текста НАШИ ссылки-строки на карточку и линзы.

    Нужно для `post_override` — текста, который основатель написал (или
    одобрил) в консоли ДО 2 сентября 2026, когда эти ссылки ещё стояли в
    теле поста. Теперь они живут кнопками под постом, и без чистки старый
    override показал бы их дважды. Трогаем только строки, состоящие ровно
    из нашей ссылки: ссылка на источник и любая ссылка внутри предложения
    остаются на месте."""
    lines = [l for l in str(text or '').split('\n') if not _OWN_LINK_LINE.match(l)]
    out = '\n'.join(lines)
    return re.sub(r'\n{3,}', '\n\n', out).strip()


def render_buttons(deal):
    """Клавиатура под постом: карточка сделки — широкой кнопкой первым рядом,
    линзы — вторым. Формат готов для `reply_markup` Telegram."""
    did = deal.get('id')
    if not did:
        return None
    rows = [[{'text': 'Открыть карточку сделки', 'url': '%s/#/deal/%s' % (SITE, did)}]]
    lenses = [{'text': label, 'url': '%s/#/deal/%s?lens=%s' % (SITE, did, lens)}
              for label, lens in lens_links(deal)]
    if lenses:
        rows.append(lenses)
    return {'inline_keyboard': rows}


def buttons_preview(deal_or_buttons):
    """Строка для консоли основателей: что за кнопки будут под постом и куда
    ведут. Черновик обязан показывать ВЕСЬ пост — а кнопки в текст сообщения
    не видны, и без этой строки проверяющий не мог бы ни увидеть их, ни
    пройти по ссылке."""
    buttons = (deal_or_buttons if isinstance(deal_or_buttons, dict) and 'inline_keyboard' in deal_or_buttons
               else render_buttons(deal_or_buttons))
    if not buttons:
        return ''
    items = ['%s — %s' % (b['text'], b['url']) for row in buttons['inline_keyboard'] for b in row]
    return 'Кнопки под постом: ' + ' · '.join(items)


def render_milestone(deal, event):
    """Текст ОТДЕЛЬНОГО поста-вехи (раздел A, 22 августа) — не правка живого
    поста, а новое сообщение об одном подтверждённом этапе сделки
    (`review.POSTWORTHY_MILESTONE_KINDS`: согласование, закрытие, срыв).

    ЧЕСТНОСТЬ МОМЕНТА. Поля берутся из СНИМКА события (`event['snapshot']`,
    записан `review.build_snapshot()` в момент `--milestone`), а не из
    текущих полей сделки: к моменту публикации карточка могла обогатиться
    более поздними фактами (например, уточнённой ценой закрытия), а веха
    обязана честно показывать то, что было известно НА МОМЕНТ ЭТОГО ЭТАПА,
    а не задним числом — тот же принцип, что и у панели «Карточка на
    момент этого этапа» на странице этапа.
    """
    snap = event.get('snapshot') or {}
    lines = ['📌 <b>%s</b>' % esc(event.get('headline') or '')]
    lines.append('')
    lines.append('Сделка: %s' % esc(snap.get('title') or deal.get('title')))

    parties = []
    if has(snap.get('seller')):
        parties.append('Продавец: %s' % esc(snap['seller']))
    if has(snap.get('asset')):
        parties.append('Предмет: %s' % esc(snap['asset']))
    if has(snap.get('buyer')):
        parties.append('Покупатель: %s' % esc(snap['buyer']))
    if parties:
        lines.append('')
        lines += parties

    facts = []
    if has(snap.get('sum')):
        facts.append('Сумма: %s' % esc(snap['sum']))
    if has(snap.get('status')):
        facts.append('Статус: %s' % esc(snap['status']))
    if facts:
        lines.append('')
        lines += facts


    return '\n'.join(lines)


def changes(old, new):
    """Что изменилось между версиями карточки — человеческими словами."""
    label = {'sum': 'сумма', 'buyer': 'покупатель', 'buyer_name': 'покупатель',
             'seller': 'продавец', 'target': 'предмет сделки', 'asset': 'предмет сделки',
             'status': 'статус', 'advisers': 'консультанты', 'events': 'этап сделки'}
    out = []
    for field in SIGNIFICANT:
        was = old.get(field) if field != 'advisers' else advisers(old)
        now = new.get(field) if field != 'advisers' else advisers(new)
        if field not in ('advisers', 'events'):
            was, now = (was if has(was) else None), (now if has(now) else None)
        if field == 'events':
            # Сравниваем только виды этапов: повторная публикация о том же
            # закрытии добавит источник, но не должна считаться новым этапом.
            kinds = lambda rows: tuple(e.get('kind') for e in (rows or []) if isinstance(e, dict))
            was, now = kinds(was), kinds(now)
        if was == now:
            continue
        # Закрытие сделки — не переформулировка, а событие: сделка, о которой
        # писали «обсуждается», состоялась. По общему правилу это считалось
        # «уточнением статуса» и проходило молча — то есть самое важное
        # обновление было единственным, о котором читатель не узнавал.
        if field == 'status' and str(now) == 'Закрыта':
            out.append('сделка закрыта')
            continue
        if field == 'events' and len(now) > len(was):
            out.append('добавлен этап сделки')
            continue
        text = label[field]
        out.append(('добавлен(а) ' + text) if not was else ('уточнён(а) ' + text))
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def should_notify(change_list):
    """Уведомлять ответом на пост — только когда факт ДОБАВИЛСЯ, а не уточнился.

    Иначе каждая правка формулировки будила бы читателя. Уточнение видно в
    самом посте строкой «⟳ Обновлено», и этого достаточно.

    Исключение одно и оно по смыслу такое же: «сделка закрыта» — это появление
    факта, а не другая формулировка прежнего.
    """
    return any(c.startswith('добавлен') or c == 'сделка закрыта' for c in change_list)


def sample():
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    rich = [d for d in data['deals']
            if has(d.get('sum')) and (d.get('seller') or d.get('seller_id'))
            and ((d.get('law') or {}).get('adv'))]
    deal = rich[0]
    print(render(deal, comps))
    print('\n' + '-' * 60)
    older = json.loads(json.dumps(deal))
    older['sum'] = '—'
    older['law']['adv'] = []
    ch = changes(older, deal)
    print('изменения:', ch, '| уведомлять:', should_notify(ch))
    print('-' * 60)
    print(render(deal, comps, updates=ch))


if __name__ == '__main__':
    if '--sample' in sys.argv:
        sample()
    else:
        print(__doc__)
