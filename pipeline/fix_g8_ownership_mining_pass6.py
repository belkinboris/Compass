# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — шестая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания снова пусты (12 сентября 2026).

Тот же уточнённый метод (слово-триггер и имя профиля — в одном
предложении). С учётом уже занятых 18 профилей (пассы 1-5) замер дал 55
кандидатов; отобраны три с однозначным, не оспариваемым фактом.
Отклонены (тот же класс, что и в прошлые партии): кандидаты с оговоркой
(«не установлен», «неизвестны», «не раскрываются», «оспариваемая» —
«Дельта Холдинг», «Дедал», «Прайм рост», «Саратов-Птица», Фabcell/
Халилов) и случаи, где слово-триггер относится к ДРУГОЙ стороне того же
предложения (Isnad For Business — факт о доле, которую Isnad ПОЛУЧИЛ, а
не о том, кто владеет самим Isnad; «Юнитики» — факт о структуре
покупателя «Олеот», а не о самой «Юнитики»; «Илим»/«Ozon»/«Траст» —
факт относится к другой сущности, совпавшей по подстроке имени).

- `g8a2c05fa` (ООО «Регент Голд», target сделки `g51fbc8c8`): по данным
  ЕГРЮЛ, фирмы «Виолан» (бенефициар Искандар Махмудов) и «Элариум»
  (бенефициар Андрей Бокарев) получили по 4,65% компании.
- `gc5df9ed1` (Marathon Group, seller/сторона сделки `g8a8ae3f7`): доля
  International Restaurant Brands ранее была подконтрольна структуре
  Marathon Group Александра Винокурова — то есть сам Marathon Group
  контролируется им.
- `g260800fc` (ООО «Продукты питания», buyer сделки `g236a9b88`):
  подконтрольно ЗПИФ «Сигнет-Инвестиции 1».

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass6.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass6.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g8a2c05fa': [
        {
            'name': 'ООО «Виолан» (бенефициар — Искандар Махмудов)',
            'id': None,
            'share': '4,65%',
            'as_of': '2024-12',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/1000914'],
        },
        {
            'name': 'ООО «Элариум» (бенефициар — Андрей Бокарев)',
            'id': None,
            'share': '4,65%',
            'as_of': '2024-12',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/1000914'],
        },
    ],
    'gc5df9ed1': [{
        'name': 'Александр Винокуров',
        'id': None,
        'as_of': '2024',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7870292'],
    }],
    'g260800fc': [{
        'name': 'ЗПИФ «Сигнет-Инвестиции 1»',
        'id': None,
        'as_of': '2023-11',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6123358'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-5."""
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
