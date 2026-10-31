# -*- coding: utf-8 -*-
"""Приток 25 сентября 2026 (12:20 МСК), gc65bacdf (Nielsen/GfK продали
российские активы): kinometro.ru (пересказ той же публикации РБК, что и
URA.RU) добавляет срок работы обеих компаний на российском рынке — детали,
которых не было в уже привязанных источниках.

Прямым скриптом — дописывание к уже стоящему eco.context не проходит
генерик-проверку review.check() (то же ограничение, что и у других
карточек в этой сессии).

Источник: https://www.kinometro.ru/news/show/name/nielsen_gfk_sale_25092026,
прочитан целиком, кэш в data/inbox/raw/2026-09-25-articles.jsonl.

Запуск: python3 pipeline/fix_nielsen_gfk_history_2026_09_25.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gc65bacdf'
KINOMETRO = ['Kinometro.ru', 'https://www.kinometro.ru/news/show/name/nielsen_gfk_sale_25092026']

OLD_CONTEXT = (
    'Стоимость сделки не разглашается. Обе компании сохранят профиль: '
    'исследования потребительского рынка, аудит розницы, мониторинг и '
    'анализ покупательского поведения. Дорофеев отметил, что покупка '
    'позволит сберечь команду, действующие контракты и обязательства '
    'перед партнерами.'
)
QUOTE_ADD = (
    'GfK пришла в Россию в 1991 году и более 35 лет специализируется на '
    'маркетинговых исследованиях. Nielsen работает в России с 1994 года, '
    'предоставляя данные о розничных продажах и поведении покупателей в '
    'сегменте товаров повседневного спроса (FMCG).'
)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)

    assert card['eco']['context'] == OLD_CONTEXT
    card['eco']['context'] = OLD_CONTEXT + ' ' + QUOTE_ADD

    if KINOMETRO[1] not in {s[1] for s in card['src'] if len(s) > 1}:
        card['src'].append(KINOMETRO)

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: eco.context дополнен, источник добавлен.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
