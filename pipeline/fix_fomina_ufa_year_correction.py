# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gac77519e` («Сеть «Клиники Фомина» приобрела 51% в клинике «Здоровье
женщины и мужчины» в Уфе», Закрыта) — год сделки неверен: карточка
собрана по ретроспективному интервью 2022 года, которое само не
называет дату сделки, а сделка на самом деле закрылась в 2021 году.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- vademec.ru/article/dmitriy_fomin... (уже единственный источник
  карточки, повторно прочитан целиком): интервью опубликовано «23
  ноября 2022» и говорит «В Уфе выкупили 51% в компании, которая
  присутствовала в регионе порядка 13–15 лет» — БЕЗ указания года самой
  сделки. Именно эта дата публикации (2022), видимо, и стала годом
  карточки при разборе — хотя интервью описывает событие в прошлом,
  а не как происходящее в 2022 году.
- vademec.ru/news/2021/03/24/v-sostav-kliniki-fomina-voshla-set-
  tsentrov-eko-iz-bashkirii/ (НОВЫЙ источник, независимая современная
  публикация, опубликована 24.03.2021): «управляющая сетью «Клиника
  Фомина» компания «КДФ Групп» выкупила 51% долей в уфимском ООО «ЦМТ»»
  — головная компания сети «Здоровье женщины и мужчины»; «в 2020 году
  выручка сети «Здоровье женщины и мужчины» (ООО «ЦМТ» и ООО «Уфа
  Доктор») составила 206 млн рублей».

Год меняется НЕ через review.py (`date_is_supported()` намеренно
отклоняет смену года — см. прецедент `fix_osnova_sviblovo_date.py` в
CLAUDE.md), а отдельным скриптом с `assert` на исходное состояние.

НЕ ВНЕСЕНО: имя продавца — реестровые агрегаторы (checko.ru,
rusprofile.ru) недоступны напрямую (403), а связь нынешней совладелицы
Эльзы Фазлыевой с продажей 2021 года не подтверждена дословным чтением
первоисточника, только косвенным совпадением (она фигурирует как
«главный врач клиники» на сайте сети) — это осталось бы домыслом.

Запуск: python3 pipeline/fix_fomina_ufa_year_correction.py
        python3 pipeline/fix_fomina_ufa_year_correction.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gac77519e'

OLD_DATE = '2022'
NEW_DATE = '2021-03-24'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Дата сделки уточнена: единственный источник карточки — ретроспективное '
    'интервью основателя (ноябрь 2022 года), которое само не называет год '
    'сделки, а независимая публикация того же издания от 24 марта 2021 года '
    'подтверждает закрытие сделки этой датой; выручка сети «Здоровье женщины '
    'и мужчины» за 2020 год — 206 млн ₽.'
)

OLD_SRC = [
    ['Vademecum', 'https://vademec.ru/article/dmitriy_fomin-_-nash_plan_-_vyrastit_kompaniyu_s_kapitalizatsiey_v_-1_mlrd-_osnovatel_-kliniki_fomin/'],
]
NEW_SRC = [
    ['Vademecum', 'https://vademec.ru/news/2021/03/24/v-sostav-kliniki-fomina-voshla-set-tsentrov-eko-iz-bashkirii/'],
] + OLD_SRC


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
