# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g7b2a78bf («Guess выкупил 30% долю российского партнера Вячеслава
Шикулова в местном бизнесе», закрыта 22 мая 2023) — судьба бизнеса
после консолидации 100% не прослежена.

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/8860639): «Выручка ООО «Гесс Сиайэс» в
2025 году выросла на 1% год к году, до 6,6 млрд руб., чистый убыток
увеличился в три раза, до 434,3 млн руб.»; «В конце 2025 года в России
сеть управляла 46 точками в Москве, Санкт-Петербурге, Новосибирске,
Воронеже, Хабаровске и других российских городах»; «Новым генеральным
директором... ООО «Гесс Сиайэс» 29 июля стал Олег Силюк» — бизнес не
закрылся и не был продан дальше, продолжает работать и расти сетью,
хотя и с растущим убытком.

НЕ ВКЛЮЧЕНО: смена контроля над интеллектуальными правами на бренд
Guess в США (Authentic Brands Group приобрела 51% IP в январе 2026) —
это отдельная, нероссийская сделка без российского элемента, не
публикуется отдельной карточкой (правило CLAUDE.md); упомянута только
как вероятный контекст кадровых перестановок в России, но без
дословно подтверждённой прямой связи — не вносится как факт. Судьба
других активов Шикулова (Boggi Milano, Robinzon/«Чемодан PRO») —
органический рост (новые магазины), новых сделок M&A не найдено, не
относится к этой карточке.

Запуск: python3 pipeline/fix_guess_shikulov_aftermath.py
        python3 pipeline/fix_guess_shikulov_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7b2a78bf'

OLD_ECO_TARGET_FIN = 'В 2022 году выручка российской Guess выросла на 24%, до 4 млрд руб., чистая прибыль — в 3,5 раза, до 283,1 млн руб.'
NEW_ECO_TARGET_FIN = (
    'В 2022 году выручка российской Guess выросла на 24%, до 4 млрд руб., '
    'чистая прибыль — в 3,5 раза, до 283,1 млн руб. К 2025 году выручка '
    'выросла до 6,6 млрд ₽ (+1% год к году), но чистый убыток увеличился '
    'втрое, до 434,3 млн ₽.'
)

OLD_ECO_CONTEXT = (
    'Он также выступает совладельцем и гендиректором российской структуры '
    'итальянского одежного бренда Boggi Milano и владеет Robinzon Retail '
    'Group. Последняя в 2022 году стала основным владельцем российской '
    'сети магазинов американского производителя чемоданов Samsonite, '
    'которая теперь работает под вывеской «Чемодан PRO».'
)
NEW_ECO_CONTEXT = (
    'Он также выступает совладельцем и гендиректором российской структуры '
    'итальянского одежного бренда Boggi Milano и владеет Robinzon Retail '
    'Group. Последняя в 2022 году стала основным владельцем российской '
    'сети магазинов американского производителя чемоданов Samsonite, '
    'которая теперь работает под вывеской «Чемодан PRO». К концу 2025 '
    'года российская сеть Guess управляла уже 46 точками; 29 июля 2026 '
    'года новым гендиректором ООО «Гесс Сиайэс» стал Олег Силюк.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8860639'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
