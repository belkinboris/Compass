# -*- coding: utf-8 -*-
"""Профиль «Мария-Ра» и его ИНН — то, что надо было сделать на черновике.

Владелец 23 сентября 2026: «мы же на этапе черновика уже можем найти профиль
и посмотреть отчётность». Может: имя юрлица стояло прямо в карточке
(«ООО «Розница К-1»»), и поиск по ЕГРЮЛ отдал ИНН 2225074005 за секунду.
Вместо этого читатель отложил профиль с причиной «профиля в базе ещё нет»,
и пост о сделке вышел без финансов покупаемой компании.

Правило, чтобы это не повторилось, — в `accept_card.check_answer`:
отложить профиль нельзя, когда роль названа ОДНИМ юрлицом. Здесь —
исправление самой карточки.

    python3 pipeline/fix_maria_ra_profile_2026_09_23.py
    python3 pipeline/fix_maria_ra_profile_2026_09_23.py --write
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(HERE, 'ingest')):
    if p not in sys.path:
        sys.path.insert(0, p)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD = 'gb7ea4703'
INN = '2225074005'
LEGAL = 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РОЗНИЦА К-1"'
NAME = 'Мария-Ра'
REG_ROW = (
    '{"company_id": "gc6091c34", "decision": "confirmed", "inn": "2225074005",\n'
    '     "reason": "Искали по бренду «Мария-Ра» — ЕГРЮЛ его не знает, и 28.08.2026 '
    'запись была no_match. Имя операционного юрлица принесла карточка сделки '
    'gb7ea4703 (23.09.2026): ООО «Розница К-1» — точное совпадение в ЕГРЮЛ нашлось '
    'сразу. Решение no_match относилось к ИМЕНИ, по которому искали, а не к компании.",\n'
    '     "date": "2026-09-23"}')
DESC = ('Продуктовая сеть Сибири и Алтая: 1303 магазина в 280 населённых пунктах '
        'Алтайского края, Республики Алтай, Новосибирской, Кемеровской и Томской '
        'областей. Операционное юрлицо — ООО «Розница К-1».')


def main(write: bool) -> int:
    import accept_card

    data = json.loads(open(DATA, encoding='utf-8').read())
    comps = data['companies']
    card = next((d for d in data['deals'] if d['id'] == CARD), None)
    if card is None:
        print('карточки %s нет' % CARD)
        return 1

    cid = next((c for c, v in comps.items() if v.get('name') == NAME), None)
    if cid is None:
        print('профиля «%s» нет — этот скрипт писался для случая, когда он ЕСТЬ' % NAME)
        return 1
    print('профиль «%s» существует с 2023 года: %s' % (NAME, cid))
    if str(comps[cid].get('desc') or '') != DESC:
        print('   описание дополняется юрлицом и масштабом сети:')
        print('   было:  %s' % comps[cid].get('desc'))
        print('   стало: %s' % DESC)
        if write:
            comps[cid]['desc'] = DESC

    if card.get('asset_id') == cid:
        print('карточка уже привязана к профилю')
    else:
        print('карточка %s: asset_id -> %s (текст предмета остаётся «%s»)'
              % (CARD, cid, card.get('asset')))
        if write:
            card['asset_id'] = cid

    notes = card.get('accepted_notes') or {}
    if (notes.get('no_profile') or {}).get('target'):
        print('снимаю отложенный профиль предмета: «%s»' % notes['no_profile']['target'][:70])
        if write:
            notes['no_profile'].pop('target', None)
            if not notes['no_profile']:
                notes.pop('no_profile', None)

    # В реестре у этого профиля уже лежит решение `no_match` от 28 августа:
    # искали по БРЕНДУ «Мария-Ра», а ЕГРЮЛ знает операционное юрлицо под
    # другим именем. Имя юрлица дала карточка сделки — и поиск по нему
    # находит ИНН сразу. `by_company_id()` берёт ПОСЛЕДНЮЮ строку, поэтому
    # новое решение дописывается блоком в конец, а прежнее остаётся в файле
    # как история: отрицательный ответ был верен для того имени, по которому
    # искали.
    print('реестр ИНН: %s -> %s (%s)' % (cid, INN, LEGAL))
    print('   прежняя строка no_match ЗАМЕНЯЕТСЯ: инвариант — одна запись на профиль')
    if write:
        # Строка ЗАМЕНЯЕТСЯ, а не дописывается: инвариант базы —
        # `test_data.py::test_fns_registry_company_id_is_not_duplicated` —
        # запрещает две текущие записи на один профиль. Прежний отказ живёт
        # теперь внутри причины, а не отдельной строкой.
        import re as _re
        path = accept_card.REGISTRY_PATH
        src = open(path, encoding='utf-8').read()
        m = _re.search(r'\{[^{}]*"company_id": "%s"[^{}]*\}' % cid, src)
        assert m, 'строки профиля %s нет в реестре' % cid
        print('   прежняя строка заменяется (инвариант: одна запись на профиль)')
        open(path, 'w', encoding='utf-8').write(src[:m.start()] + REG_ROW + src[m.end():])
        open(DATA, 'w', encoding='utf-8').write(
            json.dumps(data, ensure_ascii=False, indent=1) + '\n')
        print('\nзаписано. Отчётность подтянется ближайшей синхронизацией ФНС на проде.')
    else:
        print('\n(сухой прогон; чтобы записать — --write)')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
