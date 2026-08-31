# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gcf9a2a91
(Топ-менеджер АТОЛ выкупил 100% акций производителя касс) — единственный
источник был Telegram-агрегатором (@dealsma), покупатель не назван по
имени, а `extra` нёс непроверяемую версию о финансировании со стороны
Андрея Кирикова.

Проверено лично прямым WebFetch (CNews, 23.12.2024, 10:12,
cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya):
«Все активы приобрел бывший CEO Роман Володин», «Макаровым, по данным
СПАРК, принадлежало по 50% в компании» (независимо подтверждено
mergers.ru, RB.RU, PLUSworld — все датированы тем же днём). Причина
срыва более ранних переговоров с «Софтлайном»: «компания вышла из части
переговоров из-за текущей ключевой ставки, а ее оценка стоимости бизнеса
"Атол" могла не оправдать ожидания собственников».

`src` заменён: Telegram-агрегатор — на первоисточники (CNews, mergers.ru).
`buyer_name` заполнен («Роман Володин», бывший гендиректор АТОЛ; профиля
компании для физлица нет). `title` уточнён именем покупателя.
`eco.context` дополнен причиной срыва переговоров с «Софтлайном».

Версия о финансировании от Андрея Кирикова (владелец «Сибирского
цемента») из `extra` СНЯТА, а не перенесена в другое поле: прямая
проверка (WebFetch CNews, mergers.ru, RB.RU, PLUSworld, попытки RBC/TASS
— недоступны, 401/403) не нашла имени «Кириков» ни в одном источнике;
единственная страница, где оно всплыло в поисковой выдаче рядом с
«АТОЛ» (kompromat1.online), при прямом чтении оказалась вообще не про
это — про офшорные схемы других лиц, без единого слова о Кирикове или
«Сибирском цементе». Оставлять непроверяемую версию как факт карточки
нельзя — честная пустота лучше правдоподобной догадки.

НЕ ВКЛЮЧЕНО: смена гендиректора на Александра Бочкова (13.11.2024, до
завершения сделки) и рост выручки АТОЛ в 2024 году (агрегированная
цифра из непроверенной построчно выдачи финансовых баз) — оба факта
не проверены дословным прямым чтением первоисточника, оставлены на
будущий заход.

Запуск: python3 pipeline/fix_atol_volodin_buyer_and_real_source.py
        python3 pipeline/fix_atol_volodin_buyer_and_real_source.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcf9a2a91'

OLD_TITLE = 'Топ-менеджер АТОЛ выкупил 100% акций производителя касс'
NEW_TITLE = 'Бывший гендиректор АТОЛ Роман Володин выкупил 100% акций производителя касс'

OLD_EXTRA = (
    'Выкуп 100% долей холдинговой компании ООО «УК «АТОЛ»» '
    'топ-менеджером. Возможно привлечение финансирования от Андрея '
    'Кирикова (основатель холдинга «Сибирский цемент»).'
)
NEW_EXTRA = (
    'Выкуп 100% долей холдинговой компании ООО «УК «АТОЛ»» бывшим '
    'гендиректором Романом Володиным. Основателям компании, Алексею и '
    'Ирине Макаровым, принадлежало по 50%.'
)

OLD_SRC = [['@dealsma (Telegram)', 'https://t.me/dealsma/5654']]
NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya'],
    ['Mergers.ru', 'https://mergers.ru/news/U-krupnejshego-rossijskogo-proizvoditelya-kassovogo-oborudovaniya-ATOL-smenilsya-sobstvennik-84549'],
]

OLD_CONTEXT = (
    'В феврале «Коммерсантъ» писал, что переговоры о покупке АТОЛ ведет '
    'IT-компания «Софтлайн». По словам источника издания, переговоры '
    'находились в завершающей стадии, сумма сделки оценивалась в 5 млрд '
    'руб.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Переговоры сорвались: «компания вышла из части переговоров из-за '
    'текущей ключевой ставки, а ее оценка стоимости бизнеса "Атол" '
    'могла не оправдать ожидания собственников» (CNews, 23 декабря 2024 '
    'года).'
)

NEW_BUYER_NAME = 'Роман Володин'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['title'] == OLD_TITLE
    assert deal['extra'] == OLD_EXTRA
    assert deal['src'] == OLD_SRC
    assert deal['eco']['context'] == OLD_CONTEXT
    assert 'buyer_name' not in deal
    assert deal['buyer'] is None

    print('=== title: станет ===')
    print(NEW_TITLE)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: станет ===')
    for s in NEW_SRC:
        print(s)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)

    if write:
        deal['title'] = NEW_TITLE
        deal['extra'] = NEW_EXTRA
        deal['src'] = NEW_SRC
        deal['eco']['context'] = NEW_CONTEXT
        deal['buyer_name'] = NEW_BUYER_NAME
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
