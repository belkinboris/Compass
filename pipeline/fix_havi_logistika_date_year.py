# -*- coding: utf-8 -*-
"""У карточки `gc92ba4cb» («„Логистика и точка" приобретает российский бизнес
Havi») дата стояла 2023-12-08 — день и месяц совпадают с реальным событием
(ходатайство «Логистики и точки» в ФАС), но год ошибочен на целый год: все
источники (Коммерсантъ, AK&M, «Интерфакс») датируют и подачу ходатайства
(08.12.2022), и его удовлетворение ФАС (26.12.2022) 2022 годом, а не 2023-м —
обнаружено при дочитывании (REVISION_BRIEF.md) поиском под несколько углов,
подтверждено четырьмя независимыми источниками без единого расхождения.

Статус карточки («Согласование получено») остаётся верным — просто дата
теперь указывает на реальное событие подтверждения, а не на день, которого
у сделки не было. `review.py` намеренно не умеет переносить дату в другой
год (см. CLAUDE.md, «review.py не умеет переносить сделку в другой год — и
не должен»), поэтому это отдельный одноразовый скрипт со своим `assert`.

Запуск: python3 pipeline/fix_havi_logistika_date_year.py
        python3 pipeline/fix_havi_logistika_date_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gc92ba4cb'
OLD_DATE = '2023-12-08'
NEW_DATE = '2022-12-26'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]
    assert card['date'] == OLD_DATE, 'дата уже другая — проверьте карточку заново'
    print('ПРАВИМ  %s date: %r -> %r' % (CARD_ID, OLD_DATE, NEW_DATE))
    print('        (день подачи ходатайства и решения ФАС — 2022 год, не 2023)')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv[1:])
