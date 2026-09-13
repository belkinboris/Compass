#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приёмка карточки: последнее чтение целиком перед консолью и каналом.

ЗАЧЕМ. 11 сентября 2026 владелец открыл две свежие карточки подряд —
Positive Technologies/CyberOK и «Совко Капитал Партнерс»/Совкомбанк — и в
каждой нашёл то, что видно с первого взгляда: предмет в косвенном падеже с
описанием вместо имени, некликабельные стороны, дословную фразу газеты под
«Юристом», «Зачем», которое не отвечает на «зачем», единственный источник
там, где статья сама ссылается на пресс-релиз. «Это уже не первый раз… нужно
подойти с архитектурной точки зрения, чтобы такого больше не было».

ПОЧЕМУ ЭТО ПОВТОРЯЛОСЬ. Каждый из дефектов уже был закрыт правилом — но
правило стоит на ОДНОМ пути (draft.py, review.py, link_parties) и проверяет
ОДНО поле по ФОРМЕ (дословность, регэксп). Карточка приходит несколькими
путями (ворота притока, кнопка «в работу», правки дочитывания), а вопросы
владельца — про СМЫСЛ («это имя компании?», «это ответ на зачем?», «это
условие сделки или пресс-релиз?»), на который регэксп не отвечает. Не было
шага, где кто-то читает ГОТОВУЮ карточку и пост целиком глазами читателя.
Владельцу приходилось быть этим читателем.

ЧТО ЭТО. Шаг приёмки: одно чтение на карточку по чек-листу
(`CARD_ACCEPTANCE_BRIEF.md`) — читатель (саб-агент рутины) правит карточку
через уже существующие механизмы (профили и привязки здесь, факты с цитатой
через review.py, проза через proofread.py) и отвечает файлом; скрипт
проверяет ответ механически и ставит штамп `accepted`. БЕЗ ШТАМПА карточка
не показывается в консоли (send_drafts), не выходит по молчанию (approve) и
не уходит постом в канал (send_telegram) — три места, куда карточка попадает
любым путём. Забыть шаг нельзя: он не совет в промпте, а замок на выходе.

ГРАНИЦА. Скрипт не судит о смысле — это делает читатель. Скрипт делает две
вещи: (1) собирает досье с механическими НАХОДКАМИ (`findings`), чтобы
читатель знал, куда смотреть, и (2) не даёт ответу читателя внести
выдумку: новое имя в заголовке, профиль-описание, профиль-близнец,
описание с пресс-атрибуцией. Штамп ставится только когда находок не
осталось (кроме названных в `no_profile` с причиной).

Запуск:
    python3 pipeline/ingest/accept_card.py --queue            # досье по всем без штампа
    python3 pipeline/ingest/accept_card.py --queue <id>       # досье по одной
    python3 pipeline/ingest/accept_card.py --check  answers.json
    python3 pipeline/ingest/accept_card.py --apply  answers.json [--write]
    python3 pipeline/ingest/accept_card.py --self-check
"""
import json
import os
import re
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import casing                      # noqa: E402
import link_parties                # noqa: E402
import review                      # noqa: E402
import format_post                 # noqa: E402
import check_post                  # noqa: E402
import proofread                   # noqa: E402
import source_names                # noqa: E402
import normalize_sum               # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
RAW_DIR = os.path.join(ROOT, 'data', 'inbox', 'raw')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')
TRIAGE_DIR = os.path.join(ROOT, 'data', 'inbox', 'triage')
REGISTRY_PATH = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
# Сколько дней назад приток мог найти публикацию об этой же сделке: карточка
# принимается в день-два после появления, дальше её читают дельта-уровни.
COVERAGE_DAYS = 14

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from pipeline import fns_registry          # noqa: E402

STAMP = 'accepted'
CHECKLIST = ('sources', 'parties', 'asset', 'title', 'why', 'fields', 'wording', 'post', 'status')
ROLES = {'target': ('asset', 'target'), 'buyer': ('buyer_name', 'buyer'), 'seller': ('seller', 'seller_id')}
PROSE_FIELDS = proofread.PROOFREAD_FIELDS
PLACEHOLDER = re.compile(r'^\s*(—|-|не раскрыт[а-яё]*|публично не сообщал[а-яё]*|не привлекал[а-яё]*|нет данных|n/?a)?\s*$', re.I)

# Аудит 12 сентября 2026 (audit_prompt_fable): опровержение или неснятая
# гипотеза о МЕХАНИКЕ сделки, дожившая до закрытия/срыва. Шире узкого
# `denial_re`/`speculative_re` из test_data.py (тот регэксп — для уже
# записанных карточек с именным списком исключений; здесь исключений нет,
# потому что это НОВЫЕ карточки — находка обязана быть починена, а не
# унаследована). Проверяется на себе в `_self_check()`.
STALE_STATEMENT_RE = re.compile(
    r'не соответствует действительности|опроверг|опровержени'
    r'|возможно,?\s*будет\s+провед|может быть проведена?\s+через|будет\s+проведена?\s+через'
    r'|планир(?:ует|уется|ует[а-яё]*)\s+(?:провести|заключить|закрыть|осуществить)'
    r'|рассматрива(?:ет|ют)\s+возможность\s+(?:провед|заключ|закрыти|осуществ)'
    r'|ожида(?:ется|ем)\s+закрыти'
    r'|в случае одобрени', re.I)
# ТОЛЬКО law.struct/law.terms: `eco.context` — ЕДИНСТВЕННОЕ документированное
# место для «кто опроверг» и «чем кончилось потом» (см. семантику поля в
# CARD_ACCEPTANCE_BRIEF.md/READER_BRIEF) — сканировать его на слово
# «опроверг» значило бы находить факт ровно там, где ему положено быть.
# Проверено на живой базе 12 сентября 2026: с этим набором полей находки —
# ровно два уже известных, сознательно оставленных исключения
# (`DENIAL_ALLOWED_IN_LAW` в test_data.py), новых ложных срабатываний нет.
STALE_STATEMENT_FIELDS = ('law.struct', 'law.terms')
# «Активы <иностранца>»/«(российский бизнес X)»/«(бренд X в России)» —
# документированное соглашение для проданного российского бизнеса
# иностранной компании (см. «Knauf (российский бизнес)», «российские активы
# Rockwool», «Viola (бренд Valio в России)» в брифе читателя), а не
# PARTY_IN_ASSET_NAME: имя стороны стоит там по замыслу.
PARTY_IN_ASSET_NAME_EXEMPT = re.compile(
    r'\(российск\w+\s+бизнес|российск\w+\s+актив|\(бренд\s+\S+\s+в\s+росси', re.I)

# Аудит 13 сентября 2026 (2420 находок, 62 партии): пять узких проверок,
# каждая измерена на живой базе перед принятием (см. коммит с отчётом
# `pipeline/audit_field_placement/2026-09-13-report.md`) — ни одна не даёт
# ложных срабатываний на текущих 1382 карточках.
#
# Служебная вики-разметка источника (TAdviser): «Компания:», «Персона:»,
# заголовок «История 20XX: …» — те же три маркера, что нашлись в трёх
# карточках живой базы (gc5951fac, gac1a0c11, gb0f1f736), узнаваемы дословно.
TADVISER_MARKUP_RE = re.compile(r'(?:^|\n)\s*(?:Компания|Персона)\s*:\s|История\s+20\d\d\s*:\s', re.I)
# Обрыв текста многоточием на середине предложения — тот же класс, что уже
# дважды чинился в draft.py (`truncate_note()`), но нашёлся снова в 9
# карточках живой базы: либо путь записи другой, либо регрессия. Узкий
# признак (текст оканчивается на «…»/«...») — обрыв в НАЧАЛЕ поля этим не
# ловится, это отдельный, более редкий класс (см. TRUNCATED в отчёте).
TRAILING_CUTOFF_RE = re.compile(r'(?:…|\.\.\.)\s*$')
# Одна и та же фраза дословно в двух прозаических полях — расширение уже
# существовавшей проверки `why_dup` (только rationale/extra) на соседние
# пары, которые аудит нашёл дублирующими друг друга (`c59e65efb`,
# `c71e19cc1`). Порог — точное совпадение после `review.flat()`, без
# нечёткого сравнения: как и у `sum_fields_differ`, риска ложных
# срабатываний нет, потому что совпадение либо есть побайтово, либо нет.
DUPLICATE_PAIRS = (
    ('eco.rationale', 'extra'),          # исторический код 'why_dup', не переименован
    ('eco.rationale', 'eco.context'),
    ('eco.context', 'extra'),
    ('eco.share', 'extra'),
    ('eco.rationale', 'eco.share'),
)


def has(v):
    return bool(v) and not PLACEHOLDER.match(str(v))


def _party_name_inside(needle, haystack):
    """Заметная часть имени `needle` встречается внутри `haystack` — признак
    PARTY_IN_ASSET_NAME (см. Dogma/ПИК: продавец «ГК ПИК» внутри имени
    профиля предмета «2 участка ГК ПИК в Москве (6 га)»). Правовая форма
    (ООО/ЗАО/ПАО/АО/МКАО/НКО) снимается — профили чаще носят бренд без неё;
    короткие обрубки (<4 знаков) не проверяются, чтобы не поймать «ВТБ» на
    любом упоминании банка где угодно в тексте."""
    n = re.sub(r'^(ооо|зао|пао|мкао|нко|ао)\s+', '', str(needle or '').strip().strip('«»"').strip(), flags=re.I)
    n = n.strip('«»" ').lower()
    if len(n) < 4:
        return False
    return n in str(haystack or '').lower()


# ---------------------------------------------------------------------------
# Загрузка: карточка может лежать в базе или в очереди предпросмотра

def load():
    base = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    return base, pending


def save(base, pending):
    for path, obj in ((DATA, base), (PENDING, pending)):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write('\n')


def find_card(cid, base, pending):
    for c in pending.get('cards', []):
        if c['id'] == cid:
            return c, 'pending'
    for c in base['deals']:
        if c['id'] == cid:
            return c, 'base'
    return None, None


def queue(base, pending):
    """Что ждёт приёмки: вся очередь предпросмотра без штампа и карточки базы,
    которым ещё предстоит ПЕРВЫЙ пост (свежие, без записи в telegram_posts) —
    ровно те, кого гейты ниже по течению не пропустят."""
    out = [c for c in pending.get('cards', []) if not c.get(STAMP)]
    posts = base.get('telegram_posts') or {}
    for c in base['deals']:
        if c.get(STAMP) or c['id'] in posts or c.get('no_post') or c.get('post_override'):
            continue
        if format_post.is_fresh(c):
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Механические находки — куда смотреть читателю (и что не даст поставить штамп)

def _text(card, field):
    return proofread.get_field(card, field) if '.' in field else card.get(field)


def _scannable_texts(card):
    """(поле, текст) по прозаическим полям и по заметкам этапов — общее место
    для проверок, которым всё равно, где именно лежит текст (обрыв на
    многоточии, чужая вики-разметка источника: оба класса находились в
    аудите и в `events[].note`, и в обычных прозаических полях)."""
    for f in PROSE_FIELDS:
        v = _text(card, f)
        if has(v):
            yield f, str(v)
    for i, e in enumerate(card.get('events') or []):
        v = e.get('note') if isinstance(e, dict) else None
        if has(v):
            yield 'events[%d].note' % i, str(v)


def _title_words(text):
    # В заголовке первое слово — тоже имя (титул начинается со стороны:
    # «Иванов купил…»), поэтому начало предложения НЕ пропускается. Обычное
    # первое слово («Пакет», «Правительство») найдётся в карточке по
    # `name_match` без учёта регистра и отказ не вызовет.
    return proofread.capitalised_words(text or '', skip_sentence_start=False)


def coverage(card, days=COVERAGE_DAYS):
    """Публикации об ЭТОЙ сделке, которые приток нашёл и никто не прочитал.

    11 сентября 2026 CNews о Positive Technologies/CyberOK лежал в
    `data/inbox/hold/2026-09-11-enrich.json` с вердиктом «слабое совпадение:
    общие слова заголовка: 3» — `enrich.py` по слабому совпадению правильно
    ничего не пишет, но файл, куда он откладывает такие находки, не читал ни
    один шаг: ни дочитывание, ни приёмка, ни консоль. Конкурент тем временем
    процитировал CNews. Здесь тот же файл (и разбор дня, если он на диске)
    читается для карточки, которую принимают: каждая найденная публикация —
    или источник карточки после чтения (`src_add`), или отведена с причиной
    (`no_source`), но не потеряна молча."""
    have = {str(s[1]) for s in card.get('src') or [] if len(s) > 1}
    want = 'enrich:%s' % card.get('id')
    since = (date.today() - timedelta(days=days)).isoformat()
    out, seen = [], set()
    for folder, only_enrich in ((HOLD_DIR, True), (TRIAGE_DIR, False)):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith('.json') or name[:10] < since:
                continue
            if only_enrich and not name.endswith('-enrich.json'):
                continue
            try:
                doc = json.load(open(os.path.join(folder, name), encoding='utf-8'))
            except ValueError:
                continue
            for it in (doc.get('items') if isinstance(doc, dict) else None) or []:
                if str(it.get('verdict') or '') != want:
                    continue
                url = str(it.get('news') or it.get('url') or '')
                if not url.startswith('http') or url in have or url in seen:
                    continue
                seen.add(url)
                out.append({'url': url, 'title': it.get('title'), 'why': it.get('why'), 'day': name[:10]})
    return out


def registry_ids(registry=None):
    """Профили, о юрлице которых реестр ИНН уже что-то знает — подтверждённый
    ИНН или честное решение «иностранец / физлицо / лот / банк»."""
    return {r.get('company_id') for r in (fns_registry.REGISTRY if registry is None else registry)}


_RESOLVED = {}


def resolve_inn(legal_name):
    """(ИНН, официальное имя) по бесплатному поиску ЕГРЮЛ — единственное
    действующее юрлицо с точным именем, иначе None. Латинский бренд ЕГРЮЛ не
    знает («CyberOK» → пусто), поэтому читатель называет юрлицо кириллицей —
    с сайта компании, из статьи или из раскрытия."""
    key = str(legal_name or '').strip()
    if not key:
        return None
    if key not in _RESOLVED:
        from pipeline import fns_unresolved_queue
        _RESOLVED[key] = fns_unresolved_queue.attempt_public_egrul_match(key)
    return _RESOLVED[key]


def add_registry_row(cid, name, inn, legal_name, card_id, registry=None, path=None, day=None):
    """Дописывает подтверждённый ИНН в `pipeline/fns_registry.py` — тем же
    блоком в конце REGISTRY, что и очередь «нужен ИНН». Реестр — код, который
    импортирует сайт: строка доедет до боевого процесса со следующей сборкой
    `release`, а пост канала (send_telegram.build_fin) увидит её сразу."""
    registry = fns_registry.REGISTRY if registry is None else registry
    path = path or REGISTRY_PATH
    day = day or date.today().isoformat()
    reason = ('Приёмка карточки %s (%s): юрлицо %s названо читателем, ИНН подтверждён точным '
              'совпадением имени в ЕГРЮЛ (единственное действующее юрлицо).'
              % (card_id, day, (legal_name or name).replace('"', "'")))
    row = {'company_id': cid, 'decision': 'confirmed', 'inn': str(inn), 'reason': reason, 'date': day}
    src = open(path, encoding='utf-8').read()
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src, 'не нашли конец REGISTRY в fns_registry.py — формат файла изменился'
    if '"company_id": %r,' % cid in src or '"company_id": "%s",' % cid in src:
        # Повторный прогон того же ответа (приёмка не поставила штамп с
        # первого раза) не должен дописать ту же строку второй раз.
        registry.append(row)
        return row
    block = '\n'.join([
        '', '',
        '# Приёмка карточки %s — %s (pipeline/ingest/accept_card.py).' % (card_id, day),
        'REGISTRY += [',
        '    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (cid, str(inn)),
        '     "reason": %r,' % reason,
        '     "date": %r},' % day,
        ']',
    ])
    open(path, 'w', encoding='utf-8').write(src.replace(marker, block + marker, 1))
    registry.append(row)
    return row


def fns_client_or_none():
    """Живой клиент ФНС или None — без ключа приёмка обходится без финансов,
    а не падает (тот же приём, что у send_telegram)."""
    try:
        from fns_client import ApiFnsClient
        return ApiFnsClient()
    except Exception:                                                     # noqa: BLE001
        return None


def employees_from_egr(egr):
    """(год, средняя численность) из открытых данных ЕГРЮЛ; None, если нет."""
    try:
        # Ответ метода `egr` завёрнут так же, как у `changes`: {"items": [{"ЮЛ": {...}}]}.
        if isinstance(egr, dict) and egr.get('items'):
            egr = (egr['items'][0] or {}).get('ЮЛ') or egr['items'][0]
        block = egr.get('ОткрСведения') or {}
        if isinstance(block, list):
            block = block[-1] if block else {}
        n = int(str(block.get('КолРаб') or '').strip())
        when = str(block.get('Дата') or '')
        year = int(when[:4]) - (1 if when[5:10] == '01-01' else 0)
        return (year, n) if n > 0 else None
    except (ValueError, TypeError, AttributeError):
        return None


def fin_prose(rows, legal_name=None, employees=None):
    """«Финансы покупаемой компании» из ГИР БО человеческим языком.

    Владелец 11 сентября 2026: конкурент показал выручку, убыток и
    численность АО «Сайбер ОК» за 2025 год, у нас в этом поле стояло
    описание технологий. Цифры берутся из той же отчётности, что и блок на
    странице компании, — но карточка сделки обязана нести их сама: пост и
    PDF читают поле, а не сайт. Атрибуция «по данным ГИР БО/ЕГРЮЛ» — не
    пресс-язык, а квалификация числа (правило вычитки)."""
    rows = sorted([r for r in rows or []
                   if r.get('revenue_rub') is not None or r.get('net_profit_rub') is not None],
                  key=lambda r: r['year'])
    if not rows:
        return None
    latest = rows[-1]
    prior = next((r for r in rows[:-1] if r['year'] == latest['year'] - 1), None)
    who = legal_name or 'компании'
    parts = []
    if latest.get('revenue_rub') is not None:
        s = 'выручка %s за %d год — %s' % (who, latest['year'], format_post._fmt_rub(latest['revenue_rub']))
        if prior and prior.get('revenue_rub') is not None:
            s += ' (за %d год — %s)' % (prior['year'], format_post._fmt_rub(prior['revenue_rub']))
        parts.append(s)
    if latest.get('net_profit_rub') is not None:
        v = float(latest['net_profit_rub'])
        s = '%s — %s' % ('чистая прибыль' if v >= 0 else 'чистый убыток', format_post._fmt_rub(abs(v)))
        if prior and prior.get('net_profit_rub') is not None:
            pv = float(prior['net_profit_rub'])
            s += ' (за %d год — %s %s)' % (prior['year'], 'прибыль' if pv >= 0 else 'убыток',
                                           format_post._fmt_rub(abs(pv)))
        parts.append(s)
    text = 'По данным ГИР БО, ' + ', '.join(parts) + '.'
    if employees:
        text += ' Средняя численность работников за %d год — %d человек (ЕГРЮЛ).' % employees
    return text


def target_financials(card, comps, inn, legal_name, fns):
    """Пишет `eco.target_fin` из ГИР БО, если там ещё нет ни одного числа.
    Описание, которое стояло вместо показателей, не выбрасывается — уезжает в
    `extra`, если его там ещё нет. Возвращает строку отчёта или None."""
    if fns is None or not inn:
        return None
    try:
        from fns_client import normalize_bo
        rows = normalize_bo(fns.bo(inn), inn)
    except Exception as e:                                                # noqa: BLE001
        return 'ФНС не ответила по %s: %s' % (inn, e)
    employees = None
    try:
        employees = employees_from_egr(fns.egr(inn))
    except Exception:                                                     # noqa: BLE001
        pass
    prose = fin_prose(rows, legal_name=legal_name, employees=employees)
    if not prose:
        return 'ГИР БО по %s пуста — финансов нет' % inn
    eco = card.setdefault('eco', {})
    old = eco.get('target_fin')
    if has(old) and re.search(r'\d', str(old)):
        return None
    if has(old):
        extra = str(card.get('extra') or '')
        if review.flat(old) not in review.flat(extra):
            card['extra'] = (extra.rstrip() + '\n\n' + old).strip() if has(extra) else old
    # Прежнее значение могла поставить таблица FIXES (у PT/CyberOK так и
    # было: описание технологий пришло записью дочитывания). После замены
    # запись перестанет совпадать с полем посимвольно, и
    # `test_review_table_is_applied_and_not_pending` назовёт её неприменённой
    # — хотя факт не потерян, он уехал в `extra`. Тот же ответ, что у вычитки:
    # отпечаток применённой записи ложится в `proofread_absorbed`, и
    # `review.already_applied` узнаёт её по нему. Только УЖЕ применённые
    # записи: неприменённую отпечаток спрятал бы навсегда.
    _absorb_applied_fixes(card, 'eco.target_fin')
    eco['target_fin'] = prose
    return 'eco.target_fin из ГИР БО: %s' % prose


def _absorb_applied_fixes(card, field):
    """Запомнить отпечатки записей FIXES по полю, которые применены к карточке
    СЕЙЧАС, — перед тем как поле перепишется. Возвращает число записей."""
    n = 0
    for f in review.FIXES:
        if f['id'] != card['id'] or f['field'] != field:
            continue
        if not review.already_applied(f, card):
            continue
        absorbed = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        fp = review.fix_fingerprint(f['new'])
        if fp not in absorbed:
            absorbed.append(fp)
            n += 1
    return n


def findings(card, base, waived=None, waived_inn=None, waived_sources=None, registry=None,
             waived_names=None, waived_stale=None):
    """Список (код, текст). Пусто — механика претензий не имеет; смысл судит
    читатель. `waived` — роли, для которых читатель назвал причину без профиля;
    `waived_inn` — роли, у которых юрлица с ИНН быть не может (иностранец,
    физлицо, лот); `waived_sources` — найденные притоком публикации, которые
    читатель отвёл с причиной (о другой сделке); `waived_names` — роли, для
    которых читатель подтвердил, что имя внутри имени предмета — не Dogma/ПИК,
    а законное совпадение бренда (дочка названа в честь материнской компании и
    т. п.); `waived_stale` — поля (law.struct/law.terms), в которых читатель
    подтвердил, что денай/гипотеза — часть намеренно рассказанной истории
    сделки (родня `DENIAL_ALLOWED_IN_LAW` в test_data.py, только для новых
    карточек, где решение принимает читатель, а не именной список)."""
    notes = card.get(STAMP + '_notes') or {}
    waived = waived or notes.get('no_profile') or {}
    waived_inn = set(waived_inn or notes.get('no_inn') or {})
    waived_sources = set(waived_sources or notes.get('no_source') or {})
    waived_names = waived_names or notes.get('name_ok') or {}
    waived_stale = set(waived_stale or notes.get('stale_ok') or {})
    out = []
    comps = base.get('companies') or {}
    asset = card.get('asset')
    if asset:
        fixed, changed = casing.to_nominative_asset(asset)
        if changed:
            out.append(('asset_case', 'предмет в косвенном падеже: %r → %r' % (asset, fixed)))
        if review.ASSET_IS_A_DESCRIPTION.search(asset):
            out.append(('asset_description', 'предмет — описание, а не имя компании: %r' % asset))
    if not (card.get('target') or card.get('asset_id') or has(asset)) \
            and card.get('type') in ('M&A', 'Продажа с торгов', 'Инвестиция') and 'target' not in waived:
        out.append(('asset_missing', 'предмет сделки не назван (ни профиль, ни текст)'))
    for role, (text_field, id_field) in ROLES.items():
        text = card.get(text_field)
        linked = card.get(id_field) or (role == 'target' and card.get('asset_id'))
        if has(text) and not linked and role not in waived:
            out.append(('party_unlinked:' + role, '%s «%s» — текстом, без профиля' % (role, text)))
    for f in ('title', 'asset', 'buyer_name', 'seller'):
        if '"' in str(card.get(f) or ''):
            out.append(('straight_quotes:' + f, 'прямые кавычки в %s' % f))
    for f in PROSE_FIELDS:
        v = _text(card, f)
        if not has(v):
            continue
        p = proofread.press_attribution(v)
        if p:
            out.append(('press:' + f, 'пресс-язык в %s: %s' % (f, p)))
        if proofread.long_quotes(v):
            out.append(('quote:' + f, 'длинная цитата в кавычках в %s' % f))
    rationale = _text(card, 'eco.rationale')
    if has(rationale):
        first = (format_post._sentences(rationale) or [''])[0]
        if format_post.NOT_A_MOTIVE.search(first):
            out.append(('why', '«Цель сделки» начинается с оценки рынка, а не с мотива'))
    for fa, fb in DUPLICATE_PAIRS:
        va, vb = _text(card, fa), _text(card, fb)
        if has(va) and has(vb) and review.flat(str(va)) == review.flat(str(vb)):
            code = 'why_dup' if (fa, fb) == ('eco.rationale', 'extra') else 'duplicate_text:%s=%s' % (fa, fb)
            out.append((code, '«%s» дословно повторяет «%s»' % (fa, fb)))
    for f, v in _scannable_texts(card):
        if TADVISER_MARKUP_RE.search(v):
            out.append(('tadviser_markup:' + f,
                        'служебная вики-разметка источника (TAdviser) просочилась в %s: %r' % (f, v[:80])))
        if TRAILING_CUTOFF_RE.search(v.rstrip()):
            out.append(('truncated:' + f, 'текст обрывается многоточием на середине в %s: %r' % (f, v[-60:])))
    if not any(str(s[1]).startswith('http') for s in card.get('src') or [] if len(s) > 1):
        out.append(('source', 'ни одной http-ссылки в источниках'))
    for c in coverage(card):
        if c['url'] not in waived_sources:
            out.append(('coverage:' + c['url'],
                        'публикация об этой сделке не прочитана: %s — %s' % (c['url'], c.get('title'))))
    known = registry_ids(registry)
    for role, (_tf, idf) in ROLES.items():
        cid = card.get(idf) or (role == 'target' and card.get('asset_id'))
        if cid and cid not in known and role not in waived_inn:
            out.append(('inn_missing:' + role,
                        '%s «%s» — юрлицо не установлено: в реестре ИНН нет ни строки'
                        % (role, comps.get(cid, {}).get('name') or cid)))
    tf = _text(card, 'eco.target_fin')
    if has(tf) and not re.search(r'\d', str(tf)):
        out.append(('target_fin_prose',
                    '«Финансы покупаемой компании» без единого числа — это описание, а не показатели'))
    if card.get('type') == 'Продажа с торгов' and not (card.get('seller') or card.get('seller_id')) \
            and 'seller' not in waived:
        out.append(('auction_seller', 'у продажи с торгов продавец назван всегда — здесь его нет'))
    # Аудит 12 сентября 2026 — четыре класса, найденные владельцем на живых
    # карточках (БКС/«Форштадт», S8/«Аквариус», Мать и дитя/«Инвитро»,
    # Dogma/ПИК), теперь проверяются механически у КАЖДОЙ новой карточки, а
    # не только у тех, что владелец успел открыть сам.
    target_id = card.get('target') or card.get('asset_id')
    seller_id = card.get('seller_id')
    if seller_id and target_id and seller_id == target_id and 'seller' not in waived:
        out.append(('self_sale', 'продавец и предмет — один и тот же профиль (%s): похоже на cash-in '
                    '(допэмиссия/инвестиция) под неверным типом сделки, а не на продажу'
                    % (comps.get(seller_id, {}).get('name') or seller_id)))
    asset_text = (comps.get(target_id, {}).get('name') if target_id else None) or card.get('asset')
    is_lot = bool(comps.get(target_id, {}).get('lot')) if target_id else False
    if has(asset_text) and not is_lot and not PARTY_IN_ASSET_NAME_EXEMPT.search(str(asset_text)):
        for role, role_text in (('seller', card.get('seller')), ('buyer', card.get('buyer_name'))):
            if has(role_text) and role not in waived_names and _party_name_inside(role_text, asset_text):
                out.append(('party_in_asset_name:' + role,
                            'имя стороны «%s» — внутри имени предмета «%s» (см. Dogma/ПИК: имя '
                            'продавца должно стоять в %s, а не в имени профиля предмета)'
                            % (role_text, asset_text, role)))
    # Аудит 13 сентября 2026: `check_answer()` уже проверяет описание-вместо-
    # имени для НОВОГО профиля, который читатель создаёт этим же ответом
    # (`review.ASSET_IS_A_DESCRIPTION.search(name)`), но не для профиля, УЖЕ
    # существующего в базе, на который читатель просто ссылается — а именно
    # так родился класс ASSET_IS_DESCRIPTION у 14 из 21 карточек аудита
    # (профиль создан раньше, задолго до приёмки, другим путём). Тот же
    # доверенный регэксп, применённый к уже привязанному имени: измерено на
    # живой базе 13 сентября — 0 существующих профилей ему соответствуют, то
    # есть находка появится только у НОВОГО совпадения, а не как шум сейчас.
    for role, (_tf, idf) in ROLES.items():
        cid = card.get(idf) or (role == 'target' and card.get('asset_id'))
        name = comps.get(cid, {}).get('name') if cid else None
        if name and role not in waived_names and review.ASSET_IS_A_DESCRIPTION.search(name):
            out.append(('profile_name_is_description:' + role,
                        '%s — профиль %r уже в базе, но имя — описание, а не имя компании; переименование '
                        'профиля — отдельный скрипт, не эта карточка (см. `name_ok`, если сейчас не до этого)'
                        % (role, name)))
    # Та же проверка, что `test_source_label_matches_the_link` держит для
    # всей базы (урок 9 сентября: подпись «@dealsma» на ссылке в
    # torgi.gov) — здесь раньше, до того как карточка вообще попадёт в базу.
    for item in card.get('src') or []:
        if not (isinstance(item, list) and len(item) >= 2):
            continue
        label, url = str(item[0]), str(item[1])
        if not url.startswith('http'):
            continue
        host = source_names.host_of(url)
        if source_names.label_promises_telegram(label) and not host.endswith(('t.me', 'telegram.me')):
            out.append(('source_telegram_mismatch',
                        'подпись «%s» обещает Telegram, а ссылка ведёт на %s' % (label, host)))
    top_sum, eco_sum = card.get('sum'), (card.get('eco') or {}).get('sum')
    if has(top_sum) and has(eco_sum) \
            and normalize_sum.normalize_full(str(top_sum)) != normalize_sum.normalize_full(str(eco_sum)):
        out.append(('sum_fields_differ', 'sum %r ≠ eco.sum %r — одна и та же цена должна совпадать в обоих полях'
                    % (top_sum, eco_sum)))
    if card.get('status') in ('Закрыта', 'Не состоялась'):
        for field in STALE_STATEMENT_FIELDS:
            if field in waived_stale:
                continue
            v = _text(card, field)
            if has(v) and STALE_STATEMENT_RE.search(str(v)):
                out.append(('stale_statement:' + field,
                            'денай или неснятая гипотеза о механике сделки в %s при статусе «%s»: %r'
                            % (field, card.get('status'), str(v)[:120])))
    try:
        text = format_post.render(card, base.get('companies') or {})
        for p in check_post.check(text):
            out.append(('post', 'пост: %s' % p))
    except Exception as e:  # пост, который не собирается, — тоже находка
        out.append(('post', 'пост не собирается: %s' % e))
    return out


# ---------------------------------------------------------------------------
# Досье для читателя

def candidates(name, base, limit=5):
    """Профили, похожие на имя: по ключу близнецов и по вхождению слов."""
    if not has(name):
        return []
    comps = base['companies']
    key = link_parties.company_key(name)
    out = [(cid, c['name'], 'тот же ключ') for cid, c in comps.items()
           if len(key) >= 3 and link_parties.company_key(c.get('name')) == key]
    words = [w for w in re.findall(r'[A-Za-zА-Яа-яЁё0-9-]{4,}', name.lower())
             if w not in ('ооо', 'зао', 'пао', 'акции', 'доля', 'компания', 'группа', 'холдинг')]
    for cid, c in comps.items():
        low = (c.get('name') or '').lower()
        if any(w in low for w in words) and all(cid != o[0] for o in out):
            out.append((cid, c['name'], 'по слову'))
        if len(out) >= limit:
            break
    return out


def cached_text_available(url):
    if not os.path.isdir(RAW_DIR):
        return False
    for name in os.listdir(RAW_DIR):
        if not name.endswith('-articles.jsonl'):
            continue
        with open(os.path.join(RAW_DIR, name), encoding='utf-8') as f:
            for line in f:
                if url in line:
                    return True
    return False


def dossier(card, base):
    comps = base.get('companies') or {}
    lines = ['=' * 78, '%s  %s  %s' % (card['id'], card.get('date'), card.get('status')),
             'Заголовок: %s' % card.get('title'),
             'Тип: %s · Отрасль: %s · Сумма: %s' % (card.get('type'), card.get('ind'), card.get('sum'))]
    for role, (tf, idf) in ROLES.items():
        ref = card.get(idf) or (role == 'target' and card.get('asset_id'))
        prof = comps.get(ref, {}).get('name') if ref else None
        lines.append('%-10s текст: %r | профиль: %s' % (role, card.get(tf), '%s (%s)' % (prof, ref) if ref else '—'))
        if not ref:
            for cid, nm, why in candidates(card.get(tf), base):
                lines.append('           кандидат: %s  %s  [%s]' % (cid, nm, why))
    for f in ('extra',) + tuple(PROSE_FIELDS) + ('law.appr', 'law.terms'):
        v = _text(card, f)
        if has(v):
            lines.append('%s: %s' % (f, v))
    lines.append('Источники:')
    for s in card.get('src') or []:
        url = s[1] if len(s) > 1 else ''
        lines.append('  %s — %s%s' % (s[0], url, '  [текст в кэше]' if cached_text_available(url) else ''))
    cov = coverage(card)
    if cov:
        lines.append('Другие публикации об этой сделке, найденные притоком и не прочитанные:')
        for c in cov:
            lines.append('  %s — %s  [%s, %s]%s' % (c['url'], c.get('title'), c.get('day'), c.get('why'),
                                                  '  [текст в кэше]' if cached_text_available(c['url']) else ''))
    known = registry_ids()
    for role, (_tf, idf) in ROLES.items():
        ref = card.get(idf) or (role == 'target' and card.get('asset_id'))
        if ref:
            lines.append('%-10s юрлицо: %s' % (role, 'в реестре ИНН есть' if ref in known
                                               else 'НЕТ в реестре ИНН — назовите legal_name (кириллицей, как в ЕГРЮЛ) или inn'))
    lines.append('Пост, как он уйдёт подписчику:')
    try:
        lines.extend('  | ' + l for l in format_post.render(card, comps).splitlines())
    except Exception as e:
        lines.append('  пост не собирается: %s' % e)
    f = findings(card, base)
    lines.append('Механические находки: %s' % ('нет' if not f else ''))
    lines.extend('  - %s' % t for _c, t in f)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Ответ читателя: проверка и применение

# Отрасли профилей на 11 сентября 2026 — та же таблица, что `INDUSTRIES` в
# static/index.html; к ней добавляется всё, что уже стоит у профилей базы.
KNOWN_INDUSTRIES = {
    'E-commerce', 'Автопром', 'Агро', 'Банки', 'ГМК и добыча', 'Гостиницы и туризм',
    'ЖКХ и обращение с отходами', 'Здравоохранение', 'ИТ и интернет', 'Искусственный интеллект',
    'Лесопром', 'Машиностроение', 'Медиа', 'Недвижимость', 'Нефть и газ', 'Образование',
    'Пищепром и напитки', 'Порты и инфраструктура', 'Потребительские товары', 'Производство тары',
    'Профессиональные услуги', 'Развлечения', 'Ритейл', 'Рынок ценных бумаг', 'Страхование',
    'Строительство', 'Телеком', 'Транспорт и логистика', 'Уголь', 'Управление активами',
    'Фармацевтика', 'Финансовые услуги', 'Финтех', 'Химия и удобрения', 'Холдинги', 'Энергетика',
    'Не определена'}


def industries(base):
    return KNOWN_INDUSTRIES | {c.get('ind') for c in base['companies'].values() if c.get('ind')}


def check_answer(ans, card, base):
    """Причины, по которым ответ принимать нельзя. Пусто — можно."""
    bad = []
    comps = base['companies']
    verdict = ans.get('verdict')
    if verdict not in ('accept', 'hold'):
        bad.append('verdict — accept или hold')
    if verdict == 'hold' and not str(ans.get('hold_reason') or '').strip():
        bad.append('hold без hold_reason — человеку нечего решать')
    if verdict == 'accept':
        cl = ans.get('checklist') or {}
        missing = [k for k in CHECKLIST if cl.get(k) is not True]
        if missing:
            bad.append('чек-лист не закрыт: %s' % ', '.join(missing))
    taken_roles = {r: card.get(idf) for r, (_tf, idf) in ROLES.items()}
    for p in ans.get('profiles') or []:
        role = p.get('role')
        if role not in ROLES:
            bad.append('profiles: роль %r не из target/buyer/seller' % role)
            continue
        inn, legal = p.get('inn'), str(p.get('legal_name') or '').strip()
        if inn is not None and not re.fullmatch(r'\d{10}', str(inn)):
            bad.append('profiles: inn %r — ИНН юрлица это десять цифр' % inn)
        if legal and '"' in legal:
            bad.append('profiles: прямые кавычки в legal_name %r' % legal)
        if legal and inn is None and not resolve_inn(legal):
            bad.append('profiles: ЕГРЮЛ не нашёл единственного действующего юрлица с именем %r — '
                       'уточните legal_name (кириллицей, как в ЕГРЮЛ) или назовите inn' % legal)
        if p.get('id'):
            if p['id'] not in comps:
                bad.append('profiles: профиля %s нет в базе' % p['id'])
            elif p['id'] in {v for r, v in taken_roles.items() if r != role and v}:
                bad.append('profiles: %s уже стоит в другой роли этой карточки' % p['id'])
            continue
        name = str(p.get('name') or '').strip()
        if not name:
            bad.append('profiles: у нового профиля нет имени')
            continue
        if '"' in name:
            bad.append('profiles: прямые кавычки в имени %r' % name)
        if review.ASSET_IS_A_DESCRIPTION.search(name):
            bad.append('profiles: %r — описание, а не имя компании' % name)
        fixed, changed = casing.to_nominative_asset(name)
        if changed:
            bad.append('profiles: имя %r в косвенном падеже (%r)' % (name, fixed))
        key = link_parties.company_key(name)
        twins = [cid for cid, c in comps.items() if len(key) >= 3 and link_parties.company_key(c.get('name')) == key]
        if twins:
            bad.append('profiles: %r — уже есть профиль %s, привяжите его вместо нового' % (name, twins))
        desc = str(p.get('desc') or '')
        if len(desc) < 20:
            bad.append('profiles: у %r нет описания (что это за компания)' % name)
        if proofread.press_attribution(desc):
            bad.append('profiles: описание %r с пресс-атрибуцией' % name)
        if p.get('ind') and p['ind'] not in industries(base):
            bad.append('profiles: отрасль %r не из списка' % p['ind'])
    for key in ('no_profile', 'no_inn', 'name_ok'):
        for role, reason in (ans.get(key) or {}).items():
            if role not in ROLES:
                bad.append('%s: роль %r не из target/buyer/seller' % (key, role))
            elif not str(reason or '').strip():
                bad.append('%s: у %s нет причины' % (key, role))
    for url, reason in (ans.get('no_source') or {}).items():
        if not str(url).startswith('http'):
            bad.append('no_source: ключ должен быть адресом публикации')
        elif not str(reason or '').strip():
            bad.append('no_source: у %s нет причины' % url)
    for field, reason in (ans.get('stale_ok') or {}).items():
        if field not in STALE_STATEMENT_FIELDS:
            bad.append('stale_ok: поле %r не из %s' % (field, STALE_STATEMENT_FIELDS))
        elif not str(reason or '').strip():
            bad.append('stale_ok: у %s нет причины' % field)
    title = ans.get('title')
    if title:
        old_blob = ' '.join(str(card.get(k) or '') for k in ('title', 'asset', 'buyer_name', 'seller', 'extra'))
        old_blob += ' ' + ' '.join(str(_text(card, f) or '') for f in PROSE_FIELDS)
        for p in ans.get('profiles') or []:
            old_blob += ' ' + str(p.get('name') or '') + ' ' + str(comps.get(p.get('id'), {}).get('name') or '')
        for ref in (card.get('target'), card.get('asset_id'), card.get('buyer'), card.get('seller_id')):
            old_blob += ' ' + str(comps.get(ref, {}).get('name') or '')
        known = proofread.all_words(old_blob)
        for w in _title_words(title):
            if not any(proofread.name_match(w, k) for k in known):
                bad.append('title: имя %r не встречается в карточке — новых имён в заголовке быть не может' % w)
        for n in proofread.numbers(title) - proofread.numbers(old_blob):
            bad.append('title: числа %r нет в карточке' % n)
        if '"' in title:
            bad.append('title: прямые кавычки')
        if not (20 <= len(title) <= 180):
            bad.append('title: длина вне 20–180 знаков')
    asset = ans.get('asset')
    if asset:
        fixed, changed = casing.to_nominative_asset(asset)
        if changed:
            bad.append('asset: косвенный падеж, ожидалось %r' % fixed)
        if review.ASSET_IS_A_DESCRIPTION.search(asset):
            bad.append('asset: описание вместо имени')
        if '"' in asset:
            bad.append('asset: прямые кавычки')
    share = ans.get('share')
    if share:
        if proofread.press_attribution(share):
            bad.append('share: пресс-атрибуция')
        card_blob = ' '.join(str(card.get(k) or '') for k in ('title', 'sum', 'asset', 'extra')) \
            + ' ' + ' '.join(str(_text(card, f) or '') for f in PROSE_FIELDS)
        for n in proofread.numbers(share) - proofread.numbers(card_blob):
            bad.append('share: числа %r нет в карточке' % n)
    status = ans.get('status')
    if status and status not in review.STATUS_WORDS:
        bad.append('status: %r не из списка статусов' % status)
    for s in ans.get('src_add') or []:
        if not (isinstance(s, list) and len(s) == 2 and str(s[1]).startswith('http')):
            bad.append('src_add: ожидается пара [имя, http-адрес]')
        elif any(len(x) > 1 and x[1] == s[1] for x in card.get('src') or []):
            bad.append('src_add: адрес уже в источниках: %s' % s[1])
    return bad


def apply_answer(ans, card, base, day=None, registry=None, registry_path=None, fns=None):
    """Применяет проверенный ответ к карточке. Возвращает строки отчёта и
    признак «штамп поставлен». `registry`/`registry_path`/`fns` подменяются в
    самопроверке и тестах, чтобы не трогать настоящий реестр и не ходить в сеть."""
    comps = base['companies']
    lines = []
    if fns is None and any((p.get('inn') or p.get('legal_name')) for p in ans.get('profiles') or []):
        fns = fns_client_or_none()
    known = registry_ids(registry)
    for p in ans.get('profiles') or []:
        role = p['role']
        tf, idf = ROLES[role]
        cid = p.get('id')
        if not cid:
            cid = _new_profile_id(base, p['name'])
            comps[cid] = {'name': p['name'], 'ind': p.get('ind') or card.get('ind') or 'Не определена',
                          'desc': p['desc'], 'kpi': []}
            if p.get('group'):
                comps[cid]['group'] = True
            keys = p.get('match_keys') or []
            if keys:
                base.setdefault('match_keys', {})[cid] = list(keys)
            lines.append('профиль %s: %s' % (cid, p['name']))
        card[idf] = cid
        if role == 'buyer':
            card.pop('buyer_name', None)
        elif role == 'target':
            card.pop('asset_id', None)
            if not has(card.get('asset')) and not ans.get('asset'):
                card['asset'] = comps[cid]['name']
        lines.append('%s -> %s (%s)' % (role, cid, comps[cid]['name']))
        inn, legal = p.get('inn'), str(p.get('legal_name') or '').strip()
        if legal and inn is None:
            hit = resolve_inn(legal)
            inn = hit[0] if hit else None
        if inn and cid not in known:
            add_registry_row(cid, comps[cid]['name'], inn, legal or None, card['id'],
                             registry=registry, path=registry_path, day=day)
            known.add(cid)
            lines.append('реестр ИНН + %s: %s (%s)' % (cid, inn, legal or comps[cid]['name']))
        if legal and legal not in str(comps[cid].get('desc') or ''):
            desc = str(comps[cid].get('desc') or '').rstrip()
            comps[cid]['desc'] = ((desc.rstrip('.') + '. ') if desc else '') + 'Юрлицо — %s.' % legal
        if role == 'target' and inn:
            note = target_financials(card, comps, inn, legal or None, fns)
            if note:
                lines.append(note)
    for k in ('title', 'asset', 'status'):
        if ans.get(k) and card.get(k) != ans[k]:
            lines.append('%s: %r -> %r' % (k, card.get(k), ans[k]))
            card[k] = ans[k]
    if ans.get('share'):
        card.setdefault('eco', {})['share'] = ans['share']
        lines.append('eco.share -> %r' % ans['share'])
    for s in ans.get('src_add') or []:
        label = s[0] if has(s[0]) and not re.match(r'^(tg|web):', str(s[0])) else source_names.edition_label(s[1])
        card.setdefault('src', []).append([label, s[1]])
        lines.append('src + %s' % s[1])
    waived = ans.get('no_profile') or {}
    left = findings(card, base, waived=waived, waived_inn=ans.get('no_inn') or {},
                    waived_sources=ans.get('no_source') or {}, registry=registry,
                    waived_names=ans.get('name_ok') or {}, waived_stale=ans.get('stale_ok') or {})
    if ans.get('verdict') == 'accept' and not left:
        card[STAMP] = day or date.today().isoformat()
        notes = {k: v for k, v in (('no_profile', waived), ('no_inn', ans.get('no_inn')),
                                   ('no_source', ans.get('no_source')), ('name_ok', ans.get('name_ok')),
                                   ('stale_ok', ans.get('stale_ok')), ('notes', ans.get('notes'))) if v}
        if notes:
            card[STAMP + '_notes'] = notes
        lines.append('ПРИНЯТА (%s)' % card[STAMP])
        return lines, True
    if ans.get('verdict') == 'hold':
        card['hold_reason'] = ans['hold_reason']
        lines.append('НА РЕШЕНИЕ ЧЕЛОВЕКУ: %s' % ans['hold_reason'])
    else:
        lines.append('штамп НЕ поставлен — остались находки: ' + '; '.join(t for _c, t in left))
    return lines, False


def _new_profile_id(base, name):
    import hashlib
    for n in range(1000):
        cid = 'g' + hashlib.sha1(('%s|%d' % (name, n)).encode('utf-8')).hexdigest()[:8]
        if cid not in base['companies']:
            return cid
    raise RuntimeError('не удалось выбрать id профиля')


# ---------------------------------------------------------------------------
# Правила проверяются на себе

def _self_check():
    base = {'companies': {'gsb': {'name': 'ПАО «Совкомбанк»', 'ind': 'Банки', 'desc': 'Банк.'}},
            'deals': [], 'telegram_posts': {}}
    card = {'id': 'gtest', 'title': '«Совко капитал партнерс» нарастил долю в Совкомбанке за счет акционера',
            'type': 'M&A', 'date': '2026-09-09', 'status': 'Обсуждается', 'buyer_name': '«Совко капитал партнерс»',
            'src': [['Ведомости', 'https://www.vedomosti.ru/x']],
            'eco': {'rationale': 'По оценке компании, объем рынка может достичь 8 млрд рублей.'},
            'law': {'struct': 'Книгу заявок закрыли семь инвесторов, пишут «Ведомости».'}}
    codes = {c for c, _t in findings(card, base)}
    assert 'party_unlinked:buyer' in codes and 'asset_missing' in codes and 'why' in codes, codes
    assert any(c.startswith('press:') for c in codes), codes
    # Описание вместо имени, близнец, чужое имя в заголовке — отказ.
    bad = check_answer({'verdict': 'accept', 'checklist': {k: True for k in CHECKLIST},
                        'profiles': [{'role': 'buyer', 'name': 'компания-разработчик решений в области ИБ', 'desc': 'x' * 30},
                                     {'role': 'target', 'name': 'Совкомбанк', 'desc': 'y' * 30}],
                        'title': 'Иванов купил долю в Совкомбанке'}, card, base)
    assert any('описание' in b for b in bad) and any('уже есть профиль' in b for b in bad) \
        and any('Иванов' in b for b in bad), bad
    # hold без причины, accept с незакрытым чек-листом — отказ.
    assert check_answer({'verdict': 'hold'}, card, base)
    assert any('чек-лист' in b for b in check_answer({'verdict': 'accept', 'checklist': {}}, card, base))
    # ИНН — десять цифр; legal_name, которого ЕГРЮЛ не знает, — отказ (без сети:
    # резолвер подменён). no_inn/no_source — только с причиной.
    import tempfile
    saved = dict(_RESOLVED)
    _RESOLVED.clear()
    _RESOLVED.update({'АО «Сайбер ОК»': ('9722020179', 'АКЦИОНЕРНОЕ ОБЩЕСТВО "САЙБЕР ОК"'),
                      'ООО «Нет такого»': None})
    bad = check_answer({'verdict': 'accept', 'checklist': {k: True for k in CHECKLIST},
                        'profiles': [{'role': 'target', 'id': 'gsb', 'inn': '12345'},
                                     {'role': 'buyer', 'name': 'Икс', 'desc': 'z' * 30, 'legal_name': 'ООО «Нет такого»'}],
                        'no_inn': {'seller': ''}, 'no_source': {'ftp://x': 'о другой сделке'}}, card, base)
    assert any('десять цифр' in b for b in bad) and any('ЕГРЮЛ не нашёл' in b for b in bad) \
        and any('no_inn' in b for b in bad) and any('no_source' in b for b in bad), bad
    # Верный ответ: привязка, новый профиль, честная пустота у продавца — штамп.
    ok = {'verdict': 'accept', 'checklist': {k: True for k in CHECKLIST},
          'profiles': [{'role': 'target', 'id': 'gsb', 'inn': '4401116480'},
                       {'role': 'buyer', 'name': '«Совко Капитал Партнерс»', 'ind': 'Холдинги',
                        'desc': 'Холдинговая компания основных акционеров Совкомбанка.', 'group': True,
                        'inn': '3906406196', 'legal_name': 'МКАО «Совко Капитал Партнерс»'}],
          'no_profile': {'seller': 'один из акционеров, имя не раскрыто'},
          'title': '«Совко Капитал Партнерс» увеличил долю в Совкомбанке',
          'asset': 'акции Совкомбанка', 'status': 'Закрыта',
          'src_add': [['Совкомбанк', 'https://sovcombank.ru/press']]}
    assert not check_answer(ok, card, base), check_answer(ok, card, base)

    # Аудит 12 сентября 2026: четыре класса, проверенные на живых примерах,
    # которые владелец нашёл сам (БКС/«Форштадт», S8/«Аквариус», Мать и
    # дитя/«Инвитро», Dogma/ПИК) — здесь на минимальных карточках, чтобы
    # проверка не зависела от текущего состояния базы.
    src1 = [['Ведомости', 'https://www.vedomosti.ru/x']]
    card4 = {'id': 'gtest4', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
             'seller_id': 'gsb', 'target': 'gsb', 'src': src1}
    assert 'self_sale' in {c for c, _t in findings(card4, base)}, findings(card4, base)

    base5 = {'companies': {'gpik2': {'name': '2 участка ГК ПИК в Москве (6 га)',
                                     'ind': 'Недвижимость', 'desc': 'x'}},
             'deals': [], 'telegram_posts': {}}
    card5 = {'id': 'gtest5', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
             'target': 'gpik2', 'seller': 'ГК ПИК', 'src': src1}
    assert 'party_in_asset_name:seller' in {c for c, _t in findings(card5, base5)}, findings(card5, base5)
    card5b = dict(card5); card5b['seller'] = 'Не раскрыт'
    assert 'party_in_asset_name:seller' not in {c for c, _t in findings(card5b, base5)}
    # Лот, документированная конвенция «(российский бизнес X)» и явная
    # причина читателя (`name_ok`) снимают находку без переименования.
    base5c = {'companies': {'gpik3': {'name': '2 участка ГК ПИК в Москве (6 га)',
                                      'ind': 'Недвижимость', 'desc': 'x', 'lot': True}},
              'deals': [], 'telegram_posts': {}}
    card5c = {'id': 'gtest5c', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
              'target': 'gpik3', 'seller': 'ГК ПИК', 'src': src1}
    assert 'party_in_asset_name:seller' not in {c for c, _t in findings(card5c, base5c)}
    base5d = {'companies': {'gknauf': {'name': 'Knauf (российский бизнес)', 'ind': 'Строительство', 'desc': 'x'}},
              'deals': [], 'telegram_posts': {}}
    card5d = {'id': 'gtest5d', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
              'target': 'gknauf', 'seller': 'Knauf', 'src': src1}
    assert 'party_in_asset_name:seller' not in {c for c, _t in findings(card5d, base5d)}
    assert 'party_in_asset_name:seller' not in \
        {c for c, _t in findings(card5, base5, waived_names={'seller': 'дочка названа в честь материнской'})}

    card6 = {'id': 'gtest6', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
             'sum': '12 млрд ₽', 'eco': {'sum': '15 млрд ₽'}, 'src': src1}
    assert 'sum_fields_differ' in {c for c, _t in findings(card6, base)}, findings(card6, base)
    card6b = dict(card6); card6b['eco'] = {'sum': '12 млрд ₽'}
    assert 'sum_fields_differ' not in {c for c, _t in findings(card6b, base)}

    card7 = {'id': 'gtest7', 'title': 'x', 'type': 'M&A', 'status': 'Закрыта',
             'law': {'struct': 'Сделка возможно, будет проведена через SPV.'}, 'src': src1}
    assert any(c.startswith('stale_statement:') for c, _t in findings(card7, base)), findings(card7, base)
    card7b = dict(card7); card7b['status'] = 'Обсуждается'
    assert not any(c.startswith('stale_statement:') for c, _t in findings(card7b, base))
    # eco.context — документированное место для «кто опроверг»: то же слово
    # там НЕ находка (иначе проверка ловила бы факт ровно там, где ему место).
    card7c = {'id': 'gtest7c', 'title': 'x', 'type': 'M&A', 'status': 'Закрыта',
              'eco': {'context': 'Компания публично опровергала переговоры об этом активе.'}, 'src': src1}
    assert not any(c.startswith('stale_statement:') for c, _t in findings(card7c, base))
    # Явная причина читателя (`stale_ok`) снимает находку без правки текста.
    assert not any(c.startswith('stale_statement:') for c, _t in
                   findings(card7, base, waived_stale={'law.struct': 'осознанно оставлено, полная история'}))

    class _FakeFns:
        """ГИР БО и ЕГРЮЛ без сети — ровно те числа, что у АО «Сайбер ОК»."""
        def bo(self, inn):
            return {inn: {'2024': {'2110': '87116', '2400': '1047'}, '2025': {'2110': '41371', '2400': '-40225'}}}

        def egr(self, inn):
            return {'ОткрСведения': {'КолРаб': '49', 'Дата': '2026-01-01'}}

    def _tmp_registry():
        f = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, encoding='utf-8')
        f.write('REGISTRY = []\n\n\ndef by_company_id() -> dict[str, dict]:\n    return {}\n')
        f.close()
        return f.name

    # Но проза ещё с пресс-языком и «Зачем» о рынке — штампа нет, пока не вычитано.
    _lines, stamped = apply_answer(json.loads(json.dumps(ok)), json.loads(json.dumps(card)), json.loads(json.dumps(base)),
                                   registry=[], registry_path=_tmp_registry(), fns=_FakeFns())
    assert not stamped, _lines
    card2 = json.loads(json.dumps(card))
    card2['law']['struct'] = 'Пакет продан в формате ускоренного формирования книги заявок.'
    card2['eco']['rationale'] = '—'
    # «Финансы покупаемой компании» без единого числа — описание; после приёмки
    # там показатели из ГИР БО, а описание переехало в extra, не пропало.
    card2['eco']['target_fin'] = 'Банк специализируется на розничном кредитовании.'
    base2 = json.loads(json.dumps(base))
    reg2, reg_path = [], _tmp_registry()
    assert 'target_fin_prose' in {c for c, _t in findings(card2, base2, registry=reg2)}
    lines, stamped = apply_answer(json.loads(json.dumps(ok)), card2, base2, day='2026-09-11',
                                  registry=reg2, registry_path=reg_path, fns=_FakeFns())
    assert stamped and card2[STAMP] == '2026-09-11' and card2['target'] == 'gsb' and card2.get('buyer') \
        and 'buyer_name' not in card2 and len(base2['companies']) == 2, (lines, card2)
    assert card2['accepted_notes']['no_profile']['seller']
    assert card2['eco']['target_fin'].startswith('По данным ГИР БО, выручка') and '49 человек' in card2['eco']['target_fin'] \
        and 'розничном кредитовании' in card2['extra'], card2
    assert {r['company_id'] for r in reg2} == {'gsb', card2['buyer']} and 'REGISTRY += [' in open(reg_path, encoding='utf-8').read()
    assert 'Юрлицо — МКАО «Совко Капитал Партнерс».' in base2['companies'][card2['buyer']]['desc']
    assert not findings(card2, base2, registry=reg2), findings(card2, base2, registry=reg2)
    # Без ИНН и без причины штампа нет; с причиной — есть.
    card3 = json.loads(json.dumps(card2)); card3.pop(STAMP); card3.pop(STAMP + '_notes')
    assert 'inn_missing:target' in {c for c, _t in findings(card3, base2, registry=[])}
    assert not [c for c, _t in findings(card3, base2, registry=[], waived_inn={'target': 'x', 'buyer': 'y'})
                if c.startswith('inn_missing')]
    _RESOLVED.clear()
    _RESOLVED.update(saved)

    # Аудит 13 сентября 2026 — пять новых механических классов.
    card8 = {'id': 'gtest8', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
             'events': [{'kind': 'closed', 'date': '2026-01-01', 'title': 'x',
                         'note': 'История 2026: компания купила другую в январе…'}],
             'src': src1}
    codes8 = {c for c, _t in findings(card8, base)}
    assert 'tadviser_markup:events[0].note' in codes8, codes8
    assert 'truncated:events[0].note' in codes8, codes8
    card8b = dict(card8); card8b['events'] = [{'kind': 'closed', 'date': '2026-01-01', 'title': 'x',
                                               'note': 'Сделка закрыта в январе 2026 года.'}]
    codes8b = {c for c, _t in findings(card8b, base)}
    assert not any(c.startswith(('tadviser_markup', 'truncated')) for c in codes8b), codes8b

    card9 = {'id': 'gtest9', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
             'eco': {'rationale': 'Компания расширяет присутствие на рынке за счёт нового актива.',
                     'context': 'Компания расширяет присутствие на рынке за счёт нового актива.'},
             'src': src1}
    assert 'duplicate_text:eco.rationale=eco.context' in {c for c, _t in findings(card9, base)}
    card9b = dict(card9); card9b['eco'] = dict(card9['eco'], context='Совсем другой факт про сроки.')
    assert 'duplicate_text:eco.rationale=eco.context' not in {c for c, _t in findings(card9b, base)}

    base10 = {'companies': {'gdesc': {'name': 'компания-разработчик решений для ритейла',
                                      'ind': 'ИТ и интернет', 'desc': 'x'}},
              'deals': [], 'telegram_posts': {}}
    card10 = {'id': 'gtest10', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается',
              'target': 'gdesc', 'src': src1}
    assert 'profile_name_is_description:target' in {c for c, _t in findings(card10, base10)}

    card11 = {'id': 'gtest11', 'title': 'x', 'type': 'M&A', 'status': 'Обсуждается', 'target': 'gsb',
              'src': [['@dealsma (Telegram)', 'https://torgi.gov.ru/x']]}
    assert 'source_telegram_mismatch' in {c for c, _t in findings(card11, base)}, findings(card11, base)
    card11b = dict(card11); card11b['src'] = [['@dealsma (Telegram)', 'https://t.me/dealsma/12345']]
    assert 'source_telegram_mismatch' not in {c for c, _t in findings(card11b, base)}
    return True


# ---------------------------------------------------------------------------

def main(argv):
    if '--self-check' in argv:
        _self_check()
        print('Самопроверка приёмки пройдена.')
        return 0
    base, pending = load()
    if '--queue' in argv:
        rest = [a for a in argv if a != '--queue']
        cards = queue(base, pending)
        if rest:
            cards = [c for c in cards if c['id'] in rest] or \
                [c for c in (find_card(r, base, pending)[0] for r in rest) if c]
        print('Ждут приёмки: %d' % len(cards))
        for c in cards:
            print(dossier(c, base))
        return 0
    path = next((a for a in argv if a.endswith('.json')), None)
    if not path:
        print(__doc__)
        return 1
    answers = json.load(open(path, encoding='utf-8'))
    if not isinstance(answers, list):
        print('Файл ответов обязан быть списком объектов с id и verdict.')
        return 1
    _self_check()
    write = '--write' in argv
    apply = '--apply' in argv
    refused, stamped, changed = 0, 0, 0
    for ans in answers:
        card, where = find_card(str(ans.get('id')), base, pending)
        if not card:
            print('  ОТКАЗ  %s: карточки нет ни в базе, ни в очереди' % ans.get('id'))
            refused += 1
            continue
        bad = check_answer(ans, card, base)
        if bad:
            refused += 1
            print('  ОТКАЗ  %s (%s):' % (card['id'], where))
            for b in bad:
                print('         - %s' % b)
            continue
        if not apply:
            left = findings(card, base, waived=ans.get('no_profile') or {},
                            waived_inn=ans.get('no_inn') or {}, waived_sources=ans.get('no_source') or {},
                            waived_names=ans.get('name_ok') or {}, waived_stale=ans.get('stale_ok') or {})
            print('  ГОДЕН  %s (%s)%s' % (card['id'], where,
                                          '' if not left else ' — но штамп не встанет, пока есть: ' + '; '.join(t for _c, t in left)))
            continue
        lines, ok = apply_answer(ans, card, base)
        changed += 1
        stamped += int(ok)
        print('  %s %s (%s)' % ('ПРИНЯТА' if ok else 'ПРАВКИ ', card['id'], where))
        for l in lines:
            print('         %s' % l)
    print('\nответов %d, отказов %d, применено %d, штампов %d' % (len(answers), refused, changed, stamped))
    if apply and write and changed:
        save(base, pending)
        print('Записано.')
    elif apply and changed:
        print('Сухой прогон. Запись — с ключом --write.')
    return 1 if refused else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
