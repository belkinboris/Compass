# -*- coding: utf-8 -*-
"""Приток 18.09.2026, часовой прогон 14:20 МСК — исправление собственной
ошибки того же прогона. Отвечая на заметку владельца №669, карточка
gf1608a6f была переписана под реальную сделку 2026 года (МТС продала
49,9% БИК фонду «Инвестиции 18» за 21,7 млрд ₽) — но точно такая же
сделка уже была в базе ОТДЕЛЬНОЙ, гораздо лучше проверенной карточкой
`mts-bik` (curated, 03.08.2026, факты подтверждены двумя чтениями
06.09.2026, четыре источника). `facts_derive.py` сам обнаружил
столкновение сразу после записи (`identity.possible_duplicate` появился
у ОБЕИХ карточек взаимно) — это и есть сигнал, который надо было
заметить раньше, чем переписывать `gf1608a6f` с нуля вместо того, чтобы
сначала проверить, нет ли уже готовой карточки об этой же сделке.

Оставляем `mts-bik` (полнее и надёжнее источники), переносим в неё
единственный факт, которого там не было, — историю несостоявшихся
переговоров 2021–2022 годов с внешним консорциумом (это отдельное,
более раннее событие той же сделки, источник Коммерсантъ doc/6312433),
и удаляем `gf1608a6f` с редиректом через `merged`.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

EVENT_2022 = {
    'kind': 'negotiations', 'date': '2022',
    'title': 'Переговоры о продаже консорциуму',
    'note': ('МТС выделила башенные активы в ООО «Башенная инфраструктурная компания» '
             'в сентябре 2021 года и планировала продать актив внешнему консорциуму '
             'финансовых инвесторов в первой половине 2022 года, но из-за '
             'неопределённости на рынке переговоры отложили. Ни один источник не '
             'подтвердил, что именно эти переговоры привели к сделке 2026 года, '
             'описанной ниже, — это разные по составу и структуре сделки.'),
    'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6312433'],
}


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    target = [d for d in deals if d['id'] == 'gf1608a6f']
    assert len(target) == 1, target
    old_card = target[0]
    assert old_card['title'] == 'МТС продала 49,9% башенной инфраструктуры (БИК) фонду «Инвестиции 18»'

    survivor = next(d for d in deals if d['id'] == 'mts-bik')
    assert 'events' not in survivor

    survivor['events'] = [EVENT_2022]
    if not any(s[1] == 'https://www.kommersant.ru/doc/6312433'
               for s in survivor.get('src', []) if len(s) > 1):
        survivor['src'].append(['Коммерсантъ', 'https://www.kommersant.ru/doc/6312433'])

    data['deals'] = [d for d in deals if d['id'] != 'gf1608a6f']
    data.setdefault('merged', {})['gf1608a6f'] = 'mts-bik'

    tp = data.get('telegram_posts', {})
    assert tp.get('gf1608a6f') is None and tp.get('mts-bik') is None, \
        'у одной из карточек есть живой пост в канале — слияние вручную'

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gf1608a6f слита в mts-bik. ЗАПИСАНО.')
    else:
        print('Сухой прогон: слил бы gf1608a6f в mts-bik. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
