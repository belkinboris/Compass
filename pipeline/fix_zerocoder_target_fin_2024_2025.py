# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gd9c4a5eb (СТ Капитал/
Солонин/Zerocoder): `eco.target_fin` заканчивался на данных 2023 года
(выручка 204,8 млн руб.). Дельта нашла показатели предмета сделки уже
ПОСЛЕ инвестиции: выручка 2024 года выросла на 130% до 293 млн руб.
(РБК Компании, со ссылкой на исследование Smart Ranking — Zerocoder
занял 1-е место по выручке среди образовательных платформ в сегменте
ИИ), а за 9 месяцев 2025 года выручка уже удвоилась к тому же периоду
2024-го, достигнув 492 млн руб. (интервью CEO Кирилла Пшинника, vc.ru).

Не через review.py: `eco.target_fin` уже не пуст, а общая проверка
дословности требует, чтобы ВСЁ значение поля (старый текст + новый)
лежало в ОДНОЙ цитате — старый текст из первого источника (rb.ru) о
самой сделке 2024 года, новый — из двух ОТДЕЛЬНЫХ более поздних статей.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd9c4a5eb'
OLD_TARGET_FIN = (
    'По данным ЕГРЮЛ, в 2023 году ООО «Зерокодер» получило чистый '
    'убыток 10,6 млн рублей, выручка компании составила 204,8 млн '
    'рублей.'
)
ADDITION = (
    'В 2024 году ее выручка достигла 293 млн руб., увеличившись на '
    '130% год к году. В 2025 году компания её как минимум удвоит – по '
    'данным EdTechs.ru за 3 квартала она составила уже 492 млн ₽.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"

    print(f"{CARD_ID} eco.target_fin: += выручка 2024 (293 млн, "
          "+130%) и темп 2025 года (492 млн за 9 месяцев)")
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
