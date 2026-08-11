# -*- coding: utf-8 -*-
"""Тридцать шестая партия: 8 описаний + починка имени профиля-лота.

ДЕФЕКТ. Профиль `gf546bfdb` носил имя «Букет Чувашии» и «Булгарпиво» —
но БЕЗ первой открывающей и последней закрывающей кавычки:
`Букет Чувашии» и «Булгарпиво`. Сделка (Балтика купила два пивных
завода одним лотом) — ровно тот случай, для которого сделан признак
`lot` (CLAUDE.md, «Лоту вместо разбиения ставится признак `lot`»); у
профиля признака не было вовсе. Починено: имя дополнено недостающими
кавычками, `lot: true` проставлен (родня уже описанного в прошлой
партии профиля «Транслес»/«Грузовая компания», где признак стоял
верно), добавлено описание.

ЧТО ДЕЛАЕТ. 7 описаний обычных профилей + 1 профиль-лот (починка имени,
признак `lot`, описание).

Запуск:
    python3 pipeline/fix_lot_name_quotes_and_describe_batch36.py            # сухой прогон
    python3 pipeline/fix_lot_name_quotes_and_describe_batch36.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

LOT_ID = 'gf546bfdb'
LOT_OLD_NAME = 'Букет Чувашии» и «Булгарпиво'
LOT_NEW_NAME = '«Букет Чувашии» и «Булгарпиво»'
LOT_DESC = ('Два пивоваренных завода — «Букет Чувашии» и «Булгарпиво»; в '
            '2023 году куплены «Балтикой» одним лотом.')

DESCRIPTIONS = {
    'gf32882b4': 'Предприниматель; в 2023 году выкупил у Freedom '
                 'Holding Corp. его российский брокерский и банковский '
                 'бизнес («Фридом Финанс»).',
    'gfc87f1dd': 'Бизнес-центр в Киеве, продан с баланса ликвидируемого '
                 'ВТБ Банк Украина на аукционе Фонда гарантирования '
                 'вкладов в 2019 году.',
    'gfb14be3f': 'Бизнес-центр на Свердловской набережной в '
                 'Санкт-Петербурге (около 11 100 кв. м), напротив '
                 'Смольного собора.',
    'gfb0dc8c7': 'Китайский бизнесмен, председатель Trinity Group; в '
                 '2023 году довёл долю в производителе велосипедов '
                 'Forward (ООО «Спэйс») до контрольной (66%).',
    'gf39853bc': 'Российский покупатель заводов испанской Roca Group — '
                 'производства сантехнической керамики и мебели для '
                 'ванных комнат.',
    'gf192cc52': 'Издатель настольных игр («Имаджинариум», «500 злобных '
                 'карт»); в 2022 году выкуплен конкурентом Cosmodrome '
                 'Games.',
    'gf17bdbe6': 'Лизинговая компания (операционный лизинг '
                 'железнодорожных вагонов); в 2023 году продана '
                 'менеджментом через инвестфонды.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    lot = comps[LOT_ID]
    assert lot['name'] == LOT_OLD_NAME, 'имя лота %s уже другое: %r' % (LOT_ID, lot['name'])
    assert not lot.get('lot'), 'признак lot у %s уже стоит' % LOT_ID
    print('  ИМЯ ЛОТА %s: %r -> %r' % (LOT_ID, LOT_OLD_NAME, LOT_NEW_NAME))
    print('  ПРИЗНАК lot -> True')
    if write:
        lot['name'] = LOT_NEW_NAME
        lot['lot'] = True
        lot['desc'] = LOT_DESC
    print('  ОПИСАНИЕ %-12s %-30s %s' % (LOT_ID, LOT_NEW_NAME[:30], LOT_DESC[:50]))

    wrote, skipped = 1, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-30s %s' % (cid, str(c.get('name'))[:30], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
