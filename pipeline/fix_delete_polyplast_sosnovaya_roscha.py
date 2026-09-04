# -*- coding: utf-8 -*-
"""Заметка 507 (консоль, 4 сентября 2026): «Карточку просто удалить
надо», отвечая на карточку `gc5eb971c» (ГК «Полипласт» купила крымский
санаторий «Сосновая роща»).

Не в `merged` ни как ключ, ни как значение — проверено перед удалением.
Запись FIXES, ссылавшаяся на этот id (`pipeline/ingest/fixes/
batch_b_2024.py`, поле `eco.target_fin`), снята отдельной правкой до
этого скрипта.

Запуск: python3 pipeline/fix_delete_polyplast_sosnovaya_roscha.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DELETE_ID = 'gc5eb971c'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    ids_present = {c['id'] for c in data['deals']}
    assert DELETE_ID in ids_present

    merged = data.get('merged', {})
    assert DELETE_ID not in merged
    assert DELETE_ID not in merged.values()

    before = len(data['deals'])
    data['deals'] = [c for c in data['deals'] if c['id'] != DELETE_ID]
    after = len(data['deals'])
    assert before - after == 1

    print(f'Удаляю карточку {DELETE_ID}')
    print(f'deals: {before} -> {after}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
