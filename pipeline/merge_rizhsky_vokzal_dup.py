# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — дубль карточки о продаже РЖД
Рижского вокзала.

`cf9ca3b8f` («РЖД продает Рижский вокзал в Москве», дата ошибочно «2024»,
источник tass.ru) и `gcc677615` («Продажа РЖД здания Рижского вокзала»,
2026-02-13, уже полностью проработана: указ Мишустина, четыре аукциона,
6 источников) описывают ОДНО И ТО ЖЕ: `cf9ca3b8f`'s текст про «в третий раз
не смогла найти покупателя... на аукцион с начальной ценой 4 млрд ₽ не
поступило ни одной заявки» — это ровно тот же третий аукцион (7 августа
2026 года), который уже описан в `gcc677615`'s `eco.context` («Предыдущий
аукцион 7 августа не состоялся из-за отсутствия заявок»). Уникальных
фактов в `cf9ca3b8f` не нашлось — источник (tass.ru) добавлен в `src`
`gcc677615` как дополнительное подтверждение того же события; поле
`eco.val` карточки-дубля («~1000000000.») — явно повреждённое значение,
не факт, не переносится. `cf9ca3b8f` удаляется из базы (`merged`), запись
FIXES в `pipeline/ingest/fixes/batch_agents100_r5.py`, ссылавшаяся на
удалённую карточку, помечена «СНЯТО».

Запуск:
    python3 pipeline/merge_rizhsky_vokzal_dup.py            # сухой прогон
    python3 pipeline/merge_rizhsky_vokzal_dup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

TASS_SRC = ["ТАСС", "https://tass.ru/ekonomika/22404475"]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    dup = by_id['cf9ca3b8f']
    keep = by_id['gcc677615']

    assert dup is not None, 'cf9ca3b8f не найдена'
    assert keep is not None, 'gcc677615 не найдена'
    assert 'cf9ca3b8f' not in data.get('merged', {}), 'cf9ca3b8f уже в merged'
    existing_src_urls = {s[1] for s in keep['src']}
    assert TASS_SRC[1] not in existing_src_urls, 'tass.ru уже в src gcc677615'

    print('cf9ca3b8f СЛИТА в gcc677615: источник tass.ru добавлен, '
          'уникальных фактов не найдено (дубль описывает тот же 3-й '
          'аукцион, что уже в gcc677615.eco.context)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    keep['src'].append(TASS_SRC)

    data.setdefault('merged', {})['cf9ca3b8f'] = 'gcc677615'
    data['deals'] = [d for d in data['deals'] if d['id'] != 'cf9ca3b8f']

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
