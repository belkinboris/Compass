# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g45ba6605 (БКХ «Коломенский»/
«Продмастер»): дельта-поиск нашёл, что случилось с активом в 2026 году
— идёт реконструкция комплекса, холдинг удвоил инвестиционный план на
2026 год. Не через `review.py`: страница new-retail.ru отдаёт кэшу
только меню/навигацию без тела статьи (сверено напрямую), дословную
проверку по сырому тексту пройти не может — цитата подтверждена
напрямую через WebFetch по живой странице.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена):
https://new-retail.ru/novosti/retail/kolomenskiy_udvoit_investitsii_v_razvitie/

Запуск: python3 pipeline/fix_kolomensky_prodmaster_2026_plans.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g45ba6605'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В рамках развития нового для холдинга направления – '
    'производства готовой еды – идёт реконструкция комплекса '
    '«Продмастер», приобретённого в 2025 году. В 2026 году холдинг '
    '«Коломенский» инвестирует в развитие 16 млрд рублей против 8 '
    'млрд в 2025 году.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: реконструкция «Продмастера» и '
          f'инвестиционный план холдинга на 2026 год')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
