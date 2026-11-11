# -*- coding: utf-8 -*-
"""Сверка покупателя и продавца в схеме сделки с ЕГРЮЛ: кто на самом деле вошел в
состав участников купленного общества и кто из него вышел.

ЗАЧЕМ. 11 ноября 2026 владелец открыл «Ренессанс Капитал» / «Онэксим» (g995f83cf):
покупателем в схеме стояли трое топ-менеджеров — так сделку назвал пресс-релиз,
— а в ЕГРЮЛ долю получило АО «РКИП». «Как вообще покупателем стал не настоящий
покупатель? В схеме четко должно быть, кто купил, кто продал, кто таргет».
Чтение статей этого не ловит: статья называет бенефициаров, реестр — сторону
договора. Реестр у нас уже есть (ЕГРЮЛ по API-ФНС на сайте, история участников),
его просто никто не сравнивал со схемой.

ЧТО ДЕЛАЕТ. Для каждой закрытой сделки, у предмета которой подтвержден ИНН
(pipeline/fns_registry.py), берет с сайта историю участников предмета и ищет
записи «вошел» / «вышел» возле даты сделки. Если реестр называет нового
участника, а покупатель в схеме — другое лицо, сделка попадает в находки
`buyer_not_in_registry`; то же с продавцом — `seller_not_in_registry`.
Акционерные общества реестр не раскрывает — они пропускаются. Ответы сайта
кэшируются в data/inbox/party_registry_cache.json (в git не хранится).

Находка — не приговор, а повод открыть карточку: в реестр мог войти холдинг
покупателя (тогда в схеме стоит группа, и это верно — имя группы или ее ИНН
должны совпасть), а мог — как у «Ренессанса» — совсем другой покупатель.
Правило записи сторон — docs/card_parties.md, «Покупатель и продавец — те, кто
в реестре».

    python3 pipeline/party_registry_audit.py                # все закрытые сделки, отчет
    python3 pipeline/party_registry_audit.py --ids g995f83cf
    python3 pipeline/party_registry_audit.py --json out.json
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fns_registry  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CACHE = os.path.join(ROOT, 'data', 'inbox', 'party_registry_cache.json')
SITE = os.environ.get('COMPASS_SITE', 'https://projectcompass.ru')
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/126.0 Safari/537.36')
BEFORE_DAYS, AFTER_DAYS = 90, 270      # статья выходит до записи в реестре, запись — позже закрытия
MIN_SHARE = 5.0                         # технические доли (0,0005%) сторону не определяют
OPF = re.compile(r'\b(ооо|ао|пао|зао|оао|нао|ук|гк|группа|компания|холдинг|общество с ограниченной '
                 r'ответственностью|акционерное общество|публичное акционерное общество|limited|ltd|llc|inc|plc)\b')


def norm(s):
    s = str(s or '').lower().replace('ё', 'е')
    s = re.sub(r'[«»"“”„\'().,]', ' ', s)
    s = OPF.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def deal_window(date):
    """(с, по) — окно поиска записи реестра вокруг даты сделки."""
    d = str(date or '')
    m = re.match(r'^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$', d)
    if not m:
        return None
    y, mo, da = int(m.group(1)), m.group(2), m.group(3)
    if mo and da:
        c = datetime.date(y, int(mo), int(da))
        return c - datetime.timedelta(days=BEFORE_DAYS), c + datetime.timedelta(days=AFTER_DAYS)
    if mo:
        c = datetime.date(y, int(mo), 15)
        return c - datetime.timedelta(days=BEFORE_DAYS + 15), c + datetime.timedelta(days=AFTER_DAYS + 15)
    return datetime.date(y, 1, 1) - datetime.timedelta(days=BEFORE_DAYS), datetime.date(y, 12, 31) + datetime.timedelta(days=AFTER_DAYS)


def party_keys(data, reg, cid, free_text):
    """Имена и ИНН, под которыми сторона схемы может стоять в реестре."""
    names, inns = set(), set()
    c = (data.get('companies') or {}).get(cid) or {}
    for v in (c.get('name'), c.get('legal_short'), c.get('legal_name'), free_text):
        if v:
            names.add(norm(v))
    for k in (data.get('match_keys') or {}).get(cid) or []:
        names.add(norm(k))
    row = reg.get(cid) or {}
    if row.get('inn'):
        inns.add(str(row['inn']))
    # группа: в реестр часто входит дочернее общество — его называет профиль в `group`/`parent`
    for k in ('group', 'parent'):
        g = c.get(k)
        if g and (data.get('companies') or {}).get(g):
            n2, i2 = party_keys(data, reg, g, None)
            names |= n2
            inns |= i2
    return {n for n in names if len(n) >= 3}, inns


def matches(owner, names, inns):
    if owner.get('inn') and str(owner['inn']) in inns:
        return True
    on = norm(owner.get('name'))
    if not on:
        return False
    # физлицо: в реестре «ИВАНОВ ИВАН ИВАНОВИЧ», в схеме «Иван Иванов» — сверяем фамилию и имя
    ot = set(on.split())
    for n in names:
        if n in on or on in n:
            return True
        nt = set(n.split())
        if len(nt) >= 2 and len(nt & ot) >= 2:
            return True
    return False


def fetch(cid, cache, pause):
    if cid in cache:
        return cache[cid]
    req = urllib.request.Request('%s/api/companies/%s/fns' % (SITE, cid), headers={'User-Agent': UA})
    body, err = None, ''
    for attempt in range(4):        # сайт изредка рвет соединение — повтор с паузой
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = json.loads(r.read().decode('utf-8'))
            break
        except Exception as e:  # noqa: BLE001 — сеть: сделка остается непроверенной, прогон идет дальше
            err = str(e)[:120]
            time.sleep(2 + 3 * attempt)
    if body is None:
        return {'error': err}
    ent = (body.get('entities') or [{}])[0]
    own = ent.get('ownership') or {}
    out = {'is_ao': bool(own.get('is_ao')), 'history': own.get('history') or [], 'current': own.get('current') or [],
           'legal': (ent.get('entity') or {}).get('short_name') or (ent.get('entity') or {}).get('legal_name')}
    cache[cid] = out
    time.sleep(pause)
    return out


def audit(data, ids=None, pause=0.35, cache=None, log=None):
    reg = fns_registry.by_company_id()
    cache = {} if cache is None else cache
    out = []
    for d in data.get('deals') or []:
        if ids and d['id'] not in ids:
            continue
        if not str(d.get('status') or '').startswith('Закрыт') or d.get('lot') or d.get('kind') == 'listing':
            continue
        tgt = d.get('target')
        if not tgt or (reg.get(tgt) or {}).get('decision') not in ('confirmed', 'bank'):
            continue
        win = deal_window(d.get('date'))
        if not win:
            continue
        own = fetch(tgt, cache, pause)
        if log:
            log(d['id'])
        if own.get('error'):
            out.append({'id': d['id'], 'kind': 'unchecked', 'why': own['error']})
            continue
        if own.get('is_ao'):
            continue
        ev = []
        for h in own.get('history') or []:
            try:
                hd = datetime.date.fromisoformat(str(h.get('date'))[:10])
            except ValueError:
                continue
            o = h.get('owner') or {}
            share = h.get('after_share') if h.get('kind') == 'joined' else h.get('before_share')
            if win[0] <= hd <= win[1] and (share is None or share >= MIN_SHARE):
                ev.append((h.get('kind'), hd.isoformat(), o, share))
        joined = [e for e in ev if e[0] in ('joined', 'increased')]
        left = [e for e in ev if e[0] in ('left', 'decreased')]
        for side, events, cid, free, kind in (
                ('buyer', joined, d.get('buyer'), d.get('buyer_name'), 'buyer_not_in_registry'),
                ('seller', left, d.get('seller_id'), d.get('seller'), 'seller_not_in_registry')):
            if not events:
                continue
            # Паевой фонд в реестре стоит под именем своей управляющей компании («Д.У. ЗПИФ…») — не расхождение.
            shown = '%s %s' % ((data['companies'].get(cid) or {}).get('name') or '', free or '')
            if re.search(r'зпиф|паев|фонд', shown.lower()) or all('Д.У.' in str(e[2].get('name')) for e in events):
                continue
            names, inns = party_keys(data, reg, cid, free)
            if any(matches(e[2], names, inns) for e in events):
                continue
            out.append({'id': d['id'], 'kind': kind, 'date': d.get('date'), 'title': d.get('title'),
                        'card': (data['companies'].get(cid) or {}).get('name') or free or '—',
                        'registry': ['%s %s%s — %s' % (e[2].get('name'), ('%.4g%% ' % e[3]) if e[3] is not None else '',
                                                        ('(ИНН %s)' % e[2]['inn']) if e[2].get('inn') else '', e[1])
                                     for e in events][:6],
                        'target': (data['companies'].get(tgt) or {}).get('name')})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', nargs='*')
    ap.add_argument('--json')
    ap.add_argument('--pause', type=float, default=0.35)
    a = ap.parse_args()
    data = json.load(open(DATA, encoding='utf-8'))
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding='utf-8'))
        except ValueError:
            cache = {}
    n = [0]
    def tick(_):
        n[0] += 1
        if n[0] % 50 == 0:
            print('  проверено', n[0], file=sys.stderr)
            _save(cache)
    found = audit(data, set(a.ids) if a.ids else None, a.pause, cache, tick)
    _save(cache)
    by = {}
    for f in found:
        by.setdefault(f['kind'], []).append(f)
    print('Сделок проверено: %d. Покупатель не тот, что в реестре: %d; продавец: %d; не проверено (сеть): %d.'
          % (n[0], len(by.get('buyer_not_in_registry', [])), len(by.get('seller_not_in_registry', [])), len(by.get('unchecked', []))))
    for kind in ('buyer_not_in_registry', 'seller_not_in_registry'):
        for f in by.get(kind, []):
            print('\n%s  %s  %s\n   %s\n   в схеме: %s\n   в реестре (%s): %s'
                  % (kind, f['id'], f['date'], f['title'], f['card'], f['target'], '; '.join(f['registry'])))
    if a.json:
        json.dump(found, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 0


def _save(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    sys.exit(main())
