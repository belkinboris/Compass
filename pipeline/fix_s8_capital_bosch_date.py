# -*- coding: utf-8 -*-
"""У карточки `gafda8e29` («S8 Capital приобрел активы Bosch в Энгельсе»)
`date` стоял «2022» — единственный источник карточки («Ъ») прямо датирован
28 апреля 2023 года и сообщает о сделке в настоящем/завершённом времени:
«28.04.2023, 13:00 ... Холдинг S8 Capital завершил сделку по покупке
российских активов немецкой Bosch в городе Энгельс». Год «2022» в статье
действительно встречается — но относится к СОВСЕМ ДРУГОЙ, более ранней
сделке того же холдинга («В июле 2022 года S8 Capital приобрел активы
американского производителя лифтов Otis»), не к заводам Bosch. Похоже,
это и стало источником неверного года при первичном разборе.

Почему не через review.py: перенос в другой год не поддержан
`date_is_supported()` намеренно (см. прецедент
`fix_osnova_sviblovo_date.py`).

Запуск: python3 pipeline/fix_s8_capital_bosch_date.py
        python3 pipeline/fix_s8_capital_bosch_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gafda8e29'
OLD_DATE = '2022'
NEW_DATE = '2023-04-28'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == OLD_DATE, '%s: дата уже другая' % CARD_ID
    print('ПРАВИМ  %s date: «%s» -> «%s»' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
