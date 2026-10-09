# -*- coding: utf-8 -*-
"""Приток 10:20 МСК 9 октября 2026: ТЦ «Сказка» (40 988 кв. м, Рассказовка,
новая Москва) продан ЗПИФК «Инвестпроф» девелопером «Центр-инвест». Ворота
promote.py не распознали сделку автоматически («не установлен предмет
сделки — из заголовка не видно, что продают»), ложно сочли похожей на
g076af76a (общие слова «владел»/«сменил» — другая, несвязанная сделка про
ИТ-компанию «Здоровье города»). Два источника: Ведомости (первоисточник,
по данным сервиса Asseto — сделка закрыта 6 октября) и Retailer.ru
(перепечатка с дословной цитатой тех же фактов и дополнением про СПАРК-
Интерфакс: оба ЗПИФК с таким названием связаны со структурами MR Group).
Цена не раскрыта — два разных рыночных оценщика дают разные независимые
оценки (NF Group vs Commonwealth Partnership), это не цена сделки, в
eco.context с указанием источника каждой цифры.

Собрано вручную тем же путём, что и другие лоты «Дом.РФ» этого притока
(build_ekaterinburg_dom_rf_card_2026_09_22.py): через pending.json, с
полным прогоном приёмки (accept_card.py) и вторым чтением
(second_reading.py — с 9 октября 2026 обязательно для карточек, принятых
с этого дня).

Запуск: python3 pipeline/build_tc_skazka_2026_10_09.py [--write]
"""
import json
import sys

sys.path.insert(0, 'pipeline/ingest')
import promote  # noqa: E402

PENDING = 'static/data/pending.json'

URL_VEDOMOSTI = ('https://www.vedomosti.ru/realty/articles/2026/10/09/'
                  '1235608-u-torgovogo-tsentra-skazka-vnov-smenilsya-sobstvennik')
URL_RETAILER = 'https://retailer.ru/tc-skazka-v-novoj-moskve-smenil-vladelca/'

DRAFT = {
    'draft_id': 'd-tc-skazka-2026-10-09',
    'title': 'ЗПИФК «Инвестпроф» купил ТЦ «Сказка» в новой Москве у «Центр-инвеста»',
    'date': '2026-10-06',
    'src': [['Ведомости', URL_VEDOMOSTI], ['Retailer.ru', URL_RETAILER]],
    'sum': None,
    'type': 'M&A',
    'status': 'Закрыта',
    'events': [],
    'buyer_name': 'ЗПИФК «Инвестпроф»',
    'asset': 'ТЦ «Сказка» (40 988 кв. м) в Рассказовке, новая Москва',
    'seller': '«Центр-инвест»',
    'parsed_parties': {'buyer': 'ЗПИФК «Инвестпроф»',
                        'asset': 'ТЦ «Сказка» (40 988 кв. м) в Рассказовке, новая Москва',
                        'seller': '«Центр-инвест»'},
    'ind': 'Недвижимость',
    'needs_review': True,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    card['eco']['sum'] = (
        'Цена сделки не раскрывается. Независимые оценки рыночной стоимости '
        'объекта расходятся: Марина Малахатько (NF Group) — 1,7 млрд ₽ без '
        'НДС; в Commonwealth Partnership считают цену выше — 2,5–3,5 млрд ₽.'
    )
    card['eco']['context'] = (
        'Информация о пайщиках фонда-покупателя не раскрывается. По данным '
        '«СПАРК-Интерфакса», существует два ЗПИФК с таким названием, оба '
        'связаны со структурами MR Group: один из них владеет 17,5% в '
        '«Е-девелопмент» (права на реорганизацию промзоны «Автомоторная») и '
        '30% в «Б2-девелопмент» (проект ЖК «Мыс» в Одинцовском районе). ТЦ '
        '«Сказка» — часть транспортно-пересадочного узла «Рассказовка» '
        '(около 300 000 кв. м застройки, включая жилой квартал «Городские '
        'истории» на 220 000 кв. м). В 2022 году столичные власти продали '
        '«Сказку» «Центр-инвесту» ещё не введённым в эксплуатацию объектом; '
        'открытие состоялось в декабре того же года. Среди арендаторов — '
        '«Перекрёсток», «Детский мир», «Рив Гош».'
    )
    card['law']['terms'] = (
        'По данным сервиса Asseto, сделка закрыта 6 октября 2026 года.'
    )
    card['themes'] = ['Коммерческая недвижимость']
    card['pending_since'] = '2026-10-09T10:20:00+00:00'
    if not write:
        print('Сухой прогон. Карточка была бы: %s' % deal_id)
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return
    pending['cards'].append(card)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано: %s добавлена в pending.json' % deal_id)


if __name__ == '__main__':
    main('--write' in sys.argv)
