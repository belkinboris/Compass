# -*- coding: utf-8 -*-
"""Свести все сделки в один источник правды — `deals_promoted.json`.

ЗАЧЕМ. На 3 августа 2026 данные о сделках лежали в ПЯТИ местах: три
захардкоженных массива в `static/index.html` (`DEALS` — 19, `MINI_DEALS` — 21,
`CHANNEL_DEALS` — 14), `bulk_deals.json` (107) и сама `deals_promoted.json`
(1350). Плюс три файла-копии, которые не читает никто: `curated_deals.json`,
`curated_companies.json`, `deals_2026.json` (380 КБ).

ЧЕМ ЭТО СТОИЛО. Приток строит индекс только по `deals_promoted.json` и был
структурно слеп к 54 сделкам интерфейса: новость о любой из них считалась
новой и завела бы дубль. Нашлось не проверкой кода — владелец вбил две
сделки, которые точно помнит (Яндекс/«Заряд!» и «Стокманн»/Hugo Boss), и обе
оказались на сайте, хотя разбор архива объявил их отсутствующими.

РЕШЕНИЕ ВЛАДЕЛЬЦА. Кратких записей больше нет: всё — карточки. Если фактов
мало, карточка показывает отдельный блок о том, чего не хватает
(`sparseNoticeHtml`), а не превращается в строку-ссылку наружу. Поэтому 142
компактные записи переводятся в карточки, а не остаются вторым видом.

ЧТО ПЕРЕНОСИТСЯ И ВО ЧТО.
  * 19 кураторских карточек — как есть, форма уже совпадает.
  * 36 кураторских профилей компаний — в `companies`.
  * mini (21): `firm` + `role` — это КОНСУЛЬТАНТ, он идёт в `law.adv`,
    а не теряется. Именно ради него запись когда-то и заводили.
  * channel (14): `note` — в `extra`, `channel` — в подпись источника.
  * bulk (107): `role` — в `extra`.
Ничего не выдумывается: чего в записи нет (сумма, стороны, статус), того
в карточке не появляется — пустое поле честнее заглушки.

ДУБЛИ. Компактная запись, уже описанная полной карточкой, не переносится:
это тот же отсев, который делал `loadBulkDeals()` в браузере, перенесённый
сюда. Иначе слияние породило бы ровно те дубли, от которых мы уходим.

Запуск:
    python3 pipeline/merge_into_one_base.py            # сухой прогон
    python3 pipeline/merge_into_one_base.py --write    # записать
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import draft  # noqa: E402
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CURATED = os.path.join(ROOT, 'static', 'data', 'curated_deals.json')
CURATED_CO = os.path.join(ROOT, 'static', 'data', 'curated_companies.json')
BULK = os.path.join(ROOT, 'static', 'data', 'bulk_deals.json')

INDUSTRIES_OK = None  # заполняется из base при запуске

DSTOP = {
    'ооо', 'пао', 'компания', 'компании', 'группа', 'группой', 'доля', 'долей', 'акций',
    'сделка', 'бизнес', 'приобрел', 'приобрела', 'купил', 'купила', 'может', 'купить',
    'россии', 'покупает', 'инвестирует', 'структурн', 'инвестиционн', 'совместн',
    'предприят', 'создают', 'создала', 'создаёт', 'организац', 'инвесторов', 'залог',
    'закрыт', 'провел', 'получил', 'заключил', 'заключила', 'консолидировал', 'привлек',
    'привлекла', 'выкупил', 'выкупила', 'стороны', 'участием', 'рамках', 'процентов',
}
DSTOP_STEMS = {w[:6] for w in DSTOP}


def dtoks(text):
    body = re.sub(r'«[^»]{2,40}»', ' ', str(text or '')).lower()
    body = re.sub(r'[«»"\'().,:;–—-]', ' ', body).split()
    return {w[:6] for w in body if len(w) > 4 and w[:6] not in DSTOP_STEMS}


def quoted_names(text):
    return {m.group(1).lower() for m in re.finditer(r'«([^»]{2,40})»', str(text or ''))}


def amount_of(text):
    m = re.search(r'(\d[\d\s.,]*)\s*(млрд|млн)', str(text or ''), re.I)
    if not m:
        return None
    return float(m.group(1).replace(' ', '').replace(',', '.')) * (1000 if m.group(2).lower() == 'млрд' else 1)


def days_between(a, b):
    from datetime import date
    try:
        ya, ma, da = (int(x) for x in str(a)[:10].split('-'))
        yb, mb, db = (int(x) for x in str(b)[:10].split('-'))
        return abs((date(ya, ma, da) - date(yb, mb, db)).days)
    except Exception:
        return 9999


def build_full_index(deals):
    return [{'y': str(d.get('date') or '')[:4], 'date': d.get('date'),
             't': dtoks(d.get('title')), 'q': quoted_names(d.get('title')),
             'a': amount_of(d.get('title'))} for d in deals]


def is_dup(rec, full_idx):
    """Тот же отсев, что делал loadBulkDeals() в браузере: порог 5 общих слов
    при близких датах, либо общее название в кавычках с той же суммой."""
    y = str(rec.get('date') or '')[:4]
    t, q, a = dtoks(rec.get('title')), quoted_names(rec.get('title')), amount_of(rec.get('title'))
    for f in full_idx:
        if f['y'] != y:
            continue
        if days_between(rec.get('date'), f['date']) <= 90 and len(t & f['t']) >= 5:
            return True
        if (q & f['q']) and a is not None and f['a'] is not None \
                and abs(a - f['a']) / max(a, f['a']) < 0.05 \
                and days_between(rec.get('date'), f['date']) <= 45:
            return True
    return False


def make_id(rec):
    """Устойчивый id из заголовка и даты: повторный прогон даёт тот же id, а
    не плодит новые карточки при каждом запуске."""
    raw = '%s|%s' % (str(rec.get('title') or ''), str(rec.get('date') or ''))
    return 'c' + hashlib.sha1(raw.encode('utf-8')).hexdigest()[:8]


def src_list(rec, label_fallback):
    src = rec.get('src')
    if not src:
        return []
    if isinstance(src, list) and src and isinstance(src[0], list):
        return [list(s) for s in src]
    if isinstance(src, list) and len(src) >= 2:
        return [[str(src[0]) or label_fallback, str(src[1])]]
    return []


def to_card(rec, firms_by_id):
    """Компактная запись -> карточка. Только то, что в записи есть."""
    origin = rec.get('origin') or 'bulk'
    card = {
        'id': make_id(rec),
        'date': rec.get('date') or 'unknown',
        'title': rec.get('title'),
        'ind': rec.get('ind'),
        # Тип берём штатным правилом по тексту, а не ставим всем «M&A»:
        # среди этих записей есть и IPO, и инвестиционные раунды, и жёсткая
        # подстановка была бы выдумкой в 100% случаев, где правило не согласно.
        'type': draft.guess_type('%s %s' % (rec.get('title') or '', rec.get('role') or rec.get('note') or '')),
        'src': src_list(rec, 'источник'),
        'from_compact': origin,
    }
    # mini: firm+role — это консультант; ради него запись и заводили.
    if rec.get('firm'):
        firm_name = firms_by_id.get(rec['firm'], rec['firm'])
        card['law'] = {'adv': [['Юридический консультант', firm_name, str(rec.get('role') or '')]]}
    elif rec.get('role'):
        card['extra'] = str(rec['role'])
    if rec.get('note'):
        card['extra'] = ((card.get('extra', '') + ' ') if card.get('extra') else '') + str(rec['note'])
    if rec.get('channel'):
        card.setdefault('src', [])
        if card['src']:
            card['src'][0][0] = card['src'][0][0] or str(rec['channel'])
    return card


def firm_names():
    """Имена фирм по id — они в интерфейсе, но нужны, чтобы не записать в
    карточку технический id вместо названия."""
    text = open(os.path.join(ROOT, 'static', 'index.html'), encoding='utf-8').read()
    return dict(re.findall(r'\{id:"([a-z0-9_-]+)",n:"([^"]+)"', text))


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))
    curated = json.load(open(CURATED, encoding='utf-8'))
    curated_co = json.load(open(CURATED_CO, encoding='utf-8'))
    bulk = json.load(open(BULK, encoding='utf-8'))
    firms_by_id = firm_names()

    full_cards = [c for c in curated if c.get('origin') == 'curated']
    compact = [c for c in curated if c.get('origin') in ('mini', 'channel')] + \
              [dict(b, origin='bulk') for b in bulk]

    assert len(full_cards) == 19, 'кураторских карточек не 19, а %d' % len(full_cards)
    assert len(compact) == 142, 'компактных записей не 142, а %d' % len(compact)

    existing_ids = {d['id'] for d in base['deals']}
    clash = existing_ids & {c['id'] for c in full_cards}
    assert not clash, 'id кураторских карточек уже заняты: %s' % clash

    # Отсев дублей — против ПОЛНОЙ будущей базы (1350 + 19 кураторских).
    full_idx = build_full_index(base['deals'] + full_cards)
    kept, dropped = [], []
    for rec in compact:
        (dropped if is_dup(rec, full_idx) else kept).append(rec)

    new_cards = [to_card(r, firms_by_id) for r in kept]
    # Повторный прогон не должен плодить карточки: id детерминирован.
    seen, uniq = set(), []
    for c in new_cards:
        if c['id'] in existing_ids or c['id'] in seen:
            continue
        seen.add(c['id'])
        uniq.append(c)

    new_companies = {k: v for k, v in curated_co.items() if k not in base['companies']}

    print('кураторских карточек к переносу:      %d' % len(full_cards))
    print('профилей компаний к переносу:         %d (из %d, остальные уже есть)'
          % (len(new_companies), len(curated_co)))
    print('компактных записей всего:             %d' % len(compact))
    print('  отсеяно как дубли полных карточек:  %d' % len(dropped))
    print('  становятся карточками:              %d' % len(uniq))
    print('ИТОГО карточек в базе станет:          %d (было %d)'
          % (len(base['deals']) + len(full_cards) + len(uniq), len(base['deals'])))
    print()
    print('примеры новых карточек из компактных записей:')
    for c in uniq[:4]:
        adv = [a[1] for a in (c.get('law') or {}).get('adv', [])]
        print('  %s | %s | %s' % (c['date'], (c['title'] or '')[:64], ('консультант: ' + adv[0]) if adv else ''))
    print()
    no_src = [c for c in uniq if not any(str(s[1]).startswith('http') for s in c['src'] if len(s) > 1)]
    no_ind = [c for c in uniq if not c.get('ind')]
    print('ПРОВЕРКА ИНВАРИАНТОВ до записи:')
    print('  без http-ссылки на источник: %d (тест требует 0)' % len(no_src))
    print('  без отрасли:                 %d (тест требует 0)' % len(no_ind))
    for c in no_src[:3]:
        print('     !', c['date'], (c['title'] or '')[:60], c['src'])

    if write:
        assert not no_src and not no_ind, 'инварианты не выполнены — запись отменена'
        base['deals'].extend(full_cards)
        base['deals'].extend(uniq)
        base['companies'].update(new_companies)
        json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    else:
        print('\nСухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
