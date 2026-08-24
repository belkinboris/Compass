# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gc88ca79d (Сбер/доля АФК «Система» в
Ozon, обсуждается): дельта-поиск нашёл, что основатель АФК «Система»
Владимир Евтушенков 4 июня 2026 года публично заявил, что переговоры
велись, но соглашение не достигнуто, и сделки нет и в ближайшее время
не ожидается. Это не формальное «сделка сорвалась» (нет слова из
закрытого списка STATUS_WORDS) — статус не меняем механически, тот же
класс, что уже описан в «Известных проблемах» для БКС/«Форштадт» и
Газпромбанк/«Медскан». Не через `review.py`: источник (smart-lab.ru)
не образует с уже записанным текстом `eco.context` (из другого
материала, финансовые показатели АФК за 2025 год) непрерывный кусок.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена):
https://smart-lab.ru/blog/news/1312508.php

Запуск: python3 pipeline/fix_sber_ozon_afk_sistema_denial_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gc88ca79d'

OLD_CONTEXT = (
    'В 2025 году выручка АФК «Система» выросла на 8,3%, до 1,33 трлн '
    'руб., чистый убыток на долю акционеров составил 222,2 млрд руб., '
    'консолидированные финансовые обязательства увеличились на 7,9%, '
    'до 1,42 трлн руб., чистый корпоративный долг снизился на 16,7%, '
    'до 368,2 млрд руб. Необходимость передать актив «Сберу» могла '
    'возникнуть в контексте непростой финансовой ситуации компании.'
)
CONTEXT_ADDITION = (
    ' 4 июня 2026 года основатель АФК «Система» Владимир Евтушенков '
    'публично заявил: «АФК «Система» обсуждала продажу доли в Ozon '
    '(31,8%) со «Сбером», но соглашение не достигнуто. Переговоры '
    'велись, однако сделки нет и в ближайшее время не ожидается».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += публичное заявление '
          f'Евтушенкова о том, что сделки нет')

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
