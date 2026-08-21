# -*- coding: utf-8 -*-
"""Whirlpool/Arçelik/Липецкий завод (`g1059432d`): месячный дообыск нашёл
предысторию урегулирования 2026 года (уже частично лежит в law.terms) и
свежие финансовые показатели завода за 2025 год. Источники — англоязычные
(ua.news, turkiyetoday.com, tadviser.ru) — тексты переведены и пересказаны
по-русски, а не процитированы дословно (сайт русскоязычный, `review.py`
не годится для перевода — та же граница, что у `fix_mm_packaging_german_
text.py` в прошлом прогоне). Оба поля уже заняты, слияние с другими
источниками разовым скриптом.

Запуск: python3 pipeline/fix_whirlpool_settlement_and_2025_financials.py           # проверка
        python3 pipeline/fix_whirlpool_settlement_and_2025_financials.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g1059432d'
OLD_TERMS = (
    'Arçelik, купившая российский бизнес Whirlpool ещё в 2022 году, '
    'согласилась на единовременный платёж в 40 млн евро. После этого '
    'Whirlpool откажется от любых текущих и будущих претензий по '
    'сделке.')
NEW_TERMS = (
    'Изначальные условия сделки были куда сложнее фиксированной суммы: '
    'итоговая стоимость актива должна была определяться на протяжении '
    'десяти лет после закрытия и зависела от финансовых показателей '
    'бизнеса и ряда дополнительных условий. Стороны решили упростить '
    'механизм расчётов и заменить его на разовый платёж 40 млн евро — '
    'к марту 2026 года Arçelik уже накопила по этому соглашению '
    'долгосрочные обязательства примерно на 117 млн евро, так что новая '
    'договорённость почти втрое сократила итоговую сумму выплат.')
OLD_TARGET_FIN = (
    'Выручка «Вирлпул Рус» по РСБУ в 2021 году составила 40,8 млрд '
    'руб., чистая прибыль — 1,9 млрд руб.; у «Индезит Интернэшнл» эти '
    'показатели составили 29,1 млрд руб. и 220 млн руб. соответственно.')
NEW_TARGET_FIN = OLD_TARGET_FIN + (
    ' По итогам 2025 года выручка объединённого юрлица «Ай Эйч Пи '
    'Апплаенсес» (бывший липецкий завод) составила 36,8 млрд руб. '
    '(+37% год к году), чистая прибыль — 1,2 млрд руб. (+13,3%).')
NEW_SRCS = [
    ['ua.news', 'https://ua.news/en/world/whirlpool-ostatochno-'
     'zakrila-pitannia-z-rosiiskim-biznesom'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:IHPA_-_'
     'IHP_Appliances_Sales_-_Ай_Эйч_Пи_Апплаенсес_Сейлс_-_Вирлпул_Рус_'
     '(Whirlpool_Rus)'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law'].get('terms') == OLD_TERMS, (
        'law.terms изменился с ожидаемого: %r' % card['law'].get('terms'))
    assert card['eco'].get('target_fin') == OLD_TARGET_FIN, (
        'eco.target_fin изменился с ожидаемого: %r' % card['eco'].get('target_fin'))
    src = card.setdefault('src', [])
    to_add = [s for s in NEW_SRCS if s not in src]
    print('ПРАВИМ  %s: law.terms — предыстория урегулирования 2026 года' % CARD_ID)
    print('ПРАВИМ  %s: eco.target_fin — финансы завода за 2025 год' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['law']['terms'] = NEW_TERMS
        card['eco']['target_fin'] = NEW_TARGET_FIN
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
