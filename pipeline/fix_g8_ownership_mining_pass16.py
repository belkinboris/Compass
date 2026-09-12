# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — шестнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, одиннадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-15. С учётом уже занятых
66 профилей (пассы 1-15) замер дал 222 уникальные компании-кандидата —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g936f9597` (Росхим, buyer сделки `g65557c4a` — покупка
  «Кучуксульфата»): до августа 2023 года — «Русский водород», на 100%
  принадлежит ЗПИФ «Квинта»; гендиректор холдинга с 2022 года — Эдуард
  Давыдов.
- `g36510f4e` (ПАО «Новороссийский морской торговый порт» (НМТП), target
  сделки `g672dcca1` — продажа Росимуществом госдоли): государство
  владеет 20% через Росимущество.
- `g9d236ace` (Globaltrans, target сделки `gbb1c889d` — продажа 26,2%
  казахстанскому инвестору): одному из основателей, Андрею Филатову,
  через Marigold Investments принадлежит 11,5% акций.
- `g1fdc3568` (УК «Аэропорты регионов», buyer сделки `g184477ed` —
  покупка аэропорта «Орал» в Уральске): 90% принадлежит В. Резеру, 10% —
  её менеджменту.
- `gcc7851ad` (ООО «Селена», target сделки `g595aca8d` — покупка
  «Кулинарной лавки братьев Караваевых»): до сделки 100% принадлежали
  Евгению Каценельсону и Игорю Моисееву, по 50% каждому.
- `ga3bfdee0` (ООО «Восходагро», target сделки `ga8cb5cab` — покупка
  Группой «Руском»): до сделки принадлежало Борису Мастуненко и Лео
  Шмунку в равных долях.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass16.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass16.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g936f9597': [{
        'name': 'ЗПИФ «Квинта»',
        'id': None,
        'share': '100%',
        'as_of': '2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6043082'],
    }],
    'g36510f4e': [{
        'name': 'Государство (через Росимущество)',
        'id': None,
        'share': '20%',
        'as_of': '2026',
        'source': ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/09/02/1225568-plani-prodat-nmtp'],
    }],
    'g9d236ace': [{
        'name': 'Андрей Филатов (через Marigold Investments)',
        'id': None,
        'share': '11,5%',
        'as_of': '2024',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6453387'],
    }],
    'g1fdc3568': [
        {
            'name': 'В. Резер',
            'id': None,
            'share': '90%',
            'as_of': '2023',
            'source': ['NUR.KZ', 'https://www.nur.kz/politics/universe/2008988-aeroport-uralska-kupila-rossiyskaya-kompaniya/'],
        },
        {
            'name': 'Менеджмент компании',
            'id': None,
            'share': '10%',
            'as_of': '2023',
            'source': ['NUR.KZ', 'https://www.nur.kz/politics/universe/2008988-aeroport-uralska-kupila-rossiyskaya-kompaniya/'],
        },
    ],
    'gcc7851ad': [
        {
            'name': 'Евгений Каценельсон',
            'id': None,
            'share': '50%',
            'as_of': '2023',
            'source': ['РБК', 'https://www.rbc.ru/business/27/03/2023/642050059a79470e6b0e41cd?ysclid=lfsk4d5iwp697037191'],
        },
        {
            'name': 'Игорь Моисеев',
            'id': None,
            'share': '50%',
            'as_of': '2023',
            'source': ['РБК', 'https://www.rbc.ru/business/27/03/2023/642050059a79470e6b0e41cd?ysclid=lfsk4d5iwp697037191'],
        },
    ],
    'ga3bfdee0': [
        {
            'name': 'Борис Мастуненко',
            'id': None,
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5928509'],
        },
        {
            'name': 'Лео Шмунк',
            'id': None,
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5928509'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-15."""
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
