# -*- coding: utf-8 -*-
"""Правка факта в существующей карточке — только с цитатой источника.

ЗАЧЕМ. 11 ноября 2026 прошли по истории базы (2170 версий с 15 июля) и нашли,
когда появились 34 серьезные ошибки из вычитки 45 карточек консультантов
форума: 20 — при сборке карточки в июле, 5 — при обогащении через месяц
(«дописаны» БЦ «Домино» к KR Properties, «Полекс Урал переименовано в Пегас»),
5 — массовыми правками по всей базе (продавец «СУЭК» у «Интер РАО» при выносе
продавцов в поле, заголовок «Холдинг VK купил четверть акций «Р7»» при вычитке
3 ноября), 1 — пересказом. Общее у последних десяти: факт менял скрипт или
помощник, и рядом с новым значением не было слов источника, которые его
подтверждают. Владелец, 11 ноября 2026: проверку по цитате делать.

ПРАВИЛО. У карточки, которая уже есть в базе, поле-факт (FACT_FIELDS: заголовок,
дата, статус, сумма, доля, стороны, предмет, консультанты) меняется только если
новое значение подтверждено:
  * записью таблицы правок (`pipeline/ingest/fixes/*.py`, архив
    `fixes_archive/*.json`) с тем же id, полем и значением и непустой цитатой
    (`quote`) — так пишет `review.py`, и он же проверяет, что цитата лежит в
    тексте источника;
  * или строкой в `card['fact_log']`: {field, new, quote, url, date, by} —
    так пишут разовые скрипты и `enrich.py` (функция `log()` ниже).
Правка без подтверждения — отказ записи. Смена формы без смены смысла
(«ё», кавычки, пробелы, тире, «2 500 млн ₽» → «2,5 млрд ₽») подтверждения не
требует.

Карточка с измененным фактом сама возвращается в очередь вычитки: отпечаток
`readiness.fingerprint` меняется, `reread_queue.py` ставит такие карточки
первыми («изменены после проверки»).

    python3 pipeline/fact_edit_guard.py                 # рабочая копия против HEAD
    python3 pipeline/fact_edit_guard.py --base origin/main

Разовый скрипт зовет `mass_edit_guard.check(old, new)` перед записью — эта
проверка идет внутри него. Решения владельца из консоли (`approve.py`) сюда не
ходят: владелец сам себе источник.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FACT_FIELDS = ('title', 'date', 'status', 'sum', 'eco.sum', 'eco.share', 'buyer', 'seller', 'target',
               'asset', 'buyer_name', 'seller_name', 'law.adv', 'eco.finadv')


def get(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def _norm(v):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, sort_keys=True)
    s = s.replace('ё', 'е').replace('Ё', 'Е')
    s = re.sub(r'[«»“”„"]', '"', s)
    s = re.sub(r'[–—−-]', '-', s)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s


_NUM = re.compile(r'(\d[\d\s ]*(?:,\d+)?)\s*(млн|млрд|трлн)')
_MULT = {'млн': 1e6, 'млрд': 1e9, 'трлн': 1e12}


def _amounts(s):
    out = []
    for num, unit in _NUM.findall(s or ''):
        try:
            out.append(round(float(re.sub(r'[\s ]', '', num).replace(',', '.')) * _MULT[unit]))
        except ValueError:
            pass
    return out


def same_meaning(field, old, new):
    """Смена формы, а не факта."""
    if _norm(old) == _norm(new):
        return True
    if field in ('sum', 'eco.sum') and isinstance(old, str) and isinstance(new, str):
        a, b = _amounts(old), _amounts(new)
        rest = lambda s: _norm(_NUM.sub('#', s))
        return bool(a) and a == b and rest(old) == rest(new)
    return False


PARTY_FIELDS = ('buyer', 'seller', 'target', 'asset')


def _party_name(value, comps):
    """Профиль стороны читается по его имени: привязка текста «ООО «Ромашка»» к профилю
    «Ромашка» — смена формы, а не факта."""
    if isinstance(value, str) and value in comps:
        return (comps[value] or {}).get('name') or value
    return value


def _strip_form(s):
    return re.sub(r'^(ооо|ао|пао|зао|оао|нао|мкпао|ип|гк|группа компаний|группа)\s+', '', _norm(s or '')).strip(' "')


def fact_changes(old_data, new_data):
    """(id, поле, было, стало) по карточкам, которые были и раньше."""
    before = {d['id']: d for d in old_data.get('deals') or []}
    oc, nc = old_data.get('companies') or {}, new_data.get('companies') or {}
    out = []
    for d in new_data.get('deals') or []:
        o = before.get(d['id'])
        if not o:
            continue
        for f in FACT_FIELDS:
            a, b = get(o, f), get(d, f)
            if a == b or same_meaning(f, a, b):
                continue
            if f in PARTY_FIELDS:
                na, nb = _party_name(a, oc), _party_name(b, nc)
                texts = [na]
                if isinstance(b, str) and b in nc:
                    texts += [d.get(f + '_name'), o.get(f + '_name')]
                    if f == 'target':
                        texts += [o.get('asset'), d.get('asset')]
                    texts += [o.get('title')]
                key = _strip_form(nb) if isinstance(nb, str) else ''
                # Имя профиля совпадает с прежним текстом стороны или стоит в нем
                # («доля в сети клиник Александрия…» → профиль «Александрия»).
                if len(key) >= 3 and any(isinstance(t, str) and (key == _strip_form(t) or key in _norm(t))
                                         for t in texts):
                    continue
            out.append((d['id'], f, a, b))
    return out


def _fixes():
    sys.path.insert(0, os.path.join(HERE, 'ingest'))
    import importlib
    import pkgutil
    rows = []
    archive = os.path.join(HERE, 'ingest', 'fixes_archive')
    if os.path.isdir(archive):
        for fn in sorted(os.listdir(archive)):
            if fn.endswith('.json'):
                store = json.load(open(os.path.join(archive, fn), encoding='utf-8'))
                for b in store['files'].values():
                    rows.extend(b['fixes'])
    folder = os.path.join(HERE, 'ingest', 'fixes')
    for m in sorted(x.name for x in pkgutil.iter_modules([folder])):
        rows.extend(getattr(importlib.import_module('fixes.%s' % m), 'FIXES', []) or [])
    return rows


def _backed_by_fixes(fixes):
    out = set()
    for f in fixes:
        if isinstance(f, dict) and str(f.get('quote') or '').strip() and 'new' in f:
            out.add((f.get('id'), f.get('field'), _norm(f['new'])))
    return out


def _backed_by_log(card, field, new):
    for row in card.get('fact_log') or []:
        if row.get('field') == field and str(row.get('quote') or '').strip() \
                and _norm(row.get('new')) == _norm(new):
            return True
    return False


def unbacked(old_data, new_data, fixes=None):
    changes = fact_changes(old_data, new_data)
    if not changes:
        return []
    keys = _backed_by_fixes(_fixes() if fixes is None else fixes)
    cards = {d['id']: d for d in new_data.get('deals') or []}
    return [c for c in changes
            if (c[0], c[1], _norm(c[3])) not in keys and not _backed_by_log(cards[c[0]], c[1], c[3])]


def log(card, field, new, quote, url, by, date=None):
    """Подтвердить правку факта словами источника (для разовых скриптов и enrich.py)."""
    import datetime
    card.setdefault('fact_log', []).append({
        'field': field, 'new': new, 'quote': quote, 'url': url, 'by': by,
        'date': date or datetime.date.today().isoformat()})


def problem(old_data, new_data, fixes=None):
    bad = unbacked(old_data, new_data, fixes)
    if not bad:
        return None
    lines = ['%s %s: %r → %r' % (cid, f, str(a)[:60], str(b)[:60]) for cid, f, a, b in bad[:10]]
    return ('правка факта без цитаты источника у %d полей — запишите правку через таблицу правок '
            '(review.py) или подтвердите fact_edit_guard.log(card, поле, значение, цитата, адрес, кто):\n  %s'
            % (len(bad), '\n  '.join(lines)))


def check(old_data, new_data):
    p = problem(old_data, new_data)
    if p:
        raise SystemExit('ОТКАЗ (факт без цитаты): ' + p)


def _self_check():
    old = {'deals': [{'id': 'a', 'title': 'Холдинг VK купил четверть «Р7»', 'sum': '2 500 млн ₽',
                      'eco': {'sum': '2 500 млн ₽'}, 'seller': None}]}
    form = {'deals': [{'id': 'a', 'title': 'Холдинг VK купил четверть «Р7»', 'sum': '2,5 млрд ₽',
                       'eco': {'sum': '2,5 млрд ₽'}, 'seller': None}]}
    assert unbacked(old, form, []) == []
    fact = {'deals': [{'id': 'a', 'title': 'VK купил 25% «Р7»', 'sum': '2,5 млрд ₽',
                       'eco': {'sum': '2,5 млрд ₽'}, 'seller': 'СУЭК'}]}
    bad = unbacked(old, fact, [])
    assert {b[1] for b in bad} == {'title', 'seller'}, bad
    fixes = [{'id': 'a', 'field': 'title', 'new': 'VK купил 25% «Р7»', 'quote': 'приобрела 24,996% акций'}]
    log(fact['deals'][0], 'seller', 'СУЭК', 'СУЭК продала', 'https://x', 'test')
    assert unbacked(old, fact, fixes) == []
    assert not same_meaning('sum', '2,5 млрд ₽', '2,5 млрд ₽ (по оценке)')
    new_card = {'deals': fact['deals'] + [{'id': 'b', 'title': 'новая'}]}
    assert all(c[0] != 'b' for c in fact_changes(old, new_card))


def main(argv):
    _self_check()
    base = argv[argv.index('--base') + 1] if '--base' in argv else 'HEAD'
    old = json.loads(subprocess.run(['git', 'show', '%s:static/data/deals_promoted.json' % base],
                                    capture_output=True, text=True, cwd=ROOT, check=True).stdout)
    new = json.load(open(DATA, encoding='utf-8'))
    ch = fact_changes(old, new)
    print('Изменено полей-фактов против %s: %d' % (base, len(ch)))
    p = problem(old, new)
    if p:
        print('ОТКАЗ: ' + p)
        return 1
    print('Можно: у каждой правки факта есть цитата.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
