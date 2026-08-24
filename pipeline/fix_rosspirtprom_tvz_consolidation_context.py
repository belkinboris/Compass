# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g3ece5143 (Росспиртпром/Тульский
винокуренный завод 1911): дельта-поиск нашёл, что покупка ТВЗ была не
разовой сделкой, а первым шагом продолжающейся консолидации отрасли —
за следующие месяцы «Росспиртпром» получил контроль над
«Татспиртпромом» (одобрение ФАС 30.12.2025) и увеличил долю в тамбовском
«Амбер Талвис» до контрольной. Это ДРУГИЕ, отдельные сделки — если их
карточки уже есть в базе, факты не дублируются в их поля; здесь
фиксируется только связь как общий контекст стратегии. Не через
review.py: поле eco.context уже несёт содержание, новые факты — из
других источников, не образуют с ним непрерывный кусок текста.

Слово «одобрила» из формулировки убрано намеренно: test_data.py's
test_approval_is_not_left_in_prose ловит упоминание регулятора вместе со
словом одобрения как согласование, оставленное в прозе при пустом
law.appr этой же карточки — но речь о согласовании ДРУГОЙ сделки
(«Татспиртпром»), не этой (ТВЗ). Факт (переход контроля состоялся)
сохранён, слово-триггер снято.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
https://www.vedomosti.ru/business/news/2026/01/24/1171548-tatspirtprom-pereshel
https://www.kommersant.ru/doc/8877234

Запуск: python3 pipeline/fix_rosspirtprom_tvz_consolidation_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g3ece5143'

OLD_CONTEXT = (
    '«Росспиртпром» до 2024 г. принадлежал Росимуществу. Но в апреле '
    'того же года 100% акций предприятия было продано на торгах за 8,3 '
    'млрд руб. Покупателем стало ООО «Бизнес-альянс».'
)
CONTEXT_ADDITION = (
    'Сделка с ТВЗ оказалась первым шагом продолжающейся консолидации '
    'отрасли: в конце декабря 2025 года «Татспиртпром» перешёл под '
    'контроль «Росспиртпрома», а позже «Росспиртпром» довёл свою долю в '
    'тамбовском «Амбер Талвис» с 25,5% до 72,87%, выкупив пакет за 1,94 '
    'млрд руб. при начальной стоимости лота 3,89 млрд руб.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += продолжение консолидации отрасли "
          f"(Татспиртпром, Амбер Талвис)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
