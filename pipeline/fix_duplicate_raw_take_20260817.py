# -*- coding: utf-8 -*-
"""17 августа 2026, прогон публикации: одна кнопка «в работу» дала 18 карточек
вместо 4.

КОРЕНЬ. `approve.py` строит `raw_all` конкатенацией ВСЕХ файлов
`data/inbox/hold/*.json` и сопоставляет решение «take» по `draft_id` с
КАЖДЫМ вхождением в этом списке — а RSS-ленты отдают историю на несколько
суток назад, и один и тот же `draft_id` попадает в несколько дневных
hold-файлов подряд (11, 14, 16, 17 августа для одного черновика). Решение
партнёра «это сделка» на такой `draft_id` сработало один раз на файл, а не
один раз на черновик: `plan_raw`/цикл `for draft in taken` в approve.py не
дедуплицирует `raw_all` по `draft_id` перед превращением в карточки. Это
баг кода притока (`pipeline/ingest/approve.py`, `pipeline/ingest/promote.py`),
не этой правки — здесь чинится только уже записанный результат.

ЧТО НАШЛОСЬ. 4 черновика превратились в 18 карточек `pending.json`:
  d10567566 (РИА Недвижимость, «Наследники основателя Самолета продали 18%
    компании казахстанскому фонду») x4 — та же сделка, что уже 6 суток
    живёт в базе под g0551fc60 (Fonte Capital/«Самолет», источник
    Коммерсантъ, дата 2026-08-10, полнее: есть продавец и оценка суммы).
  d89400328 (RB.ru, «ГК «Самолёт» объявила об изменении в составе
    акционеров...») x5 — тот же g0551fc60, другой источник.
  d19423493 (РИА Недвижимость, «Крупный производственно-складской комплекс
    в Ленобласти сменил владельца») x5 — сверено с базой: НЕ дубль (ложное
    подозрение притока на g677f3309 — это другая сделка, книжная сеть
    «Республика»), но сделка одна, а карточек пять.
  d84688009 (Ведомости, «ЦБ зарегистрировал допэмиссию акций «М.видео» по
    закрытой подписке») x4 — в базе такой сделки нет, но карточка одна, а
    записей четыре.

ДЕЙСТВИЕ:
  - d10567566 и d89400328: снять ВСЕ копии из очереди (сделка уже есть),
    добавить оба источника к g0551fc60 — независимое подтверждение, не
    украшение.
  - d19423493 и d84688009: оставить по ОДНОЙ карточке (первую по порядку),
    снять остальные копии.

ЗАПУСК:
    python3 pipeline/fix_duplicate_raw_take_20260817.py            # сухой прогон
    python3 pipeline/fix_duplicate_raw_take_20260817.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

# draft_id -> все id карточек-копий, в порядке появления в pending.json
GROUPS = {
    'd10567566': ['g037e16b1', 'g84c8c9e0', 'g3632bc79', 'g55f282fc'],
    'd19423493': ['gd1771616', 'gbc873496', 'g9c27cdf3', 'g12afc5c6', 'gbc870a0d'],
    'd89400328': ['gda5286e9', 'gaf286c3e', 'gc16a92fa', 'g74f4373c', 'g489b925f'],
    'd84688009': ['gb5d8a18a', 'g6fd6c8dc', 'gaa88353f', 'g85d8f4bf'],
}

# черновики-дубли уже живущей сделки — снимаются ЦЕЛИКОМ
DUP_OF_LIVE = ('d10567566', 'd89400328')
LIVE_ID = 'g0551fc60'
NEW_SOURCES = [
    ['РИА Недвижимость', 'https://realty.ria.ru/20260810/samolet-2110002634.html'],
    ['RB.ru', 'https://rb.ru/news/gk-samolyot-obyavila-ob-izmenenii-v-sostave-akcionerov-kazahstanskij-fond-priobryol-18-akcij-developera/'],
]

# черновики новых, но задвоенных сделок — оставить первую карточку
DEDUPE_ONLY = ('d19423493', 'd84688009')


def main(argv):
    pending = json.load(open(PENDING, encoding='utf-8'))
    ids_in_pending = {c['id'] for c in pending['cards']}
    for draft, ids in GROUPS.items():
        missing = [i for i in ids if i not in ids_in_pending]
        assert not missing, '%s: карточек %s уже нет в очереди — проверьте вручную' % (draft, missing)

    to_remove = set()
    for draft in DUP_OF_LIVE:
        to_remove.update(GROUPS[draft])
    keep_ids = set()
    for draft in DEDUPE_ONLY:
        ids = GROUPS[draft]
        keep_ids.add(ids[0])
        to_remove.update(ids[1:])

    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    live = by_id[LIVE_ID]
    existing_urls = {str(s[1]) for s in (live.get('src') or []) if len(s) > 1}
    to_add_src = [s for s in NEW_SOURCES if s[1] not in existing_urls]

    print('СНИМАЕМ из очереди (%d карточек): %s' % (len(to_remove), ', '.join(sorted(to_remove))))
    print('ОСТАВЛЯЕМ по одной копии: %s' % ', '.join(sorted(keep_ids)))
    if to_add_src:
        print('ДОБАВЛЯЕМ источники к %s: %s' % (LIVE_ID, ', '.join(s[1] for s in to_add_src)))
    else:
        print('источники у %s уже стоят' % LIVE_ID)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending['cards'] = [c for c in pending['cards'] if c['id'] not in to_remove]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    if to_add_src:
        live.setdefault('src', []).extend(to_add_src)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
