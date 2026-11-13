# -*- coding: utf-8 -*-
"""Вычитка, партия m235 (13 ноября 2026): снять карточки g4cd1fa52 и g4f4dc9b5 — не сделки.

Владелец поручил решать «не сделка» самим (задание марафона, 13 ноября 2026); обе
карточки висели вопросами в консоли (pipeline/open_questions.json, 3 ноября 2026).

g4cd1fa52 — «Принудительная деконсолидация активов Wintershall Dea в России»: тип
«Финансирование», статус «Не состоялась», сторон нет. Это бухгалтерское событие — Wintershall
Dea вывела российские СП из отчетности в 4 квартале 2022 года (пресс-релиз ir-23-01:
неденежный убыток €5,3 млрд). Продажа самих долей — отдельная карточка g3bb1fadb
(«Согаз» и «Газовые технологии», распоряжения правительства № 873-р и № 865-р от 16.04.2026;
факты и источники 2026 года туда уже перенесены, open_questions «wintershall-one-or-two»).

g4f4dc9b5 — «Philip Morris оценила свою долю 23% в Megapolis Distribution в $351 млн»:
переоценка доли в отчете PMI (10-Q за 3 квартал 2023 года, Интерфакс), продажи не было,
покупателя нет; поиск за 2024–2026 годы (Интерфакс, Ведомости, 2firsts, Tobacco Reporter)
продажи доли не нашел.

ВНИМАНИЕ ПРИ ЗАПИСИ. У карточек есть записи в чужих файлах правок; скрипт снимает их
(merge_duplicate_deals_batch.strip_fixes — архив и живые файлы), и эти файлы обязаны уйти в
тот же коммит, иначе test_review_table_is_applied_and_not_pending покраснеет. reread_apply.py
коммитит только файлы правок со своей меткой, поэтому этот скрипт в план партии не включен —
его записывает координатор. Запись в telegram_posts остается (история канала).

    python3 pipeline/archive/2026-11/reread_deferred_m235.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m235.py --write   # запись
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REMOVE = {'g4cd1fa52': 'Wintershall Dea', 'g4f4dc9b5': 'Megapolis'}


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
    print('ЗАПИСАНО: сняты %s; закоммитить вместе с измененными файлами правок (см. вывод выше)' % ', '.join(gone))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
