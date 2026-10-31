# -*- coding: utf-8 -*-
"""Карточка gbe13372d (ГМК «Дальполиметалл»): `events[0].note` пришел от
`promote.py`/`draft.py` почти дословной копией заголовка Mergers.ru,
обрезанной многоточием на середине фразы — находка приемки (`near_copy`,
`truncated`). Источник сделки пересмотрен на Коммерсантъ (первичный,
mergers.ru сам пишет «Об этом пишет «Коммерсант»»); дата итогов торгов по
Коммерсанту — 14, а не 15 октября. Текст события переписан своими словами.

Запуск:
    python3 pipeline/fix_gbe13372d_event_note_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_gbe13372d_event_note_2026_10_15.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'gbe13372d'
OLD_NOTE = ('АО «Русская промышленная компания» (РПК) признано победителем торгов по продаже '
            '67% акций ГМК «Дальполиметалл», производителя цинкового и свинцового концентратов '
            'с содержанием серебра в Приморском крае. РПК стала единственным участником торгов, '
            'предложив…')
NEW_NOTE = ('Итоги торгов объявлены 14 октября: единственную заявку на 67% акций «Дальполиметалла» '
            'подала «Русская промышленная компания».')
OLD_DATE = '2026-10-15'
NEW_DATE = '2026-10-14'
NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9026346']


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    ev = card['events'][0]
    assert ev['note'] == OLD_NOTE, 'note уже не тот, что ожидался: %r' % ev['note']
    assert ev['date'] == OLD_DATE, 'date уже не та, что ожидалась: %r' % ev['date']
    print('note: %s\n-> %s' % (OLD_NOTE, NEW_NOTE))
    print('date: %s -> %s' % (OLD_DATE, NEW_DATE))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    fresh_ev = fresh_card['events'][0]
    assert fresh_ev['note'] == OLD_NOTE, 'note поменяли параллельно — перечитайте'
    fresh_ev['note'] = NEW_NOTE
    fresh_ev['date'] = NEW_DATE
    fresh_ev['source'] = NEW_SRC
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
