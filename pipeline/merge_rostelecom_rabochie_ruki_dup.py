# -*- coding: utf-8 -*-
"""Слить дубль «Ростелеком инвестировал в «Рабочие Руки»».

НАЙДЕНО. `g1d28507c` и `c391a593b` — одна и та же сделка (Ростелеком через
«КоммИТ Кэпитал» купил 12,3% сервиса «Рабочие руки» у ФРИИ, закрыта в декабре
2025 года) под двумя разными id. Пара уже стояла в «Известных проблемах»
CLAUDE.md с формулировкой «не слито намеренно — слияние дублей делает
merge_into_one_base.py/ручной скрипт с проверкой match_keys, а не review.py;
это отдельная задача для G-бэклога» — это она.

КТО ОСТАЁТСЯ. `g1d28507c`: 5 источников, `target` привязан к профилю компании
(`g7ce3696d`), заполнены `eco.share/target_fin/rationale/context/finadv` и
`law.adv/terms`. `c391a593b`: 2 источника, `target` пуст, часть тех же полей
заполнена другими словами (пересказ тех же фактов из ЕГРЮЛ и того же интервью
партнёра Orion). Оставлена первая — она полнее и уже связана с профилем
компании.

ЧТО ПЕРЕНЕСЕНО. Только то, чего у оставшейся карточки НЕ БЫЛО (placeholder
«—»): `eco.val` («Размер сделки участники не раскрыли») и `law.struct`
(предложение о структуре выкупа долей ранних инвесторов). Поля, где у
оставшейся карточки УЖЕ есть содержание (rationale, context, share,
target_fin, terms, adv) — не трогаются: это другой пересказ тех же фактов, а
не новый факт (см. CLAUDE.md, «Обогащение дополняет пустое, а не исправляет
заполненное»). Источник дубля (Orion, прямая ссылка на интервью консультанта)
добавлен в `src` оставшейся карточки — этот адрес там раньше не стоял, хотя
на него ссылались текстом внутри `law.adv`.

ПРОВЕРЕНО ПЕРЕД ЗАПИСЬЮ. Значения `eco.val`/`law.struct` дубля обязаны быть
ровно теми, что переносятся (assert на исходное состояние — если кто-то уже
поправил дубль, скрипт упадёт, а не перезапишет). После записи число сделок
уменьшается ровно на одну, `merged['c391a593b'] = 'g1d28507c'`.

Запуск:
    python3 pipeline/merge_rostelecom_rabochie_ruki_dup.py            # сухой прогон
    python3 pipeline/merge_rostelecom_rabochie_ruki_dup.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP, DROP = 'g1d28507c', 'c391a593b'

VAL_ADD = 'Размер сделки участники не раскрыли.'
STRUCT_ADD = ('Одной из особенностей структуры сделки стал выкуп долей ранних частных '
              'инвесторов и частичный выкуп доли инвестора ранней стадии – Фонда развития '
              'интернет-инициатив (ФРИИ), который продал часть своей доли с высокой доходностью')
DROP_SRC = ['Orion', 'https://orion-law.com/news/komanda-orion-vystupila-konsultantom-rostelekom-v-sdelke-po-investirovaniyu-v-servis-platformennoj-zanyatosti-rabochie-ruki']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep, 'нет карточки %s' % KEEP
    assert drop, 'нет карточки %s' % DROP
    assert drop['eco'].get('val') == VAL_ADD, 'eco.val дубля уже не тот: %r' % drop['eco'].get('val')
    assert drop['law'].get('struct') == STRUCT_ADD, 'law.struct дубля уже не тот: %r' % drop['law'].get('struct')
    assert keep['eco'].get('val') == '—', 'eco.val оставшейся карточки уже заполнен: %r' % keep['eco'].get('val')
    assert keep['law'].get('struct') == '—', 'law.struct оставшейся карточки уже заполнен: %r' % keep['law'].get('struct')

    urls = {s[1] for s in (keep.get('src') or []) if isinstance(s, list) and len(s) > 1}
    src_added = DROP_SRC[1] not in urls

    print('ПЕРЕНОС %-12s -> %-12s' % (DROP, KEEP))
    print('  eco.val:', VAL_ADD[:60])
    print('  law.struct:', STRUCT_ADD[:60])
    print('  src:', DROP_SRC if src_added else '(уже есть)')

    before = len(deals)
    if write:
        keep['eco']['val'] = VAL_ADD
        keep['law']['struct'] = STRUCT_ADD
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
