# -*- coding: utf-8 -*-
"""Слить дубль «RWB купила мажоритарную долю в сервисе „Еаптека"».

НАЙДЕНО 19 сентября 2026, когда владелец спросил, почему аптечные сети
лежат в разных отраслях. Оказалось, что у «Еаптеки» одна и та же сделка
записана дважды и карточки попали в РАЗНЫЕ отрасли — «Фармацевтика» и
«E-commerce». То есть расхождение отрасли было не причиной, а следствием.

ОДНА И ТА ЖЕ СДЕЛКА, совпадает всё, что её определяет:
  дата 2026-07-01 · статус «Закрыта» · покупатель g549ab474 (ООО «РВБ»,
  Wildberries & Russ) · предмет g5a939ce1 («Еаптека»). Оценки суммы
  пересекаются (8–10 и 7–12 млрд ₽ — это одна и та же оценка в разных
  пересказах).

ПОЧЕМУ СКАНЕР ДУБЛЕЙ ЭТО ПРОПУСТИЛ: заголовки называют покупателя
по-разному — «Wildberries и Russ» и «RWB». RWB и есть их объединённая
компания, но общего слова в кавычках у заголовков нет, и признак
`near_duplicate()` не сработал.

КТО ОСТАЁТСЯ. `gf12c6323`: восемь источников (Интерфакс, Forbes,
Коммерсантъ — закрытие и анонс, Vademecum, CNews, РИА Новости,
Фармвестник), заполненный текст карточки, запись о новом учредителе в
ЕГРЮЛ от 1 июля 2026 года. `gmru-rwb-eapteka`: два источника mergers.ru,
текста карточки нет.

ЧТО ПЕРЕНЕСЕНО. Два источника mergers.ru (у оставшейся карточки их не
было) и веха «Переговоры на продвинутой стадии» от 24 июня 2026 года: у
оставшейся карточки веха переговоров есть, но ДРУГАЯ — февральская 2025
года, про самое начало разговоров. Июньская — отдельное событие, и её
текст приходит вместе со своим источником, который мы тем же заходом
добавляем.

ЧЕГО НЕ ПЕРЕНОСИЛ. Поля `eco`/`law` дубля — те же факты в другом
пересказе, у оставшейся карточки они заполнены; обогащение дополняет
пустое, а не переписывает заполненное. Оценку суммы 7–12 млрд ₽ — она не
точнее той, что уже стоит.

Запуск:
    python3 pipeline/merge_eapteka_rwb_dup.py            # сухой прогон
    python3 pipeline/merge_eapteka_rwb_dup.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP, DROP = 'gf12c6323', 'gmru-rwb-eapteka'
MERGERS_SRC = [
    ['mergers.ru', 'https://mergers.ru/news/RWB-kupila-mazhoritarnuyu-dolyu-v-servise-Eapteka-87129'],
    ['mergers.ru', 'https://mergers.ru/news/RWB-blizok-k-pokupke-Eapteki-87095'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}
    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep and drop, 'одной из карточек пары уже нет'

    # Проверка на себе: сливаем только то, что совпадает по сути сделки.
    for field in ('date', 'status', 'buyer', 'target'):
        assert keep.get(field) == drop.get(field), \
            'карточки расходятся по полю %s: %r и %r' % (field, keep.get(field), drop.get(field))

    stage = next((e for e in (drop.get('events') or [])
                  if e.get('kind') == 'negotiations' and e.get('date') == '2026-06-24'), None)
    assert stage, 'в дубле нет вехи переговоров от 24 июня 2026'
    have = {(e.get('kind'), e.get('date')) for e in (keep.get('events') or [])}
    assert ('negotiations', '2026-06-24') not in have, 'такая веха у оставшейся карточки уже есть'

    urls = {s[1] for s in (keep.get('src') or []) if isinstance(s, list) and len(s) > 1}
    add_src = [s for s in MERGERS_SRC if s[1] not in urls]

    print('СЛИЯНИЕ %s -> %s' % (DROP, KEEP))
    print('  переносим источников:', len(add_src))
    print('  переносим веху:', stage.get('date'), '—', stage.get('title'))

    before = len(deals)
    if write:
        keep.setdefault('src', []).extend(add_src)
        carried = dict(stage)
        carried['id'] = 'negotiations-2026-06-24'
        keep.setdefault('events', []).append(carried)
        keep['events'].sort(key=lambda e: str(e.get('date') or ''))
        deals[:] = [d for d in deals if d['id'] != DROP]
        data.setdefault('merged', {})[DROP] = KEEP

    after = len(deals) if write else before - 1
    print('\nСделок: %d -> %d' % (before, after))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    assert after == before - 1, 'число карточек изменилось не на одну'
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
