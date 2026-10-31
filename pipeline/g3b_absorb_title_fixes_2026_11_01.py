# -*- coding: utf-8 -*-
"""G3, вторая партия: у части карточек заголовок уже правился записью
таблицы (живые `fixes/*.py` или архив `fixes_archive/*.json`), а партия
`fixes/written_titles_g3b_2026_11_01.py` правит его еще раз. По правилу
docs/card_editing.md («новая правка поля — новой записью в живом файле,
отпечаток прежнего `new` — в `proofread_absorbed` карточки») прежние записи
надо учесть отпечатком, иначе после записи партии `already_applied()`
сочтет их непримененными: падает `test_no_duplicate_fix_for_one_field` и
`test_review_table_is_applied_and_not_pending`, а следующий
`review.py --write` откажет целиком. Образец — `g3_absorb_title_fixes_2026_11_01.py`.

Запуск — ПЕРЕД `review.py --write`:

    python3 pipeline/g3b_absorb_title_fixes_2026_11_01.py            # сухой прогон
    python3 pipeline/g3b_absorb_title_fixes_2026_11_01.py --write    # запись

Базу перечитывает прямо перед записью (CLAUDE.md: старый снимок стирает чужой пуш).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
G3B_MARK = 'G3b: единый стиль заголовков'


def plan():
    """{id: [отпечатки прежних записей title]} — только у карточек партии G3b."""
    mine = {f['id'] for f in review.FIXES if f['field'] == 'title' and G3B_MARK in str(f.get('why', ''))}
    out = {}
    for f in review.FIXES:
        if f['field'] == 'title' and f['id'] in mine and G3B_MARK not in str(f.get('why', '')) \
                and isinstance(f.get('new'), str):
            out.setdefault(f['id'], []).append(review.fix_fingerprint(f['new']))
    return out


def main():
    write = '--write' in sys.argv
    todo = plan()
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    changed = 0
    for cid, prints in sorted(todo.items()):
        card = cards.get(cid)
        if not card:
            print('%s: карточки нет в базе — пропуск' % cid)
            continue
        marks = card.setdefault('proofread_absorbed', {}).setdefault('title', [])
        new = [p for p in prints if p not in marks]
        print('%s: %d прежних записей title, добавить отпечатков: %d' % (cid, len(prints), len(new)))
        if new:
            marks.extend(new)
            changed += 1
    if not write:
        print('Сухой прогон: %d карточек изменилось бы. Запись — с ключом --write.' % changed)
        return
    if changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано: %d карточек.' % changed)


if __name__ == '__main__':
    main()
