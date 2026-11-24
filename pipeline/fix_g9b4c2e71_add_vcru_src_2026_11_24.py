# -*- coding: utf-8 -*-
"""g9b4c2e71 («Т-Технологии»/«Циан»): добавляет VC.ru как еще один источник той
же оферты (24.11.2026) — тот же факт (цена 993,05 руб., выкуп до 100%), что уже
записан со слов Абирега и Коммерсанта; новых фактов в статье нет.

Источник: VC.ru, https://vc.ru/money/3266049-t-tehnologii-predlozhili-tsianu-pokupit-aktsii?from=rss

Запуск:
    python3 pipeline/fix_g9b4c2e71_add_vcru_src_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9b4c2e71_add_vcru_src_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g9b4c2e71'
SRC = ['VC.ru', 'https://vc.ru/money/3266049-t-tehnologii-predlozhili-tsianu-pokupit-aktsii?from=rss']


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    src = card.setdefault('src', [])
    assert not any(s[1] == SRC[1] for s in src), 'источник уже есть'
    src.append(SRC)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('источник добавлен: %s' % SRC[1])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
