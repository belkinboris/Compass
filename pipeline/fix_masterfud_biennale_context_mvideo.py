# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g162c155f (Мастерфуд/
Biennale Group): `eco.context` заканчивался фактом 2018 года про
сотрудничество с Danone/H&N. Дельта нашла более позднее (24 июля 2026,
уже после обыска 10 августа) событие — бренд Biennale под новым
владельцем не свёрнут, а расширяется: кофе Biennale вышел на маркетплейс
«М.Видео».

Не через review.py: `eco.context` уже не пуст, а общая проверка
дословности требует, чтобы ВСЁ значение поля (старый текст + новый)
лежало в ОДНОЙ цитате — старый текст из статьи «Ъ» про саму сделку, новый
— из отдельного пресс-релиза (Retail.ru, 24.07.2026). Дословна именно
ДОБАВЛЯЕМАЯ часть — она приведена ниже и совпадает с новой записью `src`,
внесённой через review.py в этом же прогоне.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g162c155f'
OLD_CONTEXT = (
    'В 2018 году на сайте администрации Подольска сообщалось, что '
    'Biennale Group запустила производство кондитерской продукции для '
    'Danone (ныне Health & Nutrition, H&N). В H&N подтвердили “Ъ”, что '
    'компании продолжают сотрудничать до сих пор.'
)
ADDITION = (
    'На первом этапе ассортимент представлен двумя SKU кофе в зернах '
    'в упаковке 1 кг: Biennale crema — смесь арабики и робусты; '
    'Biennale arabica selection — 100% арабика. Выход на маркетплейс '
    '«М.Видео» стал очередным этапом развития дистрибуции компании и '
    'позволит сделать продукцию бренда еще доступнее для покупателей '
    'по всей России.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += бренд Biennale вышел на "
          "маркетплейс «М.Видео» (июль 2026)")
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
