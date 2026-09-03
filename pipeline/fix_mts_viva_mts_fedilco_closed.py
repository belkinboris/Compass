# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gef104d00` («МТС продает дочернюю компанию Viva-MTS в Армении»,
статус «Обсуждается», объявлена 01.03.2023) — сделка ЗАКРЫЛАСЬ, а
названные в карточке версии покупателя (букмекерская контора 1xBet,
«Газпром») не подтвердились: реальный покупатель — другая компания.

Прежний прогон (`batch_d_n07.py`, комментарий про gef104d00) уже нашёл
закрытие в январе 2024 года покупателю Fedilco Group Limited, но
сознательно оставил карточку как «первый этап» без изменения статуса —
на пересмотре это решение выглядит неверным: перед нами не отдельная,
более поздняя сделка, а ЗАВЕРШЕНИЕ ТОЙ ЖЕ САМОЙ продажи ТОГО ЖЕ
актива, просто растянутое на 10 месяцев из-за отказа регулятора; версии
про 1xBet/«Газпром» из объявления так и остались непроверенными
слухами, и оставлять их на экране как фактическую неопределённость,
когда реальный покупатель давно известен, — вводит читателя в
заблуждение.

Проверено лично прямым WebFetch:
- Коммерсантъ, https://www.kommersant.ru/doc/6466633, 24.01.2024:
  покупатель — «кипрская Fedilco Group Limited, данные о конечных
  бенефициарах которой не разглашаются»; сумма сделки в статье не
  указана, аналитик Тимур Нигматуллин оценивал актив «примерно в 18
  млрд руб.»; дата закрытия — 24 января 2024 года.
- Коммерсантъ, https://www.kommersant.ru/doc/5926470, 10.04.2023:
  первая заявка отклонена Комиссией по регулированию общественных
  услуг Армении — «она не соответствует требованиям, угрожает или
  может угрожать национальной безопасности или государственным
  интересам страны»; МТС получила право на обжалование в течение 30
  дней.
- telecomtalk.info, https://telecomtalk.info/viva-mts-changes-corporate-name-viva-armenia/943755/:
  «starting from March 25, 2024, the company name of Viva-MTS has
  changed. The new company name is "Viva Armenia" Closed Joint Stock
  Company».

Побочно найдено саб-агентом (не перепроверено мной лично прямым
WebFetch в этом прогоне — источники interfax.com/hetq.am, вносится с
пометкой): повторная заявка одобрена в ноябре 2023 года; бенефициары
Fedilco Group — Чжэ Чжан (75%) и Константин Соколов (25%); в январе
2024 года новый владелец объявил о безвозмездной передаче 20% акций
государству Армении «ввиду стратегического значения» компании.

НЕ ВКЛЮЧЕНО: точная сумма сделки (официально не раскрывалась нигде,
независимые оценки расходятся — 18-19 млрд ₽ на разных этапах, поле
`sum`/`eco.sum` НЕ переписано с текущих «21 млрд ₽», это оценка на
момент объявления, отдельная от цены закрытия, которую источники не
называют вовсе); последующая история 20%-й доли государства (право
обратного выкупа за $50 млн) — отдельный, ещё более поздний эпизод,
требующий отдельной проверки, если будет заводиться своя карточка;
консультанты сделки — ни один источник их не называет.

Запуск: python3 pipeline/fix_mts_viva_mts_fedilco_closed.py
        python3 pipeline/fix_mts_viva_mts_fedilco_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gef104d00'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2023-03-01'
NEW_DATE = '2024-01-24'

NEW_BUYER_NAME = 'Fedilco Group Limited (Кипр)'

OLD_EXTRA = (
    'Продажа МТС своей дочерней компании ЗАО «Viva-MTS» (оператор '
    'сотовой связи в Армении с 2 млн абонентов). Сделка ожидает '
    'разрешения Комиссии по регулированию общественных услуг Армении. '
    'Официальные покупатели не раскрыты, источники указывают на двух '
    'претендентов: букмекерскую контору 1Xbet и Газпром.'
)
NEW_EXTRA = (
    'Продажа МТС своей дочерней компании ЗАО «Viva-MTS» (оператор '
    'сотовой связи в Армении с 2 млн абонентов, с 25 марта 2024 года — '
    'ЗАО «Viva Armenia») кипрской Fedilco Group Limited. Сделка закрыта '
    '24 января 2024 года — первая заявка на согласование была отклонена '
    'Комиссией по регулированию общественных услуг Армении в апреле '
    '2023 года по мотивам национальной безопасности, повторная заявка '
    'одобрена в ноябре 2023 года. Ранние версии СМИ о претендентах '
    '(букмекерская контора 1xBet, «Газпром») не подтвердились.'
)

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'Армянский регулятор — Комиссия по регулированию общественных '
    'услуг — отклонил первую заявку в апреле 2023 года по мотивам '
    'национальной безопасности; повторную заявку одобрил в ноябре '
    '2023 года.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Официальная сумма сделки не раскрывалась; независимые оценки '
    'называли актив примерно в 18-19 млрд ₽ на разных этапах. В январе '
    '2024 года новый владелец объявил о безвозмездной передаче 20% '
    'акций государству Армении «ввиду стратегического значения» '
    'компании.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6466633'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5926470'],
    ['telecomtalk.info', 'https://telecomtalk.info/viva-mts-changes-corporate-name-viva-armenia/943755/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['extra'] == OLD_EXTRA
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert 'buyer_name' not in deal

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['extra'] = NEW_EXTRA
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
