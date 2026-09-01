# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g21beb4c1 (Дмитрий Стрежнев продал автозавод «Урал» менеджменту,
статус «Закрыта») — под новым управлением завод запустил крупную
инвестиционную программу.

Проверено лично прямым WebFetch (Миасский рабочий, 28.12.2024): ВЭБ.РФ
и АО «АЗ «Урал»» подписали кредитное соглашение на создание нового
литейного производства — «Мощность производства составит 45 тысяч
тонн чугунного литья в год», «Общая стоимость проекта составляет 9,5
млрд рублей», «участие ВЭБ.РФ – 2,6 млрд рублей».

НЕ ВКЛЮЧЕНО: прямые цифры выручки/прибыли завода за 2024-2025 годы —
отчётность за эти годы не опубликована в открытых источниках; судьба
Дмитрия Стрежнева и остальных предприятий пакета ОМГ (Ивановский
автокрановый, Тверской экскаватор и др.) — по данным саб-агента, часть
кандидатов на связь с этими активами (ИЗТС, «ИМЗ Автокран») НЕ
подтверждена как принадлежащая структурам Стрежнева, а связаны с
другими собственниками — не переносится без подтверждения.

Запуск: python3 pipeline/fix_ural_zavod_investment_program.py
        python3 pipeline/fix_ural_zavod_investment_program.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g21beb4c1'

OLD_EXTRA = (
    'Сделка касается продажи активов автозавода «Урал» (АО '
    '«Автомобильный завод «Урал»», Миасс) бизнесмена Дмитрия '
    'Стрежнева менеджменту предприятия. Завод производит тяжелые '
    'грузовики и спецтехнику. За 2020 год выручка завода составила 27 '
    'млрд руб, чистая прибыль — 1,4 млрд руб.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' В декабре 2024 года ВЭБ.РФ и завод подписали кредитное '
    'соглашение на создание нового литейного производства мощностью '
    '45 тыс. тонн чугунного литья в год — общая стоимость проекта 9,5 '
    'млрд руб., доля ВЭБ.РФ — 2,6 млрд руб.'
)

NEW_SRC = [
    ['Миасский рабочий', 'https://miasskiy.ru/20241228-proizvodstvo-unikalnyh-gruzovyh-avtomobilej-ural-budet-rasshireno-v-miasse'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
