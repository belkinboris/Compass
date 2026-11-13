# -*- coding: utf-8 -*-
"""Стороны карточки по реестру ФНС: правовая форма и история участников.

ЗАЧЕМ. Владелец, 2 ноября 2026, о первых десяти вычитанных карточках:
- «в схеме тремя разными способами написаны стороны» (ПАО «Совкомбанк»,
  «Союз» (Евгений Гинер), Капитал Медицинское Страхование), «ПармаВуд ООО,
  Лузалес ООО, а Сыктывкарский ЛПК без ОПФ — нужно единообразно»;
- «как мы можем не найти продавца, если таргет — ООО?» — и правда: наш же
  сайт отдает историю участников ООО из ЕГРЮЛ (кто вышел, кто вошел, доли
  до и после). У «Директ Стар» она показала, что «Аэрофлот» вошел через
  увеличение уставного капитала, а не купил долю у владелицы.

ЧТО ДЕЛАЕТ. Для сторон карточки (buyer, seller_id, target, asset_id) берет
`/api/companies/<id>/fns` боевого сайта и:
- предлагает `legal_short` профиля — «ООО «ПармаВуд»»: правовая форма из
  реестра, имя — как в профиле, если совпадает с реестровым без учета
  регистра, иначе реестровое (сайт показывает `legal_short` в схеме сделки и
  в «Отчетности сторон»);
- печатает историю участников ООО — читающий берет из нее продавца, долю и
  дату регистрации перехода.

    python3 pipeline/party_legal_names.py <id карточки> [...]          # показать
    python3 pipeline/party_legal_names.py <id карточки> [...] --write  # записать legal_short
    python3 pipeline/party_legal_names.py --fix-quotes [--write]        # починить кавычки в записанных

Физлица, иностранцы, профили без сопоставленного ИНН — пропускаются с причиной.
"""
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SITE = 'https://projectcompass.ru/api/companies/%s/fns'
FORMS = ('ПАО', 'НАО', 'ОАО', 'ЗАО', 'АО', 'ООО', 'МКПАО', 'МКАО', 'ГУП', 'МУП', 'ФГУП')
ROLES = ('buyer', 'seller_id', 'target', 'asset_id')


def fetch(cid):
    # Сервер реестра из контейнера часто рвет соединение (12–13 ноября 2026: пять партий
    # вычитки получили отказ party_legal_form, потому что форма молча не встала) — три попытки.
    import time
    for attempt in range(3):
        try:
            return _fetch_once(cid)
        except Exception:  # noqa: BLE001
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def _fetch_once(cid):
    with urllib.request.urlopen(SITE % cid, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def _norm(s):
    return re.sub(r'[^\wа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def _case(name, profile=''):
    """Реестр пишет ПРОПИСНЫМИ. Слово, которое есть в имени профиля, берется в
    его написании; иначе короткое (до трех букв) или без гласных — аббревиатура
    (УК, ЦФУ, СЛПК), прочие — с заглавной. Кавычки и дефисы слову не мешают:
    `"РУСАГРО` — слово «Русагро», а не «"русагро» (13 ноября 2026)."""
    seen = {w.lower(): w for w in re.findall(r'\w+', str(profile or ''))}
    def one(m):
        w = m.group(0)
        if w.lower() in seen:
            return seen[w.lower()]
        if len(w) <= 3 or not re.search(r'[АЕИОУЫЭЮЯAEIOU]', w, re.I) or not w.isupper():
            return w
        return w[:1] + w[1:].lower()
    return re.sub(r'\w+', one, ' '.join(str(name).split()))


QUOTES = '"«»“”„'


def _guillemets(text):
    """Кавычки реестра (прямые, вложенные, без закрывающих) — в «елочки» с парными
    закрывающими: `"КОНЦЕРН "ДЕТСКОСЕЛЬСКИЙ"` → «КОНЦЕРН «ДЕТСКОСЕЛЬСКИЙ»». Имя без
    кавычек (выписка: `ГРУППА СИНАРА`) и имя, где кавычки не обнимают его целиком
    (`ТД "ЛЕНТА"`), берутся в «…» снаружи."""
    out, depth = [], 0
    t = ' '.join(str(text).split())
    for i, ch in enumerate(t):
        if ch not in QUOTES:
            out.append(ch)
            continue
        nxt = t[i + 1] if i + 1 < len(t) else ''
        prev = t[i - 1] if i else ''
        if ch in '«„':
            opening = True
        elif ch in '»”':
            opening = False
        else:                       # прямая кавычка: перед словом — открывает, после — закрывает
            opening = nxt.isalnum() and not prev.isalnum()
        if opening:
            out.append('«')
            depth += 1
        elif depth:
            out.append('»')
            depth -= 1
    body = ''.join(out).strip() + '»' * depth
    # обнимает ли первая открывающая все имя
    if body.startswith('«'):
        d = 0
        for i, ch in enumerate(body):
            d += (ch == '«') - (ch == '»')
            if d == 0:
                break
        if i == len(body) - 1:
            return body
    return '«%s»' % body


def legal_short(profile_name, short_name):
    """«ООО «ПармаВуд»» из реестрового `ООО "ПАРМАВУД"` и имени профиля."""
    m = re.match(r'\s*(%s)\s+(\S.*?)\s*$' % '|'.join(FORMS), str(short_name or ''))
    if not m:
        return None
    form, rest = m.group(1), m.group(2)
    if not re.search(r'\w', rest):
        return None
    reg = _guillemets(rest)
    bare = re.sub(r'^(%s)\s+' % '|'.join(FORMS), '', str(profile_name or '')).strip()
    if _norm(bare) == _norm(reg) and reg.count('«') == 1 and not any(q in bare.strip(QUOTES) for q in QUOTES):
        return '%s «%s»' % (form, bare.strip(QUOTES))
    name = re.sub(r'«([a-zа-яё])', lambda m: '«' + m.group(1).upper(), _case(reg, bare))
    return '%s %s' % (form, name)


def broken_quotes(text):
    t = str(text or '')
    return t.count('«') != t.count('»') or '"' in t


def fix_quotes(write=False):
    """Починить уже записанные legal_short с потерянной закрывающей или прямой кавычкой
    (старый разбор вложенных кавычек, до 13 ноября 2026) — без обращения к реестру."""
    data = json.load(open(DATA, encoding='utf-8'))
    todo = {}
    for cid, c in data['companies'].items():
        ls = c.get('legal_short')
        if ls and broken_quotes(ls):
            new = legal_short(c.get('name'), ls)
            if new and '««' not in new and not broken_quotes(new):
                todo[cid] = (ls, new)
                print('  %s: %s → %s' % (cid, ls, new))
    if write and todo:
        fresh = json.load(open(DATA, encoding='utf-8'))
        for cid, (old, new) in todo.items():
            assert fresh['companies'][cid].get('legal_short') == old, cid
            fresh['companies'][cid]['legal_short'] = new
        json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано legal_short: %d' % len(todo))
    elif todo:
        print('Сухой прогон: %d. Запись — --write.' % len(todo))
    return todo


def owners_text(entity):
    own = entity.get('ownership') or {}
    lines = []
    for o in own.get('current') or []:
        lines.append('    сейчас: %s — %s%%' % (o.get('name'), o.get('share_percent')))
    for h in own.get('history') or []:
        o = h.get('owner') or {}
        lines.append('    %s %s: %s (%s → %s)' % (h.get('date'), h.get('kind'), o.get('name'),
                                                  h.get('before_share'), h.get('after_share')))
    return lines


def main(argv):
    write = '--write' in argv
    if '--fix-quotes' in argv:
        fix_quotes(write)
        return
    ids = [a for a in argv if not a.startswith('--')]
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    proposals = {}
    for did in ids:
        d = deals.get(did)
        if not d:
            print('%s: карточки нет в базе' % did)
            continue
        print('=== %s  %s' % (did, d.get('title')))
        for role in ROLES:
            cid = d.get(role)
            if not cid or cid not in comps:
                continue
            c = comps[cid]
            try:
                info = fetch(cid)
            except Exception as e:  # сайт недоступен — читающий решает сам
                print('  %s %s: реестр недоступен (%s)' % (role, c.get('name'), e))
                continue
            if not info.get('available'):
                print('  %s %s: %s' % (role, c.get('name'), info.get('reason') or 'нет в реестре'))
                continue
            ents = info.get('entities') or []
            ent = ents[0]['entity'] if ents else {}
            ls = legal_short(c.get('name'), ent.get('short_name'))
            print('  %s %s → %s  (реестр: %s, ИНН %s)' % (role, c.get('name'), ls or '—', ent.get('short_name'),
                                                       ent.get('inn')))
            if ents:
                for line in owners_text(ents[0]):
                    print(line)
            if ls and len(ents) == 1 and c.get('legal_short') != ls:
                proposals[cid] = ls
    if write and proposals:
        fresh = json.load(open(DATA, encoding='utf-8'))
        for cid, ls in proposals.items():
            fresh['companies'][cid]['legal_short'] = ls
        json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано legal_short: %d' % len(proposals))
    elif proposals:
        print('Сухой прогон: legal_short для %d профилей. Запись — --write.' % len(proposals))


def _self_check():
    assert legal_short('ООО ПармаВуд', 'ООО "ПАРМАВУД"') == 'ООО «ПармаВуд»'
    assert legal_short('Сыктывкарский ЛПК', 'АО "СЛПК"') == 'АО «СЛПК»'
    assert legal_short('Директ Стар', 'ООО "УК ДИРЕКТ СТАР"') == 'ООО «УК Директ Стар»'
    assert legal_short('ПАО «Совкомбанк»', 'ПАО "СОВКОМБАНК"') == 'ПАО «Совкомбанк»'
    assert legal_short('x', 'ИП Иванов') is None
    # вложенные кавычки, регистр, выписка без кавычек (вычитка, 13 ноября 2026)
    assert legal_short('Концерн «Детскосельский»', 'ООО "КОНЦЕРН "ДЕТСКОСЕЛЬСКИЙ"') == 'ООО «Концерн «Детскосельский»»'
    assert legal_short('Концерн Детскосельский', 'ООО "КОНЦЕРН "ДЕТСКОСЕЛЬСКИЙ""') == 'ООО «Концерн «Детскосельский»»'
    assert legal_short('Русагро', 'ПАО "ГРУППА "РУСАГРО"') == 'ПАО «Группа «Русагро»»'
    assert legal_short('Группа Астра', 'ПАО "ГРУППА АСТРА"') == 'ПАО «Группа Астра»'
    assert legal_short('Базис', 'ПАО "ГК "БАЗИС"') == 'ПАО «ГК «Базис»»'
    assert legal_short('Синара', 'АО ГРУППА СИНАРА') == 'АО «Группа Синара»'
    assert legal_short('x', 'ООО «ГК "гранель»') == 'ООО «ГК «Гранель»»'
    assert legal_short('УК Директ Стар', 'ООО «УК «ДИРЕКТ СТАР»') == 'ООО «УК «Директ Стар»»'


_self_check()

if __name__ == '__main__':
    main(sys.argv[1:])
