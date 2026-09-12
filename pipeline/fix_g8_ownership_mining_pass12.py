# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двенадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, седьмой час подряд).

Тот же расширенный триггер, что и в партиях 9-11. С учётом уже занятых
42 профилей (пассы 1-11) замер дал 245 уникальных компаний-кандидатов —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `gf093eb5c` (ООО «Плодородие», buyer сделки `g09242ae2` — покупатель
  молочного комплекса у концерна «Детскосельский»): в равных долях
  принадлежит Максиму Чистякову и Людмиле Шишлянниковой.
- `ge99563a8` (АТЭК74, target сделки `g66c6db22`): до сделки 100%
  принадлежало «Группе Голос» (материнская структура «Голос.Девелопмент»).
- `ga1d52149` (ООО «Гипфель», target сделки `g5b4a3bf8` — производитель
  булочек United buns): до выхода ресторатора Александра Колобова ему
  принадлежало 90%.
- `g356c40a0` (Уфанет, target сделки `g5e0f6a47`): до сделки принадлежал
  Марату Ахметшину (29,95%), Марату Фаттахову (29,95%), Альфие
  Хазигалеевой (25,67%) и ООО «Уфанетинвест» (14,41%).
- `gcb0948ab` (ООО «Томскводоканал», target сделки `g173f659d`): до
  сделки 80% принадлежало Кириллу Новожилову, 20% — Татьяне Мальцевой.
- `g61f26c16` (ООО «Импульс», buyer сделки `g1e73548b` — покупатель
  завода электрожгутов у Leoni): принадлежит Денису и Илье Черневым.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass12.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass12.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gf093eb5c': [{
        'name': 'Максим Чистяков и Людмила Шишлянникова',
        'id': None,
        'as_of': '2025-09',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/09/12/1138693-kontsern-detskoselskii-prodal-molochnii-kompleks'],
    }],
    'ge99563a8': [{
        'name': '«Группа Голос»',
        'id': None,
        'share': '100%',
        'as_of': '2026',
        'source': ['TAdviser', 'https://www.tadviser.ru/index.php/%D0%9A%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F:%D0%A2%D0%AD%D0%9A74'],
    }],
    'ga1d52149': [{
        'name': 'Александр Колобов',
        'id': None,
        'share': '90%',
        'as_of': '2024',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7445988'],
    }],
    'g356c40a0': [
        {
            'name': 'Марат Ахметшин',
            'id': None,
            'share': '29,95%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6745706'],
        },
        {
            'name': 'Марат Фаттахов',
            'id': None,
            'share': '29,95%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6745706'],
        },
        {
            'name': 'Альфия Хазигалеева',
            'id': None,
            'share': '25,67%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6745706'],
        },
        {
            'name': 'ООО «Уфанетинвест»',
            'id': None,
            'share': '14,41%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6745706'],
        },
    ],
    'gcb0948ab': [
        {
            'name': 'Кирилл Новожилов',
            'id': None,
            'share': '80%',
            'as_of': '2026',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/948569'],
        },
        {
            'name': 'Татьяна Мальцева',
            'id': None,
            'share': '20%',
            'as_of': '2026',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/948569'],
        },
    ],
    'g61f26c16': [{
        'name': 'Денис и Илья Черневы',
        'id': None,
        'as_of': '2024',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/969496'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-11."""
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
