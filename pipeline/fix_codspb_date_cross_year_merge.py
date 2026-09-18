# -*- coding: utf-8 -*-
"""18 сентября 2026 — точная дата сделки «ЦОД СПб» (продолжение слияния дубля).

review.py не переносит сделку в другой год (date_is_supported отказывает
смену года всегда, см. CLAUDE.md) — это отдельный одноразовый скрипт с
assert на исходное состояние, тот же приём, что и у
fix_osnova_sviblovo_date.py и fix_nordline_arctic_sum_misattribution.py.

Карточка gf080e8f0 несла дату «2025» — год без месяца и дня, источник
TAdviser (корпоративная карточка, не датированная новость). Дубль,
пришедший 16 сентября (mergers.ru, карточка предпросмотра ge92b1463,
выкинута владельцем как дубль той же сделки — «про цод спб точно две…
выкидываю, но говорю тебе») дал точную, дословно названную дату закрытия:
«7 сентября 2026 года в распоряжение ООО «Сбербанк Инвестиции»… перешла
30-процентная доля в ООО «ЦОД СПб»». Это не другая сделка: тот же
покупатель (профиль gac30cf97), та же доля (30%), тот же предмет (профиль
gcodspb, ИНН 7810776669) — двух покупок одной и той же доли не бывает,
TAdviser просто не называл точной даты и подставлял год снимка карточки.

Правит: дату сделки и дату события gf080e8f0; поле `as_of` и `source` в
ownership-записи профиля gcodspb (было привязано к тому же неточному году
TAdviser — теперь к точной, подтверждённой дате).

Запуск: python3 pipeline/fix_codspb_date_cross_year_merge.py [--write]
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'gf080e8f0'
COMPANY_ID = 'gcodspb'
OLD_DATE = '2025'
NEW_DATE = '2026-09-07'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    assert deal['date'] == OLD_DATE, 'дата сделки уже другая: %r' % deal['date']
    assert len(deal['events']) == 1, 'ожидали ровно одно событие'
    assert deal['events'][0]['date'] == OLD_DATE, \
        'дата события уже другая: %r' % deal['events'][0]['date']

    company = data['companies'][COMPANY_ID]
    own = company['ownership'][0]
    assert own['id'] == 'gac30cf97' and own['share'] == '30%', \
        'запись ownership не та, что ожидали'
    assert own['as_of'] == OLD_DATE, 'as_of уже другой: %r' % own['as_of']
    assert own['source'] == ['TAdviser', 'https://www.tadviser.ru/a/965928'], \
        'source ownership уже другой'

    deal['date'] = NEW_DATE
    deal['events'][0]['date'] = NEW_DATE
    own['as_of'] = NEW_DATE
    own['source'] = ['Mergers.ru',
                      'https://mergers.ru/news/Sberbank-kupil-dolyu-v-COD-SPb-87531']

    print('%s: date %s -> %s' % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('%s: events[0].date %s -> %s' % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('%s.ownership[0].as_of %s -> %s (source: TAdviser -> Mergers.ru)'
          % (COMPANY_ID, OLD_DATE, NEW_DATE))

    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=2)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
