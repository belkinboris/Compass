# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g150f6855 («Самолет»/«Клиентский
сервис»): дельта-поиск нашёл, что случилось с предметом сделки ПОСЛЕ
покупки — «Самолет» перепродал актив «Яндексу» (закрыто 6 мая, ЕГРЮЛ).
Не через `review.py`: источник (Интерфакс) новый, не образует с уже
записанным текстом `eco.context` (из другого материала, история
владения ДО сделки с ВТБ) непрерывный кусок.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена):
https://www.interfax.ru/business/1025082

Запуск: python3 pipeline/fix_samolet_domilend_resale_to_yandex.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g150f6855'

OLD_CONTEXT = (
    'В 2019 году ВТБ выкупил 75,7% компании для формирования '
    'собственной жилищной экосистемы. Остальное распределено между '
    'основателями «Домиленда» Дарьей (14%) и Кириллом (10,23%) '
    'Вороновыми. В 2022 году ВТБ продал долю кипрской компании '
    'Lagella Limited (принадлежит Ineth Limited и Андрею Пожиткову). '
    'После выхода ВТБ Воронова выкупила права на PropTech-платформу '
    'и перевела ее на юрлицо «Платформа Домиленд» (ее долями '
    '«Самолет» не владеет).'
)
CONTEXT_ADDITION = (
    ' В мае 2025 года «Яндекс» приобрел 100% ООО «Клиентский '
    'сервис», которому принадлежит ООО «Платформа Домиленд»: по '
    'данным ЕГРЮЛ, 6 мая 100% платформы перешло двум структурам '
    '«Яндекса» — ООО «Технояк» и ООО «Яндекс.Доставка Холдинг».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += перепродажа «Яндексу» в мае '
          f'2025 года')

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
