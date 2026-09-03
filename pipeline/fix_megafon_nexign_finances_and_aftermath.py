# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gc79e6178» («МегаФон купил разработчика биллинга Nexign», закрыта
13.01.2023) — финансы предмета и судьба компании после
внутригрупповой сделки не заполнены.

Проверено лично прямым WebFetch:
- Коммерсантъ, https://www.kommersant.ru/doc/5771650: «Выручка Nexign в
  2021 году составила 9,2 млрд руб., чистая прибыль — 2,4 млрд руб.»;
  «Сделку подтвердили и в самом «МегаФоне», однако ее сумму раскрывать
  отказались».
- РБК-Компании, https://companies.rbc.ru/news/DoOSEFBsXq/megafon-vnedrit-nexign-dra-dlya-povyisheniya-gibkosti-signalnoj-seti/,
  07.11.2025: «Nexign завершила первый этап внедрения решения Nexign
  DRA... в инфраструктуре МегаФона. Проект миграции начался в 2024
  году в рамках программы импортозамещения оператора»; «Новая
  платформа уже обеспечивает обработку 10% сигнального трафика и более
  одного миллиона успешных регистраций в сети в час»; «К концу 2026
  года планируется обеспечить пропускную способность системы в 456 000
  транзакций в секунду».

Побочно найдено и проверено лично прямым WebFetch (Интерфакс,
https://www.interfax.ru/business/880713, 13.01.2023 — раздел «Новости
по теме» ссылается на материал от 28.12.2022): «МегаФон» купил у того
же продавца (ООО «ЮэСэМ Телеком») ещё один актив — «oneFactor»
(«Единый фактор», разработчик аналитических сервисов на базе ИИ) —
то есть сделка с Nexign была частью той же волны внутригрупповой
реструктуризации активов USM в декабре 2022 года, а не отдельным
эпизодом. Точная дата закрытия самой сделки с Nexign в источниках не
названа («в декабре» — Интерфакс), карточка датирована по публикации
РБК (13.01.2023).

НЕ ВКЛЮЧЕНО: доля рынка биллинговых систем (70%) — источник (ComNews)
датирован 2018 годом, не моментом сделки, переносить как актуальную
цифру было бы искажением; выручка Nexign за 2024 год (+20% до 11,5
млрд ₽, по данным TAdviser) — источник недоступен из этой сети,
дословно не подтверждён; согласование ФАС и консультанты сделки — ни
один источник их не упоминает, при внутригрупповой сделке это
правдоподобно, но не доказано.

Запуск: python3 pipeline/fix_megafon_nexign_finances_and_aftermath.py
        python3 pipeline/fix_megafon_nexign_finances_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc79e6178'

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка Nexign в 2021 году составила 9,2 млрд ₽, чистая прибыль '
    '— 2,4 млрд ₽. Клиентами компании являются более 50 '
    'телеком-операторов в 16 странах.'
)

OLD_ECO_CONTEXT = (
    'До выкупа «Мегафоном» компания Nexign принадлежала ООО «ЮэСэМ '
    'Телеком» (входит в холдинг USM, который также контролирует '
    '«Мегафон»). Nexign была создана в 1992 году и имела тогда '
    'название АО «Петер-Сервис».'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В декабре 2022 года «МегаФон» также купил у '
    'того же продавца (ООО «ЮэСэМ Телеком») ещё один актив — 100% '
    'сервиса oneFactor («Единый фактор», объявлено 28 декабря 2022 '
    'года): сделка с Nexign была частью той же волны внутригрупповой '
    'реструктуризации активов USM. После сделки '
    '«МегаФон» сам стал заказчиком Nexign: с 2024 года в рамках '
    'программы импортозамещения внедряет Nexign DRA для маршрутизации '
    'сигнального трафика — к ноябрю 2025 года новая платформа '
    'обрабатывала 10% трафика, к концу 2026 года планируется довести '
    'пропускную способность до 456 000 транзакций в секунду.'
)

NEW_SRC = [
    ['РБК-Компании', 'https://companies.rbc.ru/news/DoOSEFBsXq/megafon-vnedrit-nexign-dra-dlya-povyisheniya-gibkosti-signalnoj-seti/'],
    ['Интерфакс', 'https://www.interfax.ru/business/880713'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
