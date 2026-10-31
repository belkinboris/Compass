# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gd75ae46f
(Продажа ТРЦ «Метрополис» фонду Balchug Capital, закрыта 06.04.2023) —
искали дальнейшую судьбу актива под новым владельцем.

Проверено лично прямым WebFetch. Управление сменилось (Ведомости,
10.07.2024): «данный объект отдан в коммерческое управление "ТПС
недвижимости"» (представители Balchug Capital, мотив не объяснили).
Портфель фонда расширился (CRE.ru, 03.09.2025): «Доля была выкуплена у
фирмы Bardsley Realty с Сейшельских островов и бывшего акционера
Росевробанка Андрея Суздальцева» (16,96% Malltech Holding, владеет ТЦ
«Планета» и «Лето»), «Сделка закрылась 8 августа» — с этим приобретением
«в портфеле девелопера — шесть торгово-развлекательных центров...
общей площадью 870 000 кв. м». Перепродажи самого «Метрополиса» не
зафиксировано.

`eco.context` дополнен обоими фактами.

НЕ ВКЛЮЧЕНО: подробная биография Давида Амаряна (место рождения,
карьера в «Тройке Диалог», история со штрафом за инсайдерскую торговлю)
— относится к личности бенефициара фонда в целом, а не к судьбе именно
этого актива; source (всеостройке.рф) также заметно ниже по
авторитетности, чем уже используемые в базе издания. Точная сумма
сделки по-прежнему не раскрыта — IBC Real Estate (консультант сделки)
прямо это подтверждает, ничего нового не появилось. Финансовые
показатели именно «Метрополиса» отдельно нигде не публиковались —
только совокупные цифры Malltech Holding (другого актива фонда,
не относящегося к этой карточке).

Запуск: python3 pipeline/fix_metropolis_balchug_management_and_portfolio.py
        python3 pipeline/fix_metropolis_balchug_management_and_portfolio.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd75ae46f'

OLD_CONTEXT = (
    'Последний, как утверждают два консультанта, работавших с '
    '«Метрополисом», до сделки с Balchug Capital был единственным '
    'владельцем торгового центра.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Управление сменилось: «данный объект отдан в коммерческое '
    'управление "ТПС недвижимости"» (Ведомости, 10 июля 2024 года), '
    'мотив стороны не объяснили. Портфель фонда расширился: в августе '
    '2025 Balchug Capital выкупил 16,96% Malltech Holding (ТЦ «Планета» '
    'и «Лето») у Bardsley Realty и Андрея Суздальцева — «Сделка '
    'закрылась 8 августа» (CRE.ru, 3 сентября 2025 года), после чего в '
    'портфеле фонда — «шесть торгово-развлекательных центров... общей '
    'площадью 870 000 кв. м».'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2024/07/10/1049033-tps-nedvizhimost-vzyala-v-upravlenie-metropolis'],
    ['CRE.ru', 'https://cre.ru/news/99489'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
