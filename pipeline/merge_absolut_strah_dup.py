# -*- coding: utf-8 -*-
"""Слить дубль «Абсолют Страхование сменила владельца».

НАЙДЕНО. `absolut-strah` и `gmru-absolut-strahovanie-owner` — одна и та же
сделка (ОАО «ЦАНЦ» купило 100% «Абсолют Страхования» у группы «Абсолют»
Александра Светакова, закрыта 26 июня 2026 года) под двумя разными id.
Пара задокументирована в CLAUDE.md («Известные проблемы», найдено партией 7
REVISION_BRIEF) как тот же класс, что уже слитые `g1d28507c`/`c391a593b` и
`g5eb6ff22`/`gd7c2b9ee` — «слияние дублей делает отдельный скрипт, а не
review.py».

КТО ОСТАЁТСЯ. `absolut-strah`: 4 источника (РБК, Коммерсантъ, Эксперт,
Банковское обозрение), `buyer`/`target` уже привязаны к профилям компаний
(`canc`/`absolutstrah`), ВСЕ подполя `eco`/`law` заполнены содержательно (ни
одного «—»). `gmru-absolut-strahovanie-owner`: 1 источник (mergers.ru),
`buyer`/`target` не привязаны вовсе, `buyer_name` несёт родовое «Группа
инвесторов» (устаревшая на момент закрытия формулировка — оставшаяся
карточка уже называет покупателя по имени через профиль `canc`).

ЧТО ПЕРЕНЕСЕНО. Только `seller` — у оставшейся карточки это поле было
пустым (`None`), у дубля — текстом «Инвестиционная группа «Абсолют»
(Александр Светаков)», что дословно совпадает с тем, что уже написано в
`eco.rationale` оставшейся карточки («Выход основателя Александра
Светакова (группа «Абсолют») из страхового бизнеса») — независимого факта
не добавляет, просто заполняет структурное поле тем, что уже известно.
Источник дубля (mergers.ru) добавлен в `src`.

ЧЕГО НЕ ПЕРЕНОСИЛ. `buyer_name` дубля («Группа инвесторов») — родовое
описание, а не имя; у оставшейся карточки покупатель уже назван по имени
через профиль компании. Все поля `eco`/`law` дубля (`eco.share`,
`eco.context`, `eco.target_fin`, `law.struct`) — версии тех же фактов,
только у оставшейся карточки эти поля уже заполнены, обогащение дополняет
пустое, а не переписывает заполненное.

ПРОВЕРЕНО ПЕРЕД ЗАПИСЬЮ. `seller` дубля обязан быть ровно тем текстом, что
переносится (assert на исходное состояние). После записи число сделок
уменьшается ровно на одну, `merged['gmru-absolut-strahovanie-owner'] =
'absolut-strah'`.

Запуск:
    python3 pipeline/merge_absolut_strah_dup.py            # сухой прогон
    python3 pipeline/merge_absolut_strah_dup.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP, DROP = 'absolut-strah', 'gmru-absolut-strahovanie-owner'
DROP_SELLER = 'Инвестиционная группа «Абсолют» (Александр Светаков)'
DROP_SRC = ['mergers.ru', 'https://mergers.ru/news/Kompaniya-Absolyut-Strahovanie-smenila-vladelca-87135']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep, 'нет карточки %s' % KEEP
    assert drop, 'нет карточки %s' % DROP
    assert drop.get('seller') == DROP_SELLER, 'seller дубля уже не тот: %r' % drop.get('seller')
    assert keep.get('seller') is None, 'seller оставшейся карточки уже заполнен: %r' % keep.get('seller')

    urls = {s[1] for s in (keep.get('src') or []) if isinstance(s, list) and len(s) > 1}
    src_added = DROP_SRC[1] not in urls

    print('ПЕРЕНОС %-30s -> %-15s' % (DROP, KEEP))
    print('  seller:', DROP_SELLER)
    print('  src:', DROP_SRC if src_added else '(уже есть)')

    before = len(deals)
    if write:
        keep['seller'] = DROP_SELLER
        if src_added:
            keep.setdefault('src', []).append(DROP_SRC)
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
