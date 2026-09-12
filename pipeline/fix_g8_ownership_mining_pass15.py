# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — пятнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, десятый час подряд).

Тот же расширенный триггер, что и в партиях 9-14. С учётом уже занятых
60 профилей (пассы 1-14) замер дал 228 уникальных компаний-кандидатов —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g5cb801c4` (ГК «Лебеди», target сделки `ga5b0724c` — покупка 51% доли
  Тавросом): остальные 49% в «Лебеди» и «Лебеди-Агро» принадлежат
  Александру Шиянову.
- `g30cd8f09` (Трехгорная мануфактура, buyer сделки `g750a2d44` — покупка
  офисного центра «Рочдельская»): 78,49% принадлежит АО «Приоритет»,
  которое также связывают с Дерипаской.
- `gb1cb0cd9` (МД Аудит, target сделки `gaa0ca672` — покупка Softline):
  образовано в марте 2019 года, с сентября 2022 года принадлежало ООО
  «К А М» из Армении.
- `g87315c72` (Уральский турбинный завод, target сделки `g5725678a` —
  покупка Интер РАО): до сделки контролировался Александром Плакидой
  через ООО «Мосэлектрощит» и ООО «Ковровский электротехнический завод».
- `gbd9d5bc1` (En+ Group, buyer сделки `gfeb4e569` — покупка гостиницы
  «Амурский залив»): Олегу Дерипаске принадлежит 44%.
- `gce291e54` (БКХ «Коломенский», buyer сделки `g31541607` — покупка
  ГК «Дарница»): принадлежит Алексею Тулупову, владельцу девелоперской
  группы «Sminex-Интеко».

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass15.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass15.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g5cb801c4': [{
        'name': 'Александр Шиянов',
        'id': None,
        'share': '49%',
        'as_of': '2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6311043'],
    }],
    'g30cd8f09': [{
        'name': 'АО «Приоритет»',
        'id': None,
        'share': '78,49%',
        'as_of': '2024',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6442985'],
    }],
    'gb1cb0cd9': [{
        'name': 'ООО «К А М» (Армения)',
        'id': None,
        'as_of': '2022-09',
        'source': ['Ведомости', 'https://www.vedomosti.ru/technology/articles/2024/06/26/1046177-softline-hochet-rasshiritsya-za-schet-sdelok-ma'],
    }],
    'g87315c72': [{
        'name': 'Александр Плакида (через ООО «Мосэлектрощит» и ООО «Ковровский электротехнический завод»)',
        'id': None,
        'as_of': '2024',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/952888'],
    }],
    'gbd9d5bc1': [{
        'name': 'Олег Дерипаска',
        'id': None,
        'share': '44%',
        'as_of': '2024',
        'source': ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2024/07/08/1048533-en-group-stala-vladeltsem-esche-odnoi-gostinitsi-vo-vladivostoke'],
    }],
    'gce291e54': [{
        'name': 'Алексей Тулупов (владелец группы «Sminex-Интеко»)',
        'id': None,
        'as_of': '2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6174028'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-14."""
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
