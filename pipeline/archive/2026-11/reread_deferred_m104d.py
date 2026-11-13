# -*- coding: utf-8 -*-
"""Вычитка, партия m104 (13 ноября 2026), часть 4: снять карточки gfe21a083 и cdbb80afb.

cdbb80afb — «ФРИИ проинвестирует в 15 стартапов до 3 млрд ₽» (Ведомости, 02.02.2024: «ФРИИ
планирует вложить до 3 млрд рублей в 15 стартапов») — план фонда, не сделка; запись
в чужом живом файле pipeline/ingest/fixes/written_titles_g3_2026_11_01.py.

gfe21a083
(«Опека-МСК» купила 49,99% «Опека-Групп») — сделка 2021 года, а база начинается
с 2022 года (решение владельца 27 октября 2026, pipeline/drop_pre_2022_deals.py;
держит test_data.py::test_base_starts_in_2022).

ДОКАЗАТЕЛЬСТВО. По ЕГРЮЛ ООО «Опека-Групп» (ИНН 7802610028) 11 мая 2021 года вышли
Олег Кедровский (31,2432%), Святослав Петрушко и Дмитрий Шульженко (по 9,373%),
вошло ООО «Опека-МСК» (49,9892%). Коммерсантъ 30.10.2024 («Владелец сети «Опека»
Алексей Маврин остался единственным бенефициаром») описал именно эту запись
реестра: «Доли Олега Кедровского (ему принадлежало 31,24%), Дмитрия Шульженко и
Святослава Петрушко (по 9,37%)» перешли ООО «Опека-МСК», что «обнаружил “Ъ” в
ЕГРЮЛ». Запись 25.07.2024 о Маврине — залог его доли в Сбербанке, не продажа.

ВНИМАНИЕ ПРИ ЗАПИСИ. У карточки есть записи в живом файле правок другой партии —
pipeline/ingest/fixes/reread_2026_11_12_m030_b.py; скрипт снимает их
(merge_duplicate_deals_batch.strip_fixes — архив и живые файлы), и этот файл обязан уйти в тот же коммит, иначе
test_review_table_is_applied_and_not_pending покраснеет («карточки нет в базе»).
reread_apply.py коммитит только файлы правок со своей меткой, поэтому этот скрипт
в план партии не включен — его записывает координатор вместе с файлом m030_b.

    python3 pipeline/archive/2026-11/reread_deferred_m104d.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m104d.py --write   # запись
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REMOVE = {'gfe21a083': '«Опека-Групп»', 'cdbb80afb': 'ФРИИ'}


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    gone = [c for c in REMOVE if c in cards]
    if not gone:
        print('Уже применено.')
        return 0
    targets = set((data.get('merged') or {}).values())
    for cid in gone:
        assert REMOVE[cid] in str(cards[cid].get('title')), cards[cid].get('title')
        assert cid not in targets
        print('  СНИМАЕМ %s %s' % (cid, cards[cid]['title']))
    import merge_duplicate_deals_batch as mdb   # снимает записи и из архива, и из живых файлов (по AST)
    mdb.strip_fixes(set(gone), write=False)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    import mass_edit_guard
    old = json.load(open(DATA, encoding='utf-8'))
    data = copy.deepcopy(old)
    data['deals'] = [d for d in data['deals'] if d['id'] not in gone]
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    mdb.strip_fixes(set(gone), write=True)
    print('ЗАПИСАНО: сняты %s; закоммитить вместе с измененными файлами правок (см. вывод выше: '
          'reread_2026_11_12_m030_b.py, written_titles_g3_2026_11_01.py, fixes_archive/2026-10.json)' % ', '.join(gone))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
