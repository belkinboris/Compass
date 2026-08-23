# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gadb5b474 (Ростех продал
«Техсервис» «ИГ Геоинвест»): дельта-поиск нашёл причину продажи (низкое
содержание золота в руде, удалённость и отсутствие энергоинфраструктуры
— работа на дизельных генераторах) и управленческую смену после сделки
(Елисеев покинул пост директора «Техсервиса», сменщик — Виктор Ефремов).
Не через review.py: старые значения eco.context/law.struct — из другого
источника (Коммерсантъ), не образуют непрерывный кусок с этой цитатой.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
ircity.ru (09.10.2025), уже добавлен в src.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gadb5b474'

OLD_CONTEXT = (
    'Ранее интерес к приобретению «Техсервиса» проявляла структура '
    '«Росатома» (см. “Ъ” от 7 декабря 2022 года), но до сделки, судя по '
    'всему, не дошло.'
)
CONTEXT_ADDITION = (
    'Месторождения находятся далеко от крупных дорог и населённых '
    'пунктов, а рядом нет энергетической инфраструктуры — предприятие '
    'работает на дизельных генераторах, что сильно увеличивает расходы. '
    'По словам экспертов, именно из-за низкого содержания золота в '
    'руде, проблем с инфраструктурой и больших затрат «Ростех» решил '
    'выйти из проекта.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION

OLD_STRUCT = (
    '100% долей «Техсервиса» переданы в залог ООО «РТ – Развитие '
    'бизнеса», учрежденного госкорпорацией «Ростех».'
)
STRUCT_ADDITION = (
    'Игорь Елисеев, один из продавцов, также был директором '
    '«Техсервиса», но в октябре 2025 года покинул этот пост; по данным '
    'системы «Контур.Фокус», гендиректором «Техсервиса» стал Виктор '
    'Ефремов.'
)
NEW_STRUCT = OLD_STRUCT + ' ' + STRUCT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} eco.context: += причина продажи (инфраструктура, содержание золота)")
    print(f"{CARD_ID} law.struct: += смена директора после сделки")
    deal['eco']['context'] = NEW_CONTEXT
    deal['law']['struct'] = NEW_STRUCT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
