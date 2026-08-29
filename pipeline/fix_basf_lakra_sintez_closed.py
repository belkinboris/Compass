# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g073bf58b
(BASF продает завод ЛКМ в Павловском Посаде компании «Лакра Синтез»).
Найдено предыдущим заходом (дельта-поиск по сестринской сделке Flint
Group/g0df6c7c4) как побочный факт: карточка стояла со статусом
«Обсуждается» с 7 мая 2024 года (дата президентского распоряжения,
разрешившего сделку), хотя закрытие произошло почти сразу же.

Проверено лично прямым WebFetch (mrc.ru, публикация 02.07.2024,
https://www.mrc.ru/news/413188-lakokrasochniy-zavod-basf-v-podmoskove-
pereshel-pod-kontrol-lakra-sintez): «ООО "Лакра Синтез" – стал
единственным владельцем ООО "БАСФ Восток"». Статья опубликована через
два месяца после президентского распоряжения и описывает уже
свершившийся факт смены собственника, а не намерение.

НЕ проверено дословно (WebFetch на rbc.ru и на текст самого распоряжения
у kommersant.ru отдал 401/не содержал деталей закрытия) — используется
торгово-отраслевой источник (mrc.ru), а не одно из трёх изданий,
уже стоящих в src карточки; решение о статусе принято на основании
прямой, недвусмысленной цитаты об уже произошедшей смене владельца,
а не намерения.

НЕ включены: консультанты сделки, точная дата внесения записи в ЕГРЮЛ
(источник её не называет), независимая оценка суммы — не найдены.

Запуск: python3 pipeline/fix_basf_lakra_sintez_closed.py
        python3 pipeline/fix_basf_lakra_sintez_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g073bf58b'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_EXTRA = (
    'Процесс продажи 100% ООО «БАСФ Восток» компании ООО «Лакра Синтез». '
    '7 мая 2024 года Президент РФ подписал распоряжение, разрешающее '
    'сделку, в связи с необходимостью исключения компании из перечня '
    'стратегических предприятий (распоряжение Президента РФ от 09.11.2022 '
    'N 372-рп). (Сделка касается продажи активов BASF, статус сделки в '
    'процессе закрытия после одобрения Президентом РФ)'
)
NEW_EXTRA = (
    'Продажа 100% ООО «БАСФ Восток» компании ООО «Лакра Синтез». 7 мая '
    '2024 года Президент РФ подписал распоряжение, разрешающее сделку, в '
    'связи с необходимостью исключения компании из перечня стратегических '
    'предприятий (распоряжение Президента РФ от 09.11.2022 N 372-рп). К '
    'началу июля 2024 года сделка закрыта: «ООО "Лакра Синтез" – стал '
    'единственным владельцем ООО "БАСФ Восток"» (mrc.ru, 02.07.2024).'
)

NEW_SRC = [
    ['MRC.ru', 'https://www.mrc.ru/news/413188-lakokrasochniy-zavod-basf-v-podmoskove-pereshel-pod-kontrol-lakra-sintez'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['extra'] == OLD_EXTRA
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== status: {OLD_STATUS!r} -> {NEW_STATUS!r} ===')
    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['extra'] = NEW_EXTRA
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
