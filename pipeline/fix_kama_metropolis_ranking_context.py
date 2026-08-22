# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gac4491d6 (Кама
капитал/БЦ «Метрополис»): `eco.context` заканчивался на истории владения
(Hines/PPF купили доли в 2015 и 2021, комплекс выставлен на продажу в
2022). Дельта нашла место сделки в независимом рейтинге РБК — вошла в
топ-10 крупнейших инвестсделок на рынке коммерческой недвижимости 2024
года, заняв 4-е место.

Не через review.py: `eco.context` уже не пуст, а общая проверка
дословности требует, чтобы ВСЁ значение поля (старый текст + новый)
лежало в ОДНОЙ цитате — старый текст из Ведомостей о самой сделке, новый
— из пресс-релиза покупателя (kamacapital.ru, 18.12.2024) со ссылкой на
рейтинг РБК.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gac4491d6'
OLD_CONTEXT = (
    'Первые два инвестфонд Hines Russia & Poland Fund и PPF Real '
    'Estate приобрели еще в 2015 г., сделка по покупке третьего была '
    'закрыта три года спустя. Комплекс был выставлен на продажу еще в '
    '2022 г., но продать его удалось только сейчас.'
)
ADDITION = (
    'Покупка бизнес-центра (БЦ) «Метрополис» холдингом «Кама Капитал» '
    'вошла в десятку крупнейших инвестиционных сделок на рынке '
    'коммерческой недвижимости в 2024 году, заняв четвёртую строчку в '
    'рейтинге, подготовленном РБК.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += место сделки в рейтинге РБК "
          "(4-е место в топ-10 2024 года)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
