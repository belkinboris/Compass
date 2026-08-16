# -*- coding: utf-8 -*-
"""Слить дубль «Росатом выкупает 51% ГК «Дело» у Шишкарева».

НАЙДЕНО. `g5eb6ff22` и `gd7c2b9ee` — одна и та же сделка (решение «Росатома»
от 6 июля 2026 выкупить 51% ГК «Дело» у Сергея Шишкарева по итогам «русской
рулетки») под двумя разными id. Пара задокументирована в CLAUDE.md («Известные
проблемы») как найденная саб-агентом партии 5 REVISION_BRIEF и намеренно НЕ
слитая — «слияние ждёт своей очереди в G-бэклоге». Это она.

КТО ОСТАЁТСЯ. `g5eb6ff22`: 6 источников, заполнены обе линзы целиком (eco:
sum/share/val/fin/rationale/context/finadv; law: struct/appr/adv/terms).
`gd7c2b9ee`: 1 источник (Forbes), из содержания — только `sum`. Оставлена
первая — она несравнимо полнее.

ЧТО НЕЛЬЗЯ ПОТЕРЯТЬ. У `gd7c2b9ee` — и только у неё — `target` привязан к
профилю компании «Дело» (`delo`); у `g5eb6ff22` `target` был пуст, хотя
профиль `delo` уже используется как сторона в других сделках той же саги
(`g6a4b0a2a`, `g24e6d8ee`, `cdfe91cd0`). Это перенесено на оставшуюся
карточку — иначе профиль компании «Дело» продолжал бы не знать об этой
сделке. Источник (Forbes) добавлен в `src` — там его не было.

ЧЕГО НЕ ПЕРЕНОСИЛ. `sum` дубля («77 млрд ₽») — частный случай уже более
точного `74–77 млрд ₽ (диапазон предложения)» у оставшейся карточки (77 —
это как раз итоговая цена продажи доли Шишкарева внутри уже описанного
диапазона, см. `eco.share`). Остальные поля `eco`/`law` дубля — сплошные
placeholder «—», переносить нечего.

ПРОВЕРЕНО ПЕРЕД ЗАПИСЬЮ. `target` и `sum` дубля обязаны быть ровно теми, что
ожидаются (assert на исходное состояние). После записи число сделок
уменьшается ровно на одну, `merged['gd7c2b9ee'] = 'g5eb6ff22'`.

Запуск:
    python3 pipeline/merge_rosatom_delo_shishkarev_dup.py            # сухой прогон
    python3 pipeline/merge_rosatom_delo_shishkarev_dup.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP, DROP = 'g5eb6ff22', 'gd7c2b9ee'
DROP_TARGET = 'delo'
DROP_SUM = '77 млрд ₽'
DROP_SRC = ['Forbes', 'https://www.forbes.ru/biznes/564428-rosatom-resil-vykupit-dolu-sergea-siskareva-v-gruppe-delo']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep, 'нет карточки %s' % KEEP
    assert drop, 'нет карточки %s' % DROP
    assert drop.get('target') == DROP_TARGET, 'target дубля уже не тот: %r' % drop.get('target')
    assert drop.get('sum') == DROP_SUM, 'sum дубля уже не тот: %r' % drop.get('sum')
    assert keep.get('target') is None, 'target оставшейся карточки уже заполнен: %r' % keep.get('target')
    assert DROP_TARGET in data['companies'], 'профиля %s нет в базе' % DROP_TARGET

    urls = {s[1] for s in (keep.get('src') or []) if isinstance(s, list) and len(s) > 1}
    src_added = DROP_SRC[1] not in urls

    print('ПЕРЕНОС %-12s -> %-12s' % (DROP, KEEP))
    print('  target:', DROP_TARGET)
    print('  src:', DROP_SRC if src_added else '(уже есть)')

    before = len(deals)
    if write:
        keep['target'] = DROP_TARGET
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
