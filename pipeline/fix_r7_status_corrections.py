# -*- coding: utf-8 -*-
"""Пять карточек раунда 7 (партия 5 агентов, 15 августа 2026), у которых
год в дате верен (2023), но статус отстал: источник прямо говорит о
закрытии сделки, а карточка всё ещё несёт «Обсуждается».

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. review.py умеет уточнять день/месяц ВНУТРИ уже
известного года по цитате, но не имеет отдельного пути для смены только
`status` без сопутствующей правки текстового поля с тем же источником —
проще и безопаснее одним скриптом со своим assert на исходное состояние,
как и `fix_r6_year_corrections.py`.

g236a9b88 (Молочная культура): ВНИМАНИЕ — по источнику покупатель получил
доли 25,1% / 79% / 79% в трёх разных юрлицах группы, а не единый
контрольный пакет. Эта карточка правится ТОЛЬКО по статусу; поле `buyer`/
доля не трогаются — решение о том, как это показать на экране, за
человеком (см. коммит).

ЗАПУСК:
    python3 pipeline/fix_r7_status_corrections.py            # сухой прогон
    python3 pipeline/fix_r7_status_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, old_date, new_date, old_status, new_status, src_label, src_url)
FIXES = [
    ('g65557c4a', '2023', '2023-12-25', 'Обсуждается', 'Закрыта',
     'Интерфакс', 'https://www.interfax.ru/business/938400'),
    ('g8de46135', '2023', '2023', 'Обсуждается', 'Закрыта',
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6454433'),
    ('g12370211', '2023', '2023-08-07', 'Обсуждается', 'Закрыта',
     'dp.ru', 'https://www.dp.ru/a/2023/08/09/peterburgskij-biletnij-agregator'),
    ('g236a9b88', '2023', '2023', 'Обсуждается', 'Закрыта',
     'dp.ru', 'https://www.dp.ru/a/2023/12/04/nevesjolij-molochnik-kreditori'),
    ('ga7232033', '2023', '2023', 'Обсуждается', 'Закрыта',
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6085072'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, old_date, new_date, old_status, new_status, label, url in FIXES:
        deal = by_id[cid]
        assert deal.get('date') == old_date, \
            '%s: date уже другой: %r (ожидали %r)' % (cid, deal.get('date'), old_date)
        assert deal.get('status') == old_status, \
            '%s: status уже другой: %r (ожидали %r)' % (cid, deal.get('status'), old_status)
        print('ПРАВИМ %s: date %r -> %r, status %r -> %r' % (
            cid, old_date, new_date, old_status, new_status))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, old_date, new_date, old_status, new_status, label, url in FIXES:
        deal = by_id[cid]
        deal['date'] = new_date
        deal['status'] = new_status
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        if url not in existing_urls:
            deal.setdefault('src', []).append([label, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
