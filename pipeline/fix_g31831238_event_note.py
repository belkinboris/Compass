# -*- coding: utf-8 -*-
"""g31831238 (Intel/Classiq): events[0].note повторял 25 слов подряд из
источника (и строил предложение по его скелету) — приемка нашла near_copy.
Переписано своими словами по уже проверенным фактам карточки.

Запуск: python3 pipeline/fix_g31831238_event_note.py [--write]
"""
import json
import sys

PATH = 'static/data/pending.json'
OLD = ('Intel договорилась о покупке израильского разработчика квантового ПО Classiq '
       'примерно за $2,3 млрд. Что известно о сроках сделки, истории стартапа и '
       'квантовой стратегии компании.')
NEW = ('Intel и Classiq подписали соглашение о сделке 26 октября 2026 года. Классик '
       'делает программную платформу для квантовых компьютеров — покупка должна дать '
       'Intel собственный программный слой в дополнение к ее кремниевым квантовым чипам.')


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'g31831238')
    assert card['events'][0]['note'] == OLD, card['events'][0]['note']
    if not write:
        print('сухой прогон: events[0].note -> %r' % NEW)
        return
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'g31831238')
    assert card['events'][0]['note'] == OLD, card['events'][0]['note']
    card['events'][0]['note'] = NEW
    json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано: events[0].note обновлен')


if __name__ == '__main__':
    main('--write' in sys.argv)
