# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gd58fa76a (АФК «Система»
продала венчурный фонд Sistema SmartTech): структурное поле `buyer` уже
верно указывает на профиль АО «Транс Капитал» (90% доли) — дельта-поиск
подтвердил это же по трём независимым источникам, поэтому имя покупателя
в карточку не дублируется. Новый факт — судьба ОСТАВШИХСЯ 10%, которых в
карточке не было вовсе. Цитата подтверждена лично прямым WebFetch.

«Оставшиеся 10% компании сохранило за собой ООО «Капитал Инвест», его
бенефициаром выступает Дмитрий Шерстобитов» (RB.ru).

Сумму сделки, консультантов и судьбу портфельных компаний фонда после
смены управляющей структуры дельта-поиск не нашёл ни в одном источнике —
честная пустота, не тронуто.

Запуск: python3 pipeline/fix_sistema_smarttech_trans_kapital_stake.py
        python3 pipeline/fix_sistema_smarttech_trans_kapital_stake.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd58fa76a'

OLD_CONTEXT = (
    'На момент создания фонда Sistema SmartTech сообщалось, что он создан '
    'на восемь лет с инвестиционным периодом пять лет. Целевой объем фонда '
    '— 5 млрд рублей; предполагалось, что АФК выступит якорным инвестором. '
    'Сообщалось также, что за время работы фонд может профинансировать '
    'около 20 венчурных проектов на ранней стадии, объем инвестиций в '
    'каждый проект может составить от 50 до 300 млн рублей. Фокус фонда — '
    'проекты компаний в основном российского происхождения на ранней '
    'стадии (от посевных инвестиций до раунда А) с перспективой '
    'перепродажи стратегическому инвестору.'
)
CONTEXT_ADDITION = (
    ' Покупателем 90% доли выступило АО «Транс Капитал» — оставшиеся 10% '
    'сохранило за собой ООО «Капитал Инвест», его бенефициаром выступает '
    'Дмитрий Шерстобитов (RB.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['RB.ru', 'https://rb.ru/news/sistema-smarttech/'],
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
