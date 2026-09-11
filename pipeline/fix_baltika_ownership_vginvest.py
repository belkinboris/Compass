# -*- coding: utf-8 -*-
"""G8 (собственники компании на её странице), 11 сентября 2026 — все
три уровня очереди дочитывания пусты, взят пункт из G-бэклога.

Профиль `baltika» («Пивоваренная компания «Балтика»») не нёс поля
`ownership` вовсе, хотя факт уже известен базе из карточки `baltika`
(сделка «Carlsberg продал «Балтику»: management buy-out через «ВГ
Инвест»») и из сегодняшнего дочитывания карточки `c374fc2ca`.

Личный WebFetch подтвердил дословно:

1) Interfax, 6 декабря 2024, https://www.interfax.ru/business/996240:
   «Пивоваренная компания "Балтика", принадлежавшая датской Carlsberg
   Group, перешла в собственность ООО "ВГ Инвест" (98,65%)».

2) shopandmall.ru, 18 июня 2026,
   https://shopandmall.ru/news/baltika-peresla-pod-polnyj-kontrol-vg-invest:
   «16 июня 2026 года ООО «Хоппи Юнион» вышло из числа совладельцев
   компании»; «доля АО «ВГ Инвест» была увеличена до 174 млн рублей,
   что соответствует 100% уставного капитала «Балтики»».

Записывается САМОЕ СВЕЖЕЕ известное состояние (100%, июнь 2026) — по
той же логике, что и уже стоящие в базе примеры `ownership`: поле
показывает актуальное владение, а не историю смены долей (история
владения остаётся в карточке сделки `baltika` и в `eco.context`
карточки `c374fc2ca`).

Запуск:
    python3 pipeline/fix_baltika_ownership_vginvest.py            # сухой прогон
    python3 pipeline/fix_baltika_ownership_vginvest.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = [
    {
        'name': 'ВГ Инвест',
        'id': 'vginvest',
        'share': '100%',
        'as_of': '2026-06',
        'source': ['shopandmall.ru', 'https://shopandmall.ru/news/baltika-peresla-pod-polnyj-kontrol-vg-invest'],
    }
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']
    items = companies.items() if isinstance(companies, dict) else None

    if items is not None:
        c = companies.get('baltika')
    else:
        c = next((x for x in companies if x.get('id') == 'baltika'), None)

    assert c is not None, 'профиль baltika не найден'
    assert not c.get('ownership'), 'ownership уже занят: %r' % (c.get('ownership'),)

    print('baltika: ownership заполнен (ВГ Инвест, 100%, июнь 2026)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    c['ownership'] = NEW_OWNERSHIP

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
