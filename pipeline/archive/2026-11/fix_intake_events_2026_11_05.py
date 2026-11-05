# -*- coding: utf-8 -*-
"""Приток 5 ноября 2026: заметки и даты этапов в очереди (pending.json) у gcc6ff548 и gf26f4994.

Что было: заметка этапа «Сделка завершена» — обрубок текста статьи с многоточием
(приемка: truncated, verbatim, near_copy), дата этапа — день публикации.
Что стало: заметка своими словами, дата — день события (31 октября — запись в ЕГРЮЛ;
16 октября — договор купли-продажи). Этап не удаляется (дедуп enrich.py).

Запуск: python3 pipeline/archive/2026-11/fix_intake_events_2026_11_05.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

EDITS = {
    'gcc6ff548': ('2026-11-05', '2026-10-31',
                  'Головная компания RBE Group, ООО РБЕ, получила 100% в ООО «Сильвер Салмон», '
                  'которое организует любительскую рыбалку на Камчатке; переход долей отражен в ЕГРЮЛ.'),
    'gf26f4994': ('2026-11-05', '2026-10-16',
                  'Конкурсный управляющий продал имущество «Садов Бештау» на повторных торгах: '
                  'договор с ООО «Простор» подписан, цена — 246,93 млн ₽.'),
}


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))           # перечитано прямо перед записью
    for card in data['cards']:
        if card['id'] not in EDITS:
            continue
        old_date, new_date, note = EDITS[card['id']]
        ev = card['events'][0]
        assert ev['kind'] == 'closed' and ev['date'] in (old_date, new_date), ev
        print(card['id'], ev['date'], '->', new_date, '|', ev['note'][:50], '->', note[:50])
        ev['date'], ev['note'] = new_date, note
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('записано')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
