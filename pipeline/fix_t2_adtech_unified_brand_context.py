# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g84a06224 (T2 приобрел три
AdTech-компании: Yabbi, Redllama и Plazkart, декабрь 2024): дельта-поиск
нашёл, что T2 готовит объединение купленных активов под единым брендом —
ADPASS (27.10.2025) со ссылкой на источник в «Коммерсанте»: компания
«создаёт новый бренд, объединяющий ранее приобретённые рекламные активы», а
запуск может быть связан с выходом собственной DSP-платформы. Дословная
цитата подтверждена лично (WebFetch). Сумма сделки и консультанты по-прежнему
не раскрыты ни в одном источнике. Не через review.py: цитата из НОВОГО
источника в поле, уже содержащем текст из другого источника (описание
продуктов трёх компаний).

Запуск: python3 pipeline/fix_t2_adtech_unified_brand_context.py
        python3 pipeline/fix_t2_adtech_unified_brand_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g84a06224'

OLD_CONTEXT = (
    'Yabbi занимается разработкой программных комплексов (DSP и SSP) для '
    'рекламодателей и паблишеров. Рекламная платформа Redllama предназначена '
    'для решения медиа и brandformance задач. Технологичная сеть Plazkart '
    'работает со всеми типами видеоинвентаря на ключевых диджитал-платформах.'
)
CONTEXT_ADDITION = (
    ' T2 готовит объединение купленных активов под единым брендом: по '
    'данным ADPASS (со ссылкой на источник в «Коммерсанте»), компания '
    '«создаёт новый бренд, объединяющий ранее приобретённые рекламные '
    'активы», а запуск нового бренда может быть связан с выходом '
    'собственной DSP-платформы для автоматической закупки интернет-рекламы.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['ADPASS', 'https://adpass.ru/t2-zapuskaet-dsp/'],
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
