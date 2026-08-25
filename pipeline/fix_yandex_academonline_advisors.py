# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g165039a0 («Яндекс
Путешествия» приобрели 100% долей в «Академ-Онлайн»): дельта-поиск
подтвердил и расширил запись о LEVEL Legal Services (собственный
пресс-релиз фирмы называет полный состав команды и объём сопровождения),
но НЕ смог подтвердить запись об АЛРУД как консультанте продавца — она
уже была помечена в карточке «точный URL статьи не подтверждён», и
второй, независимый и тщательный поиск (по обоим доменам alrud.ru и
alrud.com, включая pravo.ru) публикации не нашёл. Неподтверждённая
запись честнее снять, чем продолжать держать в карточке как факт.

Запуск: python3 pipeline/fix_yandex_academonline_advisors.py
        python3 pipeline/fix_yandex_academonline_advisors.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g165039a0'

OLD_ADV = [
    [
        'Юридический консультант продавца (Academ-Online)',
        'АЛРУД',
        'Источник: сайт АЛРУД (alrud.com/publications), точный URL статьи не подтверждён',
    ],
    [
        'Юридический консультант покупателя («Яндекс Путешествия»)',
        'LEVEL Legal Services',
        'Приобретение «Академ-Онлайн». Источник: level-legal.com',
    ],
]

NEW_ADV = [
    [
        'Юридический консультант продавца (Academ-Online)',
        'Не раскрывались',
        'Ранее предполагалось участие АЛРУД, но публикация об этом не найдена ни на alrud.ru, ни на alrud.com — запись снята как неподтверждённая',
    ],
    [
        'Юридический консультант покупателя («Яндекс Путешествия»)',
        'LEVEL Legal Services',
        'Полное юридическое сопровождение — due diligence, транзакционная документация, закрытие сделки. Команда под руководством партнёра Марии Баевой: советник Глеб Тихомиров, юристы Екатерина Сечкарева, Дарья Грехова, Екатерина Клочкова, Илья Пушкин. Источник: level-legal.com',
    ],
]

NEW_SRC = ['level-legal.com', 'https://www.level-legal.com/news/level-legal-services-soprovodila-sdelku-yandeks-puteshestvij-po-priobreteniyu-biznesa-po-onlajn-bronirovaniyu-otelej-dlya-delovogo-turizma']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV, 'law.adv изменился с момента чтения — проверьте'
    assert not any(s[1] == NEW_SRC[1] for s in deal['src']), 'источник уже в src'

    print('=== law.adv: станет ===')
    print(json.dumps(NEW_ADV, ensure_ascii=False, indent=1))
    print('=== src добавится ===')
    print(NEW_SRC)

    if write:
        deal['law']['adv'] = NEW_ADV
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
