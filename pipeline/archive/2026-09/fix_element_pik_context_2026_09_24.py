# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (20:20 МСК), gfd9c0206 (Element/ПИК, River
City): дополнение eco.context атрибутированной статистикой Дом.РФ о
падении продаж новостроек в Москве (мотив ПИК сдерживать новые проекты и
продавать земельный банк) из «Московской перспективы» — пересказ той же
сделки, но с этой отдельной, названной по источнику деталью, которой не
было у Коммерсанта. Плюс сам источник добавлен в src.

Прямым скриптом — дописывание к уже стоящему eco.context не проходит
генерик-проверку review.check() (то же ограничение, что и для других
карточек в этой сессии).

Источник: https://mperspektiva.ru/topics/peterburgskiy-element-mozhet-kupit-u-pik-ploshchadku-pod-75-tys-kv-m-zhilya-v-moskve/,
прочитан целиком, кэш в data/inbox/raw/2026-09-24-articles.jsonl.

Запуск: python3 pipeline/fix_element_pik_context_2026_09_24.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gfd9c0206'
MPERSPEKTIVA = ['Московская перспектива', 'https://mperspektiva.ru/topics/peterburgskiy-element-mozhet-kupit-u-pik-ploshchadku-pod-75-tys-kv-m-zhilya-v-moskve/']

OLD_CONTEXT = (
    'В последнее время группа ПИК активно распродает свой земельный '
    'банк. Так, в конце 2025 года площадка по соседству с River City была '
    'продана региональному девелоперу Unikey, который приобрел у '
    'входящего в ГК ПИК застройщика Forma бывшую территорию Московского '
    'винно-коньячного завода на Ленинградском шоссе. Там можно построить '
    'жилой комплекс на 145 тыс. кв. м. ПИК также избавляется и от активов '
    'в других регионах.'
)
QUOTE_ADD = (
    'По данным «Дом.РФ», в январе–августе 2026 года продажи новостроек в '
    'Москве сократились на 29% год к году, до 1,7 млн кв. м. При этом по '
    'России в целом объем продаж вырос на 2%, до 14,6 млн кв. м.'
)


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)

    assert card['eco']['context'] == OLD_CONTEXT
    card['eco']['context'] = OLD_CONTEXT + ' ' + QUOTE_ADD

    if MPERSPEKTIVA[1] not in {s[1] for s in card['src'] if len(s) > 1}:
        card['src'].append(MPERSPEKTIVA)

    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: eco.context дополнен, источник добавлен.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
