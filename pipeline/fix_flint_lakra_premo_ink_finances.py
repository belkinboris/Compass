# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g0df6c7c4
(Flint Group продал российское подразделение компании «Лакра Синтез»,
август 2024). Дельта-поиск нашёл финансы предмета сделки за 2024-2025
годы под новым именем («Премо Инк Восток») — проверено лично прямым
WebFetch (audit-it.ru).

«В 2025 году организация получила выручку в сумме 1,3 млрд руб., что на
47,4 млн руб., или на 3,7%, больше, чем годом ранее» — «Результатом
работы ООО "ПРЕМО ИНК ВОСТОК" за 2025 год стал убыток в размере 57,9
млн руб. В 2024 году убыток был в 3,8 раза меньше.»

НЕ включены: сумма самой сделки — заново перепроверены все четыре
источника карточки (Коммерсантъ дважды, rupec.ru, mrc.ru, soyuzkraska.ru)
и нигде она не названа; консультанты сделки — не найдены ни в одном
источнике. Побочная находка, не по этой карточке: у сделки продавца по
предыдущему шагу (BASF -> «Лакра Синтез», карточка g073bf58b) статус
стоит «Обсуждается», хотя РБК прямо описывает закрытие в июле 2024 —
кандидат для отдельного прохода, не трогается здесь.

Запуск: python3 pipeline/fix_flint_lakra_premo_ink_finances.py
        python3 pipeline/fix_flint_lakra_premo_ink_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0df6c7c4'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'После сделки предприятие сменило название на «Премо Инк Восток». В '
    '2025 году организация получила выручку в сумме 1,3 млрд руб., что на '
    '47,4 млн руб., или на 3,7%, больше, чем годом ранее; результатом '
    'работы за 2025 год стал убыток в размере 57,9 млн руб. — в 2024 году '
    'убыток был в 3,8 раза меньше (audit-it.ru).'
)

NEW_SRC = [
    ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1127746680973_ooo-premo-ink-vostok'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
