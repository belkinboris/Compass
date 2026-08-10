# -*- coding: utf-8 -*-
"""У карточки `g010ece87` («Игорь Ким продал сербский Expobank A.D.
Belgrade компании Adriatic Bank») `eco.rationale` заканчивался протёкшей
служебной пометкой роли «(Игорь Ким (продавец, бенефициарный владелец
Экспобанка))» — тот же класс дефекта, что уже чинили
`strip_leaked_role_tags_2022.py` (не попала под общий шаблон — доп.
уточнение в скобках внутри пометки роли).

Запуск: python3 pipeline/fix_expobank_belgrade_tag.py
        python3 pipeline/fix_expobank_belgrade_tag.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g010ece87'
TAG = ' (Игорь Ким (продавец, бенефициарный владелец Экспобанка))'
OLD_RATIONALE = (
    'Сделка по продаже сербского банка Expobank A.D. Belgrade покупателю '
    'Adriatic Bank A.D. Podgorica. Это был последний европейский '
    'банковский актив Игоря Кима после продажи латвийского Signet Bank в '
    'феврале 2022 года и чешского Expobank CZ в сентябре 2022 года.' + TAG
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
