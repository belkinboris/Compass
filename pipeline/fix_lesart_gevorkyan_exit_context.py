# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g016f1b13 (Vizant/LesArt Resort): дельта-
поиск нашёл, что «возможный конечный владелец» Вазген Геворкян,
названный в `extra` с оговоркой, вышел из этого актива и продал свою
долю ещё в 2023 году — за два года до сделки с Vizant (2025). Не
меняем `extra` механически (нет прямой цитаты «Геворкян не бенефициар
на момент сделки», только факт продажи доли в 2023-м, из которого это
следует) — добавляем факт в `eco.context`, решение о правке `extra`
оставляем человеку. Не через `review.py`: два источника (msk1.ru про
структуру владения, Коммерсантъ про биографию Геворкяна) не образуют
с уже записанным текстом `eco.context` (пресс-релиз Vizant) непрерывный
кусок.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
https://msk1.ru/text/incidents/2024/11/13/74329517/
https://www.kommersant.ru/doc/7497718

Запуск: python3 pipeline/fix_lesart_gevorkyan_exit_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g016f1b13'

OLD_CONTEXT = (
    '«Мы сохраним концепцию отеля — семейный отдых, которую будем '
    'развивать и совершенствовать. Также мы обсуждаем вопрос '
    'расширения комплекса с увеличением инфраструктуры и номерного '
    'фонда», — поделилась генеральный директор управляющей компании '
    'VIZANT Нелли Шатова.'
)
CONTEXT_ADDITION = (
    ' До сделки гостиничным комплексом управляло ООО «Лесресорт» '
    '(принадлежит Рузанне Абрамян), которое, по данным «Контур.Фокус», '
    'является преемницей ООО «Прометей-Сити». Ранее ООО '
    '«Прометей-Сити» принадлежал членам семьи Геворкян, в частности '
    'Вазгену Геворкяну — но в 2022 году он перестал участвовать в '
    'управлении активом, а в 2023-м продал свою долю в нём, то есть за '
    'два года до сделки с Vizant.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += история владения до сделки '
          f'(Геворкян продал долю в 2023-м)')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
