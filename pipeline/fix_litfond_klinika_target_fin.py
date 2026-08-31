# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g2544a5cb
(Покупка клиник Литфонда бывшими топ-менеджерами Роснефти и МКБ) —
единственный источник карточки уже помечен честно как испорченный
(«Источник не подтверждён (ссылка утеряна при переносе в базу)», ведёт
на статью Ведомостей 2014 года не по теме — см. запись в CLAUDE.md
«Правка, снимающая одну находку, может тихо сломать другой, более
старый инвариант»). Настоящую статью о сделке (2024, покупатели — бывшие
топ-менеджеры «Роснефти» и МКБ) найти не удалось: проверены РБК,
Коммерсантъ, Vademecum, Forbes, mergers.akm.ru, mergers.ru — совпадений
нет. Имена покупателей, продавец, точная сумма, структура и
консультанты остаются честно неизвестными — это НЕ починено и не должно
изображаться починенным.

Единственное, что удалось подтвердить лично прямым WebFetch — финансовые
показатели самого предприятия-цели (ЗАО «Центральная поликлиника
Литфонда», ИНН 7714066169) за 2024 год, из реестрового источника (РБК
Компании, companies.rbc.ru/id/1027739113214-...), не связанного со
сделкой напрямую, но описывающего саму компанию: «выручка за 2024 год —
1 054 330 000 ₽» и «прибыль компании составляет — 114 796 000 ₽».
Это идёт в `eco.target_fin` (стоял прочерком) как факт о ЦЕЛИ, а не о
сделке — отдельным источником, не заменяющим и не чинящим испорченный
`src[0]`.

НЕ ВКЛЮЧЕНО: переименование клиники в 2024 году («Центральная
поликлиника Литфонда» → «Центральная поликлиника на Ленинградке») —
факт подтверждён (ProDoctorov, официальный сайт), но ни один источник
не связывает его прямо со сменой собственника; это осталось бы
недоказанным домыслом, а не перенесённым фактом. Расхождение источников
по имени гендиректора (Checko/list-org называют Сезина А.В., vademec.ru
и rusprofile — Коломенцеву М.В.) — не разрешено, оставлено как есть, в
карточку не вносится.

Запуск: python3 pipeline/fix_litfond_klinika_target_fin.py
        python3 pipeline/fix_litfond_klinika_target_fin.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2544a5cb'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'По данным РБК Компании (реестровые данные, не связаны напрямую со '
    'сделкой), выручка ЗАО «Центральная поликлиника Литфонда» за 2024 '
    'год составила 1 054 330 000 ₽, чистая прибыль — 114 796 000 ₽.'
)

NEW_SRC_RBC = [
    'РБК Компании',
    'https://companies.rbc.ru/id/1027739113214-zao-zakryitoe-aktsionernoe-obschestvo-tsentralnaya-poliklinika-litfonda/',
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN

    new_src = deal['src'] + [NEW_SRC_RBC]

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== src: добавится ===')
    print(NEW_SRC_RBC)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
