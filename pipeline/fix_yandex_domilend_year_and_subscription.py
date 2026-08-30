# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g64141daa (Яндекс купил оставшуюся долю в «Домиленд») — карточка несла
год 2024, хотя сделка закрылась в мае 2025 года, а платформа уже
запустила первый заметный продукт под Яндексом. Проверено лично прямым
WebFetch двух источников.

Год сделки (2024 → 2025) — НЕ через `review.py` (смена года — отдельный
скрипт). Дословно (Интерфакс, 12.05.2025, 09:58): «6 мая 100% платформы
перешло двум структурам "Яндекса" – ООО "Технояк" и ООО "Яндекс.Доставка
Холдинг"», «Продавцом выступили структуры группы "Самолет". Так, до 6
мая ООО "Самолет-Резерв" владело 75,68% ООО "Клиентский сервис"»,
«Сумма сделки не называется», «команда во главе с... Дарьей Вороновой
перейдет в "Яндекс" и продолжит работу под брендом "Домиленд"» —
независимо подтверждено релизами самого Яндекса и юрфирмы Denuo
(21.05.2025).

`eco.context` (заполнено, было «—»). Дословно (CNews, 13.03.2026):
«объявила о запуске новой бизнес-модели — подписки для жителей на
умные сценарии в ЖК», «Первым партнером proptech-платформы стал
девелопер "А101"» — первый заметный продукт «Домиленда» под Яндексом,
почти год спустя после закрытия сделки.

НЕ ВКЛЮЧЕНО: точная сумма сделки — все пять проверенных источников
(РИА, Интерфакс, сам Яндекс, Denuo, Право.ру) прямо говорят «сумма не
называется»; юридический консультант ПОКУПАТЕЛЯ (Яндекса) — не найден
ни в одном источнике, названные консультанты (Denuo) сопровождали
только продавца.

Запуск: python3 pipeline/fix_yandex_domilend_year_and_subscription.py
        python3 pipeline/fix_yandex_domilend_year_and_subscription.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g64141daa'

OLD_DATE = '2024'
NEW_DATE = '2025'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Дословно (CNews, 13 марта 2026): «объявила о запуске новой '
    'бизнес-модели — подписки для жителей на умные сценарии в ЖК», '
    '«Первым партнером proptech-платформы стал девелопер "А101"» — '
    'первый заметный продукт «Домиленда» под Яндексом.'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1025082'],
    ['CNews', 'https://www.cnews.ru/news/line/2026-03-13_domilend_zapuskaet_podpisku'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
