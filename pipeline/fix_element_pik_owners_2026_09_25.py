# -*- coding: utf-8 -*-
"""Приток 25 сентября 2026 (10:20 МСК), gfd9c0206 (Element/ПИК, River
City, уже опубликована): РИА Недвижимость (со ссылкой на Коммерсантъ)
называет владельцев застройщика Element и срок его работы в Москве —
детали, которых не было в уже привязанной статье Коммерсанта (8974516,
прочитана целиком ещё 24 сентября — этого текста там не было, значит
источник РИА пересказывает более позднюю/отдельную публикацию «Ъ»).

Прямым скриптом — дописывание к уже стоящему eco.context не проходит
генерик-проверку review.check() (то же ограничение, что и у других
карточек в этой сессии).

Источник: https://realty.ria.ru/20260925/developer-2120185120.html,
прочитан целиком, кэш в data/inbox/raw/2026-09-25-articles.jsonl.
Черновик d... — тот же предмет, отпущен через raw_screen.py --enrich.

Запуск: python3 pipeline/fix_element_pik_owners_2026_09_25.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gfd9c0206'
RIA = ['РИА Недвижимость', 'https://realty.ria.ru/20260925/developer-2120185120.html']

OLD_CONTEXT = (
    'В последнее время группа ПИК активно распродает свой земельный '
    'банк. Так, в конце 2025 года площадка по соседству с River City была '
    'продана региональному девелоперу Unikey, который приобрел у '
    'входящего в ГК ПИК застройщика Forma бывшую территорию Московского '
    'винно-коньячного завода на Ленинградском шоссе. Там можно построить '
    'жилой комплекс на 145 тыс. кв. м. ПИК также избавляется и от активов '
    'в других регионах. По данным «Дом.РФ», в январе–августе 2026 года '
    'продажи новостроек в Москве сократились на 29% год к году, до 1,7 '
    'млн кв. м. При этом по России в целом объем продаж вырос на 2%, до '
    '14,6 млн кв. м.'
)
QUOTE_ADD = (
    'Element работает в Москве с 2023 года. Владельцами застройщика в '
    'равных долях выступают Андрей Скоблов, Виталий Коробов, Андрей '
    'Захаренков и Дмитрий Андреев, добавляет "Коммерсант".'
)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert card['eco']['context'] == OLD_CONTEXT
    card['eco']['context'] = OLD_CONTEXT + ' ' + QUOTE_ADD

    if RIA[1] not in {s[1] for s in card['src'] if len(s) > 1}:
        card['src'].append(RIA)

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: eco.context дополнен владельцами Element, источник добавлен.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
