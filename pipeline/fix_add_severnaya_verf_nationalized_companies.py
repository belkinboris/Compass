# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (11:20 МСК) — реальная сделка, которую ворота
не пропустили дважды подряд (сначала «не установлен предмет сделки» по
заголовку, затем «не видно связи с российским рынком» — хотя весь текст
кириллический; вторая причина, судя по всему, — общий отказ, который
`russian_evidence()` даёт, когда структурные поля черновика (buyer/asset/
seller) не разобраны вовсе, а не буквальная латиница).

Источник — dp.ru, 19 августа 2026 (WebFetch, целевые цитаты). АО
«Судостроительный завод «Северная верфь»» (входит в ОСК) в июле-августе
2026 года оформило право собственности на 100% акций пяти компаний —
«Норд-Вест СВ», «Инструмент-СВ», «Машиностроение СВ», «Эфес-СВ» и
«Нива-СВ». Эти компании ранее были национализированы (возвращены
государству судебными решениями о незаконности приватизации) и
передаются «Северной верфи» на основании указа президента №633 «О
дальнейшем развитии акционерного общества «Объединённая судостроительная
корпорация»» от 8 сентября 2025 года.

Денежная сумма сделки не раскрыта (это не купля-продажа, а безвозмездная
передача акций государством по указу) — названа только совокупная
выручка пяти компаний за 2025 год (515 млн ₽), она идёт в
`eco.target_fin`, не в `sum`.

Продавцом записано «Государство» текстом (дословно источнику: «До того
они находились в собственности государства») — не «Росимущество»: само
слово «Росимущество» в источнике не встречается, а придумывать конкретное
ведомство не стоит (родня урока «Переносить факт в правильное поле можно,
сочинять — нет»).

Дата — только месяц: пять разных дат регистрации (9, 21 июля, 1, 4, 13
августа 2026), выбирать одну означало бы выдумывать точный день сделки в
целом; используется август 2026 (последняя из пяти дат публикации).

Заведён профиль покупателя (АО «Судостроительный завод «Северная верфь»»)
со связью `holding` на уже существующий профиль ОСК (`g7e9287cb`) — это
дочернее юрлицо группы, а не сама ОСК (родня урока про УГМК-Инвест/УГМК).
Профиль для пяти мелких переданных компаний не заводится: они
незначительны по отдельности (совокупная выручка 515 млн ₽) и названы
текстом в `asset` — состав лота назван там, где его видит читатель.

Запуск: python3 pipeline/fix_add_severnaya_verf_nationalized_companies.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_URL = 'https://www.dp.ru/a/2026/08/19/severnaja-verf-oficialno'
DRAFT_ID = 'd31066141'

BUYER_ID = 'gseververf'
BUYER_NAME = 'АО «Судостроительный завод «Северная верфь»»'
OSK_HOLDING_ID = 'g7e9287cb'

ASSET_TEXT = ('АО «Норд-Вест СВ», «Инструмент-СВ», «Машиностроение СВ», '
              '«Эфес-СВ» и «Нива-СВ»')

QUOTE_MAIN = (
    'АО «Судостроительный завод «Северная верфь»» стало собственником '
    '100%-ных пакетов акций пяти национализированных компаний.'
)

QUOTE_STRUCT = (
    'На основании указа президента России №633 «О дальнейшем развитии '
    'акционерного общества «Объединённая судостроительная корпорация»», '
    'подписанного 8 сентября 2025 года, «Северной верфи» переданы акции '
    'АО «Норд-Вест СВ», «Инструмент-СВ», «Машиностроение СВ», «Эфес-СВ» и '
    '«Нива-СВ». До того они находились в собственности государства. Право '
    'собственности на акции оформлено 9 июля, 21 июля, 1 августа, 4 '
    'августа и 13 августа 2026 года.'
)

QUOTE_TARGET_FIN = (
    'Суммарная выручка компаний, чьи акции стали собственностью Северной '
    'верфи, составила в 2025 году 515 млн рублей.'
)


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    existing_ids = {c['id'] for c in pending['cards']}
    assert not any('Северная верфь' in (c.get('title') or '')
                   for c in pending['cards']), \
        'карточка про Северную верфь уже есть в pending.json'
    assert BUYER_ID not in base['companies'], \
        'профиль %s уже есть' % BUYER_ID
    assert OSK_HOLDING_ID in base['companies'], \
        'профиль ОСК не найден — holding не на что ссылаться'

    new_id = promote.new_id(existing_ids)
    card = {
        'id': new_id,
        'date': '2026-08',
        'title': ('«Северная верфь» получила 100% акций пяти '
                   'национализированных компаний'),
        'ind': 'Машиностроение',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['dp.ru', SRC_URL]],
        'from_ingest': True,
        'eco': {'sum': '—', 'share': '—', 'val': '—',
                'target_fin': QUOTE_TARGET_FIN,
                'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': QUOTE_STRUCT, 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer': BUYER_ID,
        'seller': 'Государство',
        'asset': ASSET_TEXT,
        'events': [{
            'kind': 'closed',
            'date': '2026-08',
            'title': 'Право собственности оформлено',
            'note': QUOTE_MAIN,
            'source': ['dp.ru', SRC_URL],
        }],
    }

    pending['cards'].append(card)
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'take'

    base['companies'][BUYER_ID] = {
        'name': BUYER_NAME,
        'ind': 'Машиностроение',
        'desc': ('Судостроительный завод, входит в группу ОСК; строит '
                 'военные и гражданские корабли.'),
        'kpi': ['Профиль', 'Автоматический'],
        'holding': {'id': OSK_HOLDING_ID, 'confidence': 'высокая',
                    'source': 'dp.ru'},
    }
    base.setdefault('match_keys', {})[BUYER_ID] = ['северная верфь',
                                                    'severnaya verf']

    print('Добавлена карточка %s: Северная верфь/пять национализированных '
          'компаний.' % new_id)
    print('Заведён профиль покупателя %s.' % BUYER_ID)

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
