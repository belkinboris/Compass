# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — тринадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, восьмой час подряд).

Тот же расширенный триггер, что и в партиях 9-12. С учётом уже занятых
48 профилей (пассы 1-12) замер дал 240 уникальных компаний-кандидатов —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g9476f043` (Торговый дом «Трэи», buyer сделки `g9a575c07` —
  получатель 35% в гостинице «Пётр I»): принадлежит Диане Саидовой,
  совладелице Русской аграрной группы.
- `g84204bcd` (Герофарм, buyer сделки `gca3a8810` — покупатель доли в
  Группе АЗТ): компанией руководит Пётр Родионов, ему и его семье она и
  принадлежит.
- `gee31f8cf` (ООО «Парус электро», target сделки `g5013525f`): до
  сделки с «Росатомом» принадлежало Владимиру Хлебникову (55%) и Денису
  Павлюку (45%).
- `g5c16aa2d` (Юнион Апарт, buyer сделки `g5d4b3840` — покупатель
  страховой сети «Медэкспресс» у Allianz Group): принадлежит Виктору
  Полугрудову (85%) и Ивану Смирнову (15%).
- `g79decbf9` (Zielinski & Rozen, buyer сделки `g0f7d3941` — покупатель
  участка у ГК «Галс Девелопмент»): на 45% принадлежит Эрезу Розену,
  основателю парфюмерного бренда.
- `g93ffdb3c` (ООО «Санатории Камчатки», buyer сделки `g814d89bf` —
  покупатель санатория «Жемчужина Камчатки»): 65% принадлежит «Реам
  менеджмент» Михаила Сиволдаева, 35% — Корпорации развития Камчатского
  края.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass13.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass13.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g9476f043': [{
        'name': 'Диана Саидова (совладелец Русской аграрной группы)',
        'id': None,
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2023/10/06/999095-u-gostinitsi-petr-i-poyavilsya-novii-sovladelets'],
    }],
    'g84204bcd': [{
        'name': 'Пётр Родионов и его семья',
        'id': None,
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/12/07/1009732-gerofarm-priobrel-49-v-proizvoditele-populyarnogo-lekarstva-protiv-vich'],
    }],
    'gee31f8cf': [
        {
            'name': 'Владимир Хлебников',
            'id': None,
            'share': '55%',
            'as_of': '2024',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6649302'],
        },
        {
            'name': 'Денис Павлюк',
            'id': None,
            'share': '45%',
            'as_of': '2024',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6649302'],
        },
    ],
    'g5c16aa2d': [
        {
            'name': 'Виктор Полугрудов',
            'id': None,
            'share': '85%',
            'as_of': '2023',
            'source': ['РБК', 'https://www.rbc.ru/spb_sz/02/11/2023/6543b6b49a79472c391b4d04'],
        },
        {
            'name': 'Иван Смирнов',
            'id': None,
            'share': '15%',
            'as_of': '2023',
            'source': ['РБК', 'https://www.rbc.ru/spb_sz/02/11/2023/6543b6b49a79472c391b4d04'],
        },
    ],
    'g79decbf9': [{
        'name': 'Эрез Розен (основатель бренда Zielinski & Rozen)',
        'id': None,
        'share': '45%',
        'as_of': '2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6252746'],
    }],
    'g93ffdb3c': [
        {
            'name': '«Реам менеджмент» Михаила Сиволдаева',
            'id': None,
            'share': '65%',
            'as_of': '2025',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6148032'],
        },
        {
            'name': 'Корпорация развития Камчатского края',
            'id': None,
            'share': '35%',
            'as_of': '2025',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6148032'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-12."""
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
