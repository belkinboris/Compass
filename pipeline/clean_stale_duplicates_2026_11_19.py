# -*- coding: utf-8 -*-
"""Очередь дублей за 19 ноября 2026 несла 9 устаревших записей из 10:

- `ge6b04680`/`g1a2f9d60` — решены этим же днем (resolved.json: verdict
  `enrich`/`separate`), но `resolve_duplicates.py --queue` не вычищает
  запись из `items` файла дня после `--apply`, поэтому остались висеть.
- `pending-1`×4, `ga91c5821`×2, `g2a07c829`×1 — черновики о продаже картины
  Ван Гога на Sotheby's и о клиентах ВТБ, продавших инвестмонеты (розничная
  статистика, не сделка): кандидат на дубль у каждой записи либо выброшенный
  id (`ga91c5821`, `g2a07c829` — drop_pending.py этим же прогоном), либо
  плейсхолдер `pending-1`. Сами черновики не станут карточкой в любом случае
  — тот же вердикт («не сделка»), что уже вынесен сиблингам по той же
  новости.

Остается ровно одна настоящая запись — `gf5bdb983` (Дом.РФ/Дмитров), ее эта
правка не трогает: решает `resolve_duplicates.py --queue`.

Без ключа — сухой прогон; запись — `--write` (файл перечитывается перед
записью на случай параллельной сессии).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'data', 'inbox', 'duplicates', '2026-11-19.json')

DROP_CANDIDATES = {'pending-1', 'ga91c5821', 'g2a07c829', 'ge6b04680', 'g1a2f9d60', 'g8695856c'}


def apply(data):
    before = len(data['items'])
    kept = [it for it in data['items'] if it['candidate_id'] not in DROP_CANDIDATES]
    removed = before - len(kept)
    data['items'] = kept
    return before, len(kept), removed


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    before, after, removed = apply(data)
    print('было записей: %d, осталось: %d, убрано: %d' % (before, after, removed))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PATH, encoding='utf-8'))
    apply(data)
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
