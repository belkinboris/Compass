# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
gb9a22f5f («Русский Стандарт водка» продаёт офисно-складской комплекс)
— первая узкая дельта поверх полного обыска (25.08.2026): найдена
процедурная деталь торгов и уточнение по свободной земле в лоте.
Проверено лично прямым WebFetch.

`eco.context` (дополнено). Дословно (mr-7.ru, 24.08.2026): «Российский
аукционный дом (РАД) 24 августа объявил о проведении закрытых торгов,
на которых попытаются продать офисно-складской комплекс», «Одно из
преимуществ лота — "2,5 га свободной земли"» (замглавы департамента
РАД в Петербурге Дарья Гончарова) — уточняет уже известный размер
участка (5,45 га): половина свободна от застройки.

НЕ ВКЛЮЧЕНО: причина продажи не раскрывается ни одним источником (сама
статья dp.ru прямо пишет «Причины продажи не раскрываются»); признаков
более широкой распродажи активов холдинга «Руст» в 2026 году не
найдено; конкретные претенденты на лот, судьба аренды «Руст
Инкорпорэйтэд» и консультанты торгов — не найдены ни в одном
источнике. Торги назначены на 28 сентября 2026 года — статус
«Обсуждается» не меняется, исход ещё не наступил.

Запуск: python3 pipeline/fix_rst_ibs_auction_closed_form.py
        python3 pipeline/fix_rst_ibs_auction_closed_form.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb9a22f5f'

OLD_CONTEXT = (
    'Российский аукционный дом (РАД) назначил на 28 сентября торги по '
    'продаже офисно-складского комплекса на Пулковском шоссе, 52 в '
    'Шушарах. Как указано в объявлении, здание 2007 года постройки '
    'общей площадью 9 049,7 м2 реализуется вместе с участком 5,45 га.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Торги закрытые: «Российский аукционный дом (РАД) 24 августа '
    'объявил о проведении закрытых торгов, на которых попытаются '
    'продать офисно-складской комплекс». По словам замглавы '
    'департамента РАД в Петербурге Дарьи Гончаровой, «одно из '
    'преимуществ лота — "2,5 га свободной земли"» (mr-7.ru).'
)

NEW_SRC = ['mr-7.ru', 'https://mr-7.ru/articles/2026/08/24/ofisno-skladskoi-kompleks-na-pulkovskom-shosse-prodaiut-za-dva-milliarda-rublei-news']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src']), 'источник уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
