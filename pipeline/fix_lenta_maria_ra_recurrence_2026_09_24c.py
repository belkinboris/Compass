# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (10:20 МСК), карточка gb7ea4703 («Лента»/
«Мария-Ра»): ТРЕТИЙ раз за сутки enrich.py переключил статус на
«Закрыта» — на этот раз сразу по двум совпадениям (dp.ru повторно и
новый источник Mergers.ru). Mergers.ru прочитан полностью: это агрегатор,
дословно пересказывающий тот же нарратив «Банкфакс» («консультант...
подтвердил... что сделка состоялась», «в пресс-службе "Ленты" заявили,
что "не комментируют рыночные слухи"») — НЕ независимое подтверждение,
та же цепочка анонимных источников, что уже разобрана дважды сегодня
(KNOWN_ISSUES.md). Mergers.ru как источник добавлен в карточку (не вредит,
отдельная публикация), но статус/заголовок/оба события kind=closed
откачены снова.

Запуск: python3 pipeline/fix_lenta_maria_ra_recurrence_2026_09_24c.py --write
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
        print('Записано: статус и заголовок откачены третий раз, оба события closed сняты.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
