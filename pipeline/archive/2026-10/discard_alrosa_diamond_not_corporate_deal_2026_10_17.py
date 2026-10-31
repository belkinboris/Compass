# -*- coding: utf-8 -*-
"""Ворота пропустили не-сделку: «АЛРОСА продаст лавандовый бриллиант
стоимостью $1,5 млн по инвестпрограмме» (`d78357115`, Коммерсантъ) —
заголовок попал в шаблон «продаст» с подлежащим-компанией, но это продажа
ОДНОГО камня через инвестиционную программу АЛРОСА (частным инвесторам,
без названного покупателя), не корпоративная M&A-сделка: нет ни стороны-
покупателя, ни контрольного пакета, ни актива уровня компании. Та же
история уже отклонена сегодня утром (другой источник, ТАСС,
`raw_screen.py --drop`), и второй черновик о том же камне (RBC, не прошел
ворота сам) просто повторяет ее.

Замечено до записи — отмечаю оба заголовка в raw_titles, чтобы не выпало
снова завтра, когда АЛРОСА или кто-то еще перескажет эту же продажу.

Запуск:
    python3 pipeline/discard_alrosa_diamond_not_corporate_deal_2026_10_17.py            # сухой прогон
    python3 pipeline/discard_alrosa_diamond_not_corporate_deal_2026_10_17.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

ITEMS = [
    ('https://www.kommersant.ru/doc/9041051',
     'АЛРОСА продаст лавандовый бриллиант стоимостью $1,5 млн по инвестпрограмме'),
    ('https://www.rbc.ru/rbcfreenews/6ad332c739894adbe493dac5',
     'АЛРОСА продаст лавандовый бриллиант в форме сердца по инвестпрограмме'),
]
REASON = ('не сделка для этой базы: продажа одного бриллианта через инвестпрограмму АЛРОСА — '
          'не корпоративная M&A сделка, нет стороны-покупателя и контрольного пакета')


def main(write=False):
    state = json.load(open(STATE, encoding='utf-8'))
    for url, title in ITEMS:
        assert url not in state.get('discarded_urls', {}), 'URL уже отмечен: %s' % url
        print('ОТКЛОНЯЮ до записи: %s' % title)
        print('  discarded_urls += %s' % url)
        print('  raw_titles += %s -> drop' % promote.raw_key(title))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_state = json.load(open(STATE, encoding='utf-8'))
    for url, title in ITEMS:
        assert url not in fresh_state.get('discarded_urls', {}), 'URL отметили параллельно — перечитайте'
        fresh_state.setdefault('discarded_urls', {})[url] = {
            'reason': REASON,
            'date': datetime.now(timezone.utc).date().isoformat(),
        }
        fresh_state.setdefault('raw_titles', {})[promote.raw_key(title)] = 'drop'
    json.dump(fresh_state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
