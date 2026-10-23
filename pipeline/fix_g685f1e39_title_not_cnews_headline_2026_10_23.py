# -*- coding: utf-8 -*-
"""Заголовок карточки «1С»/«Райтек» (g685f1e39) дословно повторял заголовок
статьи CNews («„1С“ и „Райтек“ создают совместное предприятие для развития
цифровых технологий управления производством») без кавычек и атрибуции —
находка второго чтения (SECOND_READING_BRIEF.md), 23 октября 2026. Новый
заголовок собран из слов самой карточки (`asset`: «совместное предприятие
«1С» и «Райтек» для автоматизации промышленных предприятий»), а не из
формулировки издания.

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static/data/deals_promoted.json')

DEAL_ID = 'g685f1e39'
OLD = '«1С» и «Райтек» создают совместное предприятие для развития цифровых технологий управления производством'
NEW = '«1С» и «Райтек» запускают совместное предприятие по автоматизации промышленных предприятий'


def apply(data):
    n = 0
    for d in data['deals']:
        if d['id'] == DEAL_ID:
            if d.get('title') == NEW:
                continue
            assert d.get('title') == OLD, (d['id'], d.get('title'))
            d['title'] = NEW
            n += 1
            print('%s: %s' % (d['id'], NEW))
    return n


def main(write):
    apply(json.load(open(DATA, encoding='utf-8')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    if apply(data):
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
