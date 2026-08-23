# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g43b0394d (Wildberries и
Russ приобрели «Инфо-Ю»): Коммерсантъ (kommersant.ru/doc/8096717) даёт
цепочку бенефициаров покупателя до конечных физлиц (карточка знала
только доли Wildberries/Russ Outdoors, не дальше) и два факта о
продавцах/предмете, которых не было. Не через review.py: старые
значения law.struct/eco.context — из других источников (sostav.ru/РБК),
не образуют непрерывный кусок с цитатой Коммерсанта.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
Коммерсантъ (kommersant.ru/doc/8096717).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g43b0394d'

OLD_STRUCT = (
    'Теперь продажи рекламного инвентаря в регионе централизованы и '
    'осуществляются через инфраструктуру Russ.'
)
STRUCT_ADDITION = (
    'По данным Rusprofile, созданное в июле 2024 года ООО «РВБ» получило '
    'контроль над 99% ООО «Русс Аутдор» (ещё 1% — у московского АО '
    '«Олимп», которым владеет ООО «РВБ»); собственниками самого ООО '
    '«РВБ» выступают ООО «Вайлдберриз» (65%) Татьяны Ким и Владислава '
    'Бакальчука и ООО «Стинн» (35%) — 50% «Стинн» принадлежит Григорию '
    'Садояну, ещё 50% ЗПИФ «Гало» (управляется ростовским ООО УК '
    '«Эмрис», основной владелец — Алексей Власов).'
)
NEW_STRUCT = OLD_STRUCT + ' ' + STRUCT_ADDITION

OLD_CONTEXT = (
    'ООО «РВБ» (Группа WBR) — совместная компания Russ и Wildberries, '
    'созданная в 2024 году. Доли участников: 65% — Wildberries, 35% — '
    'Russ Outdoors. Финансовые показатели группы за 2024 год: Оборот — '
    '4,1 трлн руб. (+60% г./г.). Чистая прибыль — 104 млрд руб. Группа '
    'управляет классическими и цифровыми носителями в более чем 150 '
    'городах России, включая Москву и Санкт-Петербург. Суммарный '
    'месячный охват аудитории превышает 85 млн человек.'
)
CONTEXT_ADDITION = (
    'Продавцы, Татьяна Плахотникова и Леонид Рудой, также владеют '
    'равными долями в тамбовском ООО «Монтажреклама» того же профиля — '
    'этот актив в сделку не вошёл. Покупка «Инфо-Ю» — не разовая сделка: '
    'в том же месяце группа Russ объявила о покупке оператора '
    '«Транспортная Реклама» в Новосибирске, а весной 2024 года —'
    ' операторов «Восток-Медиа», «Билборд-68» и «Компания СТА».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} law.struct: += цепочка бенефициаров РВБ до физлиц")
    print(f"{CARD_ID} eco.context: += исключённый актив продавцов, стратегия скупки Russ")
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
