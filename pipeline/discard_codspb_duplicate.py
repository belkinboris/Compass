# -*- coding: utf-8 -*-
"""18 сентября 2026 — выкидываем дубль «ЦОД СПб» из очереди предпросмотра.

Владелец одобрил gf080e8f0 (уже в базе, дообогащена этим же заходом —
см. pipeline/ingest/fixes/batch_codspb_merge_2026_09_18.py и
pipeline/fix_codspb_date_cross_year_merge.py) и велел выкинуть дубль
ge92b1463 из очереди предпросмотра (та же сделка, второй источник,
mergers.ru). Источник и факты дубля не потеряны — они перенесены в
gf080e8f0 до этого шага; сама карточка-дубль в базу так и не попала
(жила только в pending.json), поэтому карты `merged` не требуется —
нечего перенаправлять.

Запуск: python3 pipeline/discard_codspb_duplicate.py [--write]
"""
import json
import sys

PATH = 'static/data/pending.json'
DISCARD_ID = 'ge92b1463'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    cards = data['cards']
    match = [c for c in cards if c['id'] == DISCARD_ID]
    assert len(match) == 1, 'ожидали ровно одну карточку %s в очереди' % DISCARD_ID
    assert match[0]['title'] == 'Сбербанк купил долю в «ЦОД СПб»', \
        'заголовок карточки другой — не тот дубль'

    data['cards'] = [c for c in cards if c['id'] != DISCARD_ID]
    print('Выкинута карточка предпросмотра %s (%s): %d -> %d карточек в очереди'
          % (DISCARD_ID, match[0]['title'], len(cards), len(data['cards'])))

    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=2)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
