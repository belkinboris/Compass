# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g87234072` («АФК «Система» и Allur рассматривают покупку завода
Volkswagen в Калуге», февраль 2023, «Обсуждается») — ни АФК «Система»,
ни Allur завод не купили: реальным покупателем стала совсем другая
структура.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- vedomosti.ru/business/news/2023/05/23/976370-avilon-zakril-sdelku-po-pokupke-volkswagen:
  покупатель — «ООО «Арт-Финанс», которому принадлежит дилерский центр
  «Авилон»», бенефициар — Андрей Павлович, президент группы «Авилон»;
  сумма — «125 млн евро (по сообщению «Интерфакса»)»; дата закрытия —
  «22 мая 2023 года»; в периметр сделки, помимо завода в Калуге, вошли
  «Volkswagen Group Rus», «Фольксваген компоненты и сервисы», а также
  сервисные и лизинговые структуры Scania; про опцион на обратный выкуп
  статья не сообщает;
- interfax.ru/business/976129: завод возобновил работу под новым
  оператором — «АГР приступил с августа месяца к серийной сборке
  автомобилей и планирует до конца года собрать 27 тыс. автомобилей»;
  «Марки автомобилей, которые будут собирать на предприятии, [замгубернатора
  Калужской области] Попов не уточнил».

Внесено: `status` меняется с «Обсуждается» на «Не состоялась» — не через
`review.py`/FIXES (источники не в локальном кэше притока), а прямым
скриптом с `assert`; ни один источник не подтверждает участие АФК
«Система» или Allur в итоговой сделке — реальный покупатель другой.
`eco.context` дополнен фактом о реальном исходе.

НЕ ВНЕСЕНО: название бренда, под которым завод работает сейчас («AGR
Automotive Group»/«Tenet» в некоторых источниках) — встретилось только
в агрегированной выдаче поиска, не в дословно прочитанной странице,
официальный представитель марки в интервью Interfax прямо отказался
называть; опцион на обратный выкуп для Volkswagen — статья Ведомостей
не подтверждает и не опровергает его наличие.

Запуск: python3 pipeline/fix_vw_kaluga_plant_sold_to_art_finance.py
        python3 pipeline/fix_vw_kaluga_plant_sold_to_art_finance.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g87234072'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Ни АФК «Система», ни Allur завод не купили. Реальным покупателем '
    'всех российских активов Volkswagen (включая завод в Калуге) стало '
    'ООО «Арт-Финанс» бизнесмена Андрея Павловича, президента группы '
    '«Авилон» — сделка на 125 млн евро закрылась 22 мая 2023 года. Завод '
    'возобновил серийную сборку в августе с планом выпустить 27 тыс. '
    'автомобилей до конца года; марки собираемых машин представители '
    'предприятия не раскрывают.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5810668'],
]
NEW_SRC = OLD_SRC + [
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/05/23/976370-avilon-zakril-sdelku-po-pokupke-volkswagen'],
    ['Интерфакс', 'https://www.interfax.ru/business/976129'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
