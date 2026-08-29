# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gf577d893
(Леонид Гольдорт продал 55,44% СДЭК компании «Кластер Капитал»). Факт уже
лежал в самой карточке — но в комментарии `why` к записи консультанта
ПОКУПАТЕЛЯ, а не в поле `law.adv` как отдельная запись (родня уроку
CLAUDE.md «Факт лежит в поле «Дополнительная информация», а не в своём»,
только здесь факт лежал в служебном комментарии таблицы правок, а не на
экране вовсе).

Комментарий к записи ELWI гласил: «Коммерсантъ («Сделки года») прямо
называет ELWI консультантом покупателя, а Denuo — консультантом продавца
в продаже 55,44% СДЭК» — но вторая половина факта (Denuo) не была добавлена
как отдельная запись `law.adv`, и на экране консультант продавца не
показывался вовсе.

Проверено лично прямым WebFetch того же источника, что уже стоит в `src`:
Коммерсантъ («Сделки года»), дословно: «Интересы Леонида Гольдорта по
сделке продажи принадлежащего ему мажоритарного пакета участия в бизнесе
СДЭК представляла юридическая фирма Denuo.»
Источник: https://www.kommersant.ru/doc/7327316 (уже в src)

Запуск: python3 pipeline/fix_sdek_goldort_denuo_advisor.py
        python3 pipeline/fix_sdek_goldort_denuo_advisor.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf577d893'

NEW_ADV_ENTRY = [
    'Юридический консультант продавца (Леонида Гольдорта)',
    'Denuo',
    'Коммерсантъ («Сделки года»), дословно: «Интересы Леонида Гольдорта по '
    'сделке продажи принадлежащего ему мажоритарного пакета участия в '
    'бизнесе СДЭК представляла юридическая фирма Denuo.» Источник: '
    'https://www.kommersant.ru/doc/7327316',
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    adv = deal['law']['adv']
    assert len(adv) == 1, f'ожидалась ровно одна запись adv, найдено {len(adv)}'
    assert adv[0][1] == 'ELWI'
    assert not any(a[1] == 'Denuo' for a in adv), 'Denuo уже в law.adv'

    print('=== law.adv: добавится запись ===')
    print(NEW_ADV_ENTRY)

    if write:
        deal['law']['adv'].append(NEW_ADV_ENTRY)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
