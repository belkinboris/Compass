# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (11:20 МСК), карточка gb7ea4703 («Лента»/
«Мария-Ра»): ЧЕТВЁРТЫЙ раз за сутки enrich.py переключил статус на
«Закрыта» — снова по тому же кэшированному dp.ru (повторное совпадение,
у enrich.py нет памяти уже разобранных новостей, см. KNOWN_ISSUES.md) и
снова по Mergers.ru (тот же агрегированный пересказ «Банкфакс», уже
прочитан и признан НЕ независимым подтверждением дважды сегодня). Ни
одного НОВОГО источника с 18 сентября так и не появилось. Оба события
kind=closed сняты, статус и заголовок возвращены к «Обсуждается»/
настоящему времени.

Запуск: python3 pipeline/fix_lenta_maria_ra_recurrence_2026_09_24d.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
UPDATES = os.path.join(ROOT, 'data', 'inbox', 'updates', '2026-09-24.json')

CARD_ID = 'gb7ea4703'
OLD_TITLE = '«Лента» купила крупнейшую сибирскую торговую сеть «Мария-Ра»'
NEW_TITLE = '«Лента» покупает сеть «Мария-Ра»'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert card['title'] == OLD_TITLE
    card['title'] = NEW_TITLE

    assert card['status'] == 'Закрыта'
    card['status'] = 'Обсуждается'

    closed = [e for e in card['events'] if e['kind'] == 'closed']
    assert len(closed) == 2
    card['events'] = [e for e in card['events'] if e['kind'] != 'closed']

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if os.path.exists(UPDATES):
            json.dump({'made': '2026-09-24', 'updates': []},
                      open(UPDATES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: статус и заголовок откачены четвёртый раз, оба события closed сняты.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
