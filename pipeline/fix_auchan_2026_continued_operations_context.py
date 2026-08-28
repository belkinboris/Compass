# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g17fc21d6 (Auchan продаёт
российский бизнес неизвестному покупателю, статус «Обсуждается» с октября
2024): карточка уже почти два года висит в статусе «Обсуждается» с двумя
опровержениями (январь и декабрь 2025). Дельта-поиск нашёл, что в 2026 году
компания продолжает и расширяет операционную деятельность в России — без
нового формального заявления о судьбе переговоров, но с делами, которые
прямо противоречат версии «сеть уходит»: в апреле 2026 «Ашан» объявил о
планах инвестировать в открытие новых супермаркетов «без участия
французского офиса», а в июне подал заявку на товарный знак для запуска
собственных кафе. Статус НЕ меняется механически (нет прямого заявления,
что переговоры о продаже окончательно прекращены) — только честный
контекст фактического поведения компании. Дословная цитата подтверждена
лично прямым WebFetch.

Запуск: python3 pipeline/fix_auchan_2026_continued_operations_context.py
        python3 pipeline/fix_auchan_2026_continued_operations_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g17fc21d6'

OLD_CONTEXT = (
    'Ранее французская газета La Lettre опубликовала новость о том, что '
    '«Ашан» получил предложение от «Газпромбанка». Предполагаемая сумма '
    'сделки в публикации не приводилась, но, по данным издания, '
    'предложение было отклонено.'
)
CONTEXT_ADDITION = (
    ' Спустя почти два года после первых сообщений о продаже вопрос '
    'формально не решён ни в ту, ни в другую сторону, но фактическое '
    'поведение компании в 2026 году говорит о продолжении работы: в '
    'апреле 2026 «Ашан» объявил, что «планирует расширить бизнес в '
    'России и намерен инвестировать в запуск новых супермаркетов» без '
    'участия французского офиса (producttoday.ru), а в мае подал заявку '
    'на регистрацию товарного знака «Бон Кафе» для запуска собственных '
    'кафе.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['ProductToday', 'https://producttoday.ru/2026/04/03/ashan-planiruet-otkryvat-novye-magaziny-v-rossii/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
