# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g5e4677da
(Продажа Александром Клячиным 67% ООО «Бизнес центр «Салют»»
неизвестному физлицу) — карточка год держала статус «Обсуждается» и
называла покупателя «неизвестным физлицом» (только одобрение ФАС
ходатайства). Проверено лично прямым WebFetch (vedomosti.ru,
«Ведомости», 19.01.2026, realty/articles/2026/01/19/1170055-
sozdannaya-sberom-i-vladeltsem-azimut-hotels-kompaniya-prodala-aktiv):
«офис "Салют" на 9000 кв. м на Сущевской улице – связанному с "Альфа
капиталом" ЗПИФ "Союз-инвест"» — глагол в прошедшем времени («перешел»)
относится ко всему перечню активов «КР плюс»/Клячина в этом абзаце,
включая «Салют».

`status`: «Обсуждается» → «Закрыта» — «перешл»/«перешёл» есть в списке
`STATUS_WORDS['Закрыта']` review.py, но правка меняет сразу несколько
взаимосвязанных полей (title/extra/law.appr/buyer_name), поэтому сделана
отдельным скриптом, а не через review.py (тот же приём, что уже применён
к `g809f9155`/«Исток» и `gf13fba9e`/ТПК Челябинск).

`title`/`buyer_name`/`extra`/`law.appr` — «неизвестное физлицо» заменено
на найденного конечного держателя актива. Источник не уточняет, было ли
физлицо, подавшее ходатайство в ФАС, номинальным держателем перед фондом,
или это разные, но последовательные шаги одной сделки — формулировки ниже
не утверждают ни то, ни другое, только называют конечного покупателя.

`eco.context` не менялся: факт про покупателя «Домино» (ЗПИФ «Церера»,
Газпромбанк) уже стоял в карточке ДО этого прогона — та же статья
«Ведомостей» его лишь подтверждает, не добавляет нового.

НЕ ВКЛЮЧЕНО: точная дата закрытия и сумма сделки в источнике не названы
(«Ведомости» также не раскрывают их для соседней сделки по «Авиатору» —
только для неё есть точная дата, «Салюта» это не касается). Цифры «1,6
млрд руб.», «1,92 млрд руб.», встретившиеся при поиске, относятся к
текущим ценам продажи офисных площадей внутри БЦ на риелторских сайтах,
а не к сумме сделки — не использованы.

Запуск: python3 pipeline/fix_klyachin_salut_buyer_and_closed.py
        python3 pipeline/fix_klyachin_salut_buyer_and_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5e4677da'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_TITLE = 'Продажа Александром Клячиным 67% ООО «Бизнес центр «Салют»» неизвестному физлицу'
NEW_TITLE = 'Продажа Александром Клячиным 67% ООО «Бизнес центр «Салют»» ЗПИФ «Союз-инвест»'

OLD_EXTRA = (
    'Одобрение ФАС ходатайства неизвестного физлица на приобретение 67% '
    'ООО «Бизнес центр «Салют»». Сделка ещё не закрыта. На балансе '
    'компании находится офисный комплекс на 9000 кв.м на Сущевской '
    'улице. (ФАС одобрила приобретение (регулятор); покупатель)'
)
NEW_EXTRA = (
    'ФАС одобрила ходатайство на приобретение 67% ООО «Бизнес центр '
    '«Салют»». Сделка закрыта: актив перешёл связанному с «Альфа '
    'капиталом» ЗПИФ «Союз-инвест». На балансе компании находится '
    'офисный комплекс на 9000 кв.м на Сущевской улице. Сумма сделки не '
    'раскрывалась.'
)

OLD_APPR = 'Одобрение ФАС ходатайства неизвестного физлица на приобретение 67% ООО «Бизнес центр «Салют»».'
NEW_APPR = OLD_APPR + (
    ' Сделка закрылась: «офис "Салют" на 9000 кв. м на Сущевской улице – '
    'связанному с "Альфа капиталом" ЗПИФ "Союз-инвест"» (Ведомости, '
    '19 января 2026 года).'
)

NEW_SRC_VEDOMOSTI = [
    'Ведомости',
    'https://www.vedomosti.ru/realty/articles/2026/01/19/1170055-sozdannaya-sberom-i-vladeltsem-azimut-hotels-kompaniya-prodala-aktiv',
]

NEW_BUYER_NAME = 'ЗПИФ «Союз-инвест» (связан с «Альфа капиталом»)'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['title'] == OLD_TITLE
    assert deal['extra'] == OLD_EXTRA
    assert deal['law']['appr'] == OLD_APPR
    assert 'buyer_name' not in deal
    assert deal['buyer'] is None

    new_src = deal['src'] + [NEW_SRC_VEDOMOSTI]

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== title: станет ===')
    print(NEW_TITLE)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== law.appr: станет ===')
    print(NEW_APPR)
    print('\n=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== src: добавится ===')
    print(NEW_SRC_VEDOMOSTI)

    if write:
        deal['status'] = NEW_STATUS
        deal['title'] = NEW_TITLE
        deal['extra'] = NEW_EXTRA
        deal['law']['appr'] = NEW_APPR
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
