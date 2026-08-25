# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gc567457f (Виктор Харитонин
приобрел Котласский химзавод, декабрь 2024): дельта-поиск нашёл, что новый
собственник в первые 2-3 месяца сменил руководство обеих структур
(АО «Котласский химзавод» и ООО «КХЗ-Менеджмент»), а в октябре 2025 года
завод запустил новый цех индустриальных лакокрасочных покрытий для
арктических условий с инвестициями свыше 500 млн ₽. Сумма самой сделки
по-прежнему нигде не раскрыта; свежая отчётность за 2023-2025 годы
независимо не подтверждена (единственная найденная цифра совпадает с уже
известной за 2021 год — переносить её как новую было бы неверно). Не через
review.py: цитаты из НОВЫХ источников (arh.mk.ru, реестровые данные) в поле,
уже содержащем текст из другого источника.

Запуск: python3 pipeline/fix_kotlas_himzavod_investment_and_management.py
        python3 pipeline/fix_kotlas_himzavod_investment_and_management.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc567457f'

OLD_CONTEXT = (
    'Прежде «КХЗ-Менеджмент» и «КХЗ-Сервис» владели Ирина Доброхотова и '
    'Павел Ахмадеев соответственно.'
)
CONTEXT_ADDITION = (
    ' В феврале-марте 2025 года новый собственник сменил руководство '
    'обеих структур: гендиректором АО «Котласский химзавод» с 5 марта '
    '2025 года стал Михаил Тихонов (сменил Доброхотову), гендиректором '
    'ООО «КХЗ-Менеджмент» с 19 февраля 2025 года — Максим Шиленков. В '
    'октябре 2025 года завод запустил новый цех по производству '
    'индустриальных лакокрасочных покрытий (эмали, грунтовки) для защиты '
    'металлоконструкций в арктических условиях — инвестиции в расширение '
    'превысили 500 млн ₽, проектная мощность после выхода на полную '
    'загрузку — 8 тыс. тонн в год.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['МК Архангельск', 'https://arh.mk.ru/economics/2025/10/13/kotlasskiy-khimzavod-zapustil-cekh-po-vypusku-industrialnykh-pokrytiy.html'],
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
