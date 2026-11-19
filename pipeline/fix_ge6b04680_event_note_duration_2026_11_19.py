# -*- coding: utf-8 -*-
"""«Бургер Кинг»/«Вилла-элит» (ge6b04680), 19 ноября 2026: второе чтение нашло
домысел в `events[0].note` — слово «давно» (сколько «Бургер Кинг» снимает
помещение, Коммерсантъ не пишет). Элемент списка `review.py` не адресует
(card_editing_scripts.md), поэтому правка — одноразовым скриптом с `assert`
на старое значение; синхронная запись FIXES —
pipeline/ingest/fixes/ge6b04680_rationale_no_motive_2026_11_19.py (там же
правило: kompas-style п.1, «в тексте только то, что есть в источнике»).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью,
на случай параллельной сессии).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'ge6b04680'
OLD = ('17 ноября 2026 года ООО «Бургер Рус» (управляет сетью «Бургер Кинг» в России) стало '
       'единственным владельцем ООО «Вилла-элит». Эта компания, по данным сервиса Asseto, — '
       'собственник 4 тыс. кв. м в здании «Улей» на Медовом переулке, где давно снимает '
       'помещение «Бургер Кинг».')
NEW = ('17 ноября 2026 года ООО «Бургер Рус» (управляет сетью «Бургер Кинг» в России) стало '
       'единственным владельцем ООО «Вилла-элит». Эта компания, по данным сервиса Asseto, — '
       'собственник 4 тыс. кв. м в здании «Улей» на Медовом переулке, где снимает помещение '
       '«Бургер Кинг».')


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CID)
    assert card['events'][0]['note'] == OLD, card['events'][0]['note']
    card['events'][0]['note'] = NEW


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    print('%s: events[0].note переписана (снято "давно")' % CID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv))
