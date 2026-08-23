# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gbb7e25e1 (Wildberries и
Russ приобрели туроператора Fun&Sun): дельта-поиск нашёл в Коммерсанте
(kommersant.ru/doc/8140246) один абзац, несущий сразу несколько фактов
сверх уже известного — структуру собственности продавца, чистую прибыль
предмета (в карточке была только выручка), масштаб турагентской сети и
факт регистрации «РВБ Трэвел» в июле 2025 года (до сделки). Не через
review.py: старые значения трёх полей — из ДРУГИХ источников (Известия,
данные бухотчётности), не образуют непрерывный кусок с новой цитатой.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
Коммерсантъ (kommersant.ru/doc/8140246).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbb7e25e1'

OLD_CONTEXT = (
    'В сентябре 2025 года Wildberries&Russ и Fun&Sun договорились о '
    'партнерстве в развитии туристических сервисов для пользователей '
    'цифровой платформы. Первым продуктом в рамках сотрудничества стала '
    'услуга раннего бронирования туров Fun&Sun на сезон зима 2025–2026 '
    'на маркетплейсе Wildberries. Wildberries развивает туристическое '
    'направление с 2023 года.'
)
CONTEXT_ADDITION = (
    'Fun&Sun создан на базе совместного предприятия «Севергрупп» и TUI '
    'Group (контрольный пакет с 2008 года у кипрской Unifirm Ltd, '
    'принадлежащей Алексею Мордашову); ранее работал под брендом «TUI '
    'Россия», сменил название в 2022 году. Туроператор обслуживает '
    'около 12 тыс. турагентов.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION

OLD_TARGET_FIN = (
    'По итогам 2024 года выручка «ТТ-трэвел» (юридическое лицо Fun&Sun) '
    'составила 104,4 млрд рублей, показав рост на 46,2% по сравнению с '
    'предыдущим годом.'
)
TARGET_FIN_ADDITION = (
    'По данным Коммерсанта, выручка в 2024 году превысила 104 млрд руб. '
    'с чистой прибылью почти в 5 млрд руб.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + ' ' + TARGET_FIN_ADDITION

OLD_STRUCT = (
    'В декабре 2025 года он стал единственным собственником основного '
    'юрлица Fun&Sun, следует из пояснений к бухгалтерской отчетности '
    'компании.'
)
STRUCT_ADDITION = (
    'В июле 2025 года Wildberries & Russ зарегистрировала подразделение '
    '«РВБ Трэвел» для туроператорской и экскурсионной деятельности — за '
    'три месяца до объявления сделки.'
)
NEW_STRUCT = OLD_STRUCT + ' ' + STRUCT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, \
        f"eco.target_fin: неожиданное значение {deal['eco']['target_fin']!r}"
    assert deal['law']['struct'] == OLD_STRUCT, \
        f"law.struct: неожиданное значение {deal['law']['struct']!r}"

    print(f"{CARD_ID} eco.context: += структура собственности Fun&Sun, масштаб сети")
    print(f"{CARD_ID} eco.target_fin: += чистая прибыль ~5 млрд ₽")
    print(f"{CARD_ID} law.struct: += регистрация «РВБ Трэвел» (июль 2025)")
    deal['eco']['context'] = NEW_CONTEXT
    deal['eco']['target_fin'] = NEW_TARGET_FIN
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
