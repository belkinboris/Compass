# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
gad66fcec (ЗПИФ «Вим недвижимость» купил складской комплекс в Новой
Москве у Parametr) — найден второй независимый источник с оценкой
суммы сделки и деталями по объекту.

Проверено лично прямым WebFetch (MirKvartir.ru, обзор рынка
недвижимости, 26.08.2026, со ссылкой на Коммерсантъ): «Эксперты
оценивают стоимость сделки в 7,5–8,2 млрд рублей. Среди арендаторов
комплекса — «Яндекс.Маркет». В целом склад заполнен на 90%.» Прямую
статью Коммерсанта найти не удалось (поиск по kommersant.ru её не
отдаёт) — цитата взята из независимого агрегатора со ссылкой на
источник, а не выдумана.

`sum`/`eco.sum`: «—» → «7,5–8,2 млрд ₽ (по оценке)» — источник прямо
говорит «оценивают», пометка законна (см. правило sum_is_supported в
review.py). `eco.share`: «—» → факт о заполненности и арендаторе, с
атрибуцией «по данным Коммерсанта» — единственный источник этого
факта, вторым независимым изданием не подтверждён.

НЕ ВКЛЮЧЕНО: причина продажи именно этого объекта Parametr — по
косвенным данным (CRE.ru, 15.05.2025; Ведомости/РИА Недвижимость,
11.06.2026) компания системно монетизирует активы через ЗПИФы, но это
ОТДЕЛЬНАЯ, более мелкая розничная программа (порог входа 1000 ₽,
10-15 тыс. кв.м в 2026 году) — не тождественна этой сделке, и
подставлять её как причину было бы домыслом; планы «Вим недвижимость»
на актив — источники не раскрывают ничего сверх уже известной фразы
«соответствует стратегии фонда».

Запуск: python3 pipeline/fix_vim_nedvizhimost_kuvekino_sum_and_tenant.py
        python3 pipeline/fix_vim_nedvizhimost_kuvekino_sum_and_tenant.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gad66fcec'

OLD_SUM = None
NEW_SUM = '7,5–8,2 млрд ₽ (по оценке)'

OLD_ECO_SUM = '—'
NEW_ECO_SUM = '7,5–8,2 млрд ₽ (по оценке)'

OLD_SHARE = '—'
NEW_SHARE = (
    'По данным Коммерсанта, склад заполнен на 90%, среди арендаторов — '
    '«Яндекс.Маркет».'
)

NEW_SRC = [
    ['MirKvartir.ru', 'https://www.mirkvartir.ru/journal/news/2026/08/26/obzor-klyuchevyh-sobytiy-rynke/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('sum') == OLD_SUM
    assert deal['eco']['sum'] == OLD_ECO_SUM
    assert deal['eco']['share'] == OLD_SHARE

    new_src = deal['src'] + NEW_SRC

    print('=== sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.sum: станет ===')
    print(NEW_ECO_SUM)
    print('\n=== eco.share: станет ===')
    print(NEW_SHARE)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_ECO_SUM
        deal['eco']['share'] = NEW_SHARE
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
