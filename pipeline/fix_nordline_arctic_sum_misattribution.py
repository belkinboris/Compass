# -*- coding: utf-8 -*-
"""Сумма карточки «Нордлайн»/TotalEnergies — не цена сделки, а чужая цифра.

ЧТО СЛОМАНО. У `gmru-nordline-totalenergies-arctic` (продажа 10% в «Арктик
СПГ 2» от TotalEnergies компании «Нордлайн») поля `sum` и `eco.sum` несли
«$4,1 млрд». Источник (mergers.ru) действительно называет эту цифру — но
она относится к СОВСЕМ ДРУГОМУ событию: «Французская TotalEnergies в 2022
году списала свои активы в России в сумме $4,1 млрд, главным образом это
касалось акций «Арктик СПГ 2»» — это бухгалтерское списание ВСЕХ активов
TotalEnergies в России в 2022 году (обесценение по МСФО), а не цена продажи
10%-й доли «Нордлайну» в 2026-м. Ни один из двух источников карточки не
называет цену ЭТОЙ сделки вовсе.

Тот же класс дефекта, что уже чинили у ВТБ/Holiday Inn («Разбор источника
доверяет числу из чужого абзаца» — там взяли сумму продажи всего
«Галс-Девелопмента» вместо гостиницы) и у «Арнест»/Reckitt («Число может
быть верным фактом и совсем не той величиной» — там взяли убыток продавца
вместо цены актива): число из статьи правда там есть, но описывает не то,
что показано на экране как «Сумма сделки».

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `review.py` умеет ДОПОЛНЯТЬ и УТОЧНЯТЬ сумму по
цитате, но не проверяет, что цифра относится именно к этой сделке, — это
решение принимает человек, читающий статью целиком, а не механическая
подстрока. Здесь верная правка — не новое значение, а честный прочерк:
факт о списании 2022 года остаётся в `eco.context` (перенесён отдельной
записью в review.py, партия 2026-B), а поле суммы сделки становится
прочерком «Не раскрыта» — правдой, а не более точной ложью.

ЗАПУСК:
    python3 pipeline/fix_nordline_arctic_sum_misattribution.py            # сухой прогон
    python3 pipeline/fix_nordline_arctic_sum_misattribution.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-nordline-totalenergies-arctic'
OLD = '$4,1 млрд'
NEW = 'Не раскрыта'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('sum') == OLD, 'sum уже другой: %r' % deal.get('sum')
    assert deal.get('eco', {}).get('sum') == OLD, 'eco.sum уже другой: %r' % deal.get('eco', {}).get('sum')

    print('ПРАВИМ %s: sum и eco.sum %r -> %r' % (DEAL_ID, OLD, NEW))
    print('  причина: «$4,1 млрд» — списание TotalEnergies ВСЕХ российских '
          'активов в 2022 году, а не цена продажи 10% «Арктик СПГ 2» '
          '«Нордлайну» в 2026-м; цену этой сделки источники не называют')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NEW
    deal['eco']['sum'] = NEW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
