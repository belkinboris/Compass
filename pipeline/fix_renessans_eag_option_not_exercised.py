# -*- coding: utf-8 -*-
"""Месячная очередь, карточка ge2e2c71c («Ренессанс»/«Евразийская
алкогольная группа»): дельта-поиск нашёл, что опцион на увеличение
доли до 50% (уже упомянутый в `extra`) за год так и не был
реализован — на конец 2025 года у «Ренессанса» по-прежнему 25%.
Не через `review.py`: источник (shoppers.media) отличается от того, с
которого собран текущий текст `eco.context`.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://shoppers.media/news/27711_proizvoditel-santo-stefano-mozet-vypustit-limonady

Запуск: python3 pipeline/fix_renessans_eag_option_not_exercised.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge2e2c71c'

OLD_CONTEXT = 'ЕАГ не раскрывает владельцев, но прежде основным собственником был Отар Балинов.'
NEW_CONTEXT = OLD_CONTEXT + (
    ' На конец 2025 года, согласно бухгалтерской отчётности ЕАГ, '
    '«Ренессанс» по-прежнему владеет 25% (опцион на увеличение доли до '
    '50% не реализован); 50% принадлежит ООО «РТД боттлерс» (Сергей '
    'Журавлёв и Амир Мидов), ещё 25% остаются за Отаром Балиновым.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += опцион не реализован, полная '
          f'структура владения на конец 2025 года')

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
