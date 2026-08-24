# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g38e5718e (Ордовский-
Танаевский Бланко приобрёл 60% «Ной-М», сеть «ПиццаН»): дельта-поиск
нашёл личности миноритариев (в карточке были только доли без имён),
масштаб портфеля покупателя и рыночный контекст падения сети (кризис
пиццерий в России 2025 года). Не через review.py: старые значения
law.struct/eco.context — из другого источника (Коммерсантъ), не
образуют непрерывный кусок с новыми цитатами.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
Lenta.ru (26.09.2025) и logistics.ru (обзор рынка пиццерий).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g38e5718e'

OLD_STRUCT = (
    'Господин Ордовский-Танаевский Бланко пояснил “Ъ”, что получил '
    'долю в обмен на консультирование.'
)
STRUCT_ADDITION = (
    'Оставшиеся доли принадлежат совладельцу сети One Price Coffee '
    'Алексею Чайке (10%) и гендиректору ООО «Корпэстейт» (контролируется '
    '«Ростик») Светлане Берснёвой (10%).'
)
NEW_STRUCT = OLD_STRUCT + ' ' + STRUCT_ADDITION

OLD_CONTEXT = (
    'Ной-М» занимается ее развитием с 2022 года после покупки у польской '
    'группы Amrest (см. “Ъ” от 7 июня 2022 года).'
)
CONTEXT_ADDITION = (
    'Покупатель — основатель холдинга «Ростик» и «Росинтер Ресторантс '
    'Холдинг», в портфеле которого 30 различных брендов, включая IL '
    'Patio, «Планету Суши» и «Шикари». Сеть «ПиццаН» работает на базе '
    'Pizza Hut и включает 67 кафе в Москве, Подмосковье, Санкт-Петербурге '
    'и Ленинградской области. Рынок пиццерий в кризисе: по данным '
    '«Яндекс Карт», за год их число в России сократилось на 4% — с 6584 '
    'до 6337 точек, особенно резко в городах-миллионниках (Красноярск '
    '−26,8%, Екатеринбург −24,3%, Пермь −18,2%, Уфа −16,7%); по оценке '
    'NF Group, обороты «ПиццаН» — в 2,5 раза ниже среднерыночных. По '
    'словам директора по развитию Gagawa Алёны Овчинниковой, многие '
    'пиццерии сейчас банкротятся и закрываются — потребители всё реже '
    'посещают пиццерии офлайн, предпочитая онлайн-заказы из dark '
    'kitchen.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} law.struct: += личности миноритариев")
    print(f"{CARD_ID} eco.context: += масштаб покупателя, рыночный кризис пиццерий")
    deal['law']['struct'] = NEW_STRUCT
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
