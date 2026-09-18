# -*- coding: utf-8 -*-
"""Месячная очередь 18.09.2026: карточка `gb5d8a18a` (ЦБ зарегистрировал
допэмиссию акций «М.видео» по закрытой подписке) — дельта-поиск подтвердил,
что размещение НЕ ЗАВЕРШЕНО: по данным Abn.Agency (17.09.2026), совет
директоров на дату публикации только ПРЕДСТОЯЛО рассмотреть вопрос о цене
размещения — статус карточки «Обсуждается» остаётся верным, менять не на что.

Дописаны два новых факта из того же источника, СВЕРХ уже известного:
  1. Точный объём размещения (до 500 млн акций) и номинал одной акции
     (10 рублей) — раньше в карточке было только общее «дофинансирование
     на 30 млрд ₽», без структуры выпуска.
  2. Развёрнутая цель средств: не только «дофинансирование», а конкретные
     направления — мультикатегорийный маркетплейс, офлайн-розница, сеть
     партнёрских ПВЗ и постаматов.

Источник: https://abn.agency/2026/09/17/m-video-opredelit-czenu-razmeshheniya-akczij-dopemissii-na-30-mlrd-rublej/
(проверено личным curl-запросом 18.09.2026, ранее в `src` не значился).

Запуск: python3 pipeline/fix_mvideo_dopemissiya_pricing_pending.py           # проверка
        python3 pipeline/fix_mvideo_dopemissiya_pricing_pending.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb5d8a18a'

OLD_CONTEXT = (
    '22 июля годовое собрание акционеров одобрило перевод дополнительной '
    'эмиссии акций в формат закрытой подписки.'
)
OLD_RATIONALE = (
    'Размещение акций по закрытой подписке позволит завершить '
    'дофинансирование компании на 30 млрд ₽.'
)

QUOTE = (
    'Совет директоров ПАО «М.видео» в четверг рассмотрит вопрос о цене '
    'размещения акций дополнительной эмиссии. Компания намерена выпустить '
    'до 500 млн бумаг по закрытой подписке. Номинальная стоимость одной '
    'акции составляет 10 рублей. Решение о проведении допэмиссии акционеры '
    '«М.видео» одобрили в июне, а в середине августа ЦБ РФ зарегистрировал '
    'выпуск. Допэмиссия должна завершить процесс дофинансирования компании '
    'на 30 млрд рублей за счет действующих акционеров. Размещение '
    'планируется провести в пользу ООО «КэпиталГард», ПАО «ЭсЭфАй», ООО '
    '«ЭсЭфАй Кэпитал» и ООО «Лэнбури». Средства компания намерена направить '
    'на развитие ключевых направлений бизнеса. В их числе — реализация '
    'новой стратегии по созданию мультикатегорийного маркетплейса. '
    'Стратегия также предусматривает развитие офлайн-розницы, сети '
    'партнерских ПВЗ и постаматов.'
)

ADD_CONTEXT = (
    'Компания намерена выпустить до 500 млн бумаг по закрытой подписке, '
    'номинальная стоимость одной акции составляет 10 рублей.'
)
ADD_RATIONALE = (
    'Средства компания намерена направить на развитие ключевых направлений '
    'бизнеса. В их числе — реализация новой стратегии по созданию '
    'мультикатегорийного маркетплейса. Стратегия также предусматривает '
    'развитие офлайн-розницы, сети партнерских ПВЗ и постаматов.'
)

ABN_URL = ('https://abn.agency/2026/09/17/'
           'm-video-opredelit-czenu-razmeshheniya-akczij-dopemissii-na-30-mlrd-rublej/')


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context уже другой: %r' % card['eco'].get('context'))
    assert card['eco'].get('rationale') == OLD_RATIONALE, (
        'eco.rationale уже другой: %r' % card['eco'].get('rationale'))

    for add in (ADD_CONTEXT, ADD_RATIONALE):
        assert flat(add) in flat(QUOTE), 'не лежит дословно в цитате: %r' % add

    new_context = OLD_CONTEXT + ' ' + ADD_CONTEXT
    new_rationale = OLD_RATIONALE + ' ' + ADD_RATIONALE

    print('НОВОЕ eco.context:')
    print(new_context)
    print()
    print('НОВОЕ eco.rationale:')
    print(new_rationale)

    if not write:
        print()
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['eco']['context'] = new_context
    card['eco']['rationale'] = new_rationale
    urls = {s[1] for s in (card.get('src') or []) if isinstance(s, list) and len(s) > 1}
    if ABN_URL not in urls:
        card.setdefault('src', []).append(['Abn.Agency', ABN_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
