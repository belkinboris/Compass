# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g814d89bf («Михаил Сиволдаев и Корпорация развития Камчатки приобрели
санаторий «Жемчужина Камчатки»», закрыта 14 июня 2023) — прогресс
реновации (заявленный как цель сделки) не был прослежен дальше самого
факта закрытия.

Проверено лично прямым WebFetch (kam24.ru,
https://kam24.ru/news/main/20250819/120011.html): «инвестором в
реновацию здравницы к началу июля вложено более 1 миллиарда 227
миллионов рублей» (данные на середину 2025 года — актуальнее исходных
«свыше 700 млн ₽» на момент закрытия сделки).

Проверено лично прямым WebFetch (Vademecum,
https://vademec.ru/news/2025/01/30/na-vozvedenie-sanatoriya-zhemchuzhina-kamchatki-planiruetsya-napravit-3-mlrd-rubley/):
«инвестор планирует направить на строительство санаторно-курортного
комплекса до 3 млрд рублей»; «получило статус резидента территории
опережающего развития (ТОР) «Камчатка»»; итоговая мощность — 250
номеров, «сможет ежегодно принимать около 146 тысяч человек», «будет
создано 324 рабочих места».

НЕ ВКЛЮЧЕНО: слух о смерти Михаила Сиволдаева, всплывший в одной из
поисковых сводок, — прямая проверка (rusprofile.ru, отдельные
источники 2024-2025 годов, где он назван действующим владельцем «Реам
менеджмент») не подтвердила это, похоже на артефакт спутанных данных
ЕГРЮЛ разных юрлиц; не переносится в карточку как непроверенный слух.
Связь с проектом СПА-отеля «Лагуна» (по одним источникам — актив
«Реам менеджмент», по другим — управляется Cosmos Hotel Group/АФК
«Система») — противоречиво, требует отдельной проверки, не
разрешается додумыванием. Консультанты сделки 2023 года — ни в одном
источнике не названы.

Запуск: python3 pipeline/fix_zhemchuzhina_kamchatki_progress.py
        python3 pipeline/fix_zhemchuzhina_kamchatki_progress.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g814d89bf'

OLD_ECO_CONTEXT = (
    'Михаил Сиволдаев — бывший зампред правления «Реновы» Виктора '
    'Вексельберга. Фонд «Реам менеджмент» управляет активами стоимостью '
    'более $1 млрд'
)
NEW_ECO_CONTEXT = (
    'Михаил Сиволдаев — бывший зампред правления «Реновы» Виктора '
    'Вексельберга. Фонд «Реам менеджмент» управляет активами стоимостью '
    'более $1 млрд. К середине 2025 года в реновацию здравницы вложено '
    'более 1,227 млрд ₽ (изначальный план — свыше 700 млн ₽); проект '
    'получил статус резидента территории опережающего развития (ТОР) '
    '«Камчатка», плановый объём инвестиций вырос до 3 млрд ₽, итоговая '
    'мощность — 250 номеров, около 146 тыс. посетителей в год и 324 '
    'рабочих места.'
)

NEW_SRC = [
    ['kam24.ru', 'https://kam24.ru/news/main/20250819/120011.html'],
    ['Vademecum', 'https://vademec.ru/news/2025/01/30/na-vozvedenie-sanatoriya-zhemchuzhina-kamchatki-planiruetsya-napravit-3-mlrd-rubley/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
