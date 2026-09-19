# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№701. Карточка gaa603e6d уже не упоминает «ЭПТ» (это, похоже, уже
исправлено раньше — вычитал карточку целиком, «ЭПТ» в ней нет ни в одном
поле) — первая часть просьбы уже выполнена. Вторая часть — «в карте не
вижу схемы» — оказалась настоящим пробелом: у сделок с type=«Создание СП»
плашка «Участники совместного предприятия» рисуется, только если ОБА
участника — профили компаний (buyer/target — id, не текст), а у карточки
не было ни того, ни другого поля вовсе, только текстовое `asset`.
Заводим два профиля по независимо проверенным источникам (официальная
страница evo-centre.ru; данные ЕГРЮЛ по ИНН 2312328217, тот же ИНН, что
уже назван в известных вопросах CLAUDE.md) и связываем ими карточку.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

NOVO_ID = 'gnovocenter'
IRANIANEURASIA_ID = 'giranianeurasia'

NOVO_PROFILE = {
    'name': '«Центр развития НОВО»',
    'ind': 'Агро',
    'desc': (
        'Головная структура государственной программы развития '
        'зернопроводящей инфраструктуры и логистики. Зарегистрирована в '
        'Краснодаре в июле 2024 года (ИНН 2312328217), самостоятельна и не '
        'входит в группу «ЭПТ» (сибирский проект зернового коридора с '
        'другим ИНН — отдельная, не связанная структура).'
    ),
    'kpi': ['Профиль', 'Автоматический'],
}
IRANIANEURASIA_PROFILE = {
    'name': 'IranianEurasia Trading and Logistics',
    'ind': 'Агро',
    'desc': (
        'Иранская логистическая компания — партнёр «Центра развития НОВО» '
        'по совместному предприятию для зернового хаба в особой '
        'экономической зоне Серахс на северо-востоке Ирана.'
    ),
    'kpi': ['Профиль', 'Автоматический'],
}


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    companies = data.setdefault('companies', {})
    card = next(d for d in data['deals'] if d['id'] == 'gaa603e6d')

    assert card['title'] == '«Центр развития НОВО» и IranianEurasia создают СП для зернового хаба в Иране'
    assert 'ЭПТ' not in json.dumps(card, ensure_ascii=False)
    assert 'buyer' not in card and 'target' not in card
    assert NOVO_ID not in companies and IRANIANEURASIA_ID not in companies

    companies[NOVO_ID] = NOVO_PROFILE
    companies[IRANIANEURASIA_ID] = IRANIANEURASIA_PROFILE
    card['buyer'] = NOVO_ID
    card['target'] = IRANIANEURASIA_ID

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gaa603e6d: добавлена схема (два профиля-участника СП). ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
