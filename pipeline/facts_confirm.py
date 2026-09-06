# -*- coding: utf-8 -*-
"""Подтверждение фактов чтением источников: очередь, проверка ответов
читателей, запись в `facts` (см. facts.py).

Три уровня проверки, и они разные (разбор рецензента, 6 сентября 2026):
  1. ИСТОЧНИК — цитата читателя дословно лежит в тексте статьи (кэш
     data/inbox/raw/*-articles.jsonl, статьи скачиваются при сборке очереди);
     значение выводимо из цитаты (доля — deal_multiples.acquired_percents,
     сумма — parse_rub_sum, дата — день и месяц названы).
  2. СМЫСЛ — цитата подтверждает существование слов, но не трактовку
     («500 млрд ₽» стояли в источнике и относились к допэмиссии). Поэтому
     читатель отвечает на вопросы об ОБЪЕКТЕ, СОБЫТИИ и ПЕРИМЕТРЕ, а факт
     становится verified только когда два НЕЗАВИСИМЫХ чтения сошлись в
     значении и смысле. Разошлись — disputed, факт ждёт человека и в
     расчёты не идёт. Чтение моделью и подтверждение человеком различаются
     полем verified_by ('model×2' / 'human:<имя>').
  3. АРИФМЕТИКА — facts.number_checks: порядок величины, единицы, валюта,
     доля против периметра цены. Считается при derive и в тестах.

Ответ читателя — JSON-список (схема в pipeline/FACTS_READING_BRIEF.md):
  {"id", "reader", "unreadable": bool,
   "stake":     {"value", "object", "event", "quote", "source"} | null,
   "price":     {"value_rub", "meaning", "scope", "quote", "source"} | null,
   "date":      {"value", "meaning", "quote", "source"} | null,
   "nature":    {"control_change": bool, "quote"} | null,
   "perimeter": {"ok": bool, "entity", "quote", "source"} | null,
   "notes"}
null у факта значит «источник этого не устанавливает» — это тоже результат,
он записывается (reading.result = 'not_in_source'), основание не растёт.

Запуск:
    python3 pipeline/facts_confirm.py --queue --metric multiple --out data/inbox/facts/queue-multiple.json
    python3 pipeline/facts_confirm.py --queue --metric top --limit 40 --out data/inbox/facts/queue-top.json
    python3 pipeline/facts_confirm.py --check data/inbox/facts/read-A.json
    python3 pipeline/facts_confirm.py --write data/inbox/facts/read-A.json data/inbox/facts/read-B.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'pipeline' / 'ingest'))
import deal_multiples as dm  # noqa: E402
import facts  # noqa: E402
from pipeline import fns_registry, source_names  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
RAW = ROOT / 'data' / 'inbox' / 'raw'
EVENTS = ('closing', 'signing', 'announcement', 'publication', 'registry')
# Кто назвал число: стороны/официальное сообщение, документ (отчётность,
# проспект, раскрытие), реестр, анонимные источники СМИ, аналитик. Только
# первые три дают meaning 'disclosed'; «по данным источников» — 'reported'.
ATTRIBUTIONS = ('parties', 'filing', 'registry', 'adviser', 'media_sources', 'analyst', 'unknown')
PARTY_ATTRIBUTIONS = ('parties', 'filing', 'registry')
PROD = 'https://projectcompass.ru'
MONTHS = ('январ', 'феврал', 'март', 'апрел', 'ма[йя]', 'июн', 'июл', 'август', 'сентябр', 'октябр', 'ноябр', 'декабр')


def flat(s: str) -> str:
    s = str(s or '').lower().replace('ё', 'е').replace('\xa0', ' ')
    s = re.sub(r'[«»"“”„‘’\'`]', '', s)
    s = re.sub(r'[—–‑]', '-', s)
    return re.sub(r'\s+', ' ', s).strip()


def load_base():
    return json.load(open(DATA, encoding='utf-8'))


def save_base(base):
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def source_texts() -> dict[str, str]:
    """url -> текст статьи из кэша притока (только -articles.jsonl: там полный текст)."""
    out: dict[str, str] = {}
    if not RAW.is_dir():
        return out
    for name in sorted(os.listdir(RAW)):
        if not name.endswith('-articles.jsonl'):
            continue
        for line in open(RAW / name, encoding='utf-8'):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get('url') and rec.get('summary'):
                out[rec['url']] = rec['summary']
    return out


# ---------- очередь ----------

def _urls(card) -> list[str]:
    return [str(s[1]) for s in card.get('src') or [] if isinstance(s, list) and len(s) > 1 and str(s[1]).startswith('http')]


def build_queue(metric: str, limit: int, base, ctx) -> list[dict]:
    deals = {d['id']: d for d in base['deals']}
    reg = ctx['registry']
    rows = []
    if metric == 'multiple':
        confirmed = {c for c, r in reg.items() if r['decision'] == 'confirmed'}
        banks = {c for c, r in reg.items() if r['decision'] == 'bank'}
        for did, d in deals.items():
            cand, _ = dm.admission(dict(d, id=did), confirmed, banks, ctx['lot_ids'])
            if cand and d['facts']['reasons']['multiple_text'] != 'ok':
                rows.append(d)
    elif metric == 'top':
        for d in deals.values():
            f = d['facts']
            if f['price'].get('meaning') == 'disclosed' and f['price'].get('value_rub') \
                    and f['price'].get('basis') not in ('read', 'verified', 'disputed') \
                    and f['reasons']['purchase_sums'] in ('price_not_read', 'stale'):
                rows.append(d)
        rows.sort(key=lambda d: -(d['facts']['price'].get('value_rub') or 0))
    elif metric == 'price_recheck':
        # Повторное чтение цены с вопросом «кто назвал число» (attribution) —
        # для уже подтверждённых цен без этого признака.
        for d in deals.values():
            pf = d['facts']['price']
            if pf.get('basis') in ('read', 'verified') and not pf.get('attribution'):
                rows.append(d)
        rows.sort(key=lambda d: -(d['facts']['price'].get('value_rub') or 0))
    elif metric == 'perimeter':
        # Периметр по КОНКРЕТНОМУ отчёту: подтверждённые доля и цена, но
        # периметр без привязки к отчёту (или не прочитан).
        for d in deals.values():
            f = d['facts']
            if f['stake'].get('basis') == 'verified' and f['price'].get('basis') == 'verified' \
                    and f['nature'].get('control_change') and not (f['target'].get('perimeter_report') or {}).get('inn') \
                    and f['target'].get('perimeter') != 'refuted':
                rows.append(d)
    else:
        raise SystemExit('metric: multiple | top | price_recheck | perimeter')
    rows = rows[:limit]
    tasks = []
    for d in rows:
        target = dm.target_of(d)
        prof = (base['companies'] or {}).get(target) or {}
        r = reg.get(target) or {}
        tasks.append({
            'id': d['id'], 'title': d['title'], 'date': d.get('date'), 'status': d.get('status'), 'type': d.get('type'),
            'sum': d.get('sum'), 'share_text': (d.get('eco') or {}).get('share'), 'asset': d.get('asset'),
            'buyer': d.get('buyer_name') or ((base['companies'] or {}).get(d.get('buyer')) or {}).get('name'),
            'seller': d.get('seller') or ((base['companies'] or {}).get(d.get('seller_id')) or {}).get('name'),
            'target_profile': prof.get('name'), 'target_inn': r.get('inn') if r.get('decision') == 'confirmed' else None,
            'sources': _urls(d),
            'confirm': (['price'] if metric == 'price_recheck' else ['perimeter'] if metric == 'perimeter'
                        else ['price', 'date', 'nature'] + (['stake', 'perimeter'] if metric == 'multiple' else [])),
            'current': {k: d['facts'][k] for k in ('stake', 'price', 'date')},
        })
        if metric in ('perimeter', 'multiple') and target:
            tasks[-1]['report'] = report_for(target, d)
    return tasks


def report_for(company_id: str, deal: dict) -> dict | None:
    """Отчёт, который пойдёт в знаменатель: юрлицо, ИНН, год и выручка с
    боевого сайта (/api/companies/<id>/fns) — тот же выбор года, что в
    compute_market_multiples (последний полный год до сделки, разрыв 1–2).
    Читатель подтверждает периметр относительно ЭТОГО отчёта."""
    import urllib.request
    # тот же год, что возьмёт compute_market_multiples: подтверждённая дата
    # закрытия сильнее даты карточки (multiple_year), отчёты — строго до него
    year, _ = dm.multiple_year(deal)
    year = year or 0
    try:
        with urllib.request.urlopen(f'{PROD}/api/companies/{company_id}/fns?as_of_year={year}', timeout=60) as r:
            j = json.load(r)
    except Exception as e:  # noqa: BLE001
        return {'error': str(e)[:80]}
    ent = (j.get('entities') or [{}])[0]
    e = ent.get('entity') or {}
    reps = [x for x in (ent.get('reports') or []) if x.get('revenue_rub') is not None and x.get('year') and year - dm.MAX_YEAR_GAP <= x['year'] < year]
    reps.sort(key=lambda x: -x['year'])
    if not reps:
        return {'legal_name': e.get('legal_name'), 'inn': e.get('inn'), 'note': 'подходящего отчёта нет'}
    r0 = reps[0]
    return {'legal_name': e.get('legal_name'), 'inn': e.get('inn'), 'year': r0['year'],
            'revenue_rub': r0['revenue_rub'], 'operating_profit_rub': r0.get('operating_profit_rub')}


def prefetch(tasks) -> None:
    import fetch_article_texts as fat  # noqa: E402  (pipeline/ingest в sys.path)
    targets = []
    for t in tasks:
        for u in t['sources']:
            targets.append((t['id'], u, t['title']))
    if targets:
        got, failed = fat.fetch_and_store(targets, write=True)
        print(f'Тексты источников: скачано {got}, не вышло {failed}, уже были {len(targets) - got - failed}.')


# ---------- проверка ----------

def stake_supported(value, quote) -> bool:
    if value is None or not quote:
        return False
    if any(abs(value - x) < 0.05 for x in dm.acquired_percents(quote)):
        return True
    return value == 100 and dm.stake_established({'title': quote, 'eco': {}}) == 100.0


def price_supported(value_rub, quote) -> bool:
    if value_rub is None or not quote:
        return False
    parsed = dm.parse_rub_sum(quote)
    if parsed and abs(parsed - value_rub) <= max(1.0, 0.01 * value_rub):
        return True
    # «8,7 млрд руб.» без значка — parse_rub_sum требует ₽; проверяем число и единицу
    m = re.search(r'(\d[\d\s\xa0]*(?:[.,]\d+)?)\s*(тыс|млн|млрд|трлн)', quote, re.I)
    if m:
        n = float(m.group(1).replace(' ', '').replace('\xa0', '').replace(',', '.')) * dm.UNIT_MULT[m.group(2).lower()]
        return abs(n - value_rub) <= max(1.0, 0.01 * value_rub)
    return False


def date_supported(value, quote) -> bool:
    if not value or not quote:
        return False
    if not re.fullmatch(r'\d{4}(-\d{2}(-\d{2})?)?', value):
        return False
    q = flat(quote)
    if len(value) == 10:
        y, m, d = value.split('-')
        return (re.search(r'(?:^|[^\d])%d\s+%s' % (int(d), MONTHS[int(m) - 1]), q) is not None
                or value in q or f'{d}.{m}.{y}' in q)
    if len(value) == 7:
        y, m = value.split('-')
        return re.search(MONTHS[int(m) - 1], q) is not None and y in q
    return value in q


def entity_supported(entity, quote) -> bool:
    if not entity or not quote:
        return False
    words = [w for w in re.findall(r'[а-яёa-z0-9]{3,}', flat(entity)) if w not in ('ооо', 'пао', 'зао', 'акционерное', 'общество')]
    q = flat(quote)
    return bool(words) and all(w[:6] in q for w in words)


def check_reading(rec: dict, card: dict, texts: dict[str, str]) -> tuple[dict, list[str]]:
    """Возвращает (нормализованная запись, список проблем)."""
    problems = []
    out = {'id': rec['id'], 'reader': rec.get('reader') or '?', 'unreadable': bool(rec.get('unreadable'))}
    if not out['reader'] or out['reader'] == '?':
        problems.append('нет reader')

    def quote_ok(q, url):
        if not q:
            return False
        text = texts.get(url) if url else None
        if text is None:
            return None  # источника в кэше нет — проверить нельзя
        return flat(q) in flat(text)

    def find_source(q):
        """Источник по цитате: в каком из скачанных текстов карточки она лежит
        дословно (для nature читатель раньше источник не указывал)."""
        for u in _urls(card):
            t = texts.get(u)
            if t and flat(q) in flat(t):
                return u
        return None

    for key in ('stake', 'price', 'date', 'nature', 'perimeter'):
        fact = rec.get(key)
        if fact is None:
            out[key] = None
            continue
        if not isinstance(fact, dict):
            problems.append(f'{key}: не объект')
            continue
        q, url = fact.get('quote') or '', fact.get('source')
        if key == 'nature' and not url and q:
            url = find_source(q)
            if url:
                fact = dict(fact, source=url)
        if not (url and str(url).startswith('http')):
            problems.append(f'{key}: нет source' + (' (цитата не найдена ни в одном источнике карточки)' if key == 'nature' else ''))
        qc = quote_ok(q, url)
        if qc is False:
            problems.append(f'{key}: цитата не найдена дословно в {url}')
        f = dict(fact, quote_checked=qc)
        if key == 'stake':
            try:
                f['value'] = float(fact.get('value'))
            except (TypeError, ValueError):
                problems.append('stake: value не число'); f['value'] = None
            if f['value'] is not None and not stake_supported(f['value'], q):
                problems.append(f'stake: {f["value"]} не выводится из цитаты')
            if fact.get('event') not in EVENTS:
                problems.append(f'stake: event вне {EVENTS}')
            if not fact.get('object'):
                problems.append('stake: нет object')
        elif key == 'price':
            if fact.get('meaning') not in dm.SUM_BASES:
                problems.append(f'price: meaning вне списка')
            if fact.get('scope') not in facts.PRICE_SCOPES:
                problems.append('price: scope вне package/equity/ev/unknown')
            v = fact.get('value_rub')
            attr = fact.get('attribution')
            if attr is not None and attr not in ATTRIBUTIONS:
                problems.append(f'price: attribution вне {ATTRIBUTIONS}')
            if fact.get('event') is not None and fact.get('event') not in EVENTS:
                problems.append(f'price: event вне {EVENTS}')
            if fact.get('meaning') == 'disclosed' and attr in ('adviser', 'media_sources', 'analyst'):
                # Число, поданное консультантом стороны в таблицу издания
                # («Сделки года» Ъ, запись Verba Legal о ВТБ/«Аврора Инвест»,
                # 255 млрд ₽), — не раскрытие сторонами: сам ВТБ цену не называл.
                problems.append('price: disclosed при attribution adviser/media_sources/analyst — это reported или estimate')
            if fact.get('meaning') == 'disclosed':
                if v is None:
                    problems.append('price: disclosed без value_rub')
                elif not price_supported(float(v), q):
                    problems.append(f'price: {v} не выводится из цитаты')
                else:
                    card_v = dm.parse_rub_sum(card.get('sum'))
                    if card_v and abs(card_v - float(v)) > 0.01 * card_v:
                        problems.append(f'price: {v} расходится с суммой карточки {card.get("sum")!r} — сначала правка карточки через review.py')
        elif key == 'date':
            if fact.get('meaning') not in dm.DATE_BASES:
                problems.append('date: meaning вне списка')
            if not date_supported(fact.get('value'), q):
                problems.append(f'date: {fact.get("value")} не выводится из цитаты')
        elif key == 'nature':
            if not isinstance(fact.get('control_change'), bool):
                problems.append('nature: control_change не bool')
        elif key == 'perimeter':
            if not isinstance(fact.get('ok'), bool):
                problems.append('perimeter: ok не bool')
            if fact.get('ok') and not entity_supported(fact.get('entity'), q):
                problems.append('perimeter: entity не встречается в цитате')
            rep = fact.get('report')
            if rep is not None and (not isinstance(rep, dict) or not rep.get('inn') or not rep.get('year')):
                # У задания без подходящего отчёта (ТПГК: выручки за нужный
                # год нет) читатель подтверждает только юрлицо — отчёта, к
                # которому привязать периметр, нет, и это не ошибка чтения.
                fact['report'] = rep = None
            if rep is not None:
                # версия 2: периметр относительно конкретного отчёта
                if fact.get('ok') and fact.get('covers_business') is not True:
                    problems.append('perimeter: ok=true, но covers_business не true')
                if fact.get('ok') and fact.get('other_entities'):
                    problems.append(f'perimeter: ok=true при других юрлицах в периметре {fact.get("other_entities")}')
        out[key] = f
    out['notes'] = rec.get('notes') or ''
    return out, problems


def check_files(paths, base=None, texts=None):
    base = base or load_base()
    texts = texts if texts is not None else source_texts()
    deals = {d['id']: d for d in base['deals']}
    ok_all = True
    result = {}
    for path in paths:
        recs = json.load(open(path, encoding='utf-8'))
        for rec in recs:
            card = deals.get(rec.get('id'))
            if not card:
                print(f'✗ {rec.get("id")}: карточки нет в базе'); ok_all = False
                continue
            norm, problems = check_reading(rec, card, texts)
            result.setdefault(rec['id'], []).append(norm)
            mark = '✓' if not problems else '✗'
            print(f'{mark} {rec["id"]} [{norm["reader"]}] {card["title"][:60]}')
            for p in problems:
                print('     ', p)
            if problems:
                ok_all = False
    return ok_all, result


# ---------- запись ----------

# Согласие двух чтений — по той части факта, от которой зависит ДОПУСК:
# для цены это «названа ли цена сторонами» и её величина, для даты — день,
# для доли — процент, для природы — смена контроля, для периметра — ok.
# Оттенки (estimate против not_a_price, announcement против publication,
# scope пакета) не делают факт спорным: они хранятся вариантами, а для
# показа берётся более осторожный. Периметр цены (scope) нужен только
# мультипликатору и подтверждается отдельно (scope_basis).
DATE_STRENGTH = {'publication': 0, 'announcement': 1, 'signing': 2, 'closing': 3, 'registry': 4}


def _agree(key, a, b) -> bool:
    if key == 'stake':
        return abs(float(a['value']) - float(b['value'])) < 0.05
    if key == 'price':
        da, db = a.get('meaning') == 'disclosed', b.get('meaning') == 'disclosed'
        if da != db:
            return False
        if not da:
            return True  # оба: «это не цена, названная сторонами» — какая именно, для допуска не важно
        # одно и то же СОБЫТИЕ: если оба читателя назвали событие цены, оно обязано совпасть
        # (Shell/«Сахалин-2»: равные суммы у разрешения 2023 года и у покупки 2024-го)
        # Ярлык события (объявление / подписание / закрытие / реестр) у
        # одной и той же цены читатели ставят по-разному — это не спор о
        # цене: девять из 25 цен первого прогона «разошлись» только в нём.
        # Две РАЗНЫЕ сделки с одной суммой (Shell/«Сахалин-2»: разрешение
        # НОВАТЭКу и покупка «Газпромом») ловит спорная ДАТА — она снимает
        # сделку с показателей по годам; ярлыки сохраняются в event_variants.
        va, vb = a.get('value_rub'), b.get('value_rub')
        return va is not None and vb is not None and abs(va - vb) <= 0.01 * max(va, vb, 1)
    if key == 'date':
        return a.get('value') == b.get('value')
    if key == 'nature':
        return a.get('control_change') == b.get('control_change')
    if key == 'perimeter':
        if a.get('ok') != b.get('ok'):
            return False
        ra, rb = a.get('report') or {}, b.get('report') or {}
        # Два чтения подтверждают периметр ОДНОГО отчёта: разные ИНН или
        # годы — это два разных знаменателя, а не согласие.
        return (ra.get('inn'), ra.get('year')) == (rb.get('inn'), rb.get('year'))
    return False


def merged_fields(key, readings: list[dict]) -> dict:
    """Значение для записи по согласным чтениям: осторожный вариант там, где
    читатели разошлись в оттенке."""
    r0 = readings[0]
    if key == 'price':
        meanings = [r.get('meaning') for r in readings]
        scopes = [r.get('scope') for r in readings]
        attrs = [r.get('attribution') for r in readings if r.get('attribution')]
        out = {'value_rub': r0.get('value_rub') if all(m == 'disclosed' for m in meanings) else None,
               'meaning': r0.get('meaning'), 'meaning_variants': sorted(set(meanings))}
        if attrs:
            out['attribution'] = attrs[0] if len(set(attrs)) == 1 else 'disputed'
            out['attribution_variants'] = sorted(set(attrs))
        events = [r.get('event') for r in readings if r.get('event')]
        if events:
            out['event'] = events[0] if len(set(events)) == 1 else 'disputed'
            out['event_variants'] = sorted(set(events))
        if len(scopes) >= 2 and len(set(scopes)) == 1 and scopes[0] != 'unknown':
            out['scope'], out['scope_basis'] = scopes[0], 'verified'
        elif len(scopes) == 1 and scopes[0] != 'unknown':
            out['scope'], out['scope_basis'] = scopes[0], 'read'
        else:
            out['scope'], out['scope_basis'] = 'unknown', 'disputed' if len(set(scopes)) > 1 else 'unknown'
            out['scope_variants'] = sorted(set(scopes))
        return out
    if key == 'date':
        meanings = [r.get('meaning') for r in readings]
        return {'value': r0.get('value'), 'meaning': min(meanings, key=lambda m: DATE_STRENGTH.get(m, 0)),
                'meaning_variants': sorted(set(meanings))}
    if key == 'stake':
        return {'value': float(r0['value']), 'object': r0.get('object'), 'event': r0.get('event'),
                'event_variants': sorted({r.get('event') for r in readings})}
    if key == 'nature':
        return {'control_change': r0.get('control_change')}
    if key == 'perimeter':
        out = {'perimeter_entity': r0.get('entity')}
        if r0.get('report'):
            out['perimeter_report'] = {k: r0['report'].get(k) for k in ('inn', 'year', 'revenue_rub', 'legal_name')}
            out['perimeter_other_entities'] = r0.get('other_entities') or []
        return out
    return {}


def _basis_for(readings: list[dict]) -> tuple[str, str]:
    """Основание по набору чтений одного факта: verified / read / disputed."""
    if len(readings) >= 2:
        if all(_agree_key(readings[0], r) for r in readings[1:]):
            checked = any(r.get('quote_checked') for r in readings)
            if checked or _same_quote(readings):
                return 'verified', 'model×%d' % len(readings)
            return 'read', 'model×%d, цитаты не сверены с текстом' % len(readings)
        return 'disputed', 'model×%d' % len(readings)
    r = readings[0]
    return 'read', 'model×1' + ('' if r.get('quote_checked') else ', цитата не сверена с текстом')


def _agree_key(a, b):
    return _agree(a['_key'], a, b)


def _same_quote(readings) -> bool:
    qs = [flat(r.get('quote')) for r in readings]
    words = [set(q.split()) for q in qs]
    return all(len(words[0] & w) >= 8 for w in words[1:])


def write_readings(paths, write=False, asked=('stake', 'price', 'date', 'nature', 'perimeter')):
    base = load_base()
    ctx = facts.build_ctx(base, fns_registry.REGISTRY)
    texts = source_texts()
    ok, result = check_files(paths, base, texts)
    if not ok:
        print('\nЕсть проблемы — запись отменена, исправьте ответы читателей.')
        return 1
    deals = {d['id']: d for d in base['deals']}
    today = date.today().isoformat()
    summary = {'verified': 0, 'read': 0, 'disputed': 0, 'not_in_source': 0}
    discrepancies = []
    for did, recs in result.items():
        d = deals[did]
        f = d.setdefault('facts', {})
        for key, target_key in (('stake', 'stake'), ('price', 'price'), ('date', 'date'), ('nature', 'nature'), ('perimeter', 'target')):
            if key not in asked:
                continue
            readings = [dict(r[key], reader=r['reader'], _key=key) for r in recs if r.get(key)]
            fact = dict(f.get(target_key) or {})
            if not readings:
                if any(r.get(key) is None and not r.get('unreadable') for r in recs):
                    fact['reading'] = {'result': 'not_in_source', 'at': today,
                                       'readers': [r['reader'] for r in recs if r.get(key) is None],
                                       'notes': [r.get('notes') for r in recs if r.get('notes')][:2]}
                    summary['not_in_source'] += 1
                f[target_key] = fact
                continue
            basis, by = _basis_for(readings)
            summary[basis] += 1
            r0 = readings[0]
            if basis == 'disputed':
                fact['disputed'] = [{k: v for k, v in r.items() if k not in ('_key',)} for r in readings]
            else:
                fact.update(merged_fields(key, readings))
            if key == 'perimeter':
                fact['perimeter'] = (basis if r0.get('ok') else 'refuted') if basis != 'disputed' else 'disputed'
                if basis == 'disputed':
                    fact.pop('perimeter_report', None)
            elif key == 'nature':
                fact['control_change_basis'] = basis  # флаги природы остаются правилом (basis 'rule')
            else:
                fact['basis'] = basis
            # Подтверждённый двумя чтениями смысл — в явные поля карточки
            # (они сильнее разбора текста и видны PDF, ассистенту и правилам):
            # sum_basis, date_basis, stake_acquired. Поля ставятся ДО отпечатка,
            # иначе факт сам себя сделал бы stale.
            if basis == 'verified':
                if key == 'price' and fact.get('meaning') in dm.SUM_BASES and dm.sum_basis(d) != fact['meaning']:
                    d['sum_basis'] = fact['meaning']
                if key == 'date' and fact.get('value') == d.get('date') and fact.get('meaning') in dm.DATE_BASES \
                        and d.get('date_basis') != fact['meaning']:
                    d['date_basis'] = fact['meaning']
                if key == 'stake' and fact.get('value') and d.get('stake_acquired') != fact['value'] \
                        and dm.stake_established(d) != fact['value']:
                    d['stake_acquired'] = fact['value']
            fact.update(quote=r0.get('quote'), source=r0.get('source'), verified_by=by, verified_at=today,
                        card_hash=facts.card_hash(d, target_key),
                        readings=[{k: v for k, v in r.items() if k not in ('_key',)} for r in readings])
            f[target_key] = fact
            # расхождение прочитанного факта с полем карточки — не правится молча:
            # это очередь для review.py (цитаты уже есть), а не для этого шага
            if basis in ('read', 'verified'):
                if key == 'date' and fact.get('value') and str(d.get('date') or '')[:len(fact['value'])] != fact['value'] \
                        and not str(d.get('date') or '').startswith(fact['value'][:4]) or (
                        key == 'date' and fact.get('value') and len(fact['value']) == 10 and d.get('date') != fact['value']):
                    discrepancies.append((did, 'date', d.get('date'), fact['value'], fact.get('meaning')))
                if key == 'price' and fact.get('meaning') != 'disclosed' and dm.sum_basis(d) == 'disclosed':
                    discrepancies.append((did, 'sum', d.get('sum'), fact.get('meaning'), (r0.get('notes') or '')[:80]))
            # источник, по которому подтверждена цитата, — в src карточки
            url = r0.get('source')
            if url and url not in _urls(d) and r0.get('quote_checked'):
                d.setdefault('src', []).append([source_names.edition_label(url), url])
        d['facts'] = facts.derive(d, ctx)
        print(f'{did}: ' + ', '.join(f'{k}={d["facts"][k].get("basis")}' for k in ('stake', 'price', 'date'))
              + f', perimeter={d["facts"]["target"].get("perimeter")}, multiple_text={d["facts"]["reasons"]["multiple_text"]}, top={d["facts"]["reasons"]["top_purchases"]}')
    print('Итог: ' + ', '.join(f'{k} — {v}' for k, v in summary.items()))
    if discrepancies:
        print('Расхождения прочитанного с карточкой (очередь для review.py / человека):')
        for row in discrepancies:
            print('  ', ' | '.join(str(x) for x in row))
        if write:
            # Очередь расхождений живёт в git (контейнер рутины одноразовый):
            # рутина качества берёт отсюда, что править через review.py с уже
            # готовыми цитатами, а человек — что решать (год сделки).
            qpath = ROOT / 'pipeline' / 'facts_discrepancies.json'
            queue = json.load(open(qpath, encoding='utf-8')) if qpath.exists() else []
            seen = {(q['id'], q['field']) for q in queue}
            for did, field, card_value, read_value, extra in discrepancies:
                if (did, field) in seen:
                    continue
                queue.append({'id': did, 'field': field, 'card': card_value, 'read': read_value, 'note': extra,
                              'found': today, 'resolved': None})
            json.dump(queue, open(qpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'Очередь расхождений: {qpath.relative_to(ROOT)} ({len(queue)} записей)')
    if write:
        save_base(base)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--queue', action='store_true')
    ap.add_argument('--metric', default='multiple')
    ap.add_argument('--limit', type=int, default=40)
    ap.add_argument('--out')
    ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--check', nargs='+')
    ap.add_argument('--apply', nargs='+', help='файлы читателей для записи')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--asked', default='stake,price,date,nature,perimeter',
                    help='какие факты спрашивали у читателей (для очереди top — price,date,nature)')
    a = ap.parse_args()
    if a.queue:
        base = load_base()
        ctx = facts.build_ctx(base, fns_registry.REGISTRY)
        tasks = build_queue(a.metric, a.limit, base, ctx)
        print(f'Очередь «{a.metric}»: {len(tasks)} сделок.')
        for t in tasks:
            print(f'  {t["id"]} {t["title"][:70]} | {t["sum"]} | источников {len(t["sources"])}')
        if not a.no_fetch:
            prefetch(tasks)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(tasks, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('Задания:', a.out)
        return 0
    if a.check:
        ok, _ = check_files(a.check)
        return 0 if ok else 1
    if a.apply:
        return write_readings(a.apply, write=a.write, asked=tuple(x.strip() for x in a.asked.split(',') if x.strip()))
    ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
