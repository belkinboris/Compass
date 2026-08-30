# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gca369d72 (Wildberries приобретет долю в AliExpress Россия) — карточка
несла год 2024, хотя сама новость («сделка должна быть закрыта к
сентябрю») — про 2026 год, и единственный источник вёл не на статью, а
на профиль Telegram-канала внутри мессенджера MAX. Проверено лично
прямым WebFetch.

Год сделки (2024 → 2026) — НЕ через `review.py`: `date_is_supported()`
допускает только уточнение дня/месяца внутри уже известного года, смена
года — отдельный одноразовый скрипт (правило CLAUDE.md, «review.py не
умеет переносить сделку в другой год»). Дословно (iXBT, 01.06.2026,
16:58): «Wildberries может войти в капитал «AliExpress Россия»»,
«сделка может быть закрыта уже к сентябрю» — публикация датирована
июнем 2026 года, речь о сроке «к сентябрю 2026», а не 2024/2025: карточка
добавлена в базу 23.07.2026 — на полтора месяца позже настоящей даты
новости, что согласуется с июнем 2026, а не с 2024 годом.

`src` заменён: `Max.ru` (`max.ru/svobodakassa`) — это НЕ статья, а
профиль Telegram-канала «Свободная касса» внутри мессенджера MAX, не
подтверждает факт сделки текстом. Заменён на два независимых пересказа
того же источника: РБ.ру и iXBT (оба от 01.06.2026).

Статус «Обсуждается» НЕ меняется — по состоянию на 30 августа 2026 года
(дата этого обыска) заявленный срок закрытия «к сентябрю 2026» ещё не
наступил, ни подтверждения закрытия, ни срыва не найдено ни в одном
источнике (Ведомости от 10.08.2026 пишут про Wildberries/AliExpress
только по другому сюжету — опровержение слухов о «сгоревших товарах»,
сделку о доле не упоминают вовсе).

НЕ ВКЛЮЧЕНО: происхождение СП AliExpress Russia (Mail.ru Group/Alibaba/
МегаФон/РФПИ, 2019, выход МегаФона в 2021) — суб-агент не процитировал
дословно по-русски первоисточник, требует отдельной проверки; изменения
в структуре владения — не найдено, доли Alibaba/USM/VK/РФПИ подтверждены
без изменений; консультанты — не найдены (сделка не подтверждена).

Запуск: python3 pipeline/fix_wildberries_aliexpress_year_and_source.py
        python3 pipeline/fix_wildberries_aliexpress_year_and_source.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gca369d72'

OLD_DATE = '2024'
NEW_DATE = '2026'

OLD_SRC = [['Max.ru', 'https://max.ru/svobodakassa']]
NEW_SRC = [
    ['РБ.ру', 'https://rb.ru/news/wildberries-mozhet-kupit-dolyu-v-aliexpress-rossiya-po-dannym-smi-sdelku-hotyat-zakryt-k-sentyabryu-2026-goda/'],
    ['iXBT', 'https://www.ixbt.com/news/2026/06/01/wildberries-sobiraetsja-kupit-dolju-aliexpress-rossija.html'],
]

OLD_CONTEXT = (
    'В процессе сотрудничества пользователи AliExpress смогут заказать '
    'доставку своих покупок в ПВЗ Wildberries, а с января у части '
    'российских покупателей уже реализована возможность оплаты товаров с '
    'помощью WB Кошелька. В данный момент компании тестируют доступ к '
    'китайским товарам для пользователей Wildberries в России и странах '
    'СНГ.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' По состоянию на 30 августа 2026 года сделка ни подтверждена '
    'закрытой, ни объявлена сорванной — заявленный срок «к сентябрю '
    '2026» ещё не наступил.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['src'] == OLD_SRC
    assert deal['eco']['context'] == OLD_CONTEXT

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== src: станет ===')
    for s in NEW_SRC:
        print(s)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['date'] = NEW_DATE
        deal['src'] = NEW_SRC
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
