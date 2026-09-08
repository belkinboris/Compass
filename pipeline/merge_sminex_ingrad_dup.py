# -*- coding: utf-8 -*-
"""Слияние дубля: `c514e8712` («Sminex покупает девелопера «Инград» у
концерна «Россиум»») — тонкая карточка из рэнкинга «Ъ — Сделки года»
(`from_compact: mini`) — и `gdda3e685` («Продажа «Инграда» девелоперу
Sminex») описывают ОДНУ И ТУ ЖЕ сделку: та же дата (2024-10-17), тот же
покупатель (профиль `gdc41f40b`, Sminex), тот же продавец (концерн
«Россиум»), тот же предмет (профиль `g5ca09975`, «Инград»). Найдено
списком кандидатов сканера `find_duplicate_deal_candidates_by_buyer_date.py`
(месячная очередь, 8 сентября 2026).

Оставлена карточка `gdda3e685` — она полнее: 11 источников против одного,
предмет привязан к профилю компании (`target`), уже прошла weekly и
followup обыск, богаче `eco.context` (судьба одного из проектов после
сделки). У `c514e8712` — единственный источник (Коммерсантъ, «Сделки
года»), но он несёт факт, которого у `gdda3e685` НЕ БЫЛО: юридический
консультант продавца (Nextons). `gdda3e685.law.adv` до этой правки нёс
плейсхолдер «Не раскрывались» — а источник называет консультанта прямо.

Личный WebFetch (kommersant.ru/doc/8077927, «Ъ — Сделки года») подтвердил
дословно: «Юридический консультант: Nextons со стороны продавца... для
ООО "Концерн Россиум". Консультант покупателя не указан. Сумма: не
разглашается. Статус: завершена» — совпадает с тем, что уже стояло в
`c514e8712`.

Перенесено в `gdda3e685`:
1) `law.adv` — плейсхолдер заменён на запись о Nextons (продавец), с
   пометкой, что консультант покупателя не назван ни одним источником.
2) Источник «Коммерсантъ — Сделки года» (doc/8077927), которого в списке
   `gdda3e685` не было.

Остальные факты `c514e8712` (финансы 2023 года, оценки Трубачева/
Шелковского, одобрение ФАС) дословно совпадают с уже стоящими в
`gdda3e685` — не новые, не переносятся.

Запуск:
    python3 pipeline/merge_sminex_ingrad_dup.py            # сухой прогон
    python3 pipeline/merge_sminex_ingrad_dup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP_ID = 'gdda3e685'
DROP_ID = 'c514e8712'

OLD_ADV = [['Стороны сделки', 'Не раскрывались',
            'Юридические консультанты в публичных источниках не раскрывались']]
NEW_ADV = [['Юридический консультант продавца (концерна «Россиум»)', 'Nextons',
            'Nextons — за продавца; консультант покупателя (Sminex) в '
            'публичных источниках не назван. Источник: Коммерсантъ — '
            '«Сделки года».']]

NEW_SRC = ['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    assert DROP_ID in by_id, '%s должна существовать до слияния' % DROP_ID
    keep = by_id[KEEP_ID]
    assert keep['law']['adv'] == OLD_ADV, 'law.adv уже другой: %r' % (keep['law']['adv'],)

    print('law.adv: %r -> %r' % (OLD_ADV, NEW_ADV))
    existing_urls = {s[1] for s in keep['src']}
    if NEW_SRC[1] not in existing_urls:
        print('src: добавляется', NEW_SRC)
    print('deals: было %d, станет %d' % (len(deals), len(deals) - 1))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    keep['law']['adv'] = NEW_ADV
    if NEW_SRC[1] not in existing_urls:
        keep['src'].append(NEW_SRC)

    merged = data.setdefault('merged', {})
    merged[DROP_ID] = KEEP_ID
    data['deals'] = [d for d in deals if d['id'] != DROP_ID]

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано. Сделок было: %d, стало: %d' % (len(deals), len(data['deals'])))


if __name__ == '__main__':
    main('--write' in sys.argv)
