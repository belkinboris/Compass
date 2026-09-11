# -*- coding: utf-8 -*-
"""G8 (собственники компании на её странице), 11 сентября 2026 — все
три уровня очереди дочитывания пусты, взят второй пункт из G-бэклога.

Профиль `g2cbdb3e8` («Вамин Р», покупатель российского бизнеса Danone)
не нёс поля `ownership`, хотя факт уже частично известен базе
(карточка `g96da922c` несёт в `extra`: «которой владеют ООО «Вамин
Татарстан» (99%) и Руслан Алисултанов (1%)»).

Личный WebFetch подтвердил дословно (РеалноеВремя,
https://realnoevremya.ru/news/323948-byvshie-aktivy-danone-v-rossii-pereshli-chechencam):
«На момент учреждения компании 25 сентября 2023 года... его владельцами
являлись «Вамин Татарстан» (99%) и Алисултанов (1%)».

Дата фиксируется как дата учреждения (сентябрь 2023) — источник не
подтверждает изменений долей ПОСЛЕ этой даты; смена контроля над самим
«Вамин Татарстан» (Алисултанов консолидировал 100% в декабре 2024,
уже отражено в `g96da922c`) не меняет напрямую зарегистрированную
структуру владения «Вамин Р».

Запуск:
    python3 pipeline/fix_vamin_r_ownership.py            # сухой прогон
    python3 pipeline/fix_vamin_r_ownership.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = [
    {
        'name': 'Вамин Татарстан',
        'id': 'g896e444d',
        'share': '99%',
        'as_of': '2023-09',
        'source': ['РеалноеВремя', 'https://realnoevremya.ru/news/323948-byvshie-aktivy-danone-v-rossii-pereshli-chechencam'],
    },
    {
        'name': 'Руслан Алисултанов',
        'share': '1%',
        'as_of': '2023-09',
        'source': ['РеалноеВремя', 'https://realnoevremya.ru/news/323948-byvshie-aktivy-danone-v-rossii-pereshli-chechencam'],
    },
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']
    c = companies.get('g2cbdb3e8') if isinstance(companies, dict) else \
        next((x for x in companies if x.get('id') == 'g2cbdb3e8'), None)

    assert c is not None, 'профиль g2cbdb3e8 не найден'
    assert not c.get('ownership'), 'ownership уже занят: %r' % (c.get('ownership'),)

    print('g2cbdb3e8 (Вамин Р): ownership заполнен (Вамин Татарстан 99%, '
          'Руслан Алисултанов 1%, сентябрь 2023)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    c['ownership'] = NEW_OWNERSHIP

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
