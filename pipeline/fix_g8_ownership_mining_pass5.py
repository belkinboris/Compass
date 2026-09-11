# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — пятая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания пусты седьмой час подряд.

Тот же уточнённый метод (слово-триггер и имя профиля — в одном
предложении). С учётом уже занятых 14 профилей (пассы 1-4) замер дал 60
кандидатов; отобраны четыре с однозначным, не оспариваемым фактом.
Отклонены: кандидаты с оговоркой («не установлен», «неизвестны»,
«не раскрываются», «оспариваемая» — Говор/Каноков, «Дедал», «Прайм
рост», «Саратов-Птица»); случаи, где слово-триггер относится к ДРУГОЙ
стороне того же предложения, а не к проверяемому профилю (например,
«Ростелеком передал долю в «Булате» подконтрольной компании «Рестрим»» —
факт о «Рестриме», а не о самом «Булате»; «Траст» — предложение о
истории актива-здания, а не о структуре владения самим банком).

- `g5d077374` (Евроонко, buyer сделки `ga75a4d0a`): прямым покупателем
  выступило АО «Тетра» — структура Евгения Туголукова, конечного
  бенефициара «Евроонко» (Коммерсантъ).
- `ga16d4baa` (Ароса-Логистика, buyer сделки `cea87de0a`): бенефициар —
  Василий Цветков (Коммерсантъ).
- `g3817a50b` (ООО «Стинн» — сам профиль покупателя сделки `g3e7bc840`,
  торгуется как «Russ Outdoor»): бенефициар — Григорий Садоян (уже
  назван в `desc` профиля — перенос в структуру).
- `gd1e424d0` (ООО «Медиа-1 Аутдор», target той же сделки): ДО сделки —
  единственный владелец головной структуры Gallery, ООО «Гэллари
  сервис»; конечный бенефициар — инвесткомпания Kismet Capital Group
  Ивана Таврина (Ведомости).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass5.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass5.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g5d077374': [{
        'name': 'Евгений Туголуков (через АО «Тетра»)',
        'id': None,
        'as_of': '2025-06',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8463640'],
    }],
    'ga16d4baa': [{
        'name': 'Василий Цветков',
        'id': None,
        'as_of': '2024-11',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7330299'],
    }],
    'g3817a50b': [{
        'name': 'Григорий Садоян',
        'id': None,
        'as_of': '2023-06',
        'source': ['Ведомости', 'https://www.vedomosti.ru/media/articles/2023/06/23/982081-russ-outdoor-gallery'],
    }],
    'gd1e424d0': [{
        'name': 'Kismet Capital Group (Иван Таврин), до сделки',
        'id': 'ga2d76207',
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/media/articles/2023/06/23/982081-russ-outdoor-gallery'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-4."""
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
