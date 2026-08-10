# -*- coding: utf-8 -*-
"""У карточки `gd96404f2` («Vershina Capital инвестировала в холдинг
Ultimate Education») `eco.rationale` заканчивался протёкшей служебной
пометкой роли «(Vershina Capital (инвестор))» — тот же класс дефекта, что
уже чинили `strip_leaked_role_tags_2022.py`.

Запуск: python3 pipeline/fix_ultimate_education_tag.py
        python3 pipeline/fix_ultimate_education_tag.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd96404f2'
TAG = ' (Vershina Capital (инвестор))'
OLD_RATIONALE = (
    'Vershina Capital была инвестором в сделку по созданию/развитию '
    'холдинга Ultimate Education, включающего 6 онлайн-школ (MAED, '
    'Fashion Factory School, XYZ school, Bang Bang Education, Psycodemia, '
    'Moscow Digital School). В 2022 году холдинг привлёк новое '
    'финансирование по оценке почти в 2 раза выше предыдущей оценки, по '
    'которой Vershina Capital входила в проект. Сумма: ~1,2 млрд руб. '
    '(выручка холдинга за 2022 год).' + TAG
)
NEW_RATIONALE = OLD_RATIONALE[:-len(TAG)]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['eco']['rationale'] == NEW_RATIONALE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['eco']['rationale'] == OLD_RATIONALE, '%s: значение уже другое' % CARD_ID
    print('ПРАВИМ  %s eco.rationale: снята протёкшая пометка роли' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['eco']['rationale'] = NEW_RATIONALE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
