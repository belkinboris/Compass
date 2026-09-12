# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — девятая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания снова пусты (12 сентября 2026,
четвёртый час подряд).

Метод РАСШИРЕН по итогам предыдущего часа: узкий триггер («бенефициар»/
«подконтролен»/«конечный владелец») исчерпал кандидатов (партия 8 дала
ноль новых). Добавлены триггеры «принадлежит»/«принадлежал»/«владеет» —
слова более общие и потому более шумные, замер дал 322 срабатывания
против 38 уникальных компаний (было 26 у узкого триггера). Отобраны три
с однозначным направлением (предложение — именно о ТОЙ стороне сделки, к
которой привязан профиль, а не о соседней сущности в том же предложении)
и без оговорок.

Отклонены (тот же класс направления, что и раньше, только на новом
триггере): Wink (`g050522dd`) — факт о пред-сделочных владельцах ЛайфСтрим
(цели), не самого Wink; Займер (`gd51874a0`) — факт о владельце БЭСТ
(цели), не Займера; VEON (`gc6434a72`) — предложение говорит, ЧЕМ владеет
VEON (Вымпелкомом), а не кто владеет самим VEON; аналогично отклонены
ГК «Евростройконсалт» (описание рода деятельности, не владения),
Elbrus Capital (факт о доле в HeadHunter, не в самом фонде), ВТБ Капитал/
АФК «Система» (факт о структуре сделки, не о владении самими профилями).

- `gf9a640d2` (Башнефть, target сделки `gf6232eec`): до сделки
  «Роснефти» принадлежало 57,66% уставного капитала, ещё 4,41% —
  ООО «Башнефть-Инвест».
- `g58575e9c` (ООО «Новые технологии», buyer сделки `g5bb3e777` —
  покупатель российского бизнеса Essity): Игорь Шилов владеет 94,5%,
  Андрей Яновский — 5,5%.
- `gd685b926` (ВымпелКом/«Билайн», target сделки `g64a94e27` — MBO):
  до выкупа менеджментом компания принадлежала VEON.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass9.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass9.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gf9a640d2': [
        {
            'name': 'Роснефть',
            'id': None,
            'share': '57,66%',
            'as_of': '2026-06',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/1098261'],
        },
        {
            'name': 'ООО «Башнефть-Инвест»',
            'id': None,
            'share': '4,41%',
            'as_of': '2026-06',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/1098261'],
        },
    ],
    'g58575e9c': [
        {
            'name': 'Игорь Шилов',
            'id': None,
            'share': '94,5%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6110116'],
        },
        {
            'name': 'Андрей Яновский',
            'id': None,
            'share': '5,5%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6110116'],
        },
    ],
    'gd685b926': [{
        'name': 'VEON',
        'id': 'gc6434a72',
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/news/2022/11/24/951964-veon-prodala-vimpelkom-rossiiskomu-menedzhmentu'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-8."""
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
