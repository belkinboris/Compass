# -*- coding: utf-8 -*-
"""Разовая миграция: память о сырье по заголовку, а не только по draft_id.

ЧТО СЛОМАНО. draft_id меняется у одной и той же новости от прогона к
прогону: Рижский вокзал пришёл тремя id за два дня, и партнёр трижды жал
«не сделка»; «издание Гоголя» и Atomic dohaeris показались в консоли
повторно на следующий день. Память по id помнит прогон, а не новость.

ЧТО ДЕЛАЕТ. Проходит все hold-файлы, находит черновики, чьи draft_id уже
есть в sent_raw/decided_raw, и записывает их нормализованные заголовки в
state['raw_titles'] с тем же вердиктом ('sent' для просто показанных).
Дальше send_drafts/approve ведут эту память сами.

Запуск:
    python3 pipeline/ingest/backfill_raw_titles.py            # сухой прогон
    python3 pipeline/ingest/backfill_raw_titles.py --write    # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import promote  # noqa: E402

HOLD = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'data', 'inbox', 'hold')


def main(write=False):
    state = promote.load_state()
    decided = state.get('decided_raw', {})
    sent = set(state.get('sent_raw', []))
    titles = dict(state.get('raw_titles', {}))
    added = 0
    for name in sorted(os.listdir(HOLD)) if os.path.isdir(HOLD) else []:
        if not name.endswith('.json'):
            continue
        for d in json.load(open(os.path.join(HOLD, name), encoding='utf-8')).get('drafts', []):
            did = str(d.get('draft_id'))
            verdict = decided.get(did) or ('sent' if did in sent else None)
            if not verdict:
                continue
            key = promote.raw_key(d.get('title'))
            if key and titles.get(key) != verdict:
                # drop/take сильнее простого 'sent': решение не затирается показом.
                if titles.get(key) in ('drop', 'take') and verdict == 'sent':
                    continue
                titles[key] = verdict
                added += 1
                print('  %-5s %s' % (verdict, str(d.get('title'))[:80]))
    print('Записей в памяти заголовков: %d (добавлено/обновлено %d).' % (len(titles), added))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    state['raw_titles'] = titles
    promote.save_state(state)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
