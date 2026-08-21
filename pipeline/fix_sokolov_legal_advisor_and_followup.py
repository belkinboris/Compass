# -*- coding: utf-8 -*-
"""Sokolov/Антон Пак (`g68975b9d`): месячный дообыск нашёл юридического
консультанта продавца — ELWI, названного структурированной сводкой
Коммерсанта «Сделки M&A, значимые для российского рынка в 2025 году»
(имя фирмы в источнике набрано с пробелами между буквами — «E L W I» —
особенность вёрстки листинга, не опечатка). `law.adv` — списочное поле,
`review.py` его не проверяет (см. прецедент `fix_mm_packaging_advisors.
py`). Заодно добавлен источник и дополнена `eco.context` планами Артёма
Соколова после продажи (венчурные инвестиции) — из ДРУГОГО источника,
чем уже занятое поле, слияние разовым скриптом.

Запуск: python3 pipeline/fix_sokolov_legal_advisor_and_followup.py           # проверка
        python3 pipeline/fix_sokolov_legal_advisor_and_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g68975b9d'
OLD_ADV = [
    ['Финансовый консультант продавца', 'Aspring Capital',
     'The Moscow Times со ссылкой на источники «Коммерсанта» называет '
     'Aspring Capital финансовым консультантом продавца в продаже '
     'холдинга Sokolov; управляющий партнёр Aspring Capital Сергей '
     'Айрапетов подтвердил факт закрытия сделки. Источник: '
     'https://ru.themoscowtimes.com/2025/08/14/benefitsiar-'
     'yuvelirnogo-kholdinga-sokolov-prodal-ego-chastnomu-investoru-'
     'paku-gazeta-a171592'],
]
NEW_ADV = OLD_ADV + [
    ['Юридический консультант продавца', 'ELWI',
     '«Юридическая фирма, сопровождающая сделку: E L W I со стороны '
     'продавца... Команда E L W I осуществляла полное юридическое '
     'сопровождение сделки... на всех ее этапах.» Источник: '
     'kommersant.ru/doc/8077927 («Сделки M&A, значимые для российского '
     'рынка в 2025 году»)'],
]
OLD_CONTEXT = (
    'Артему Соколову ювелирный бизнес перешел в 2014 году от родителей '
    '— Елены и Алексея Соколовых, основавших холдинг в 1993 году. '
    'Вначале это было производство украшений, позже появилась '
    'одноименная розничная сеть, объединяющая на начало 2025 года, по '
    'собственным данным, около 1 тыс. магазинов по всей России.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' После продажи Артём Соколов заявил «Ъ», что хочет сосредоточиться '
    'на собственных проектах и венчурных инвестициях, а также '
    'продолжит поддерживать Благотворительный фонд семьи Соколовых.')
NEW_SRCS = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8077927'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7959713'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law'].get('adv') == OLD_ADV, (
        'law.adv изменился с ожидаемого: %r' % card['law'].get('adv'))
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    to_add = [s for s in NEW_SRCS if s not in src]
    print('ПРАВИМ  %s: law.adv — добавлен юрконсультант ELWI' % CARD_ID)
    print('ПРАВИМ  %s: eco.context — планы Соколова после продажи' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['law']['adv'] = NEW_ADV
        card['eco']['context'] = NEW_CONTEXT
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
