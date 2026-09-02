# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка ga1f2b443
(«УльтимаТек приобрёл доли в Датана и Датабриз», закрыта июль 2023) —
не были перенесены санкции против «Датана», стратегия дальнейшего
выделения вендорского направления и рост показателей после сделки.

Проверено лично прямым WebFetch (ComNews, https://www.comnews.ru/content/239169/2025-05-15/2025-w20/1013/prodavat-znachit-prodavat-nelzya-putat-turizm-emigraciey):
Павел Растопшин, гендиректор ГК «УльтимаТек» — «Все эти компании
занимаются вендорским бизнесом (продуктовой разработкой), и мы
рассматриваем возможность привлечь в него внешних инвесторов. В
«УльтимаТек» мы инвесторов не зовем — интеграционный бизнес должен
развиваться органически».

Проверено лично прямым чтением кэша (TAdviser, дозабран
`fetch_article_texts.py`, https://www.tadviser.ru/index.php/Компания:Датана_(Datana)):
«В феврале 2024 года компания Datana попала в санкционный SDN-список
США»; «По итогам 2024 года... «Датана» получил 138,5 млн рублей
выручки. Это на 79,8% больше по сравнению с предыдущим годом, когда
компания показала результат в 77,05 млн рублей» — то есть после
провального 2022 года (убыток 133 млн ₽) компания впервые вышла в
плюс.

НЕ ВКЛЮЧЕНО: точная структура и даты перехода долей «Датана»/«Датабриз»
в холдинг «Экспанта» — по данным TAdviser (текущий реестр) доли уже
показаны за «Экспантой» с июля-августа 2024 года, что расходится с уже
записанным в CLAUDE.md выводом о выделении «Экспанты» в декабре
2024-го; расхождение не разрешено в этом прогоне, переносить в карточку
конкретные проценты и даты не стал, чтобы не закрепить противоречие.
Консультанты сделки и точная сумма — по-прежнему нигде не названы.
Механика «двухступенчатой сделки» по выкупу «Датана» (уже упомянута в
`extra`) — ни один источник её не детализирует.

Запуск: python3 pipeline/fix_ultimatek_datana_databriz_growth_and_context.py
        python3 pipeline/fix_ultimatek_datana_databriz_growth_and_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga1f2b443'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'По словам гендиректора ГК «УльтимаТек» Павла Растопшина, вендорский '
    '(продуктовый) бизнес компаний вроде «Датана» и «Датабриз» развивают '
    'отдельно от интеграционного бизнеса самой «УльтимаТек», рассчитывая '
    'привлечь в него внешних инвесторов: «В «УльтимаТек» мы инвесторов '
    'не зовём — интеграционный бизнес должен развиваться органически». '
    'В феврале 2024 года «Датана» попала в санкционный SDN-список США.'
)

OLD_ECO_TARGET_FIN = (
    'Выручка ООО «Датана» в 2022 г. составила 45,5 млн руб. (в 2021 г. '
    '- 53,6 млн руб.), при этом два последних года компания закончила с '
    'чистым убытком: 133 млн руб. в 2022 г. и 58,7 млн руб. годом ранее. '
    'Выручка ООО «Датабриз» в 2022 г. достигла почти 16,7 млн руб. (при '
    'чистой прибыли 3,4 млн руб.), а в 2021 г. превысила 12,3 млн руб. '
    '(чистая прибыль — почти 2 млн руб.)'
)
NEW_ECO_TARGET_FIN = OLD_ECO_TARGET_FIN + (
    ' После сделки «Датана» впервые вышла в плюс: выручка выросла с '
    '77,05 млн ₽ (2023) до 138,5 млн ₽ (2024, +79,8%).'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/239169/2025-05-15/2025-w20/1013/prodavat-znachit-prodavat-nelzya-putat-turizm-emigraciey'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Датана_(Datana)'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    new_src = deal['src'] + NEW_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
