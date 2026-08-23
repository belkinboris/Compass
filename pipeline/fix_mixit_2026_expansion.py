# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g9fc75a9c (ВИМ Инвестиции
вышли из капитала Mixit): дельта-поиск нашёл, как компания развивается
после выхода фондов и отказа от IPO — финансовые показатели за 2025 год
и выход в новые товарные категории (одежда, парфюмерия). Не через
review.py: несколько разных источников на одно поле.

Источники — читал напрямую (fetch_article_texts.py, все закэшированы):
Ведомости (04.06.2026), Retailer.ru (13.03.2026).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g9fc75a9c'
OLD_TARGET_FIN = 'В ноябре 2025 г. компания запустила завод стоимостью 1,4 млрд руб. в Солнечногорске.'
ADDITION = (
    'По данным СПАРК, в 2025 г. выручка ООО «УК Миксит» выросла на '
    '76,8% до 616,8 млн руб., а чистая прибыль составила 14,6 млн руб. '
    'против убытка годом ранее. Прибыль от продаж увеличилась почти в '
    '27 раз и превысила 114 млн руб. Компания продолжила расширять '
    'ассортимент за пределы косметики: в марте 2026 года объявила о '
    'планах выпустить парфюмерию (три аромата объемом 50 и 15 мл), а в '
    'июне 2026 года запустила линейку одежды под маркой «Mixit Wear» — '
    'первую продукцию под этой маркой компания планирует начать '
    'продавать уже в конце июня, лимитированной партией, продажи '
    'исключительно онлайн.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"

    print(f"{CARD_ID} eco.target_fin: += финансы 2025 года и выход в одежду/парфюмерию")
    deal['eco']['target_fin'] = NEW_TARGET_FIN

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
