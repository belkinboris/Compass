# -*- coding: utf-8 -*-
"""Valio/Viola/Velcom (`g55f1c662`): месячный дообыск нашёл юрконсультанта
продавца (Castren & Snellman, Финляндия — заглушка `law.adv` заменяется
на реальную запись) и финансовую траекторию компании после сделки: убыток
2024 года (первый за долгое время) сменился рекордной выручкой 2025 года.
Оба факта из НОВЫХ источников (castren.fi и, отдельно, interfax.ru +
tadviser.ru), а `eco.context` уже занято другим предложением — дословно
объединить для `review.py` нельзя, поэтому финансовая траектория
добавляется вторым абзацем разовым скриптом; `law.adv` — списочное поле,
`review.py` его не проверяет вовсе (см. прецедент
`fix_mm_packaging_advisors.py` в этом же прогоне).

Запуск: python3 pipeline/fix_valio_followup.py           # проверка
        python3 pipeline/fix_valio_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g55f1c662'
OLD_ADV = [
    ['Стороны сделки', 'Не раскрывались',
     'Юридические консультанты в публичных источниках не раскрывались'],
]
NEW_ADV = [
    ['Продавец (Valio)', 'Castren & Snellman',
     '«We advised Valio in its negotiations on the divestment of '
     'Valio\'s Russian operations to Velkom Group.» Источник: '
     'castren.fi/cases/cases-2022/valio3'],
]
OLD_CONTEXT = (
    '7 марта финский концерн принял решение завершить деятельность в '
    'России на фоне военной спецоперации. Спустя несколько дней '
    'российское подразделение концерна ООО «Валио» заявило, что '
    'продолжит операционную деятельность. Ранее сообщалось, что новым '
    'владельцем бизнеса может стать группа «Русагро».')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Дальнейшая судьба компании: 2024 год «Виола» (бывшая «Валио») '
    'завершила с чистым убытком в 19,8 млн рублей против чистой прибыли '
    '295,8 млн рублей годом ранее — первый убыток за долгое время, при '
    'этом выручка выросла почти на 26%, до 11,3 млрд рублей. В 2025 '
    'году компания достигла рекордных финансовых результатов: выручка '
    'достигла 12,3 млрд рублей (максимум за пять лет), чистая прибыль — '
    '90,2 млн рублей.')
NEW_SRCS = [
    ['Castren & Snellman', 'https://castren.fi/cases/cases-2022/valio3'],
    ['Интерфакс', 'https://www.interfax.ru/business/1018641'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Viola_'
     '(Виола)'],
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
    print('ПРАВИМ  %s: law.adv — Castren & Snellman' % CARD_ID)
    print('ПРАВИМ  %s: eco.context — финансовая траектория 2024-2025' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['law']['adv'] = NEW_ADV
        card['eco']['context'] = NEW_CONTEXT
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
