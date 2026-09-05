# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gc4c76129` («МТС приобретает TicketsCloud», закрыта, 2023-09-04) —
условия сделки 2023 года были уже подробно описаны; не было судьбы
опциона на полную консолидацию.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/business/1000319 (24.12.2024): «"МТС Лайв" (дочерняя
  организация ПАО "МТС") увеличило долю в ООО "Тикетсклауд" с 85% до
  100%, говорится в данных ЕГРЮЛ»; «Финансовые параметры сделки тогда
  не раскрывались» (о покупке 85% в 2023 году — сумма допвыкупа тоже
  не названа); «сделка предполагала опцион по консолидации актива в
  течение двух лет» — опцион исполнен точно в срок;
- blogs.forbes.ru/2024/04/02/kak-integrirovat-startap-v-korporaciju-
  kejs-ticketscloud-i-mts-live/: «Ticketscloud остался отдельной
  компанией со своим юрлицом, команда не поменялась»; Егор Егерев: «я
  продолжаю работать на должности генерального директора»; «Объединённых
  функций с МТС Live у нас сейчас нет. Мы запланировали плавную
  интеграцию».

НЕ ВНЕСЕНО: (1) цифра «664 млн ₽» за 85%-й пакет — встречается только
у telesputnik.ru со ссылкой на агрегатор «Контур — Фокус», расходится
с уже стоящим в карточке пределом earn-out «до 900 млн ₽» и не
подтверждена ни interfax.ru, ни первоисточником самой сделки —
использовать нельзя без независимого подтверждения; (2) финансовые
показатели TicketsCloud за 2024 год (выручка/прибыль) — найдены только
через WebSearch-сниппет без указания конкретного издания, не первичный
источник, не вносятся; (3) судьба TicketsCloud Ltd (Британские
Виргинские острова) и ООО «Облако билетов» после продажи их доли —
ноль по всем источникам; (4) консультанты — ноль.

Запуск: python3 pipeline/fix_mts_ticketscloud_consolidation.py
        python3 pipeline/fix_mts_ticketscloud_consolidation.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc4c76129'

OLD_ECO_CONTEXT = (
    'В 2018 году МТС уже купила за 3,6 млрд ₽ сразу двух российских '
    'билетных операторов — Ticketland и Ponominalu. В 2020 году '
    'оператор создал отдельную структуру для управления билетным '
    'бизнесом — «МТС Энтертейнмент»; её возглавил сооснователь '
    'Ponominalu Михаил Минин.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В декабре 2024 года МТС довела долю в '
    'TicketsCloud с 85% до 100%, реализовав опцион на полную '
    'консолидацию точно в двухлетний срок; финансовые параметры ни '
    'первой, ни второй сделки не раскрывались. Компания осталась '
    'отдельным юрлицом со своей командой — гендиректор Егор Егерев '
    'сохранил должность и отмечает, что «объединённых функций с МТС '
    'Live... сейчас нет», интеграция «плавная».'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5861955'],
    ['Хабр (со ссылкой на РБК)', 'https://habr.com/ru/news/758758/'],
]
NEW_SRC = OLD_SRC + [
    ['Интерфакс', 'https://www.interfax.ru/business/1000319'],
    ['Forbes', 'https://blogs.forbes.ru/2024/04/02/kak-integrirovat-startap-v-korporaciju-kejs-ticketscloud-i-mts-live/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
