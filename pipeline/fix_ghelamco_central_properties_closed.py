# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g7e90c94a (Ghelamco продаёт складской комплекс в Дмитрове компании
Central Properties) — карточка держала статус «Обсуждается», хотя
собственное поле `law.appr` уже несло цитату о подписанных обязывающих
документах и полученных разрешениях правкомиссии — внутреннее
противоречие.

Проверено лично прямым WebFetch. CRE.ru (21.04.2025, cre.ru/news/98081,
тот же день, что и уже стоящий в карточке источник «Ведомости»): «По
данным источников Ведомостей, компания Ghelamco завершила сделку по
продаже Дмитровского логистического парка площадью 243 тыс. кв. м».
РБК Недвижимость (15.12.2025, realty.rbc.ru/news/693c00079a79475e5b2e7993,
статья про топ-10 закрытых сделок 2025 года): «В десятку крупнейших
сделок на рынке недвижимости уходящего года также попала покупка
российской компанией Central Properties логистического парка в
Дмитрове, который принадлежал бельгийской компании Ghelamco» — сделка
учтена как закрытая сделка ГОДА, спустя восемь месяцев после первого
источника.

`status`: «Обсуждается» → «Закрыта».

НЕ ВКЛЮЧЕНО: точная дата закрытия — ни один источник её не называет
(только «состоялась» / «завершила», без числа). Фактическая
(не оценочная) сумма — по-прежнему не раскрыта нигде, только оценки
консультантов на разных стадиях сделки (14–15,8 млрд ₽, 13–14 млрд ₽,
11 млрд ₽ — все относятся к периоду ДО закрытия, когда искали
покупателя, не к цене закрытия); top-level `sum`/`eco.sum` остаются с
уже стоявшей оценкой 15–18,5 млрд ₽, новую цифру вносить не из чего.
Описание Central Properties (основатели — Денис Степанов и Сергей
Егоров, портфель 2,1 млн м²) не вносится в карточку сделки: профиль
компании (`gce068d4f`) уже несёт собственное описание, дублировать его
здесь значило бы показывать тот же факт под другой подписью.

Запуск: python3 pipeline/fix_ghelamco_central_properties_closed.py
        python3 pipeline/fix_ghelamco_central_properties_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7e90c94a'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

NEW_SRC = [
    ['CRE.ru', 'https://cre.ru/news/98081'],
    ['РБК Недвижимость', 'https://realty.rbc.ru/news/693c00079a79475e5b2e7993'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS

    new_src = deal['src'] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
