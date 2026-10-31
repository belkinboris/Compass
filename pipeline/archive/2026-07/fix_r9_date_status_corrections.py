# -*- coding: utf-8 -*-
"""Раунд 9 (финальный раунд бэклога 2022-2025), партия 5 агентов, 15 августа
2026: карточки, у которых дата и/или статус разошлись с источником —
большинство в пределах 2023 года. Через review.py эти правки не идут:
смена статуса вместе с датой в одной записи FIXES не разделяется на
отдельные проверяемые поля так же чисто, как отдельный скрипт со своим
assert на исходное состояние (см. прецедент раунда 8).

g60280ac0 (Decathlon/АРМ) — источник прямо называет дату вступления сделки
в силу (3 октября 2023), а не дату публикации новости об обсуждении.
gfd78ef6d (MTS AI/Primo RPA) — источник прямо пишет «Сделка состоялась 12
июля», а новость (и дата карточки) — от 13 июля, на день позже.
gfca749be (Kraft Heinz/Черноголовка) и g78e14953 (S8 Capital/Bridgestone) —
обе карточки стояли «Обсуждается» на дате первой новости о переговорах;
более поздние источники (тот же холдинг цитирует более поздний РБК/
Интерфакс) подтверждают закрытие сделки датой, названной в источнике
словами.

ЗАПУСК:
    python3 pipeline/fix_r9_date_status_corrections.py            # сухой прогон
    python3 pipeline/fix_r9_date_status_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, old_date, new_date, old_status, new_status, src_label, src_url)
FIXES = [
    ('g60280ac0', '2023-07-01', '2023-10-03', 'Обсуждается', 'Закрыта',
     'realnoevremya.ru',
     'https://m.realnoevremya.ru/news/292261-magaziny-decathlon-v-rossii-hotyat-otkryt-v-dekabre'),
    ('gfca749be', '2023-06-01', '2024-03-19', 'Обсуждается', 'Закрыта',
     'Интерфакс',
     'https://www.interfax.ru/business/951165'),
    ('g78e14953', '2023-06-05', '2023-12-20', 'Обсуждается', 'Закрыта',
     'Коммерсантъ',
     'https://www.kommersant.ru/doc/6412480'),
    ('gfd78ef6d', '2023-07-13', '2023-07-12', 'Закрыта', 'Закрыта',
     'Интерфакс',
     'https://www.interfax.ru/amp/911415'),
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
