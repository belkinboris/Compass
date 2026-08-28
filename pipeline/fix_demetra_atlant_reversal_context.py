# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g42e11ded («Деметра-Холдинг»
приобрел 100% железнодорожного оператора «Атлант», ноябрь 2024): дельта-
поиск нашёл ролевой разворот — купленный «Атлант» сам стал покупателем
активов у своего нового владельца. В конце 2024 года «Атлант» приобрёл у
«Деметры» контрольный пакет (51%) другого оператора, «Транслес», за
5,75 млрд руб. (МСФО «Трансфин-М»); а в июне 2025 года «Деметра-холдинг»
продала «Атланту» оставшиеся 49% «Транслеса» и 100% «Грузовой компании» —
то есть полностью вышла из железнодорожных активов, которые сама же
собирала. Обе цитаты подтверждены лично прямым WebFetch. Не через
review.py: цитаты из НЕСКОЛЬКИХ новых источников описывают событие,
случившееся ПОСЛЕ самой сделки, а не дополняют дословно уже записанный
факт.

Запуск: python3 pipeline/fix_demetra_atlant_reversal_context.py
        python3 pipeline/fix_demetra_atlant_reversal_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g42e11ded'

OLD_CONTEXT = (
    'Прежде «Атлант» принадлежал гендиректору компании Евгению Ястребову и '
    'Андрею Гомону. Последний в 2006–2012 годах возглавлял «Трансойл», '
    'одного из крупнейших операторов нефтеналивного парка, был советником '
    'гендиректора Первой грузовой компании (ПГК) и на февраль 2024 года '
    'входил в совет директоров Globaltrans.'
)
CONTEXT_ADDITION = (
    ' Дальнейший сюжет развернулся: купленный «Атлант» сам стал покупателем '
    'активов у нового владельца. В конце 2024 года «Атлант» приобрёл у '
    '«Деметры» контрольный пакет другого оператора, «Транслес», — 51% за '
    '5,75 млрд руб. (данные МСФО «Трансфин-М»). А в июне 2025 года '
    '«Деметра-холдинг» продала «Атланту» и оставшиеся 49% «Транслеса», и '
    '100% «Грузовой компании» — полностью выйдя из железнодорожных '
    'активов, которые сама же собирала.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/06/25/1119813-demetra-holding-prodal-vse-svoi-zheleznodorozhnie-aktivi'],
    ['РБК Кубань', 'https://kuban.rbc.ru/krasnodar/freenews/685baaf09a794718ae356831'],
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
