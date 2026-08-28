# -*- coding: utf-8 -*-
"""Дубль карточки + профиль-близнец, найденные кампанией самопроверки ИНН
вебом (28 августа 2026, партия 3, `pipeline/fns_registry.py`). Живой поиск
на «Инград» дал ОДИН и тот же ИНН (7702336269, ПАО «Инград») для двух
разных `company_id` — потому что это в буквальном смысле два профиля одной
и той же реальной компании: `g5ca09975` («Группа «Инград»») и `g942e9f9e`
(«девелопер «Инград»»).

ПОЧЕМУ ЭТО ДУБЛЬ, А НЕ ДВЕ СВЯЗАННЫЕ КОМПАНИИ. Обе карточки, где эти
профили стоят ЦЕЛЬЮ сделки, описывают ОДНО И ТО ЖЕ событие — выход Sminex
на рынок девелопмента через покупку «Инграда», закрытую в октябре 2024:
`gdda3e685` («Продажа «Инграда» девелоперу Sminex», 17.10.2024, 6
источников) и `g70ea4673` («Sminex выкупил девелопера «Инград»…»,
01.10.2024, 1 источник). Совпадают дословно ключевые цифры (19 проектов,
7,1 млн кв. м, 15 тыс. га земельного банка, выручка 2023 года 63,3 млрд
руб./EBITDA 11,1 млрд руб. по МСФО) — это не «две похожие сделки», а одна
и та же, увиденная дважды.

ЧТО ОСТАЁТСЯ, ЧТО УХОДИТ (сделка). `gdda3e685` — сильнее: 6 источников
против 1, есть настоящее согласование ФАС (`law.appr`), есть независимая
оценка (`eco.val`), карточка дочитана позже и глубже
(`followup_researched`). У `g70ea4673` есть ОДИН факт, которого у
`gdda3e685` нет, — Sminex одновременно ищет покупателей на часть активов
(8 конкретных площадок: «Новое Пушкино», «БелыйGRAD», «Филатов луг»,
«Одинград» и др.) — переносится в `extra` дословно. Источник дубля
(другой пост того же телеграм-канала, `t.me/dealsma/5610` против уже
имеющегося `.../5415`) — переносится тоже: это другая ссылка, а не
украшение.

ЧТО ОСТАЁТСЯ, ЧТО УХОДИТ (профиль компании). После слияния сделок у
`g5ca09975` — 2 роли (цель в `gdda3e685`, покупатель в `g5e50ec94`,
отдельная, не связанная сделка — «Группа «Инград» купила склад «Киевское,
22»), у `g942e9f9e` — 0. Остаётся `g5ca09975` (та же логика выбора, что в
`merge_company_twins_fns_campaign.py`: больше ролей — меньше ссылок
переписывать). ИНН, подтверждённый партией 3 кампании самопроверки для
`g942e9f9e` (7702336269 — см. `pipeline/fns_registry.py`), переносится на
`g5ca09975` ОТДЕЛЬНОЙ правкой того же файла (не задача этого скрипта, тот
же принцип разделения, что и в прошлых слияниях-близнецах ФНС-кампании).

Три записи `pipeline/ingest/fixes/batch_agents100_r1.py`, ссылавшиеся на
`g70ea4673`, сняты вместе с этой правкой (см. комментарий в файле).

Запуск:
    python3 pipeline/merge_smineks_ingrad_dup.py            # сухой прогон
    python3 pipeline/merge_smineks_ingrad_dup.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

KEEP_DEAL, DROP_DEAL = 'gdda3e685', 'g70ea4673'
KEEP_COMPANY, DROP_COMPANY = 'g5ca09975', 'g942e9f9e'

# Дословный кусок extra дубля (не пересказ) — с якорем на «Sminex», чтобы после
# склейки со старым extra получилось отдельное предложение, а не оборванная фраза.
EXTRA_ADD = ('Sminex в октябре выкупил девелопера «Инград» и начал поиск покупателей на часть его '
             'активов — 8 площадок примерно на 2,7 млн кв.м комфорт-класса, включая проекты ЖК '
             '«Новое Пушкино», «БелыйGRAD» в Мытищах, «Филатов луг» в новой Москве, «Одинград» в '
             'Одинцове и другие.')
DROP_SRC = ['@dealsma (Telegram)', 'https://t.me/dealsma/5610']


def norm(s):
    return ' '.join(str(s or '').split())


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals, comps = data['deals'], data['companies']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP_DEAL), by_id.get(DROP_DEAL)
    assert keep and drop, 'карточек пары нет в базе — состояние изменилось, скрипт остановлен'
    assert keep.get('target') == KEEP_COMPANY, 'у оставляемой карточки цель уже не та'
    assert drop.get('target') == DROP_COMPANY, 'у дубля цель уже не та'
    both = [d['id'] for d in deals if {d.get(f) for f in REFS} >= {KEEP_COMPANY, DROP_COMPANY}]
    assert not both, 'сделка ссылается на оба профиля сразу: %s' % both

    assert EXTRA_ADD in norm(drop.get('extra')), 'факт про поиск покупателей не лежит в extra дубля дословно'
    assert EXTRA_ADD not in norm(keep.get('extra')), 'факт уже перенесён'

    keep_urls = {str(s[1]) for s in (keep.get('src') or []) if len(s) > 1}
    assert DROP_SRC[1] not in keep_urls, 'источник дубля уже есть у оставляемой карточки'

    assert comps.get(KEEP_COMPANY) and comps.get(DROP_COMPANY), 'профиля компании нет'

    print('СЛИЯНИЕ ДУБЛЯ СДЕЛКИ')
    print('  оставляем %s  %s' % (KEEP_DEAL, keep['title']))
    print('  удаляем   %s  %s' % (DROP_DEAL, drop['title']))
    print('  переносим факт: поиск покупателей на 8 площадок')
    print('  переносим источник: %s' % DROP_SRC[1])
    print('\nСЛИЯНИЕ ПРОФИЛЯ-БЛИЗНЕЦА')
    print('  оставляем %s  «%s»' % (KEEP_COMPANY, comps[KEEP_COMPANY]['name']))
    print('  удаляем   %s  «%s»' % (DROP_COMPANY, comps[DROP_COMPANY]['name']))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    keep['extra'] = (norm(keep.get('extra')) + ' ' + EXTRA_ADD).strip()
    keep.setdefault('src', []).append(DROP_SRC)
    was_deals = len(deals)
    data['deals'] = [d for d in deals if d['id'] != DROP_DEAL]
    assert len(data['deals']) == was_deals - 1, 'удалилась не одна карточка'
    data.setdefault('merged', {})[DROP_DEAL] = KEEP_DEAL

    was_comps = len(comps)
    for d in data['deals']:
        for f in REFS:
            if d.get(f) == DROP_COMPANY:
                d[f] = KEEP_COMPANY
    keys = data.get('match_keys', {})
    aliases = [a for a in (keys.get(DROP_COMPANY) or []) if a not in (keys.get(KEEP_COMPANY) or [])]
    if aliases:
        keys[KEEP_COMPANY] = (keys.get(KEEP_COMPANY) or []) + aliases
    keys.pop(DROP_COMPANY, None)
    comps.pop(DROP_COMPANY)
    data.setdefault('merged_companies', {})[DROP_COMPANY] = KEEP_COMPANY
    assert len(comps) == was_comps - 1, 'удалился не один профиль'

    for d in data['deals']:
        refs = [d.get(f) for f in REFS if d.get(f)]
        assert len(refs) == len(set(refs)), 'после слияния компания заняла две роли: %s' % d['id']

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Сделок: %d (было %d). Профилей: %d (было %d).'
          % (len(data['deals']), was_deals, len(comps), was_comps))


if __name__ == '__main__':
    main('--write' in sys.argv)
