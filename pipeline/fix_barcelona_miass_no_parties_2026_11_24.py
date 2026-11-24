# -*- coding: utf-8 -*-
"""Карточка g0e0bbb2c (спортбаза «Барселона», Миасс): accept_card.py требует
`no_parties` — стороны не названы (анонимное объявление на «Авито»,
пересказанное URA.RU). Тот же класс и та же формулировка, что уже приняты
сегодня у g6e759772 («Пятый элемент», Тюмень) и g221460e5 (база у
«Масловского», Воронеж): "Продавец и покупатель не раскрыты: объявление о
продаже (<источник>) не называет стороны."

Запуск:
    python3 pipeline/fix_barcelona_miass_no_parties_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_barcelona_miass_no_parties_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
CARD_ID = 'g0e0bbb2c'
NO_PARTIES = ('Продавец и покупатель не раскрыты: объявление о продаже '
              '(«Авито», пересказано URA.RU) не называет стороны.')


def find(cards):
    for c in cards:
        if c['id'] == CARD_ID:
            return c
    raise SystemExit('карточка %s не найдена в pending.json' % CARD_ID)


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = find(pending['cards'])
    assert not card.get('no_parties'), 'no_parties уже стоит: %r' % card.get('no_parties')
    print('Карточка: %s — %s' % (card['id'], card['title']))
    print('Текущий no_parties: %r' % card.get('no_parties'))
    print('Новый no_parties:   %r' % NO_PARTIES)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))
    card = find(pending['cards'])
    assert not card.get('no_parties'), 'no_parties уже стоит (гонка записи): %r' % card.get('no_parties')
    card['no_parties'] = NO_PARTIES
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: no_parties добавлен карточке %s' % CARD_ID)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
