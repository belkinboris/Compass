# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `gda6baa02`
(«IBS приобрела разработчика ИТ-решений на базе искусственного
интеллекта Rubbles», август 2026) называла покупателем только бренд
«IBS» текстом (`buyer_name`), а `law.struct` знал лишь продавца
(кипрская SBDA Group Ltd.) — реальное юрлицо-покупатель внутри группы
не было названо вовсе.

Личный WebFetch подтвердил дословно (ComNews, 10 августа 2026,
https://www.comnews.ru/content/246823/2026-08-10/2026-w33/1010/
ibs-poglotila-rubbles): «Группа компания IBS, в лице ООО "УК Центр",
поглотила 100% долей в капитале ООО "Раблз"»; «99,99% капитала "УК
Центр" принадлежит ООО "Цифровые бизнес-системы", которое в свою
очередь контролируется АО "ИБС ИТ Услуги" и Павлом Кутузовым».

ВАЖНО, что НЕ внесено. (1) Выход FinSight Ventures (2024) — уже стоит в
`eco.context`, не новость. (2) Выход Elbrus Capital Fund III — саб-агент
нашёл только КОСВЕННОЕ подтверждение (консолидация долей у одного
продавца к 2026 году), прямой цитаты нет — не вносится. (3) Источник
(ComNews) называет дату закрытия «7 августа 2026», расходясь с уже
стоящей в карточке датой (10 августа, по CNews/TAdviser) — неясно,
какая из дат подписание, а какая объявление; `date` не меняется, пока
это не прояснено отдельно. (4) Найденное противоречие о статусе SBDA
Group Ltd. (TAdviser пишет, что фирма была ликвидирована ещё в 2022
году, а ComNews в 2026-м называет её же продавцом) — саб-агент прямо
рекомендует не переносить это в карточку без проверки ЕГРЮЛ/реестра
Кипра; оставлено на будущее чтение.

Запуск:
    python3 pipeline/fix_ibs_rubbles_buyer_entity_structure.py            # сухой прогон
    python3 pipeline/fix_ibs_rubbles_buyer_entity_structure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_STRUCT = (
    'До сделки 100% долей ООО «Раблз» принадлежали кипрской фирме SBDA '
    'Group Ltd.'
)

NEW_LAW_STRUCT = OLD_LAW_STRUCT + (
    ' Приобретателем выступило ООО «УК Центр» (входит в группу IBS): '
    '99,99% его капитала принадлежит ООО «Цифровые бизнес-системы», '
    'которое контролируется АО «ИБС ИТ Услуги» и Павлом Кутузовым.'
)

NEW_SRC = ['ComNews', 'https://www.comnews.ru/content/246823/2026-08-10/2026-w33/1010/ibs-poglotila-rubbles']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gda6baa02']

    assert d['law'].get('struct') == OLD_LAW_STRUCT, 'law.struct изменился: %r' % (d['law'].get('struct'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('gda6baa02: law.struct дополнен (реальный покупатель — ООО «УК '
          'Центр», цепочка контроля до АО «ИБС ИТ Услуги» и Павла '
          'Кутузова); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
