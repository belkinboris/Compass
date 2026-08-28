# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g77b24b1c (ООО «Хайв»
инвестировала в Briskly): дельта-поиск нашёл ВТОРОЙ раунд того же
инвестора в тот же стартап — карточка знала только первый (2024 год).
Цитаты подтверждены лично прямым WebFetch.

В июле 2025 года «Хайв» нарастил долю в Briskly до 14% (с 10%), а
сооснователь Максим Полетаев размыл свою долю с 44% до 42%. Финансовые
показатели компании за 2024 год при этом ухудшились: выручка почти
удвоилась (с 231 до 415 млн руб.), но чистая прибыль 2023 года (325,7 млн
руб.) обернулась убытком 11,8 млн руб. по итогам 2024 года. Компания
рассматривает выход на IPO (АБН, июль 2025).

Консультантов ни по первому, ни по второму раунду не нашли ни в одном
источнике — честная пустота. Судьбу B-Pay отдельно от общей выручки
компании и новых цифр за 2025 год дельта-поиск не нашёл — показатель «8+
млн покупок на 1,5 млрд ₽» остаётся датированным сентябрём 2024 года
везде.

Запуск: python3 pipeline/fix_hive_briskly_second_round.py
        python3 pipeline/fix_hive_briskly_second_round.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g77b24b1c'

OLD_CONTEXT = (
    'ООО «ХАЙВ» — венчурный фонд, созданный компанией «ВымпелКом», '
    'соинвестором которого в 2024 году стал «ТАГРАС». В настоящий момент '
    'в портфеле 15 компаний.'
)
CONTEXT_ADDITION = (
    ' В июле 2025 года «Хайв» нарастил долю в Briskly до 14% (с 10%), а '
    'сооснователь Максим Полетаев снизил участие с 44% до 42%. За тот же '
    'период выручка компании выросла почти вдвое, с 231 до 415 млн '
    'рублей, но по итогам 2024 года Briskly показал убыток 11,8 млн '
    'рублей — против чистой прибыли 325,7 млн рублей в 2023-м. По данным '
    'редакции АБН, компания рассматривает выход на IPO (АБН, июль 2025).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['АБН', 'https://abn.agency/2025/07/15/venchurnyj-fond-bilajna-narastil-dolyu-v-startape-briskly/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
