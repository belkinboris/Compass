# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двадцать вторая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, девятнадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-21. С учётом уже занятых
119 профилей (пассы 1-21) замер дал 181 уникальную компанию-кандидата.
Отобраны семь с однозначным направлением (проверено по
`target`/`buyer`/`seller_id` каждой сделки) и без оговорок источника.

- `g935fdad2` (Highway Operations B.V., target сделки `gff20fb8d` —
  Нацпроектстрой выкупил оставшиеся 50%): нидерландская компания создана
  в 2015 году как паритетное СП французской Vinci Concessions и ПАО
  «Мостотрест» — по 50% у каждого.
- `gfffc5ddd` (ГК «Альянс», buyer сделки `gc681c2b6` — покупка 100%
  «АГ Майнинг» у Kopy Goldfields): принадлежит Мусе Бажаеву.
- `gfcf13ca6` (Kopy Goldfields, seller_id той же сделки): Мусе Бажаеву
  принадлежит 88% самой компании.
- `gf06a3acd` (ГК «Азот», target сделки `gf0ce42ac` — выход Михаила
  Федяева из капитала): по собственному тексту карточки сделка
  закрылась 28 мая 2026 года иначе, чем предполагалось изначально —
  Александр Орехов увеличил долю со 100% (перешедшей через Светлану
  Рыбальченко, сестру Федяева) и стал единственным владельцем. Записан
  ИТОГОВЫЙ факт (Орехов, 100%, на дату закрытия), а не промежуточный
  (Федяев/Рыбальченко) — он устарел бы уже на момент записи.
- `gabdc9810` (ООО «Интикетс», target сделки `g807a5625` — VK купил
  40% билетного сервиса Intickets.ru): на первом этапе сделки (27 июня
  2024 года) ВК получил 15%, доли остальных участников сократились —
  Анна Субчева до 8,5%, Кондратенко до 76,5%.
- `g1fe9e5c0` (GBM Holding, buyer сделки `g5190658a` — покупка 75% BCS
  Prime Brokerage): консорциум контролируют Джеральд Бэнкс (Герман
  Алиев) и Майкл Эббот.
- `gfd02a072` (BCS Prime Brokerage Ltd., target той же сделки): до
  сделки принадлежала Олегу Михасенко через ФГ БКС.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass22.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass22.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g935fdad2': [
        {
            'name': 'Vinci Concessions',
            'id': None,
            'share': '50%',
            'as_of': '2015-2024',
            'source': ['Интерфакс', 'https://www.interfax.ru/russia/1004096'],
        },
        {
            'name': 'ПАО «Мостотрест»',
            'id': None,
            'share': '50%',
            'as_of': '2015-2024',
            'source': ['Интерфакс', 'https://www.interfax.ru/russia/1004096'],
        },
    ],
    'gfffc5ddd': [{
        'name': 'Муса Бажаев',
        'id': None,
        'as_of': '2024',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1016640'],
    }],
    'gfcf13ca6': [{
        'name': 'Муса Бажаев',
        'id': None,
        'share': '88%',
        'as_of': '2024',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1016640'],
    }],
    'gf06a3acd': [{
        'name': 'Александр Орехов',
        'id': None,
        'share': '100%',
        'as_of': '2026-05-28',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8693027'],
    }],
    'gabdc9810': [
        {
            'name': 'ООО «Компания ВК»',
            'id': None,
            'share': '15%',
            'as_of': '2024-06-27',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6686581'],
        },
        {
            'name': 'Анна Субчева',
            'id': None,
            'share': '8,5%',
            'as_of': '2024-06-27',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6686581'],
        },
        {
            'name': 'Кондратенко',
            'id': None,
            'share': '76,5%',
            'as_of': '2024-06-27',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6686581'],
        },
    ],
    'g1fe9e5c0': [{
        'name': 'Джеральд Бэнкс (Герман Алиев) и Майкл Эббот',
        'id': None,
        'as_of': '2024-06',
        'source': ['Bloomberg', 'https://www.bloomberg.com/news/articles/2024-07-09/former-potanin-executive-buys-uk-unit-of-top-russian-brokerage'],
    }],
    'gfd02a072': [{
        'name': 'Олег Михасенко (через ФГ БКС)',
        'id': None,
        'as_of': 'до 2024-06',
        'source': ['Bloomberg', 'https://www.bloomberg.com/news/articles/2024-07-09/former-potanin-executive-buys-uk-unit-of-top-russian-brokerage'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-21."""
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
