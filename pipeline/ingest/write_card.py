# -*- coding: utf-8 -*-
"""Текст карточки — по фактам, своими словами (порядок — `WRITING_BRIEF.md`).

Три шага, по ключу на шаг:

    # 1. что увидит пишущий: нумерованные факты БЕЗ цитат
    python3 pipeline/ingest/write_card.py --facts evidence.json

    # 2. проверка написанного (сухо): правки собираются и идут через
    #    те же проверки, что и любая правка review.py
    python3 pipeline/ingest/write_card.py --check <id> evidence.json written.json

    # 3. запись: партия в fixes/ и review.py --write
    python3 pipeline/ingest/write_card.py --check <id> evidence.json written.json --write

`evidence.json` — список `{"field", "fact", "quote", "source", "url"}` от
собирающего (READING_BRIEF.md). `written.json` — ответ пишущего:
`{"<поле>": {"text": "...", "facts": [номера]}}`.

ЗАЧЕМ ОТДЕЛЬНЫЙ ШАГ. До 14 октября 2026 читающий и собирал, и писал — и
переносил прозу из статьи в поле целиком, потому что review.py требовал
дословности от всех полей. Пишущий, который видит только факты, не может
списать построение чужого предложения: самой статьи у него нет. Цитаты
остаются доказательством: каждая правка несёт цитаты своих фактов, review.py
сверяет их с сырьём и проверяет, что текст не повторяет их (`prose_problems`).
"""
import argparse
import json
import os
import pprint
import re
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import review  # noqa: E402

FIXES_DIR = os.path.join(HERE, 'fixes')
# Заголовок пишется по правилам docs/card_parties.md и правится обычной
# правкой title — здесь он только печатается как предложение.
WRITTEN_FIELDS = tuple(sorted(review.PROSE_WRITTEN))
EMPTY = ('', '—', None)


def load_evidence(path):
    ev = json.load(open(path, encoding='utf-8'))
    if not isinstance(ev, list) or not all(isinstance(e, dict) and e.get('fact') for e in ev):
        raise SystemExit('%s: ожидался список {"field","fact","quote","source","url"}' % path)
    return ev


def facts_text(evidence):
    """То, что получает пишущий: факты по номерам, без цитат и без изданий."""
    lines = []
    for i, e in enumerate(evidence, 1):
        hint = (' [поле: %s]' % e['field']) if e.get('field') else ''
        lines.append('%d. %s%s' % (i, e['fact'].strip(), hint))
    return '\n'.join(lines)


def build_fixes(deal_id, card, evidence, written):
    """Правки review.py из ответа пишущего; второе — замечания, не правки."""
    fixes, notes = [], []
    for field, item in written.items():
        if field == 'title':
            text = (item or {}).get('text', '').strip()
            if text and text != card.get('title'):
                notes.append('заголовок (правится отдельно, docs/card_parties.md): %s' % text)
            continue
        if field not in review.PROSE_WRITTEN:
            notes.append('поле %s не текстовое — переносится через review.py с цитатой' % field)
            continue
        text = str((item or {}).get('text', '')).strip()
        idx = (item or {}).get('facts') or []
        old = review.get_field(card, field)
        if text in EMPTY:
            if old not in EMPTY:
                notes.append('%s: пишущий оставил пусто, в карточке есть текст — не стираю' % field)
            continue
        if text == old:
            continue
        bad_idx = [n for n in idx if not (isinstance(n, int) and 1 <= n <= len(evidence))]
        if bad_idx or not idx:
            notes.append('%s: нет фактов-опор или неверные номера %s — поле пропущено' % (field, bad_idx))
            continue
        quotes = []
        for n in idx:
            q = (evidence[n - 1].get('quote') or '').strip()
            if q and q not in quotes:
                quotes.append(q)
        if not quotes:
            notes.append('%s: у фактов %s нет цитат — поле пропущено' % (field, idx))
            continue
        fixes.append(dict(id=deal_id, field=field, old=old, new=text,
                          quote=' … '.join(quotes),
                          why='текст написан по фактам %s (WRITING_BRIEF.md)'
                              % ', '.join(map(str, idx))))
    return fixes, notes


def find_card(deal_id):
    data = json.load(open(review.DATA, encoding='utf-8'))
    for d in data['deals']:
        if d['id'] == deal_id:
            return d, data
    if os.path.exists(review.PENDING):
        for c in json.load(open(review.PENDING, encoding='utf-8')).get('cards', []):
            if c['id'] == deal_id:
                return c, data
    raise SystemExit('карточки %s нет ни в базе, ни в очереди' % deal_id)


def check_fixes(fixes, card, data):
    texts, inds, urls = review.source_texts(), review.industries(), review.source_urls()
    found = {}
    for fix in fixes:
        bad = review.check(fix, card, texts, data['companies'], inds, urls)
        if bad:
            found[fix['field']] = bad
    return found, bool(texts)


def save_batch(deal_id, fixes):
    name = 'written_%s_%s.py' % (deal_id, date.today().strftime('%Y_%m_%d'))
    path = os.path.join(FIXES_DIR, name)
    n = 2
    while os.path.exists(path):
        path = os.path.join(FIXES_DIR, name[:-3] + '_%d.py' % n)
        n += 1
    body = ('# -*- coding: utf-8 -*-\n'
            '"""Текст карточки %s, написанный по фактам (write_card.py, WRITING_BRIEF.md).\n\n'
            'Запуск: python3 pipeline/ingest/review.py --write\n"""\n\n'
            'FIXES = %s\n' % (deal_id, pprint.pformat(fixes, width=100, sort_dicts=False)))
    open(path, 'w', encoding='utf-8').write(body)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--facts', metavar='EVIDENCE')
    ap.add_argument('--check', nargs=3, metavar=('ID', 'EVIDENCE', 'WRITTEN'))
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    if a.facts:
        print(facts_text(load_evidence(a.facts)))
        return 0
    if not a.check:
        ap.error('нужен --facts или --check')
    deal_id, ev_path, wr_path = a.check
    evidence = load_evidence(ev_path)
    written = json.load(open(wr_path, encoding='utf-8'))
    card, data = find_card(deal_id)
    fixes, notes = build_fixes(deal_id, card, evidence, written)
    found, have_texts = check_fixes(fixes, card, data)
    for f in fixes:
        mark = 'ОТКАЗ' if f['field'] in found else 'ок'
        print('[%s] %s: %s' % (mark, f['field'], f['new']))
        for b in found.get(f['field'], ()):
            print('       - %s' % b)
    for n in notes:
        print('  замечание: %s' % n)
    if not have_texts:
        print('ВНИМАНИЕ: сырья на диске нет — цитаты не сверены с текстом статей.')
    if found:
        print('\nЕсть находки — отдайте пишущему перечень выше и проверьте заново.')
        return 1
    if not fixes:
        print('Править нечего.')
        return 0
    if not a.write:
        print('\nСухой прогон: %d правок. Запись — с ключом --write.' % len(fixes))
        return 0
    path = save_batch(deal_id, fixes)
    print('партия: %s' % os.path.relpath(path, ROOT))
    return subprocess.run([sys.executable, os.path.join(HERE, 'review.py'), '--write'],
                          cwd=ROOT).returncode


if __name__ == '__main__':
    sys.exit(main())
