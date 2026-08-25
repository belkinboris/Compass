# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g14443784 («Пикалевская
сода» приобрела месторождение кварцевого песка): дельта-поиск нашёл, что
спустя год после сделки ни добыча, ни обогащение месторождения не
начаты — старая инфраструктура ГОК физически снесена («всё разбомбили»),
а инвестиции блокирует высокая ключевая ставка ЦБ. Судьба Купцова после
продажи не прослеживается отдельно, кроме факта, что бо́льшая часть
юрлиц «АВК-Холдинга» уже ликвидирована. Не через review.py: цитата из
НОВОГО источника (lipetsknews.ru) в поле, уже содержащем текст из
других источников.

Запуск: python3 pipeline/fix_pikalevskaya_soda_gorlovskoe_context.py
        python3 pipeline/fix_pikalevskaya_soda_gorlovskoe_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g14443784'

OLD_CONTEXT = (
    'Прежним владельцем актива был Алексей Купцов — собственник '
    '«АВК-Холдинга», который занимался строительством ГОКа на '
    'месторождении. Оно началось еще в 2000 году по заказу ЗАО '
    '«Горнорудная компания "Ранова"». Но через год из-за нехватки '
    'средств возведение объекта остановилось, а в 2005 году предприятие '
    'обанкротилось. Впоследствии актив перешел к «АВК-Холдинг», который '
    'смог запустить ГОК стоимостью 1 млрд руб. в 2013 году. Но уже в '
    '2016 году из-за недостатка инвестиций в развитие предприятия '
    'месторождение и ГОК были выставлены на продажу.'
)
CONTEXT_ADDITION = (
    ' Спустя год после сделки новый совладелец Максим Волков рассказал, '
    'что на месте прежнего комбината «всё разбомбили» — построек не '
    'осталось; инвестиции в обогащение (около 1,5 млрд руб.) пока не '
    'начаты — по словам Волкова, высокая ключевая ставка ЦБ не '
    'позволяет вкладываться в развитие месторождения. Большая часть '
    'юрлиц «АВК-Холдинга» Купцова к этому моменту уже ликвидирована.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = ['lipetsknews.ru', 'https://lipetsknews.ru/biznes/42075']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert not any(s[1] == NEW_SRC[1] for s in deal['src'])

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===', NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].append(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
