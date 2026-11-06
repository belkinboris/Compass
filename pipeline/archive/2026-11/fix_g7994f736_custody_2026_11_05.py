# -*- coding: utf-8 -*-
"""g7994f736 (JTI, временное управление, указ № 817 от 5 ноября 2026): служебные поля временного
управления в очереди (pending.json): kind=custody и причина пустых сторон — review.py и ответ приемки
их не пишут. Тот же вид, что у g2fd3ab54 («Главпродукт»).

Запуск: python3 pipeline/archive/2026-11/fix_g7994f736_custody_2026_11_05.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
NO_PARTIES = 'Временное управление по указу, собственность не переходила — покупателя и продавца нет.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))           # перечитано прямо перед записью
    card = [c for c in data['cards'] if c['id'] == 'g7994f736'][0]
    assert card['type'] == 'Временное управление', card['type']
    card['kind'] = 'custody'
    card['no_parties'] = NO_PARTIES
    card['date_basis'] = 'announcement'
    print('g7994f736: kind=custody, no_parties, date_basis=announcement')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
