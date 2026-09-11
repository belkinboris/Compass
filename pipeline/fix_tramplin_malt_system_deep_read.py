# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (13:20 МСК) — карточка `g6743f902» (АО «Трамплин
Холдинг»/«Мальт Систем») собрана из заголовка TAdviser, и в `buyer_name`/
`asset` попали описательные обороты («Производитель процессоров «Иртыш»
«Трамплин Холдинг»», «разработчик микроэлектроники Malt System») вместо
имён. WebSearch нашёл дословный источник (CNews, 10 сентября 2026) с
чёткими фактами: покупатель, продавец, доля, дата закрытия, сумма по
независимой оценке, мотив сделки и причина, по которой процессор «Иртыш»
называют «скандальным» (Минпромторг: сходство с китайским аналогом).

Продавец — Сергей Елизаров, основатель дизайн-центра «Мальт Систем» (не
профиль: физлицо). Сумма официально не раскрыта — названа только оценка
независимого эксперта (Алексей Бойко, 300-400 млн ₽).

Запуск: python3 pipeline/fix_tramplin_malt_system_deep_read.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g6743f902'
BUYER_ID = 'gtramplin'
BUYER_NAME = 'АО «Трамплин Холдинг»'
TARGET_ID = 'gmaltsystem'
TARGET_NAME = 'ООО «Мальт Систем»'

SRC_CNEWS = ['CNews', 'https://www.cnews.ru/news/top/2026-09-10_vladelets_razrabotchika_skandalnogo']
SRC_COMPUTERRA = ['Компьютерра', 'https://www.computerra.ru/361624/ao-tramplin-holding-obedinilos-s-ooo-malt-sistem-dlya-uskoreniya-razvitiya-rossijskoj-mikroelektroniki/']

NEW_TITLE = '«Трамплин Холдинг» купил 51% дизайн-центра «Мальт Систем»'
NEW_ASSET = '51% ООО «Мальт Систем»'

QUOTE_RATIONALE = ('«Трамплину» требовалась команда с компетенциями в '
                    'криптографии и отраслевых связями для усиления '
                    'проекта «Иртыш» через разработку модуля безопасности '
                    'и криптоускорителя.')
QUOTE_CONTEXT = ('Malt System известна разработкой процессоров с '
                  'оригинальной архитектурой Malt-C для потоковой '
                  'обработки сетевого трафика и криптопреобразований. '
                  'Минпромторг ранее заявил, что характеристики процессора '
                  '«Иртыш C632» почти идентичны китайскому Loongson '
                  'LS3C6000/D, а «Иртыш C616» полностью идентичен '
                  'китайскому аналогу, что потенциально создаёт угрозу '
                  'национальной безопасности.')
NEW_SUM = '300-400 млн ₽ (по оценке)'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена в pending.json' % CARD_ID
    assert card['buyer_name'] == 'Производитель процессоров «Иртыш» «Трамплин Холдинг»'
    assert card['asset'] == 'разработчик микроэлектроники Malt System'
    assert BUYER_ID not in base['companies']
    assert TARGET_ID not in base['companies']

    base['companies'][BUYER_ID] = {
        'name': BUYER_NAME,
        'ind': 'ИТ и интернет',
        'desc': 'Разработчик российских процессоров под брендом «Иртыш».',
        'kpi': ['Профиль', 'Автоматический'],
    }
    base['companies'][TARGET_ID] = {
        'name': TARGET_NAME,
        'ind': 'ИТ и интернет',
        'desc': ('Дизайн-центр микроэлектроники: разрабатывает процессоры '
                 'с архитектурой Malt-C для потоковой обработки сетевого '
                 'трафика и криптопреобразований.'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[BUYER_ID] = ['трамплин холдинг', 'трамплин электроникс']
    base.setdefault('match_keys', {})[TARGET_ID] = ['мальт систем', 'malt system']

    card['title'] = NEW_TITLE
    card['buyer'] = BUYER_ID
    card.pop('buyer_name', None)
    card['target'] = TARGET_ID
    card['asset'] = NEW_ASSET
    card['seller'] = 'Сергей Елизаров'
    card['date'] = '2026-09-03'
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    card['eco']['rationale'] = QUOTE_RATIONALE
    card['eco']['context'] = QUOTE_CONTEXT
    card['src'].append(SRC_CNEWS)
    card['src'].append(SRC_COMPUTERRA)
    card['events'][0]['date'] = '2026-09-03'
    card['events'][0]['note'] = ('АО «Трамплин Холдинг» приобрело 51% в уставном '
                                  'капитале ООО «Мальт Систем» у основателя '
                                  'дизайн-центра Сергея Елизарова.')
    card['events'][0]['source'] = SRC_CNEWS
    card.pop('party_evidence', None)

    print('Карточка %s починена: %s' % (CARD_ID, NEW_TITLE))

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
