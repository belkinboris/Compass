"""Убрать из текста карточек пересказ изданий, признанных в РФ нежелательными (4 ноября 2026, D6).

Ссылки уже сняты (remove_undesirable_sources_2026_11_04.py); здесь — три карточки,
где издание названо в тексте.
    python3 pipeline/archive/2026-11/remove_undesirable_mentions_2026_11_04.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CUT = ('The Insider (СМИ, признанное в РФ иностранным агентом и нежелательной организацией), ссылаясь на '
       'внутреннюю финансовую документацию фонда, утверждает, что его единственный вкладчик — Аркадий '
       'Ротенберг; это совпадает с неофициальной версией 2024 года о совсем другой компании, но подтверждено '
       'единственным источником и остается неустановленным. ')
EDITS = [
    ('g5d1be523', 'context', CUT, ''),
    ('g64462179', 'context', 'The Insider нашел компанию на сайте регистратора в разделе «Готовые акционерные общества»',
     'на сайте регистратора компания значится в разделе «Готовые акционерные общества»'),
    ('g2daf32fe', 'context', 'The Insider нашел его на сайте регистратора среди «готовых акционерных обществ».',
     'На сайте регистратора он значится среди «готовых акционерных обществ».'),
]


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for cid, field, old, new in EDITS:
        text = by_id[cid]['eco'][field]
        assert text.count(old) == 1, (cid, 'старый текст не найден')
        by_id[cid]['eco'][field] = text.replace(old, new)
        print(cid, 'ok')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
