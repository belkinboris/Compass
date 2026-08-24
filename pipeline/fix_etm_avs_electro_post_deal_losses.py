# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gdf93c62d (ЭТМ/«АВС-Электро»): дельта-
поиск нашёл, что произошло с предметом сделки уже ПОСЛЕ объединения —
компания ушла в убыток почти на миллиард рублей за 2025 год, выручка
упала вдвое, сменился гендиректор. Не через `review.py`: источник
(Коммерсантъ-Черноземье, doc/8553683) уже добавлен как источник новой
структуры собственности (law.struct), но текст этого блока не
контигуален уже записанному в `eco.context` (тот собран из ДРУГОГО
материала о рыночных долях после сделки).

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.kommersant.ru/doc/8553683

Запуск: python3 pipeline/fix_etm_avs_electro_post_deal_losses.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gdf93c62d'

OLD_CONTEXT = (
    'Таким образом, по оценке инсайдеров рыночная доля ЭТМ после '
    'поглощения «АВС-Электро» составит около 40%, а «Русский свет» и '
    '«Минимакс» будут контролировать до 30% рынка электротехники. '
    'Ориентировочный размер рынка к концу 2025 года оценивается '
    'экспертами в 480–520 млрд. рублей.'
)
CONTEXT_ADDITION = (
    ' С убытками на 964,6 млн руб. завершило 2025 год воронежское ООО '
    '«АВС-Электро». Годом ранее предприятие фиксировало чистую прибыль '
    '197,7 млн. Выручка компании упала с 10,28 до 5,16 млрд руб. С '
    '1 апреля 2026-го генеральным директором предприятия был назначен '
    'Евгений Поздняков — он сменил Наталью Шишкину, которая руководила '
    'фирмой с мая 2020 года.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += убыток и смена гендиректора '
          f'предмета сделки год спустя')

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
