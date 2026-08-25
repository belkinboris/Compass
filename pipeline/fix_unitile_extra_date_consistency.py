# -*- coding: utf-8 -*-
"""Карточка gb207417a: pipeline/fix_unitile_plitekspert_egrul_date.py
поправил структурное поле `date` на дату регистрации в ЕГРЮЛ (21 ноября
2024), но `extra` осталось со старой формулировкой «закрыта 28 декабря
2024 года» — тот самый класс дефекта из REVISION_BRIEF.md («после
правки — перечитайте карточку целиком, не только своё поле»).

Запуск: python3 pipeline/fix_unitile_extra_date_consistency.py
        python3 pipeline/fix_unitile_extra_date_consistency.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb207417a'

OLD_EXTRA = (
    'Сделка заключена осенью 2024 года, закрыта 28 декабря 2024 года. '
    'Покупатель — ООО «Плитэксперт» (70% владеет ООО «Проксима кэпитал '
    'групп» Владимира Ермошина и Владимира Татарчука, 20% у Катарины '
    'Конкс, 10% у Виталия Баранова). Продавец — Александр Файн. 5% доли '
    'в ООО «Юнитайл Холдинг» были выданы продавцу в качестве частичной '
    'оплаты за сделку по продаже бизнеса Quadro Decor вместо денежных '
    'средств.'
)
NEW_EXTRA = (
    'Сделка заключена осенью 2024 года, зарегистрирована в ЕГРЮЛ 21 '
    'ноября 2024 года. Покупатель — ООО «Плитэксперт» (70% владеет ООО '
    '«Проксима кэпитал групп» Владимира Ермошина и Владимира Татарчука, '
    '20% у Катарины Конкс, 10% у Виталия Баранова). Продавец — '
    'Александр Файн. 5% доли в ООО «Юнитайл Холдинг» были выданы '
    'продавцу в качестве частичной оплаты за сделку по продаже бизнеса '
    'Quadro Decor вместо денежных средств.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA, 'extra изменился с момента чтения — проверьте'

    print('=== extra: станет ===')
    print(NEW_EXTRA)

    if write:
        deal['extra'] = NEW_EXTRA
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
