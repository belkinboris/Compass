# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двадцать четвёртая партия майнинга уже
собранного текста карточек. Три уровня очереди дочитывания снова пусты
(12 сентября 2026, двадцать первый час подряд).

Тот же расширенный триггер, что и в партиях 9-23. С учётом уже занятых
132 профилей (пассы 1-23) замер дал 170 уникальных компаний-кандидатов —
но метод заметно исчерпывается: подавляющее большинство оставшихся
кандидатов относится к уже известным классам отказа (профиль-физлицо,
предложение описывает, ЧТО компания сама держит, а не кто владеет ЕЮ,
пересказ уже известного факта сделки, неоднозначный референт). Партия
меньше обычной (одна запись, а не 6) — честный итог такого прохода, а не
повод занижать планку качества ради размера партии.

- `ge02c264d` (ООО «МПК «Тосненский»», target сделки `g1c47b363` —
  ГК «Таврос» купила 33%): до сделки (декабрь 2024) предприятие
  контролировали Олег Селихов (37%), Екатерина Яснова (36%) и Виктор
  Крылов (27%) — все трое затем полностью вышли из бизнеса.

Отклонённые кандидаты того же прохода (для памяти, не повторять поиск):
`gc4b2178f` (ГК «Эксперт») — текст описывает структуру ООО «Баррель»
(управляющей компании клиник) с внутренним противоречием («доли
распределены поровну между структурами Газпромбанка» сразу после
«Газпромбанк полностью вышел из капитала»); `g1ae3f373` (ООО «Радуга») —
неоднозначный референт местоимения «она»; `ge828c124`/Hilding Anders и
`g354705fa`/Аскона уже заполнены в более раннем проходе.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass24.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass24.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'ge02c264d': [
        {
            'name': 'Олег Селихов',
            'id': None,
            'share': '37%',
            'as_of': 'до 2024-12',
            'source': ['audit-it.ru (данные СПАРК)', 'https://www.audit-it.ru/contragent/1044701893389_ooo-mpk-tosnenskiy'],
        },
        {
            'name': 'Екатерина Яснова',
            'id': None,
            'share': '36%',
            'as_of': 'до 2024-12',
            'source': ['audit-it.ru (данные СПАРК)', 'https://www.audit-it.ru/contragent/1044701893389_ooo-mpk-tosnenskiy'],
        },
        {
            'name': 'Виктор Крылов',
            'id': None,
            'share': '27%',
            'as_of': 'до 2024-12',
            'source': ['audit-it.ru (данные СПАРК)', 'https://www.audit-it.ru/contragent/1044701893389_ooo-mpk-tosnenskiy'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-23."""
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
