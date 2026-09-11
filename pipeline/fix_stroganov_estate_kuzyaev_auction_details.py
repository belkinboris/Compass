# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `g8827d795`
(«Бывший топ-менеджер «Лукойла» приобрел старинную усадьбу в Москве»,
июль 2026) уже несла верную итоговую цену (552,6 млн ₽) и имя Андрея
Кузяева (в `extra`), но не называла подробности самих торгов и условие,
на котором победитель получил здание, а `eco.sum` (линза «Экономист»)
не была заполнена, хотя верхнеуровневая `sum` — была (тот же класс, что
уже записан в CLAUDE.md: «Сумма на «Обзоре» и сумма в «Экономисте» — два
разных поля»).

Личный WebFetch подтвердил дословно:
- Mskagency.ru (https://www.mskagency.ru/materials/3559673): «Торги
  прошли 31 июля»; «на лот претендовало три участника»; «победителем
  аукциона признан участник ООО «Рид Ойл», предложивший наибольшую цену
  объекта недвижимого имущества в размере 552 миллиона 608 тысяч
  рублей».
- Msk1.ru (https://msk1.ru/text/gorod/2026/08/06/76568280/): «победитель
  купил здание за 552,6 миллиона рублей, то есть почти в три раза дороже
  стартовой цены»; «До 2019 года здесь находился Московский институт
  телевидения и радиовещания «Останкино» (МИТРО)»; «на здании нет
  таблички об объекте культурного наследия. Ее необходимо будет
  установить до 1 декабря 2026 года»; «возродить облик усадьбы
  Строгановых на Яузе, открыть новый культурный центр притяжения в
  Москве».

Запуск:
    python3 pipeline/fix_stroganov_estate_kuzyaev_auction_details.py            # сухой прогон
    python3 pipeline/fix_stroganov_estate_kuzyaev_auction_details.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SUM = '—'
NEW_ECO_SUM = '552,6 млн ₽'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Торги прошли 31 июля 2026 года, на лот претендовали три участника; '
    'победитель предложил 552,6 млн ₽ — почти втрое выше стартовой цены '
    '198,7 млн ₽.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'На здании нет таблички об объекте культурного наследия — новый '
    'собственник обязан установить её до 1 декабря 2026 года.'
)

OLD_ECO_RATIONALE = (
    'С конца XIX века и до 1930-х годов на территории усадьбы стояли '
    'таможенные склады. Позже складские корпуса перестроили под '
    'административные нужды, а в главном доме долго располагался '
    'Московский институт телевидения и радиовещания «Останкино»'
)

NEW_ECO_RATIONALE = OLD_ECO_RATIONALE + (
    '. Институт съехал в 2019 году; покупатель планирует возродить '
    'облик усадьбы и открыть в здании культурный центр с выставочным '
    'пространством.'
)

NEW_SRC = [
    ['Mskagency.ru', 'https://www.mskagency.ru/materials/3559673'],
    ['Msk1.ru', 'https://msk1.ru/text/gorod/2026/08/06/76568280/'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g8827d795']

    assert d['eco'].get('sum') == OLD_ECO_SUM, 'eco.sum уже занят: %r' % (d['eco'].get('sum'),)
    assert d['law'].get('struct') == OLD_LAW_STRUCT, 'law.struct уже занят: %r' % (d['law'].get('struct'),)
    assert d['law'].get('terms') == OLD_LAW_TERMS, 'law.terms уже занят: %r' % (d['law'].get('terms'),)
    assert d['eco'].get('rationale') == OLD_ECO_RATIONALE, 'eco.rationale изменился: %r' % (d['eco'].get('rationale'),)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('g8827d795: eco.sum заполнен (552,6 млн ₽); law.struct заполнен '
          '(ход торгов — дата, число участников, превышение старта); '
          'law.terms заполнен (обязательство установить табличку ОКН к '
          '1 декабря 2026); eco.rationale дополнен (судьба здания после '
          'института, планы покупателя); добавлено 2 источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['sum'] = NEW_ECO_SUM
    d['law']['struct'] = NEW_LAW_STRUCT
    d['law']['terms'] = NEW_LAW_TERMS
    d['eco']['rationale'] = NEW_ECO_RATIONALE
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
