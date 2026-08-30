# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g3f86f907 (Aktivo приобрела логопарк в Краснодарском крае) — карточка
несла год 2024, хотя объект размещён для инвестиций в октябре 2025
года, а само название объекта и фонда были опущены. Проверено лично
прямым WebFetch.

Год сделки (2024 → 2025) — НЕ через `review.py` (смена года — отдельный
скрипт). Дословно (Рамблер/Финансы, 15.10.2025, 16:14): «Платформа
коллективных инвестиций Aktivo разместила для инвестиций логопарк
"Раевская" под Новороссийском», «20 928 м², три корпуса класса "А"»,
«Арендаторы: Wildberries, "Лента", "Интерлогистика"» — совпадает с уже
известной карточке площадью и списком арендаторов; независимо
подтверждено lognews.ru той же датой.

`eco.context` (дополнено). Точное название объекта («Раевская») и
фонда (ЗПИФН «Активо двадцать два», по данным суб-агента с портала
aktivo.ru — не перепроверено личным WebFetch, поэтому название фонда не
вносится дословной цитатой, только название объекта, подтверждённое
WebFetch).

НЕ ВКЛЮЧЕНО: продавец объекта — не назван ни в одном из проверенных
источников; фактическая доходность против обещанных 22,4% годовых — не
подтверждена независимо (только прогнозные оценки аналитиков в разных
материалах, дословно не перепроверены); расширение портфеля Aktivo
(«Активо 23», бизнес-центр «Европа Билдинг») — это отдельный, более
поздний фонд, не относящийся к предмету ЭТОЙ карточки, не внесено;
консультанты сделки — не найдены.

Запуск: python3 pipeline/fix_aktivo_raevskaya_year.py
        python3 pipeline/fix_aktivo_raevskaya_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3f86f907'

OLD_DATE = '2024'
NEW_DATE = '2025'

OLD_CONTEXT = (
    'Данный объект станет вторым логистическим комплексом в портфеле '
    'Aktivo. Ранее она приобрела склад на 19 560 кв.м в Екатеринбурге.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Название объекта — логопарк «Раевская» под Новороссийском: '
    '«Платформа коллективных инвестиций Aktivo разместила для '
    'инвестиций логопарк "Раевская" под Новороссийском», «20 928 м², '
    'три корпуса класса "А"» (Рамблер/Финансы, 15 октября 2025).'
)

NEW_SRC = ['Рамблер/Финансы', 'https://finance.rambler.ru/money/55466044-platforma-kollektivnyh-investitsiy-aktivo-razmestila-dlya-investitsiy-logopark-raevskaya-pod-novorossiyskom/']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_CONTEXT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src']), 'источник уже в src'

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    print(NEW_SRC)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
