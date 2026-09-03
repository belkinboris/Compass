# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g048c2ca3` («Роман Абрамович и партнеры продали Truphone компании TP
Global Operations за 1 фунт стерлингов», закрыта 24.01.2023) —
структура сделки (предпакетированное банкротство), причина продажи
(санкции) и условия (отложенное вознаграждение) не были заполнены.

Проверено лично прямым WebFetch:
- Companies House, https://find-and-update.company-information.service.gov.uk/company/04187081/insolvency:
  «Administration» началась 24 January 2023, закончилась 22 January
  2025 — в тот же день компания перешла в «Creditors voluntary
  liquidation».
- NZ Herald, https://www.nzherald.co.nz/business/companies/banking-finance/roman-abramovich-backed-telecoms-company-truphone-sold-for-1/PRRAVTBQHRFE5N4QAEPEUTDNEM/,
  25.01.2023: санкции против Абрамовича (март 2022) поставили бизнес
  «in limbo»; «15 consecutive years of losses, including £16m in
  2020»; Абрамович владел 23% акций; сделка потребовала проверки на
  национальную безопасность («extensive government review due to
  national security concerns»).
- Mobile News, https://mobilenewscwp.co.uk/News/article/truphone-reportedly-sold-1/,
  13.06.2022: «Sale conditions mean the current owners have agreed to
  invest over £10 million in the business and will receive up to a
  third of the funds they invested if the firm performs well, but
  those sanctioned are exempt from this part of the deal» — то есть
  прежние владельцы (кроме санкционных лиц) сохраняли право на
  отложенное вознаграждение при успехе бизнеса.

Побочно найдено саб-агентом (НЕ перепроверено мной лично прямым
WebFetch — источники Edwin Coe/Davis Polk/FCC, вносится с пометкой):
проданы не 100% акций, а «бизнес и активы» Truphone, причём только
«нероссийская» часть; согласование по UK National Security and
Investment Act 2021 с условием о назначении одобренного государством
директора по информационной безопасности.

НЕ ВКЛЮЧЕНО: точное содержание FCC Consent Decree от 20.10.2022 — сам
документ (PDF) не поддался чтению WebFetch, содержание известно только
через пересказ саб-агента; полная структура владения TP Global
Operations (доли Коча и Куссиоса через цепочку джерсийских холдингов) —
источник тот же, не перепроверен; юрфирма, представлявшая лично
Абрамовича/Абрамова/Фролова в сделке, — не названа ни в одном
источнике.

Запуск: python3 pipeline/fix_truphone_prepack_and_sanctions.py
        python3 pipeline/fix_truphone_prepack_and_sanctions.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g048c2ca3'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Сделка оформлена как pre-pack administration (предпакетированная '
    'процедура банкротства): 24 января 2023 года Truphone Limited '
    'вошла в администрацию, в тот же день проданы бизнес и активы '
    'компании. Юрлицо-оболочка Truphone Limited оставалось в '
    'процедуре до 22 января 2025 года, когда перешло в добровольную '
    'ликвидацию по решению кредиторов.'
)

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'Сделка потребовала лицензии OFSI (санкционный регулятор Минфина '
    'Великобритании) и проверки по британскому Закону о национальной '
    'безопасности и инвестициях — государственная проверка заняла '
    'заметное время до одобрения обоих покупателей.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'Помимо обязательства новых владельцев инвестировать в бизнес, '
    'соглашение предусматривало отложенное вознаграждение прежним '
    'владельцам — до трети вложенных ими средств при успешных '
    'показателях компании, но санкционные лица (включая Абрамовича) '
    'от этой части сделки были отстранены.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Причина продажи — санкции против Абрамовича, введённые в марте '
    '2022 года, из-за которых бизнес оказался «в подвешенном '
    'состоянии»; на момент продажи Truphone накопила 15 лет убытков '
    'подряд, включая £16 млн в 2020 году, а Абрамович (23% акций), '
    'Абрамов и Фролов вложили в компанию более £300 млн.'
)

NEW_SRC = [
    ['Companies House', 'https://find-and-update.company-information.service.gov.uk/company/04187081/insolvency'],
    ['NZ Herald', 'https://www.nzherald.co.nz/business/companies/banking-finance/roman-abramovich-backed-telecoms-company-truphone-sold-for-1/PRRAVTBQHRFE5N4QAEPEUTDNEM/'],
    ['Mobile News', 'https://mobilenewscwp.co.uk/News/article/truphone-reportedly-sold-1/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['appr'] = NEW_LAW_APPR
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
