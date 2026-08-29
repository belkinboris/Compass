# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g1d1ff6b2
(Продажа 24% в ООО «Азимут Кострома» компанией Azimut Hotels, август
2024). Единственный источник карточки был телеграм-агрегатором
(@dealsma) — дельта-поиск нашёл настоящий первоисточник в деловом СМИ и
уточнил цену и мотив продажи. Все факты проверены лично прямым WebFetch.

1) `eco.rationale` (новое поле) — интервью гендиректора Azimut Hotels
Максима Бродовского РБК, 22.01.2025 (доступно через зеркало
ru.hotel.report, прямой rbc.ru отдаёт 401 для WebFetch): «Объект в
Костроме, в свою очередь, работал в сети Azimut довольно давно. В
какой-то момент компания подошла к решению о необходимости реновации
гостиницы» — «После этого сеть начала искать под этот проект
соинвестора, который бы получил долю» — «Но в итоге переговоры пришли к
продаже, а предложение компанию устроило». То есть продажа — не
изначальный план, а результат несостоявшихся переговоров о партнёрстве
под реновацию.

2) `eco.val` (уточнение) — KP.RU Кострома: «в 2023 году стоимость
бизнеса снизилась с 216 до 185 миллионов рублей» — уже стоящая в карточке
цифра 216 млн ₽ была стартовой ценой объявления, а не финальной;
итоговая цена сделки по-прежнему нигде не раскрыта.

НЕ включены: подробности о покупателе Елисее Батине (местная пресса
характеризует его как костромского предпринимателя с гостинично-
арендным бизнесом с середины 2000-х — интересно для профиля компании,
но не факт о самой сделке); консультанты сделки; судьба отеля в 2025-2026
(работает под именем «СУСАНИН Парк Отель», данных о новых инвестициях
после ребрендинга не нашлось).

Запуск: python3 pipeline/fix_azimut_kostroma_real_source_and_rationale.py
        python3 pipeline/fix_azimut_kostroma_real_source_and_rationale.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g1d1ff6b2'

NEW_RATIONALE = (
    'Гендиректор Azimut Hotels Максим Бродовский объяснил продажу так: '
    '«Объект в Костроме... работал в сети Azimut довольно давно. В '
    'какой-то момент компания подошла к решению о необходимости реновации '
    'гостиницы» — «После этого сеть начала искать под этот проект '
    'соинвестора, который бы получил долю» — «Но в итоге переговоры '
    'пришли к продаже, а предложение компанию устроило» (РБК).'
)

OLD_VAL = 'Стоимость отеля, выставленного на продажу на одном из популярных сайтов региона, оценивалась в ₽216 млн.'
VAL_ADDITION = (
    ' К моменту сделки цена снизилась: «в 2023 году стоимость бизнеса '
    'снизилась с 216 до 185 миллионов рублей» (KP.RU Кострома) — итоговая '
    'цена сделки по-прежнему нигде не раскрыта.'
)
NEW_VAL = OLD_VAL + VAL_ADDITION

NEW_SRC = [
    ['РБК', 'https://www.rbc.ru/business/22/01/2025/67603dc69a7947d082db9cc2'],
    ['КП Кострома', 'https://www.kostroma.kp.ru/online/news/5963420/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert 'rationale' not in deal['eco'] or not deal['eco']['rationale']
    assert deal['eco']['val'] == OLD_VAL
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['eco']['val'] = NEW_VAL
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
