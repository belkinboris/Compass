# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g3bcf9780 (Т2 Мобайл
приобрел платформу для омниканальной коммуникации Umnico): дельта-поиск
нашёл публичный запуск/презентацию продукта после тихого закрытия сделки
(апрель 2026) — новый факт о развитии актива, а не о самой сделке, поэтому
не через review.py, поле уже занято текстом из другого источника.

Проверка ЕГРЮЛ (audit-it.ru) не подтверждена: сайт не открылся при прямой
перепроверке (connection reset), как уже бывало в этой сессии, — по
установленному правилу претензия с непроверяемого источника в карточку не
идёт.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
telecom.cnews.ru (20.04.2026).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g3bcf9780'
OLD_CONTEXT = (
    'Umnico (ООО «Омнитех») на 100% принадлежит Елене Матусевич с 2024 г., '
    'согласно СПАРК. Гендиректором компании выступает она же.'
)
ADDITION = (
    '20 апреля 2026 года Т2 публично представила платформу Umnico как '
    'часть своей линейки B2B-решений: «Т2, российский оператор мобильной '
    'связи, развивает направление цифровых решений для бизнеса. Компания '
    'представила платформу Umnico для омниканальной коммуникации с '
    'клиентами». «В декабре 2025 г. T2 приобрела платформу Umnico, '
    'интеграция которой усилила предложение для корпоративных клиентов и '
    'дополнила существующие сервисы инструментами для работы с '
    'обращениями».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += публичная презентация продукта (апрель 2026)")
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
