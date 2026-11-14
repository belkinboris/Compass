"""Доля `stake_acquired` текстом → числом в очереди и базе (14 ноября 2026).

Три карточки очереди (g0d873779, ge42606a4, g63fca144) несли долю строкой;
тест базы остановил публикацию одобренных карточек. Без ключа — сухой прогон.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import deal_multiples  # noqa: E402


def main(write):
    for name, key in (('pending.json', 'cards'), ('deals_promoted.json', 'deals')):
        path = os.path.join(ROOT, 'static', 'data', name)
        data = json.load(open(path, encoding='utf-8'))      # читается прямо перед записью
        changed = 0
        for card in data.get(key) or []:
            value = card.get('stake_acquired')
            if isinstance(value, str):
                card['stake_acquired'] = deal_multiples.stake_number(value)
                assert isinstance(card['stake_acquired'], (int, float)), (card['id'], value)
                print(name, card['id'], repr(value), '→', card['stake_acquired'])
                changed += 1
        if write and changed:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.' if write else 'Сухой прогон.')


if __name__ == '__main__':
    main('--write' in sys.argv)
