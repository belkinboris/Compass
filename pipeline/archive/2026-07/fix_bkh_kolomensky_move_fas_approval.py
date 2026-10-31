# -*- coding: utf-8 -*-
"""Исправление сразу после предыдущего скрипта в этом же заходе
(`fix_bkh_kolomensky_real_source_and_dates.py`, семьдесят второй заход)
— `pytest` поймал `test_approval_is_not_left_in_prose`: фраза
«"Волжский пекарь" — одобрение ФАС 12 сентября 2022» в `eco.context`
называла орган (ФАС) и действие (одобрение), а `law.appr` при этом
оставался плейсхолдером «Публично не сообщалось» — ровно тот класс
дефекта, который тест и ловит (согласование написано, но не туда).

Дословно (Ведомости, 12.09.2022, vedomosti.ru/business/news/2022/09/12/
940476-fas-razreshila-kupit-pekarya): «ФАС разрешила БКХ "Коломенский"
купить "Волжского пекаря"».

`law.appr` заполнен этой цитатой (был плейсхолдером). `eco.context`
переформулирован: дата сделки осталась, но формулировка одобрения ФАС
убрана оттуда — теперь она только в `law.appr`, без задвоения.

Запуск: python3 pipeline/fix_bkh_kolomensky_move_fas_approval.py
        python3 pipeline/fix_bkh_kolomensky_move_fas_approval.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g927f3242'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = 'ФАС разрешила БКХ «Коломенский» купить «Волжского пекаря» (Ведомости, 12 сентября 2022 года).'

OLD_CONTEXT = (
    'Показатели 2024:\nВыручка – 60 млрд руб. (+35% г./г.) \nОбъем '
    'продукции = 485 тыс. тонн (+13%)\nБенефициар — один из основателей '
    '«Росбилдинга», владелец девелоперской компании Sminex Алексей '
    'Тулупов. Даты сделок: Fazer — 29 апреля 2022 (4 фабрики, более 2 '
    'тыс. сотрудников, Известия); «Волжский пекарь» — одобрение ФАС '
    '12 сентября 2022 (Ведомости); «Дарница» — закрыта 15 сентября 2023 '
    '(Коммерсантъ, собственная страница холдинга называет октябрь 2023 '
    '— расхождение); «Пролетарец» — май 2024 по интервью (собственная '
    'страница холдинга называет июнь 2024 — расхождение). План '
    'реконструкции «Пролетарца» по данным холдинга: запуск первых линий '
    '— август 2025, полное завершение — осень 2026, мощность ~150 '
    'т/сутки.'
)
NEW_CONTEXT = OLD_CONTEXT.replace(
    '«Волжский пекарь» — одобрение ФАС 12 сентября 2022 (Ведомости)',
    '«Волжский пекарь» — 12 сентября 2022 (Ведомости, одобрение ФАС — '
    'см. «Согласования»)',
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    assert NEW_CONTEXT != OLD_CONTEXT

    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
