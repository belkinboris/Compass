# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `g9254527a`
(«Компания ресторатора Ферганова приобрела усадьбу в Екатеринбурге», июль
2026) уже называла продавца, сумму и предмет, но не называла УСЛОВИЯ
покупки объекта культурного наследия и не предупреждала, что на тех же
торгах отдельным лотом продавалась ограда усадьбы — за другую сумму,
которую легко спутать с ценой самого дома.

Личный WebFetch подтвердил дословно:
- eanews.ru
  (https://eanews.ru/ekaterinburg/20260630155720/usadba-ryadom-s-zhk-riviera-v-tsentre-ekaterinburga-vystavlena-na-prodazhu):
  «инвестору предстоит соблюдать требования по охране объектов культурного
  наследия»; собственник сможет «приспособить памятник под различные виды
  использования, в том числе под жилье»; отдельным лотом на тех же торгах
  продавались «исторические каменная ограда и парадные ворота усадьбы»
  стоимостью 3,18 млн рублей — это ДРУГОЙ лот, не входит в сумму 135,79
  млн ₽ за дом с гаражом.
- bankinform.ru (https://bankinform.ru/news/142615): «"СтройИнвест" будет
  обязан провести работы по сохранению объекта культурного наследия, то
  есть привести усадьбу в порядок».

Запуск:
    python3 pipeline/fix_delacier_estate_terms_and_lot_caveat.py            # сухой прогон
    python3 pipeline/fix_delacier_estate_terms_and_lot_caveat.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'Покупатель обязан провести работы по сохранению объекта культурного '
    'наследия, то есть привести усадьбу в порядок, и соблюдать требования '
    'по охране памятников; закон разрешает приспособить его под различные '
    'виды использования, в том числе под жильё.'
)

OLD_ECO_CONTEXT = 'Усадьба строилась долго и обрела окончательный облик при купце Евгении Деласье, который купил её в 1889 году.'

NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' На тех же торгах отдельным лотом продавались историческая каменная '
    'ограда и парадные ворота усадьбы — за 3,18 млн ₽, это ДРУГОЙ лот и в '
    'сумму сделки (135,79 млн ₽ за дом с гаражом) не входит.'
)

NEW_SRC = [
    ['Eanews.ru', 'https://eanews.ru/ekaterinburg/20260630155720/usadba-ryadom-s-zhk-riviera-v-tsentre-ekaterinburga-vystavlena-na-prodazhu'],
    ['Bankinform.ru', 'https://bankinform.ru/news/142615'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g9254527a']

    assert d['law'].get('terms') == OLD_LAW_TERMS, 'law.terms уже занят: %r' % (d['law'].get('terms'),)
    assert d['eco'].get('context') == OLD_ECO_CONTEXT, 'eco.context изменился: %r' % (d['eco'].get('context'),)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('g9254527a: law.terms заполнен (обязательство по сохранению ОКН); '
          'eco.context дополнен (честная оговорка про отдельный лот с '
          'оградой, 3,18 млн ₽); добавлено 2 источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['terms'] = NEW_LAW_TERMS
    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
