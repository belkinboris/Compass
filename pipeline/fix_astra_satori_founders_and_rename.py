# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g75aa1b3b
(Группа Астра приобрела 80% в ООО «Сатори»). Имена продавцов уже лежали
в источнике карточки, но не были перенесены в структурное поле.
Проверено лично прямым WebFetch.

1) `seller` (новое поле, текстом) — CNews (уже стоит в src), дословно:
«20% остались у основателей «Сатори» Константина Могилевкина, Ильяса
Мухамадуллина и Айдара Самерханова» — три физлица, сохранившие 20% доли,
названы продавцами оставшихся 80%.

2) `eco.context` (новое поле) — судьба юрлица после сделки. Audit-it.ru,
дословно: «Наименование в отчетности: ООО «САТОРИ»» — та же организация
(ИНН 1661055530) в настоящее время зарегистрирована как ООО «ТАНТОР
ДАТА ИНТЕГРЕЙШН» (краткая форма — «ТАНТОР ДИАЙ»): интеграция в
экосистему Tantor завершена переименованием юрлица.
Источник: https://www.audit-it.ru/buh_otchet/1661055530_ooo-tantor-dielaych

НЕ ВКЛЮЧЕНО: сумма сделки — независимой оценки нет, найденная на
агрегаторах цифра «~54,6 млн ₽» — расчётная оценка чистых активов за
2023 год, а не цена сделки 2024 года (родня уроку CLAUDE.md «Число
может быть верным фактом и не той величиной»); консультанты — не
найдены; судьба продукта Deductive Lake House отдельно от всей линейки
Tantor Labs — источники сообщают только о росте выручки компании
целиком, не сегмента DLH, переносить нечего.

Запуск: python3 pipeline/fix_astra_satori_founders_and_rename.py
        python3 pipeline/fix_astra_satori_founders_and_rename.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g75aa1b3b'

NEW_SELLER = 'Константин Могилевкин, Ильяс Мухамадуллин, Айдар Самерханов'

OLD_CONTEXT = (
    'Команда «Сатори» — резидент казанского «ИТ-Парка», «Сколково» и '
    'Astana Hub, которая в 2022 г. получила грант от Фонда содействия '
    'инновациям на свой флагманский продукт – платформу для управления '
    'данными Deductive Lake House (DLH).'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' «Наименование в отчетности: ООО «САТОРИ»» — та же организация '
    '(ИНН 1661055530) в настоящее время зарегистрирована как ООО «ТАНТОР '
    'ДАТА ИНТЕГРЕЙШН» (audit-it.ru): интеграция в экосистему Tantor '
    'завершена переименованием юрлица.'
)

NEW_SRC = [
    ['audit-it.ru', 'https://www.audit-it.ru/buh_otchet/1661055530_ooo-tantor-dielaych'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') is None
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== seller (новое поле): станет {NEW_SELLER!r} ===')
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
