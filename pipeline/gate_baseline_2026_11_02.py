# -*- coding: utf-8 -*-
"""Точка отсчета для правила «правка опубликованной карточки — снова на проверку».

ЧТО. Карточкам базы без единого отпечатка проверки (`readiness.CHECKED_HASHES`)
ставит `gate_baseline_hash` — отпечаток текста на 2 ноября 2026. С этого дня
любая правка такой карточки (`readiness.changed_after_check`) ставит ее
первой в очередь вычитки (pipeline/reread_queue.py).

ПОЧЕМУ ТОЧКА ОТСЧЕТА, А НЕ СРАЗУ ОЧЕРЕДЬ. Без отпечатка нельзя сказать,
менялся ли текст после проверки: у 1344 карточек проверки не было вовсе.
Их все и так проходит вычитка по порядку, с первой; точка отсчета нужна, чтобы
отличить правку, сделанную ПОСЛЕ сегодняшнего дня. Карточки, у которых
отпечаток уже есть и разошелся (принятые, а потом правленые), не трогаем —
они честно стоят в очереди первыми.

    python3 pipeline/gate_baseline_2026_11_02.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'ingest'))
import readiness  # noqa: E402

DATA = os.path.join(os.path.dirname(HERE), 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data.get('companies') or {}
    n = 0
    for d in data['deals']:
        if any(d.get(k) for k in readiness.CHECKED_HASHES):
            continue
        assert 'gate_baseline_hash' not in d
        d['gate_baseline_hash'] = readiness.fingerprint(d, comps)
        n += 1
    print('точка отсчета: %d карточек' % n)
    if write and n:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    elif n:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
