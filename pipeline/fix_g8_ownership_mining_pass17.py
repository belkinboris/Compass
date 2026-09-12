# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — семнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, двенадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-16. С учётом уже занятых
72 профилей (пассы 1-16) замер дал 216 уникальных компаний-кандидатов —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g7d8be4e1` (Алтайская вершина, target сделки `g9602cce9` — покупка
  КЛВЗ «Кристалл»): бренд с 2020 года принадлежит одноимённой компании,
  владелец и гендиректор по ЕГРЮЛ — Александр Казаков.
- `gf922fd85` (Лето Финанс, buyer сделки `gc991514e` — покупка 50% в
  «МедТехСервисе»): по данным ЕГРЮЛ принадлежит Анастасии Романовой.
- `gb44786ff` (Литнет, target сделки `g0bbefe0f` — покупка Олегом
  Новиковым 51%): до сделки принадлежал украинскому предпринимателю
  Сергею Грушко.
- `gpromresurs` (ООО «Промресурс», buyer сделки `ge0cc0dfe` — покупка
  угольного актива у «Северстали»): из Новосибирска, принадлежит Сергею
  Дьяконову.
- `gf9d213b7` (МегаФон, buyer сделки `gc79e6178` — покупка Nexign):
  контролируется холдингом USM.
- `g64d9049e` (Медэкспресс, target сделки `g5d4b3840` — продажа Allianz
  Group петербургской компании Юнион Апарт): зарегистрировано в 1992
  году, до сделки принадлежало Allianz Group.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass17.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass17.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g7d8be4e1': [{
        'name': 'Александр Казаков',
        'id': None,
        'as_of': '2020',
        'source': ['ТАСС', 'https://tass.ru/ekonomika/22653833'],
    }],
    'gf922fd85': [{
        'name': 'Анастасия Романова',
        'id': None,
        'as_of': '2024',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/945677'],
    }],
    'gb44786ff': [{
        'name': 'Сергей Грушко',
        'id': None,
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/04/05/969519-sovladelets-eksmo-ast-oleg-novikov-poluchil-51-v-servise-samizdata-litnet'],
    }],
    'gpromresurs': [{
        'name': 'Сергей Дьяконов',
        'id': None,
        'as_of': '2026',
        'source': ['ПРАЙМ', 'https://1prime.ru/20260904/severstal-873037075.html'],
    }],
    'gf9d213b7': [{
        'name': 'USM (холдинг)',
        'id': None,
        'as_of': '2023',
        'source': ['РБК', 'https://www.rbc.ru/technology_and_media/13/01/2023/63c17ded9a7947853241d24c'],
    }],
    'g64d9049e': [{
        'name': 'Allianz Group',
        'id': None,
        'as_of': '2023',
        'source': ['РБК', 'https://www.rbc.ru/spb_sz/02/11/2023/6543b6b49a79472c391b4d04'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-16."""
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
