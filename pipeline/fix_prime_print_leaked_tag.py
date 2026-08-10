# -*- coding: utf-8 -*-
"""У карточки `cdcf1a650` («Передача долей в сети типографий «Прайм Принт» от
Amedia в управление Росимущества») и `eco.context`, и `extra` заканчиваются
одной и той же протёкшей служебной пометкой сторон «(Государство
(Росимущество) / Amedia)» — тот же класс дефекта, что уже чинили
`pipeline/strip_leaked_role_tags_2022.py` и точечные скрипты для g20d4cc38 /
g62698716, только с третьим по счёту форматом («A / B» вместо «Имя (роль)»
или «Роль: Имя»). Текст до пометки не меняется.

Почему не через review.py: снимается служебный шум, а не новый факт.

Запуск: python3 pipeline/fix_prime_print_leaked_tag.py
        python3 pipeline/fix_prime_print_leaked_tag.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cdcf1a650'
TAG = ' (Государство (Росимущество) / Amedia)'
OLD_CONTEXT = (
    'Ранее в апреле 2022 года Amedia объявила о передаче своих российских '
    'типографий в управление главреду «Новой газеты» Дмитрию Муратову, '
    'включённому Минюстом в реестр иноагентов. Согласно решению Amedia, он '
    'должен был получить четыре типографии, судьба ещё двух обсуждалась с '
    'российскими миноритариями.' + TAG
)
NEW_CONTEXT = OLD_CONTEXT[:-len(TAG)]
OLD_EXTRA = (
    'Президент Путин передал в управление Росимущества доли в сети '
    'типографий «Прайм Принт», принадлежавшие норвежской компании Amedia. '
    + OLD_CONTEXT
)
NEW_EXTRA = OLD_EXTRA[:-len(TAG)]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['eco']['context'] == NEW_CONTEXT and card['extra'] == NEW_EXTRA:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['eco']['context'] == OLD_CONTEXT, '%s: eco.context уже другой' % CARD_ID
    assert card['extra'] == OLD_EXTRA, '%s: extra уже другой' % CARD_ID
    print('ПРАВИМ  %s eco.context и extra: снята протёкшая пометка сторон' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['eco']['context'] = NEW_CONTEXT
    card['extra'] = NEW_EXTRA
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
