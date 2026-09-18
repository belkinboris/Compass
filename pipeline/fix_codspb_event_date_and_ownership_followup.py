# -*- coding: utf-8 -*-
"""18 сентября 2026 — хвост слияния дубля «ЦОД СПб» (продолжение).

Владелец увидел дубль (ge92b1463, mergers.ru) уже сидевшей в базе карточки
gf080e8f0 и велел выкинуть дубль, не потеряв источник. Пока готовился
одноразовый скрипт для межгодовой правки даты (review.py такое не делает —
смена года не проходит через таблицу FIXES никогда), параллельная сессия
рутины «качество» независимо нашла и разобрала ТОТ ЖЕ дубль: поправила
`date` карточки (2025 -> 2026-09-07), убрала дубль из pending.json, добавила
второй источник и свой, тоже верный, отрывок в `eco.context` (про ГК «ЦОД
Эксперт» и Дмитрия Шарова — другая часть того же текста mergers.ru).

Три вещи она не поправила — межгодовая правка ушла только в один из трёх
мест, где стоял тот же неверный год:

1. `events[0].date` — по-прежнему «2025», хотя это то же событие, что и
   `date` карточки (одна сделка, одна дата закрытия).
2. `companies.gcodspb.ownership[0].as_of`/`source` — всё ещё год и источник
   TAdviser, хотя как раз TAdviser точной даты не называл (карточка сама
   это отмечает в `accepted_notes`); as_of обязан совпадать с тем, что
   теперь знает сама сделка.
3. `eco.context` — их отрывок и мой из одного и того же текста mergers.ru
   говорят о РАЗНОМ (они — о консалтинговом партнёре и его руководителе, я —
   о регистрации самого «ЦОД СПб» и втором учредителе, ООО «Управление»,
   70%): оба верны и не дублируют друг друга, дописываю свой следом.

Запуск: python3 pipeline/fix_codspb_event_date_and_ownership_followup.py [--write]
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'gf080e8f0'
COMPANY_ID = 'gcodspb'
CORRECT_DATE = '2026-09-07'

CONTEXT_ADDITION = (
    'ООО «ЦОД СПб» зарегистрировано в Санкт-Петербурге 28 марта 2025 года '
    'с уставным капиталом 20 тыс. рублей. Основными направлениями работ '
    'заявлены деятельность по обработке данных, предоставление услуг по '
    'размещению информации и связанная с этим деятельность. Управляющим '
    'значится Павел Стопкин. Помимо «Сбербанк Инвестиций», в число '
    'учредителей организации на начало сентября 2026-го входит ООО '
    '«Управление» с долей 70%.'
)


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    assert deal['date'] == CORRECT_DATE, \
        'дата карточки другая, чем ожидали: %r' % deal['date']
    assert len(deal['events']) == 1, 'ожидали ровно одно событие'
    assert deal['events'][0]['date'] == '2025', \
        'дата события уже другая: %r' % deal['events'][0]['date']
    assert CONTEXT_ADDITION not in deal['eco']['context'], \
        'этот отрывок уже дописан кем-то ещё'

    company = data['companies'][COMPANY_ID]
    own = company['ownership'][0]
    assert own['id'] == 'gac30cf97' and own['share'] == '30%', \
        'запись ownership не та, что ожидали'
    assert own['as_of'] == '2025', 'as_of уже другой: %r' % own['as_of']
    assert own['source'] == ['TAdviser', 'https://www.tadviser.ru/a/965928'], \
        'source ownership уже другой'

    deal['events'][0]['date'] = CORRECT_DATE
    deal['eco']['context'] = deal['eco']['context'] + ' ' + CONTEXT_ADDITION
    own['as_of'] = CORRECT_DATE
    own['source'] = ['Mergers.ru',
                      'https://mergers.ru/news/Sberbank-kupil-dolyu-v-COD-SPb-87531']

    print('%s: events[0].date 2025 -> %s' % (DEAL_ID, CORRECT_DATE))
    print('%s: eco.context дополнен регистрационными данными' % DEAL_ID)
    print('%s.ownership[0].as_of 2025 -> %s (source: TAdviser -> Mergers.ru)'
          % (COMPANY_ID, CORRECT_DATE))

    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=2)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
