# -*- coding: utf-8 -*-
"""Слияние дубля: `c985468d2` («Лента» покупает розничную сеть «Молл»
(бренды «Молния» и Spar) в Челябинской области», тонкая карточка из
рэнкинга «Ъ — Сделки года», `from_compact: mini`) и `g300d56ed` («Лента
купила челябинскую торговую сеть Молния») — одна и та же сделка (та же
дата 2025-06-26, тот же покупатель — профиль `gcca31da7`, «Лента»).
Найдено списком кандидатов сканера
`find_duplicate_deal_candidates_by_buyer_date.py` (месячная очередь,
8 сентября 2026).

Оставлена карточка `g300d56ed` — она полнее: 4 источника против одного,
предмет привязан к профилю компании (`target`), уже прошла weekly и
followup обыск, названы юристы поимённо с обеих сторон, есть суммовая
оценка и контекст о продавце.

СЛИЯНИЕ ПОПУТНО ЧИНИТ ДВА ДЕФЕКТА В `g300d56ed`, которые обнаружились
именно при сравнении с дублем:

1) `seller` у `g300d56ed` стоял ОБРЫВКОМ — буквально строка
   «предположительно» без имени продавца (видимо, след незавершённой
   правки). У `c985468d2` тот же продавец назван прямо: «ООО «Молния
   Финанс»» — и это ТОТ ЖЕ факт, что уже стоит текстом в `eco.context`
   самой карточки `g300d56ed» («Вся доля в ООО «Молл» принадлежит
   «Молния Финанс»»), просто не был перенесён в структурное поле.

2) `law.adv` карточки `g300d56ed` называл роль O2 Consulting
   НЕПОДТВЕРЖДЁННОЙ независимым источником («указана по самоотчёту
   фирмы»). Личный WebFetch (kommersant.ru/doc/8077927, «Ъ — Сделки
   года» — источник дубля `c985468d2`) НЕЗАВИСИМО подтверждает: «Продавец:
   ООО «Молния Финанс» / Юридический консультант продавца: О2
   Сonsulting» — хедж снят, роль подтверждена вторым источником.

Запуск:
    python3 pipeline/merge_lenta_molniya_dup.py            # сухой прогон
    python3 pipeline/merge_lenta_molniya_dup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP_ID = 'g300d56ed'
DROP_ID = 'c985468d2'

OLD_SELLER = 'предположительно'
NEW_SELLER = 'ООО «Молния Финанс»'

OLD_O2_ENTRY = [
    'Юридический консультант продавцов (предположительно)', 'O2 Consulting',
    'Продажа ООО «Молл» (сеть «Молния») группе «Лента». Роль по стороне '
    'сделки не подтверждена независимым источником, указана по '
    'самоотчёту фирмы. Источник: o2consult.com/projects',
]
NEW_O2_ENTRY = [
    'Юридический консультант продавца (ООО «Молния Финанс»)', 'O2 Consulting',
    'Продажа ООО «Молл» (сеть «Молния») группе «Лента». Роль независимо '
    'подтверждена рэнкингом «Коммерсантъ — Сделки года» и самоотчётом '
    'фирмы (o2consult.com/projects).',
]

NEW_SRC = ['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    assert DROP_ID in by_id, '%s должна существовать до слияния' % DROP_ID
    keep = by_id[KEEP_ID]
    assert keep['seller'] == OLD_SELLER, 'seller уже другой: %r' % (keep['seller'],)
    adv = keep['law']['adv']
    assert adv[1] == OLD_O2_ENTRY, 'law.adv[1] уже другой: %r' % (adv[1],)

    print('seller: %r -> %r' % (OLD_SELLER, NEW_SELLER))
    print('law.adv[1]: хедж снят, роль подтверждена независимым источником')
    existing_urls = {s[1] for s in keep['src']}
    if NEW_SRC[1] not in existing_urls:
        print('src: добавляется', NEW_SRC)
    print('deals: было %d, станет %d' % (len(deals), len(deals) - 1))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    keep['seller'] = NEW_SELLER
    keep['law']['adv'][1] = NEW_O2_ENTRY
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
