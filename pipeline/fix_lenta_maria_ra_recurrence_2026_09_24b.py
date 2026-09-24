# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (09:20 МСК), карточка gb7ea4703 («Лента»/
«Мария-Ра»): та же статья «Делового Петербурга» повторно всплыла в RSS
и enrich.py СНОВА механически переключил статус на «Закрыта» — второй
раз подряд за сутки, тем же самым источником. Разбор и доп. поиск уже
сделаны часом ранее (fix_lenta_maria_ra_premature_close_2026_09_24.py,
KNOWN_ISSUES.md) — независимого подтверждения по-прежнему нет. На этот
раз enrich.py тронул только title/status/event (eco/law/extra остались
такими, как после прошлой правки) — откатываются только они.

СИСТЕМНАЯ ПРИЧИНА (записана в KNOWN_ISSUES.md, чинить — работа рутины
«качество», не этой): enrich.py не помнит уже обработанные новости, и
пока эта статья остаётся в пуле RSS, правка будет повторяться каждый час.

Запуск: python3 pipeline/fix_lenta_maria_ra_recurrence_2026_09_24b.py --write
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

    events = card['events']
    assert events[0]['kind'] == 'closed' and events[0]['note'] == ''
    del events[0]

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if os.path.exists(UPDATES):
            json.dump({'made': '2026-09-24', 'updates': []},
                      open(UPDATES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: статус и заголовок откачены второй раз, событие closed снято.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
