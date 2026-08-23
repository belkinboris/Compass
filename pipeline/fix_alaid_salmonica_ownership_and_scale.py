# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ge4cded31 (Тымлатский
рыбокомбинат/Salmonica приобрёл «Алаид»): дельта-поиск нашёл структуру
владения предметом ДО сделки (KONKURENT.RU, через АиФ-Приморье), масштаб
покупателя и рыночный итог сделки (доля квот на гребешка). Не через
review.py: старые значения law.struct/eco.context — из других
источников, не образуют непрерывный кусок с новыми цитатами; и обе
добавки собраны из фраз, стоящих в РАЗНЫХ местах статей, а не одним
блоком.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
АиФ-Приморье (11.10.2025) и Интерфакс (13.10.2025), уже в src карточки.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge4cded31'

OLD_STRUCT = (
    'В структуре собственности комбината доли распределены следующим '
    'образом: 32,5% принадлежит супруге губернатора Ирине Герасименко, '
    'столько же – Никите Кожемяко. Гендиректор комбината Александр '
    'Литвиненко владеет 30% акций, а сестра губернатора Кожемяко Ольга '
    'Кравченко – 5%.'
)
STRUCT_ADDITION = (
    'До сделки, по данным KONKURENT.RU, 70% акций «Алаида» принадлежало '
    '«Органик проект» Сергея Бачина, а оставшиеся 30% находились в его '
    'прямом владении.'
)
NEW_STRUCT = OLD_STRUCT + ' ' + STRUCT_ADDITION

OLD_CONTEXT = (
    'Ранее основным бенефициаром компании был Сергей Бачин (напрямую и '
    'через ООО «Органик проект»).'
)
CONTEXT_ADDITION = (
    'После приобретения «Алаида» у группы Salmonica будет около 95% '
    'квот на морского гребешка в Дальневосточном бассейне. Тымлатский '
    'рыбокомбинат располагает собственным рыбодобывающим и '
    'вспомогательным флотом из 36 судов, двумя судами по переработке '
    'рыбы и морепродуктов и тремя сезонными перерабатывающими заводами; '
    'группа Salmonica в целом объединяет 10 рыбоперерабатывающих заводов '
    'совокупной мощностью более 100 тыс. тонн рыбы в год.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} law.struct: += структура владения «Алаидом» до сделки (70/30)")
    print(f"{CARD_ID} eco.context: += рыночный итог (95% квот), масштаб покупателя")
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
