# -*- coding: utf-8 -*-
"""Добивка к fix_research_night_questions_2026_11_03.py (3 ноября 2026).

- g796316fe «Делимобиль»: покупатель теперь профиль ООО «Делимобиль Холдинг», поэтому имя
  текстом «Винченцо Трани» снимается (test_buyer_is_named_once: у покупателя одно имя);
  Трани назван в тексте карточки и в описании профиля холдинга как конечный владелец.
- g10f783e8 Moscow Towers: слияние дописало в extra предложения дубля, запись FIXES этого
  поля получает отпечаток в proofread_absorbed (docs/card_editing.md).

    python3 pipeline/archive/2026-11/fix_research_night_questions_2026_11_03_b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    D = {d['id']: d for d in data['deals']}
    dm = D['g796316fe']
    assert dm['buyer'] and dm.get('buyer_name') in ('Винченцо Трани', None)
    dm['buyer_name'] = None
    bm = dm.setdefault('proofread_absorbed', {}).setdefault('buyer_name', [])
    fp = review.fix_fingerprint('Винченцо Трани')
    if fp not in bm:
        bm.append(fp)
    t = D['g10f783e8']
    marks = t.setdefault('proofread_absorbed', {}).setdefault('extra', [])
    n = 0
    for f in review.FIXES:
        if f['id'] == 'g10f783e8' and f['field'] == 'extra' and f.get('new'):
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp); n += 1
    print('buyer_name снят; отпечатков extra: %d' % n)
    if not write:
        print('Сухой прогон.'); return
    assert open(DATA, encoding='utf-8').read() == raw
    open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
