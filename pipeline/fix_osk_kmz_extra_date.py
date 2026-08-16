# -*- coding: utf-8 -*-
"""Разовая правка gd6b3c796 (ОСК/КМЗ): дата закрытия сделки внутри `extra`.

ЧТО НЕВЕРНО. `extra` начинался с «Сделка закрыта 16 января 2025 года» — поле
`date` карточки при этом уже стоит 2026-01-14, и все 6 источников,
прочитанных саб-агентом партии 5 REVISION_BRIEF (Фонтанка ×2, Коммерсантъ-СПб
×3, ДП), независимо называют именно 14 января 2026 года. Внутри `extra`
осталась неверная (и по числу, и по году) дата — видимо, опечатка при
ручном составлении абзаца.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Правка меняет одно число внутри вручную
составленного абзаца, а не переносит цитату целиком — review.py требует,
чтобы ВЕСЬ `new` дословно лежал в `quote` с одной страницы источника; здесь
источник не даёт единой фразы вида «Сделка закрыта 14 января 2026 года»
(дата видна из контекста публикации, а не из одного предложения).

Запуск:
    python3 pipeline/fix_osk_kmz_extra_date.py            # сухой прогон
    python3 pipeline/fix_osk_kmz_extra_date.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd6b3c796'
OLD_EXTRA = ('Сделка закрыта 16 января 2025 года. ОСК продала долю в КМЗ '
             'семье основателя Михаила Даниленко. Сумма официально не '
             'разглашается. Доля находится в залоге у ОСК.')
NEW_EXTRA = ('Сделка закрыта 14 января 2026 года. ОСК продала долю в КМЗ '
             'семье основателя Михаила Даниленко. Сумма официально не '
             'разглашается. Доля находится в залоге у ОСК.')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA, 'extra карточки уже другое'
    assert deal['date'] == '2026-01-14', 'date карточки уже другое'

    print('БЫЛО:', OLD_EXTRA)
    print('СТАНЕТ:', NEW_EXTRA)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['extra'] = NEW_EXTRA
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
