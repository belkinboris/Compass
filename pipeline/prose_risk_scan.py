# -*- coding: utf-8 -*-
"""Очередь карточек, чей текст надо перечитать против статьи, — по порядку риска.

ЗАЧЕМ. С 14 по 26 октября 2026 текст 1169 карточек (76% базы) был переписан
«по тому, что у нас написано», без статей (`prose_gate.known_texts`): ошибка,
стоявшая в карточке, возвращалась в нее с цитатой, подтвержденной ею самой
(ВТБ/«Деметра», 1 ноября 2026). Перечитывать все — бессмысленно и дорого;
этот скрипт отбирает тех, у кого есть механический след дефекта, и ставит
вперед то, что видно читателю: карточки с постом в канале.

Признаки (каждый грубый, вместе — порядок чтения, а не приговор):
  * `hedge_lost` — в цитатах правок поля есть осторожность («ожидается»,
    «будет», «по неофициальным данным»), а в нынешнем тексте нет ни ее, ни
    указания, чье это утверждение: прогноз мог стать фактом;
  * `stale_statement` — намерение в настоящем времени или допэмиссия «этапом»
    продажи при статусе «Закрыта» (`accept_card.STALE_STATEMENT_RE`);
  * `rewritten` — поле переписано пересказом 14–26 октября (сводка, не повод).
Карточки, прошедшие второе чтение с 1 ноября 2026 (новые вопросы «язык» и
«время»), в очередь не попадают: очередь сама сжимается по мере чтения.

    python3 pipeline/prose_risk_scan.py                # сводка и первые 30
    python3 pipeline/prose_risk_scan.py --top 100
    python3 pipeline/prose_risk_scan.py --ids          # только id, для --queue
Порядок чтения (Opus): `docs/card_editing.md`, «Пересказ — по статье».
"""
import glob
import json
import os
import runpy
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE, os.path.join(HERE, 'ingest')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import prose_gate  # noqa: E402
import accept_card  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
RE_READ_SINCE = '2026-11-01'
SKIP_FIELDS = ('title', 'eco.sum', 'sum')


def _get(card, field):
    if '.' not in field:
        return card.get(field)
    a, b = field.split('.', 1)
    return (card.get(a) or {}).get(b) if isinstance(card.get(a), dict) else None


def fix_history():
    """{(id, поле): [правки]} из JSON-архива партий и живых файлов fixes/."""
    hist = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(HERE, 'ingest', 'fixes_archive', '*.json'))):
        for batch in json.load(open(p, encoding='utf-8'))['files'].values():
            for f in batch['fixes']:
                hist[(f['id'], f['field'])].append(f)
    for p in sorted(glob.glob(os.path.join(HERE, 'ingest', 'fixes', '*.py'))):
        try:
            for f in runpy.run_path(p).get('FIXES', []):
                hist[(f['id'], f['field'])].append(f)
        except Exception:
            continue
    return hist


def scan(base=None):
    base = base or json.load(open(DATA, encoding='utf-8'))
    by = {d['id']: d for d in base['deals']}
    posts = base.get('telegram_posts') or {}
    risks = defaultdict(lambda: {'hedge_lost': [], 'stale_statement': [], 'rewritten': 0})
    for (cid, field), fixes in fix_history().items():
        card = by.get(cid)
        if not card or field in SKIP_FIELDS:
            continue
        if any('WRITING_BRIEF' in str(f.get('why', '')) for f in fixes):
            risks[cid]['rewritten'] += 1
        final = _get(card, field)
        if isinstance(final, str) and len(final) >= 20:
            lost = prose_gate.hedge_lost([f.get('quote') for f in fixes], final)
            if lost:
                risks[cid]['hedge_lost'].append((field, lost))
    for cid, card in by.items():
        for field in accept_card.STALE_STATEMENT_FIELDS:
            v = _get(card, field)
            if not isinstance(v, str):
                continue
            if card.get('status') in ('Закрыта', 'Не состоялась') and accept_card.STALE_STATEMENT_RE.search(v):
                risks[cid]['stale_statement'].append(field)
            elif card.get('type') in accept_card.CASH_IN_STAGE_TYPES and accept_card.CASH_IN_STAGE_RE.search(v):
                risks[cid]['stale_statement'].append(field)
    out = []
    for cid, r in risks.items():
        card = by[cid]
        if not (r['hedge_lost'] or r['stale_statement']):
            continue
        if str(card.get('second_read') or '') >= RE_READ_SINCE:
            continue
        score = 100 * bool(posts.get(cid)) + 40 * len(r['stale_statement']) + 10 * len(r['hedge_lost']) \
            + 5 * (card.get('status') == 'Закрыта')
        out.append({'id': cid, 'score': score, 'post': posts.get(cid), 'status': card.get('status'),
                    'title': card.get('title'), **r})
    return sorted(out, key=lambda x: (-x['score'], x['id']))


def main(argv):
    top = int(argv[argv.index('--top') + 1]) if '--top' in argv else 30
    queue = scan()
    if '--ids' in argv:
        print(' '.join(q['id'] for q in queue))
        return 0
    first = [q for q in queue if q['post'] or q['stale_statement'] or len(q['hedge_lost']) >= 3]
    print('К перечитыванию против статьи: %d карточек (с постом в канале %d, со следом устаревшего намерения %d).'
          % (len(queue), sum(1 for q in queue if q['post']), sum(1 for q in queue if q['stale_statement'])))
    print('Сначала (пост в канале, устаревшее намерение или потеря осторожности в трех и более полях): %d; '
          'остальные — по 30–50 в день, у большинства след в одном поле и он слабый.' % len(first))
    for q in queue[:top]:
        print('%-10s %4d  %-9s пост=%-5s %s | потеряна осторожность: %s | устарело: %s'
              % (q['id'], q['score'], q['status'], q['post'] or '—', str(q['title'])[:60],
                 ', '.join(f for f, _ in q['hedge_lost']) or '—', ', '.join(q['stale_statement']) or '—'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
