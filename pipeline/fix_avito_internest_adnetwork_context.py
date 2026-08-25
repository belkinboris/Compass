# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g7ccf80f9 (Авито приобрела
ГК Internest — AdRiver и Soloway, декабрь 2024): дельта-поиск нашёл прямое
продолжение стратегической цели сделки — Авито строит внешнюю рекламную
сеть на базе купленной Soloway, тестирование запланировано на III-IV
кварталы 2026 года (ADPASS, Oborot.ru, click.ru, интервью Артёма Кумпеля
на bfm.ru). AdRiver дважды независимо подтверждён как сохранивший
самостоятельность инструмент аудита рекламы — обещание из карточки
выполняется. `eco.context` сейчас пустая заглушка «—». Не через
review.py: цитаты из ЧЕТЫРЁХ новых источников объединены в одно связное
предложение, а не переносятся дословным куском одной статьи.

Запуск: python3 pipeline/fix_avito_internest_adnetwork_context.py
        python3 pipeline/fix_avito_internest_adnetwork_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7ccf80f9'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В феврале 2026 года Авито подтвердила, что строит внешнюю рекламную '
    'сеть на базе купленной платформы Soloway — тестирование запланировано '
    'на третий-четвёртый кварталы 2026 года (компания «постепенно подходит '
    'к пределу внутренних возможностей по наращиванию трафика»). AdRiver '
    'при этом сохраняет независимость как инструмент аудита и верификации '
    'рекламы и продаётся как отдельный сервис на рынке — подтвердил '
    'коммерческий директор Авито Артём Кумпель. Обещание сохранить '
    'самостоятельность AdRiver, данное на момент сделки, выполняется.'
)

NEW_SRC = [
    ['ADPASS', 'https://adpass.ru/avito-zapuskaet-reklamnuyu-set-soloway/'],
    ['Oborot.ru', 'https://oborot.ru/news/avito-zapuskaet-sobstvennyj-analog-rsya-novaya-set-kontekstnoj-reklamy-sozdaetsya-na-baze-soloway-i263919.html'],
    ['BFM.ru', 'https://www.bfm.ru/news/598740'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
