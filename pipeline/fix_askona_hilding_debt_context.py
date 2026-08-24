# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g39cb44b9 (Владимир Седов выкупил 73%
«Асконы» у Hilding Anders): дельта-поиск нашёл масштаб финансовых
проблем продавца (общий долг концерна) и планы покупателя на экспансию
после консолидации контроля. Не через review.py: поле eco.context уже
несёт содержание, новые факты — из двух других источников, не образуют
с ним непрерывный кусок текста.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
https://oborot.ru/news/osnovatel-askony-vladimir-sedov-vykupil-73-kompanii-u-shvedskogo-koncerna-hilding-anders-i251640.html
https://ritm-magazine.com/ru/news/novosti-otrasli/vladimir-sedov-vernul-kontrol-nad-gruppoy-kompaniy-askona

Запуск: python3 pipeline/fix_askona_hilding_debt_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g39cb44b9'

OLD_CONTEXT = (
    'С 2010 года партнером ГК «Аскона» стал шведский концерн Hilding '
    'Anders, выкупивший 51% за $100 млн, по оценке экспертов газеты '
    '«Ведомости». Позже в интервью РБК господин Седов назвал эту сумму '
    '«довольно точной». В дальнейшем шведский холдинг увеличил свою '
    'долю в «Асконе» до 73%.'
)
CONTEXT_ADDITION = (
    'Общий долг концерна Hilding Anders превысил 570 млн евро, и '
    'компания была передана кредиторам — эксперты допускают, что сделка '
    'с Седовым могла пройти по цене значительно ниже уплаченной в 2010 '
    'году. После консолидации контроля ГК «Аскона» намерена продолжать '
    'укреплять присутствие в странах СНГ и развивать экспансию на '
    'дружественных рынках.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += масштаб долга Hilding Anders "
          f"(>570 млн €) + планы экспансии в СНГ")
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
