# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026, карточка gb7ea4703: заголовок в прошедшем
времени («купила») не соответствовал статусу «Обсуждается» (сделка
официально не подтверждена) — переписан в настоящем времени, как у
источника (НГС: «Лента» покупает сеть «Мария-Ра»). Покупатель привязан к
существующему профилю «Группа Лента». Прямая правка (профиль-линк — не
факт из источника, дословная цитата не нужна; заголовок — из источника).

Запуск: python3 pipeline/fix_lenta_maria_ra_card_2026_09_23.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gb7ea4703'
BUYER_PROFILE = 'gcca31da7'


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['title'] == '«Лента» купила сеть «Мария-Ра»'
    card['title'] = '«Лента» покупает сеть «Мария-Ра»'
    assert card.get('buyer') is None
    card['buyer'] = BUYER_PROFILE
    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: заголовок переписан в настоящем времени, покупатель -> %s.' % BUYER_PROFILE)
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
