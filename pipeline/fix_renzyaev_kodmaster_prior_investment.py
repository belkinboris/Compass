# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень — первая дельта),
карточка g3f0400db (Владелец ГК CorpSoft24 Константин Рензяев
инвестировал в «Кодмастер»): дельта-поиск нашёл предыдущую венчурную
инвестицию того же человека — карточка не знала об инвестиционном
послужном списке Рензяева за пределами этой сделки. Подтверждено лично
прямым WebFetch — это тот же материал, что уже цитировался из CNews, но
опубликованный по другому адресу (поддомен safe.cnews.ru, а не www.),
именно там факт и был лично проверен; абзац про предыдущую инвестицию в
уже стоящей в src ссылке (www.cnews.ru) при первом обыске взят не был.

«Ранее, в 2025 г., Константин Рензяев инвестировал в ООО «Атом» —
разработчика full-stack-платформы для автоматизированной разработки
квантовых регуляторов для робототехники» (CNews).

Консультантов сделки, точную сумму инвестиций и опровержения статуса
дельта-поиск не нашёл ни в одном из шести новых источников — честная
пустота, не тронуто. Найденная в источниках спекулятивная версия причины
падения выручки «Кодмастера» («может объясняться переходом на новую
продуктовую линейку... но для внешнего наблюдателя выглядит тревожно») НЕ
включена — это авторская догадка издания, а не факт от компании, три
равнозначные версии через «или» не проходят стандарт дословного факта.

Запуск: python3 pipeline/fix_renzyaev_kodmaster_prior_investment.py
        python3 pipeline/fix_renzyaev_kodmaster_prior_investment.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3f0400db'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Ранее, в 2025 г., Константин Рензяев инвестировал в ООО «Атом» — '
    'разработчика full-stack-платформы для автоматизированной разработки '
    'квантовых регуляторов для робототехники (CNews).'
)

NEW_SRC = [
    ['CNews', 'https://safe.cnews.ru/news/line/2026-08-18_vladelets_gk_corpsoft24_konstantin'],
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
