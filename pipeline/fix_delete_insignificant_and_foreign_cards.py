# -*- coding: utf-8 -*-
"""Удаляет две карточки по прямому решению владельца (заметки в консоли,
4 сентября 2026):

- g6b737511 (Александр Салаев продаёт торговые центры в Рыбацком и
  Гатчине) — заметка 475: «Удаляем карту. Несущественная сделка».
- g4d7ccec0 (JPMorgan Chase приобрёл First Republic Bank) — заметка 483:
  «Удаляем карту»; известная проблема (CLAUDE.md) подтвердила прямым
  чтением, что сюжет целиком американский, без российского элемента.

Обе карточки не участвуют ни в одной записи `merged` (ни как ключ, ни как
значение) — проверено перед удалением, редиректов ломать не придётся.
Записи FIXES, ссылавшиеся на эти id (`pipeline/ingest/fixes/batch_c_2023.py`,
`pipeline/ingest/fixes/batch_agents100_r8.py`), уже сняты отдельными
правками до этого скрипта.

Запуск: python3 pipeline/fix_delete_insignificant_and_foreign_cards.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DELETE_IDS = {'g6b737511', 'g4d7ccec0'}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    ids_present = {c['id'] for c in data['deals']}
    missing = DELETE_IDS - ids_present
    assert not missing, f'карточек уже нет в базе: {missing}'

    merged = data.get('merged', {})
    for did in DELETE_IDS:
        assert did not in merged, f'{did} — ключ в merged, нельзя удалять так'
        assert did not in merged.values(), f'{did} — значение в merged, нельзя удалять так'

    before = len(data['deals'])
    data['deals'] = [c for c in data['deals'] if c['id'] not in DELETE_IDS]
    after = len(data['deals'])
    assert before - after == len(DELETE_IDS), (before, after)

    print(f'Удаляю {len(DELETE_IDS)} карточки: {sorted(DELETE_IDS)}')
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
