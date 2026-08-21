# -*- coding: utf-8 -*-
"""Bonava/Star Development (`gec6e9db6`): месячный дообыск нашёл
комментарий президента ГК «ФСК» Владимира Воронина о цели сделки (из
официального пресс-релиза ФСК) и подробную судьбу актива после
закрытия — смену гендиректора (Барков → Агаронов, апрель 2024) и
передачу флагманского проекта Magnifika в закрытый ПИФ «ФСК Капитал
Инвестиции» (декабрь 2024) — источники другие, чем уже занятые поля
`eco.rationale` и `eco.context`. Слияние разовым скриптом.

Запуск: python3 pipeline/fix_bonava_star_dev_followup.py           # проверка
        python3 pipeline/fix_bonava_star_dev_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gec6e9db6'

OLD_RATIONALE = (
    'Приобретение бизнеса по завышенной цене эксперты объяснили '
    'желанием застройщика сформировать земельный банк на несколько лет '
    'вперёд.')
NEW_RATIONALE = OLD_RATIONALE + (
    ' «Посредством сделки с Bonava мы пополняем продуктовую линейку '
    'перспективными проектами бизнес-класса и планируем занять '
    'лидирующие позиции в этом сегменте теперь и в Северной столице. '
    'При этом мы сохраним высокое качество продукта и лучшие практики, '
    'которыми славился шведский девелопер», — заявил президент ГК '
    '«ФСК» Владимир Воронин.')

OLD_CONTEXT = (
    'Изначально бизнес застройщика за 5,9 млрд рублей собиралась '
    'купить казанская G-Group, которая затем вышла из сделки. В мае '
    'этого года о приобретении активов Bonava за 3,3 млрд рублей '
    'договорилась RBI Эдуарда Тиктинского, но в результате контракт с '
    'ней был расторгнут. Потенциальному покупателю не удалось '
    'согласовать сделку с государством, следует из сообщения Bonava.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Сразу после закрытия сделки новым гендиректором назначили Олега '
    'Баркова (экс-«ВТБ-Недвижимость»), но уже 12 апреля 2024 года его '
    'сменил Заур Агаронов — компании не удалось удержать команду '
    '(«на момент прихода нового руководства каждый сотрудник имел по '
    'два-три оффера на руках»), и в итоге решили просто объединить '
    'компании с материнской структурой. 13 декабря 2024 года '
    'флагманский проект Magnifika (два корпуса, 50 тыс. м² общей '
    'площади) передан в закрытый ПИФ «ФСК Капитал Инвестиции»; по '
    'мнению партнёра NF Group Станислава Бибика, это «может '
    'свидетельствовать о необходимости упрощения управления активом и '
    'привлечения дополнительных инвестиций».')

NEW_SRCS = [
    ['ГК ФСК', 'https://fsk.ru/about/news/gk-fsk-stala-sobstvennikom-'
     'rossijskih-aktivov-shvedskogo-developera-bonava'],
    ['DP.ru', 'https://www.dp.ru/a/2024/04/12/'
     'srazu-tri-developera-v-peterburge'],
    ['DP.ru', 'https://www.dp.ru/a/2024/12/13/'
     'bivshij-proekt-shvedskoj-bonava'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('rationale') == OLD_RATIONALE, (
        'eco.rationale изменился с ожидаемого: %r' % card['eco'].get('rationale'))
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.rationale — комментарий Воронина (ФСК)' % CARD_ID)
    print('ПРАВИМ  %s: eco.context — смена руководства и судьба проекта Magnifika' % CARD_ID)
    if write:
        card['eco']['rationale'] = NEW_RATIONALE
        card['eco']['context'] = NEW_CONTEXT
        for s in NEW_SRCS:
            if s not in src:
                src.append(s)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
