# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `c3e0b0e8f`
(«Присоединение ООО «Глобус» к АО «Авиакомпания «Сибирь»» (реорганизация)»,
2023) не объясняла, ПОЧЕМУ именно «Глобус» присоединили: карточка знала
только про заморозку проекта Citrus в июне 2022 года, но не связь
самого «Глобуса» с этим проектом.

Личный WebFetch подтвердил дословно (Ведомости, 30 июня 2023,
https://www.vedomosti.ru/business/news/2023/06/30/983069-s7-obedinit-aviakompanii-globus-sibir):
«"Глобус" был создан в 2008 г. для развития внутри холдинга чартерных
перевозок. Позже, в начале февраля 2022 г., лоукостер Citrus получил
сертификат эксплуатанта именно на базе юридического лица «Глобус»»;
«Решением единственного акционера АО "Авиакомпания "Сибирь" принято
решение о реорганизации в форме присоединения к нему общества с
ограниченной ответственностью "Глобус"». В результате «Глобус»
прекратит деятельность.

Присоединение 2023 года — техническое закрытие юрлица неудавшегося
проекта, а не отдельная коммерческая сделка. Более поздних новостей о
возрождении Citrus не нашлось.

Запуск:
    python3 pipeline/fix_s7_globus_citrus_merger_reason.py            # сухой прогон
    python3 pipeline/fix_s7_globus_citrus_merger_reason.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_ECO_RATIONALE = (
    '«Глобус» был создан в 2008 году для чартерных перевозок внутри '
    'холдинга S7, а в феврале 2022 года на его базе лоукостер Citrus '
    'получил сертификат эксплуатанта. После заморозки проекта в июне '
    '2022 года юрлицо не понадобилось — присоединение 2023 года '
    'формально закрывает его, а не описывает отдельную сделку.'
)

NEW_SRC = ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/06/30/983069-s7-obedinit-aviakompanii-globus-sibir']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c3e0b0e8f']

    assert d['eco'].get('rationale') is None, 'eco.rationale уже занят: %r' % (d['eco'].get('rationale'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('c3e0b0e8f: eco.rationale заполнен (связь «Глобуса» с Citrus, '
          'мотив присоединения); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['rationale'] = NEW_ECO_RATIONALE
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
