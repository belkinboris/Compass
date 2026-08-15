# -*- coding: utf-8 -*-
"""Раунд 9, партия 5 агентов, 15 августа 2026: две карточки, у которых год в
`date` разошёлся с источником — через review.py такая правка не идёт
(`date_is_supported()` намеренно отклоняет смену года, см. CLAUDE.md).

g55a86137 (ГК «Содружество»/ООО «Хозяин») — источник опубликован 15.03.2024
и говорит «в январе стало владельцем» без указания года; по контексту
публикации (март 2024) это январь 2024-го, а не июль 2023-го, как стояло в
карточке. День не назван — в `date` идёт только год, месяц остаётся текстом
в `eco.context` (тот же приём, что уже применён к другим датам-заглушкам).

g4df9c492 (TJX Companies/Familia) — источник (цитата из годового отчёта TJX
через «Ведомости») прямо говорит: «в 2022 году мы объявили и завершили
продажу нашей миноритарной доли в российском розничном магазине Familia».
Карточка стояла 2023-05-29 — это дата, когда «Коммерсантъ» ОБНАРУЖИЛ факт в
отчёте и опубликовал новость, а не дата сделки. Ни один источник не называет
месяц/день — в `date` идёт только год. Заодно чинится испорченная ссылка:
поле `buyer` указывало на профиль ПРЕДМЕТА сделки (gc3a385ba, «Familia
Trading» — тот же объект, что уже верно стоит в `target`), хотя оба
источника прямо пишут, что новый покупатель доли TJX не раскрывается —
предмет вместо стороны, родственный уже описанному в CLAUDE.md классу
дефекта. `buyer` снимается (сторона не названа), а не переносится на
`target` — держать его пустым честнее, чем оставлять неверную ссылку.

ЗАПУСК:
    python3 pipeline/fix_r9_year_corrections.py            # сухой прогон
    python3 pipeline/fix_r9_year_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    d1 = by_id['g55a86137']
    assert d1.get('date') == '2023-07-01', 'g55a86137: date уже другой: %r' % d1.get('date')
    assert d1.get('eco', {}).get('context') == '—', \
        'g55a86137: eco.context уже не заглушка: %r' % d1.get('eco', {}).get('context')

    d2 = by_id['g4df9c492']
    assert d2.get('date') == '2023-05-29', 'g4df9c492: date уже другой: %r' % d2.get('date')
    assert d2.get('buyer') == 'gc3a385ba', 'g4df9c492: buyer уже другой: %r' % d2.get('buyer')

    print('ПРАВИМ g55a86137: date 2023-07-01 -> 2024, eco.context <- «в январе 2024»')
    print('ПРАВИМ g4df9c492: date 2023-05-29 -> 2022, buyer gc3a385ba -> убран (не назван)')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    d1['date'] = '2024'
    d1['eco']['context'] = (
        'Согласно ЕГРЮЛ, «Содружество-Сибирь» стало владельцем ООО «Хозяин» в '
        'январе 2024 года — точный день реестр не называет.')
    src1 = 'https://www.kommersant.ru/doc/6564254'
    existing1 = {str(s[1]) for s in (d1.get('src') or []) if len(s) > 1}
    if src1 not in existing1:
        d1.setdefault('src', []).append(['Коммерсантъ', src1])

    d2['date'] = '2022'
    d2.pop('buyer', None)

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
