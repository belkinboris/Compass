# -*- coding: utf-8 -*-
"""Приток 17 ноября 2026: этап в очереди (pending.json) у gcdfb645f («Логика молока» / ООО «Роял Кейк»).

Что было: черновик по заголовку ТАСС («покупает») завел этап «Переговоры» с заметкой — подзаголовком новости.
Пресс-релиз покупателя от 17 ноября 2026 года говорит о завершенной сделке («Компания завершила сделку по
приобретению ООО «Роял Кейк»»), статус карточки уже «Закрыта» (review.py) — этап спорил со статусом.
Что стало: тот же этап (не удаляется: дедуп enrich.py по виду и адресу) стал «Сделка завершена», заметка
своими словами, к источнику ТАСС добавлен пресс-релиз.

Запуск: python3 pipeline/archive/2026-11/fix_event_gcdfb645f_2026_11_17.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD = 'gcdfb645f'
TASS = ['ТАСС', 'https://tass.ru/ekonomika/28325583']
RELEASE = ['«Логика молока»',
           'https://logikamoloka.ru/press-centr/news/logika-moloka-pokupaet-brend-proteinovykh-produktov-protein-rex']
NOTE = ('«Логика молока» объявила, что купила ООО «Роял Кейк», которое выпускает протеиновые десерты и снеки '
        'под брендом Protein Rex; цену покупатель не назвал.')


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))           # перечитано прямо перед записью
    card = next(c for c in data['cards'] if c['id'] == CARD)
    assert card['status'] == 'Закрыта', card['status']
    assert len(card['events']) == 1, card['events']
    ev = card['events'][0]
    if ev['kind'] == 'closed' and ev.get('note') == NOTE:
        print('уже применено')
        return
    assert ev['kind'] == 'negotiations' and ev['date'] == '2026-11-17' and ev['source'] == TASS, ev
    print(CARD, ev['kind'], '->', 'closed', '|', ev['note'][:50], '->', NOTE[:50])
    ev.update({'kind': 'closed', 'title': 'Сделка завершена', 'note': NOTE, 'sources': [TASS, RELEASE]})
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('записано')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
