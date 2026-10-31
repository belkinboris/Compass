# -*- coding: utf-8 -*-
"""«Лента»/«Мария-Ра» (gb7ea4703): запомнить снятый статус «Закрыта».

24 сентября 2026 карточка трижды за утро получала «Закрыта» по заголовку
«„Лента“ купила…» — та же статья каждый час возвращалась в ленту, а три
отката (fix_lenta_maria_ra_premature_close_2026_09_24.py, …_24b, …_24c) не
оставляли памяти о том, что статус сняли. Независимого подтверждения нет:
покупатель «не комментирует рыночные слухи». Запись в `retracted` —
механизм `enrich.is_retracted`: та же догадка теперь уходит на решение
чтением, а не возвращается в базу молча.

    python3 pipeline/fix_lenta_maria_ra_retract_closed_2026_09_24.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == 'gb7ea4703')
    assert deal['status'] == 'Обсуждается', deal['status']
    assert 'Мария-Ра' in deal['title'], deal['title']
    retracted = deal.setdefault('retracted', {})
    values = retracted.setdefault('status', [])
    if 'Закрыта' in values:
        print('Уже записано.')
        return
    values.append('Закрыта')
    print('gb7ea4703: retracted.status = %s' % values)
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
