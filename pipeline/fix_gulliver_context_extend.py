# -*- coding: utf-8 -*-
"""Месячная очередь, карточка ga971155a (розничная сеть «Гулливер»
выставлена на продажу): дельта-поиск нашёл продолжение сюжета — 5 марта
2026 года X5 направила продавцу необязывающее предложение (второй
независимый источник, retail.ru), а «Магнит» прямо отказался от
покупки (уже цитируемый Коммерсантъ, но факт не был перенесён на
экран). Независимая оценка стоимости расширилась до 3,5–6 млрд ₽.

Не через `review.py`: источники комбинируются из ДВУХ статей (уже
цитируемый Коммерсантъ + новый retail.ru), непрерывного куска с уже
записанным текстом не образуют.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.kommersant.ru/doc/8364093 (уже в src)
https://www.retail.ru/news/kh5-i-lenta-zainteresovalis-riteylerom-gulliver-5-marta-2026-275208/

Запуск: python3 pipeline/fix_gulliver_context_extend.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga971155a'

OLD_CONTEXT = (
    'Интерес крупных игроков к сети обусловлен наличием у нее двух '
    'собственных фабрик-кухонь в Ульяновске и Балаково.'
)
CONTEXT_ADDITION = (
    ' Представитель «Магнита» пояснил, что компания не рассматривает '
    'приобретение «Гулливера», концентрируясь на росте эффективности и '
    'развитии основных собственных форматов. 5 марта 2026 года стало '
    'известно, что X5 направила продавцу необязывающее предложение '
    '(Non-Binding Offer, NBO), предполагающее последующее согласование '
    'условий сделки; эксперты к этому моменту оценивали стоимость '
    'активов уже в 3,5–6 млрд рублей — выше первоначальной оценки '
    '3–3,5 млрд ₽. Подтверждения закрытия или срыва сделки после этого '
    'не появлялось.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += интерес X5, отказ «Магнита», '
          f'более широкая оценка')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal.setdefault('src', [])
        entry = ['retail.ru', 'https://www.retail.ru/news/kh5-i-lenta-zainteresovalis-riteylerom-gulliver-5-marta-2026-275208/']
        if entry not in deal['src']:
            deal['src'].append(entry)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
