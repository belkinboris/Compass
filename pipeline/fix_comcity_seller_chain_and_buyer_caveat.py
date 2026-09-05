# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g560a4b70` («Совкомбанк приобрёл бизнес-центр Comcity у Inventa»,
август 2022, Закрыта) — `eco.context` был заглушкой («—»), а
единственный источник карточки — телеграм-агрегатор (@dealsma), сам
переславший пост ДРУГОГО канала (Filatoff Inc.), который прямо
квалифицирует вывод как предположение консультантов рынка, а не факт.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- vedomosti.ru/realty/articles/2022/12/16/955561-ppf-group-prodala-esche-dva-aktiva:
  продавцом в предыдущей, более ранней сделке (октябрь 2022) выступила
  «входящая в чешскую PPF Group компания PPF Real Estate», покупателем
  — «инвесткомпания Inventa», управляющая активами «израильско-
  грузинского бизнесмена Авигдора Ярдени»; «в середине октября новым
  владельцем фирмы Comcity Office B.V., на балансе которой находится
  Comcity, стала инвесткомпания Inventa»; рыночная оценка — «около
  25–27 млрд руб. без учета НДС»;
- interfax.ru/business/913150 (25.07.2023): о перерегистрации
  управляющей компании Anthemona в калининградский САР — «Информация о
  покупателе компании в отчетности группы не отражена» — то есть даже
  на момент публикации Интерфакс НЕ подтверждает Совкомбанк как
  покупателя, только фиксирует, что новый владелец не раскрыт;
- realty.ria.ru/20250725/comcity-2031365167.html (25.07.2025, самый
  свежий найденный материал): Совкомбанк описан только как АРЕНДАТОР
  («Совкомбанк арендовал 10,2 тысячи квадратных метров в комплексе...
  банк занимает в комплексе почти 15 тысяч квадратных метров»), о
  собственнике комплекса статья не сообщает ничего.

НЕ ВНЕСЕНО и добавлено в раздел «Известные проблемы» CLAUDE.md: сама
ПРЕМИСА карточки (Совкомбанк как покупатель Comcity у Inventa) не
подтверждена ни одним материалом делового СМИ — только телеграм-постом
со ссылкой на «консультантов рынка». Структурные поля (`buyer`/
`seller`/`status`) НЕ трогаются: решение о судьбе карточки — либо
пометить премису неподтверждённой прямо в тексте, либо оставить как
есть с оговоркой — за человеком.

Запуск: python3 pipeline/fix_comcity_seller_chain_and_buyer_caveat.py
        python3 pipeline/fix_comcity_seller_chain_and_buyer_caveat.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g560a4b70'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'До этого, в октябре 2022 года, Comcity сменил владельца впервые: '
    'чешская PPF Real Estate продала комплекс инвесткомпании Inventa, '
    'управляющей активами израильско-грузинского бизнесмена Авигдора '
    'Ярдени (рыночная оценка на тот момент — 25–27 млрд ₽ без НДС). '
    'Переход к Совкомбанку в 2023 году ни разу не подтверждён деловым '
    'изданием напрямую — Интерфакс на дату перерегистрации управляющей '
    'компании прямо писал, что «информация о покупателе... не '
    'отражена», а самая свежая публикация (июль 2025 года) называет '
    'Совкомбанк только крупным арендатором комплекса (почти 15 тыс. '
    'кв. м), не упоминая его как собственника.'
)

OLD_SRC = [['@dealsma (Telegram)', 'https://t.me/dealsma/4223']]
NEW_SRC = OLD_SRC + [
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2022/12/16/955561-ppf-group-prodala-esche-dva-aktiva'],
    ['Интерфакс', 'https://www.interfax.ru/business/913150'],
    ['РИА Недвижимость', 'https://realty.ria.ru/20250725/comcity-2031365167.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
