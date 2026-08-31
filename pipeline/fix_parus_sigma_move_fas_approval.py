# -*- coding: utf-8 -*-
"""Исправление сразу после предыдущего скрипта в этом же заходе
(`fix_parus_sigma_deal_fell_through.py`, семьдесят пятый заход) —
`pytest` поймал `test_approval_is_not_left_in_prose`: фраза «в феврале
ФАС России согласовала... приобретение» в `eco.context` называла орган
(ФАС) и действие (согласовала), а `law.appr` при этом оставался
плейсхолдером «Публично не сообщалось» — тот же класс дефекта, что уже
чинился в этом заходе у БКХ «Коломенский».

Дословно (РБК Уфа, 21.02.2025): «в феврале ФАС России согласовала
московской инвестиционной компании Parus Asset Management приобретение
уфимского ООО "Складской комплекс "Сигма""».

`law.appr` заполнен этой цитатой (был плейсхолдером). `eco.context`
переформулирован: факт согласования ФАС убран оттуда — теперь он
только в `law.appr`, без задвоения; в `eco.context` остаётся факт срыва
сделки и его причина.

Запуск: python3 pipeline/fix_parus_sigma_move_fas_approval.py
        python3 pipeline/fix_parus_sigma_move_fas_approval.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g573b8819'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'ФАС согласовала сделку: «в феврале ФАС России согласовала '
    'московской инвестиционной компании Parus Asset Management '
    'приобретение уфимского ООО "Складской комплекс "Сигма""» (РБК Уфа, '
    '21 февраля 2025 года).'
)

OLD_CONTEXT = (
    'Принадлежащая Самонову группа Accent с партнерами давно хотели '
    'продать этот актив, но до сих ни с кем договориться не удавалось. '
    'Сделка не состоялась: «в феврале ФАС России согласовала московской '
    'инвестиционной компании Parus Asset Management приобретение '
    'уфимского ООО "Складской комплекс "Сигма""», но «сделка не была '
    'завершена по независящим от нас причинам» (Антон Комаров, директор '
    'департамента складской недвижимости Accent Capital, РБК Уфа, '
    '21 февраля 2025 года).'
)
NEW_CONTEXT = (
    'Принадлежащая Самонову группа Accent с партнерами давно хотели '
    'продать этот актив, но до сих ни с кем договориться не удавалось. '
    'Несмотря на одобрение ФАС (см. «Согласования»), сделка не '
    'состоялась: «сделка не была завершена по независящим от нас '
    'причинам» (Антон Комаров, директор департамента складской '
    'недвижимости Accent Capital, РБК Уфа, 21 февраля 2025 года).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT

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
