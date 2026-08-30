# -*- coding: utf-8 -*-
"""Хвост правки geb645292 (пятидесятый девятый заход): `pytest` поймал
`test_approval_is_not_left_in_prose` — фраза про разрешение президента РФ
на продажу банковской «дочки» Volkswagen осталась в `eco.context`, пока
`law.appr` стоял заглушкой «Публично не сообщалось». Тот же класс, что
уже описан в CLAUDE.md для ПСБ/«Атом»: госорган + слово разрешения — это
`law.appr`, а не соседнее поле.

Перенос: фраза про президентское разрешение убирается из `eco.context`
(остаётся в `law.appr`, а не дублируется), остальной текст правки
(банк, доли, рэнкинг) остаётся в `eco.context` — это не согласование, а
факт о самой сделке и её предмете.

Запуск: python3 pipeline/fix_kim_vwbank_approval_field.py
        python3 pipeline/fix_kim_vwbank_approval_field.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'geb645292'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'Разрешение президента РФ на продажу российской банковской «дочки» '
    'германский автоконцерн Volkswagen получил 31 декабря 2024 года '
    '(Интерфакс, 26 февраля 2025).'
)

OLD_CONTEXT_TAIL = (
    ' 25 февраля 2025 года консолидация дошла до банка: «Бизнесмен получил '
    '45% долей в банке напрямую и еще 55% – через контролируемую им '
    'компанию "Экспомобилити"», а «разрешение президента РФ на продажу '
    'российской банковской "дочки" германский автоконцерн Volkswagen '
    'получил 31 декабря 2024 года» — по итогам 2024 года «Фольксваген банк '
    'Рус» занимал 135-е место в рэнкинге «Интерфакс-100» с активами 24 '
    'млрд ₽ и капиталом 23,6 млрд ₽ (Интерфакс, 26 февраля 2025). '
    'Купленная факторинговая «дочка» (ООО «Фольксваген Финансовые Услуги '
    'Рус») переименована в ООО «Экспофинанс» и ликвидирована 21 октября '
    '2024 года (данные ЕГРЮЛ).'
)
NEW_CONTEXT_TAIL = (
    ' 25 февраля 2025 года консолидация дошла до банка: «Бизнесмен получил '
    '45% долей в банке напрямую и еще 55% – через контролируемую им '
    'компанию "Экспомобилити"» — по итогам 2024 года «Фольксваген банк '
    'Рус» занимал 135-е место в рэнкинге «Интерфакс-100» с активами 24 '
    'млрд ₽ и капиталом 23,6 млрд ₽ (Интерфакс, 26 февраля 2025). '
    'Купленная факторинговая «дочка» (ООО «Фольксваген Финансовые Услуги '
    'Рус») переименована в ООО «Экспофинанс» и ликвидирована 21 октября '
    '2024 года (данные ЕГРЮЛ).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'].endswith(OLD_CONTEXT_TAIL)

    new_context = deal['eco']['context'][:-len(OLD_CONTEXT_TAIL)] + NEW_CONTEXT_TAIL

    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('\n=== eco.context: станет ===')
    print(new_context)

    if write:
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = new_context
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
