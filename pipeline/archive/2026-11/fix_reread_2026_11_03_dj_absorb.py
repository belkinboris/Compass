# -*- coding: utf-8 -*-
"""Партия dj: отпечатки цепочек FIXES — запускать ПОСЛЕ review.py --write.

ПОЧЕМУ НЕ ТОЛЬКО absorb_fix_chain.py. На этих полях запись партии dj стоит в СЕРЕДИНЕ
цепочки: load_fixes() сортирует партии по имени, и более ранние `written_<id>_2026_10_16`,
`written_titles_g3*_2026_11_01` идут ПОСЛЕ `reread_2026_11_03_dj`. absorb_fix_chain кладет
отпечатки всех записей, кроме последней, — а последняя здесь чужая и после записи партии dj
с полем уже не совпадает: test_review_table_is_applied_and_not_pending счел бы ее
непримененной. Поэтому отпечаток кладется для ВСЕХ записей цепочки (все они применены:
партия dj переписала поле поверх них). Текст карточек не меняется.

    python3 <этот файл>            # сухой прогон
    python3 <этот файл> --write
"""
import json
import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = 'static/data/deals_promoted.json'
CHAINS = {
    'g2097cc1f': ['eco.target_fin', 'eco.rationale', 'eco.context', 'law.terms'],
    'gd4e555e3': ['law.struct', 'eco.context'],
    'g17d26389': ['title', 'law.terms', 'eco.rationale', 'eco.target_fin'],
    'g53ebfe72': ['title'],
}
MINE = 'pipeline/ingest/fixes/reread_2026_11_03_dj.py'


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    mine = {}
    exec(compile(open(MINE, encoding='utf-8').read(), MINE, 'exec'), mine)
    mine = {(f['id'], f['field']): f['new'] for f in mine['FIXES']}
    added = 0
    for did, fields in CHAINS.items():
        card = deals[did]
        for field in fields:
            cur = review.get_field(card, field)
            if write:
                assert cur == mine[(did, field)], '%s.%s: партия dj еще не записана (%r)' % (did, field, str(cur)[:60])
            recs = [f for f in review.FIXES if (f['id'], f['field']) == (did, field)]
            assert len(recs) >= 2, (did, field)
            marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            for f in recs:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
                    added += 1
                    print('%s.%s: отпечаток %s (%s)' % (did, field, fp, str(f['new'])[:40]))
    print('добавлено отпечатков: %d' % added)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
