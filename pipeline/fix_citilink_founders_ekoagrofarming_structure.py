# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `g692dcc6b`
(«Создатели «Ситилинка» купили долю в производителе картошки для чипсов
Lay's», август 2026) держалась на ОДНОМ источнике (mergers.ru); второй
независимый источник и реестровая проверка подтвердили структуру и
добавили важный факт о недолгом владении продавца.

Личный WebFetch/реестр подтвердили дословно:
- Sostav.ru (второй независимый источник,
  https://www.sostav.ru/publication/sozdateli-sitilinka-kupili-dolyu-v-proizvoditele-kartoshki-dlya-chipsov-lays-85859.html):
  «Алексей Абрамов, Владислав Мангутов и Олег Карчев получили по 33,33%
  долей в компании «Ремтехно»... 49% в производителе картофеля
  «Экоагрофарминг», 100% в «Экоагрофарминг Берново» и 100% в компании
  «Грин фьюлз»» — независимо подтверждает те же доли, что и mergers.ru.
- Audit-it.ru (реестр, https://www.audit-it.ru/contragent/1227700519617_ooo-remtekhno):
  «24.04.2026 — новый учредитель АО «ЕТС»... 30.07.2026 — текущие три
  физических лица стали учредителями» — АО «ЕТС» владело «Ремтехно»
  чуть более трёх месяцев, то есть было промежуточным держателем перед
  продажей, а не долгосрочным профильным собственником.
- Mergers.ru (уже в `src`): «Основная доля 50,87% в «Экоагрофарминге»
  принадлежит основателю — Олегу Игнатову» — остаток пакета помимо 49%
  «Ремтехно» держит сам основатель компании.

Сумма сделки и мотивы сторон ни в одном из проверенных источников
(mergers.ru, sostav.ru) не названы — честная пустота, не заполняется.

Запуск:
    python3 pipeline/fix_citilink_founders_ekoagrofarming_structure.py            # сухой прогон
    python3 pipeline/fix_citilink_founders_ekoagrofarming_structure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'По данным реестра, продавец, АО «ЕТС», владел «Ремтехно» лишь с '
    '24 апреля по 30 июля 2026 года — то есть был промежуточным '
    'держателем перед продажей, а не долгосрочным собственником. '
    'Оставшиеся 50,87% в самом «Экоагрофарминге» (помимо 49% через '
    '«Ремтехно») принадлежат основателю компании Олегу Игнатову.'
)

NEW_SRC = ['Sostav.ru', 'https://www.sostav.ru/publication/sozdateli-sitilinka-kupili-dolyu-v-proizvoditele-kartoshki-dlya-chipsov-lays-85859.html']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g692dcc6b']

    assert d['law'].get('struct') == OLD_LAW_STRUCT, 'law.struct уже занят: %r' % (d['law'].get('struct'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g692dcc6b: law.struct заполнен (недолгое владение АО «ЕТС», '
          'доля основателя Игнатова); добавлен второй независимый '
          'источник (sostav.ru)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
