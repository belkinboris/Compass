# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gcface540 (Фонд «Восход» инвестировал в АО «Крибрум») — ШЕСТАЯ подряд
карточка в этой рутине с ошибочным годом: единственный источник
карточки — Telegram-агрегатор @dealsma, а реальная сделка датирована
декабрём 2025 года, не 2024-м. Проверено лично прямым WebFetch.

Год сделки (2024 → 2025) — НЕ через `review.py` (смена года — отдельный
скрипт). Дословно (Агентство Бизнес Новостей, 30.12.2025, 14:32):
«Третьей компанией, вошедшей в портфель фонда, стала платформа
Крибрум», «На раунде А компания привлекла более 300 миллионов рублей
инвестиций» — сумма совпадает с уже известной карточке («300+ млн ₽»).
Независимо подтверждено постом vc.ru от 31.12.2025.

НЕ ВКЛЮЧЕНО: точная доля фонда «Восход» после инвестиции, использование
средств, консультанты сделки, финансовые показатели за более поздний
период — не найдены ни в одном источнике, несмотря на разные углы
поиска. Отдельная, ГОРАЗДО более ранняя (2016-2019 годов) и полностью
не связанная история о неудачной попытке АО «Росинфокоминвест»
инвестировать в «Крибрум» — не перепутана с этой сделкой и не внесена.

Запуск: python3 pipeline/fix_voskhod_kribrum_year.py
        python3 pipeline/fix_voskhod_kribrum_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcface540'

OLD_DATE = '2024'
NEW_DATE = '2025'

NEW_SRC = ['Агентство Бизнес Новостей', 'https://abn.agency/2025/12/30/fond-voshod-investiroval-v-tri-deeptech-startapa-evimed-sensair-i-kribrum/']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert not any(s[1] == NEW_SRC[1] for s in deal['src']), 'источник уже в src'

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== src добавится ===')
    print(NEW_SRC)

    if write:
        deal['date'] = NEW_DATE
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
