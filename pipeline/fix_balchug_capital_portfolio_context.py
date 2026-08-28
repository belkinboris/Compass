# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf217e953 (Balchug Capital
приобрела ООО «Радуга», производителя кормов для животных, ноябрь 2024):
дельта-поиск нашёл два класса новых фактов, оба подтверждены лично прямым
WebFetch. (1) Уже цитируемый zooinform.ru содержит неизвлечённую деталь —
представитель фирмы заявил об отсутствии планов менять стратегию актива.
(2) Balchug Capital (структура армянских братьев Амарянов) — активный
скупщик российских активов: за 2023-2025 годы также приобрела аэропорт
«Пулково» (в доле, февраль 2023), завод Caterpillar в Тосно (июнь 2024),
Сыктывкарский фанерный завод (декабрь 2024) и, по отдельному распоряжению
президента, российскую «дочку» Goldman Sachs. Это не факт о самой сделке с
«Радугой», а контекст о масштабе и профиле покупателя — уместен в качестве
дополнения к уже описанной инвестиционной стратегии фонда. Не через
review.py: несколько фактов из НЕСКОЛЬКИХ новых источников, plus дополнение
уже процитированного.

Запуск: python3 pipeline/fix_balchug_capital_portfolio_context.py
        python3 pipeline/fix_balchug_capital_portfolio_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf217e953'

OLD_RATIONALE = (
    'В стратегиях прямых инвестиций мы ищем высококачественные активы, '
    'которые недооценены и/или находятся в затруднительном положении из-за '
    'корпоративных, геополитических или других событий и потрясений, — '
    'указано на сайте компании.'
)
RATIONALE_ADDITION = (
    ' Представитель фирмы сообщил, что «никаких серьёзных изменений в её '
    'работе и стратегии не предвидится». Balchug Capital (структура '
    'армянских братьев Амарянов) — активный покупатель российских активов: '
    'за 2023–2024 годы также приобрела долю в аэропорту «Пулково», завод '
    'Caterpillar в Тосно, Сыктывкарский фанерный завод, а по отдельному '
    'распоряжению президента — российскую «дочку» Goldman Sachs.'
)
NEW_RATIONALE = OLD_RATIONALE + RATIONALE_ADDITION

NEW_SRC = [
    ['DP.ru', 'https://www.dp.ru/a/2025/01/20/armjanskij-fond-vsled-za-pulkovo'],
    ['Новая газета', 'https://novayagazeta.ru/articles/2025/01/31/putin-razreshil-balchug-capital-armianskikh-bratev-amarianov-kupit-rossiiskuiu-dochku-goldman-sachs-news'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['rationale'] == OLD_RATIONALE
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.rationale: станет ===')
    print(NEW_RATIONALE)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
