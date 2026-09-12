# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — четырнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, девятый час подряд).

Тот же расширенный триггер, что и в партиях 9-13. С учётом уже занятых
54 профилей (пассы 1-13) замер дал 234 уникальные компании-кандидата —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `gfef0c494` (ГК «Юг Руси», target сделки `gba72051d` — покупка
  Агрокомплексом им. Ткачева): с 10 ноября 2023 года 100% долей принадлежит
  ООО «Ресурс» Камиля Музафарова, он же гендиректор «Юга Руси».
- `g01570552` (ЛВЗ «Саранский», buyer сделки `g7ca174fd` — покупатель
  Спиртзавода «Ромодановский»): входит в холдинг «Мордовалкопром», 50,1%
  долей принадлежит Ларисе Тетиной, 49,9% — Евгению Сидорову.
- `g308a4b2a` (ГАП «Ресурс», buyer сделки `ga95b1d54` — покупатель агрофирмы
  «Рубеж»): крупный производитель курятины, которым владеет Виктор
  Наурузов.
- `gc41515ef` (ЕвроХим, seller_id сделки `g941b547e` — продажа украинских
  «дочек»): зарегистрирован в Цуге (Швейцария), 90% принадлежало Андрею
  Мельниченко на момент сделки (май 2018 года).
- `gca80a12c` (Pioneer Capital Invest, target сделки `gc6448a17` — покупка
  санированного Азиатско-Тихоокеанского банка у ЦБ РФ): на 67,45%
  принадлежит «Назарбаев Фонду».
- `g27010a1f` (Grow Food, target сделки `gaa0f4fb7` — покупка доли Marathon
  Group): юрлицо ООО «ГФ Трейд» принадлежит ООО «Единорог» (1%) и МКООО
  «Винда Лимитед» (99%).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass14.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass14.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gfef0c494': [{
        'name': 'ООО «Ресурс» Камиля Музафарова',
        'id': None,
        'share': '100%',
        'as_of': '2023-11-10',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6196897'],
    }],
    'g01570552': [
        {
            'name': 'Лариса Тетина',
            'id': None,
            'share': '50,1%',
            'as_of': '2025',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7922850'],
        },
        {
            'name': 'Евгений Сидоров',
            'id': None,
            'share': '49,9%',
            'as_of': '2025',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7922850'],
        },
    ],
    'g308a4b2a': [{
        'name': 'Виктор Наурузов',
        'id': None,
        'as_of': '2025',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7497422'],
    }],
    'gc41515ef': [{
        'name': 'Андрей Мельниченко',
        'id': None,
        'share': '90%',
        'as_of': '2018',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/news/2018/05/16/769708-evrohim'],
    }],
    'gca80a12c': [{
        'name': '«Назарбаев Фонд»',
        'id': None,
        'share': '67,45%',
        'as_of': '2021',
        'source': ['Ведомости', 'https://www.vedomosti.ru/finance/news/2021/09/17/887100-kazahstanskii-investor-kupil-u-tsb-aziatsko-tihookeanskii-bank'],
    }],
    'g27010a1f': [
        {
            'name': 'ООО «Единорог»',
            'id': None,
            'share': '1%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6480757'],
        },
        {
            'name': 'МКООО «Винда Лимитед»',
            'id': None,
            'share': '99%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6480757'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-13."""
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']

    pending = {}
    for cid, entries in NEW_OWNERSHIP.items():
        assert cid in companies, 'нет такого профиля: %s' % cid
        current = companies[cid].get('ownership')
        if current:
            assert current == entries, 'ownership уже занят другим значением у %s: %r' % (cid, current)
            continue
        pending[cid] = entries

    if not pending:
        print('Все профили уже заполнены — нечего применять.')
        return

    print('Заполняю ownership: %s' % ', '.join('%s (%s)' % (cid, companies[cid]['name']) for cid in pending))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, entries in pending.items():
        companies[cid]['ownership'] = entries

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
