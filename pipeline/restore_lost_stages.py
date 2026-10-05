# -*- coding: utf-8 -*-
"""Вернуть в «Ход сделки» этап, на котором карточка стояла до первой новости
о новом этапе.

ЗАЧЕМ. Карточка без `events` показывает в «Ходе сделки» один этап — тот, что
выводится из её статуса и даты (`dealEvents()` в static/index.html). Когда
`enrich.py` дописывал ПЕРВОЕ событие (согласование, закрытие, срыв) и двигал
статус вперёд, прежний этап нигде не записывался и молча пропадал: у UniCredit
в «Ходе сделки» осталось одно согласование 5 октября 2026, а подписание
необязывающего term sheet 7 мая исчезло (владелец, 5 октября 2026). С этого
дня `enrich.prior_stage_event` записывает прежний этап сам; здесь — четыре
карточки, где он уже потерян.

ОТКУДА ДАННЫЕ. Прежний этап восстановлен по истории git этих же карточек:
статус, дата, заголовок и первый источник в коммите перед тем, где появилось
первое событие (UniCredit — 27e72a14, ТЦ «Июнь» — f52b4dbb, «Ашан» —
a8a7e001, «Швабе» — 8cf2c374). Источники до сих пор лежат в `src` карточек.
Остальные 30 карточек, у которых первое событие позже даты карточки, разобраны
тем же поиском и не тронуты: у них этап совпадает с прежним, сайт и так
показывает прежний этап (событие другого вида — `other`, `registered`), или
карточка с самого начала собрана вместе с этапами.

Запуск:
    python3 pipeline/restore_lost_stages.py          # сухой прогон
    python3 pipeline/restore_lost_stages.py --write  # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

STAGES = {
    'g1edb1b9d': {
        'id': 'negotiations-2026-05-07', 'kind': 'negotiations', 'date': '2026-05-07',
        'title': 'Подписано необязывающее предварительное соглашение',
        'historicalTitle': 'UniCredit продаст часть российских активов банка инвестору из ОАЭ',
        'note': 'UniCredit подписал необязывающее предварительное соглашение (term sheet) о продаже '
                'части АО «ЮниКредит Банк» частному инвестору из ОАЭ. Это не окончательный договор '
                'купли-продажи: для закрытия нужно разрешение Президента РФ и другие согласования.',
        'sources': [
            ['UniCredit Group (официальный пресс-релиз)',
             'https://www.unicreditgroup.eu/en/press-media/press-releases-price-sensitive/2026/may/'
             'unicredit-signs-non-binding-agreement-to-divest-part-of-its-acti.html'],
            ['Коммерсантъ', 'https://www.kommersant.ru/doc/8651628'],
        ],
    },
    'gde4f9941': {
        'id': 'negotiations-2023-02-14', 'kind': 'negotiations', 'date': '2023-02-14',
        'title': 'Выставлен на торги',
        'historicalTitle': 'Продажа ТРЦ «Июнь» в Красногорске (Подмосковье) через аукцион РАД',
        'note': '',
        'sources': [['РИА Недвижимость', 'https://realty.ria.ru/20230214/iyun-1851987297.html']],
    },
    'g17fc21d6': {
        'id': 'negotiations-2024-10-24', 'kind': 'negotiations', 'date': '2024-10-24',
        'title': 'Переговоры',
        'historicalTitle': 'Auchan продаёт российский бизнес неизвестному покупателю',
        'note': '',
        'sources': [['РБК', 'https://www.rbc.ru/business/24/10/2024/671a28aa9a79470c980f8145']],
    },
    'ge957fc7b': {
        'id': 'negotiations-2026-08-26', 'kind': 'negotiations', 'date': '2026-08-26',
        'title': 'Переговоры',
        'historicalTitle': '«Ростех» продает штаб-квартиру «Швабе» рядом с гостиницей «Космос» в Москве',
        'note': '',
        'sources': [['РИА Недвижимость', 'https://realty.ria.ru/20260826/shvabe-2113215916.html']],
    },
}


def apply(data):
    """Дописать этапы, которых ещё нет. Возвращает id изменённых карточек."""
    by_id = {d['id']: d for d in data['deals']}
    changed = []
    for did, stage in STAGES.items():
        deal = by_id.get(did)
        if deal is None:
            raise SystemExit('карточка %s не найдена' % did)
        events = deal.setdefault('events', [])
        if any((e.get('kind'), e.get('date')) == (stage['kind'], stage['date']) for e in events):
            continue
        known = {str(s[1]) for s in deal.get('src') or [] if len(s) > 1}
        missing = [s[1] for s in stage['sources'] if s[1] not in known]
        if missing:
            raise SystemExit('у карточки %s нет источника %s' % (did, missing))
        events.append(dict(stage))
        events.sort(key=lambda e: (str(e.get('date') or ''), str(e.get('kind') or '')))
        changed.append(did)
    return changed


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    changed = apply(data)
    print('Этапов вернуть: %d (%s)' % (len(changed), ', '.join(changed) or '—'))
    if write and changed:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('Записано.')
    elif not write:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
