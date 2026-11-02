# -*- coding: utf-8 -*-
"""Вычитка базы, партия «g» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_g.py.

- gc38bcf53 («Кубаньагроторг»/«Замок на Затоне»): дата карточки 2026-10-25 —
  день публикации 93.ru, а не событие. Событие — решение краевого суда,
  отменившее выкуп 2021 года: «В мае 2026 года крайсуд вынес новое решение»
  (93.ru, 25.10.2026, сохранено save_source.py). Дня статья не называет,
  поэтому по правилу «Нет дня — только год» (docs/card_status_dates.md,
  «Дата: какое событие и в каком виде») в `date` остается год. `review.py`
  дату-год не принимает (date_is_supported требует ГГГГ-ММ-ДД), отсюда скрипт.
  Этапов (`events[]`) у карточки нет — синхронизировать нечего.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_g.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}

    c = deals['gc38bcf53']
    set_val(c, 'date', '2026-10-25', '2026')
    assert not c.get('events'), c.get('events')

    print('gc38bcf53: date 2026-10-25 → 2026 (решение краевого суда в мае 2026 года, день не назван)')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
