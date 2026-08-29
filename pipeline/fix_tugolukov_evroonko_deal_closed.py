# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g3b9c077a
(Евгений Туголуков покупает группу «Евроонко»). Карточка стояла со
статусом «Подписана» с сентября 2024 года — почти два года, хотя источник
уже тогда писал, что закрытие ожидается «после получения регуляторных
одобрений и проведения необходимых корпоративных процедур».

ЗАКРЫТИЕ ПОДТВЕРЖДЕНО. Покупатель, АО «Тетра», — 100%-я «дочка»
сингапурской публичной компании Don Agro International Limited
(переименована в UpHealth Group Limited); её корпоративные шаги по
раскрытию SGX сами по себе публичны и обязательны к точности. Прямая
цитата НГ.ru, 02.07.2026 (проверено лично прямым WebFetch,
https://www.ng.ru/economics/2026-07-02/100_020726_1455.html): «"Don Agro
International Limited" (контролируемая Туголуковым через сингапурскую
"Strongbow Investments" и АО "Тетра") провела внеочередное собрание
акционеров и, во-первых, была переименована в UpHealth Group..., а,
во-вторых, наконец получила одобрение на приобретение медицинских
активов "Евроонко" и "ЮНИКлиник" полностью» — это про январь 2026 года
(28 января, собрание акционеров). Та же статья независимо подтверждает
сумму сделки: «приобрел сеть онкологических клиник «Евроонко» за 3,04
млрд рублей» — совпадает дословно с уже стоящим в карточке `sum` (проверка
на то, что источники говорят об одной и той же сделке).

Дата ФАКТИЧЕСКОЙ регистрационной записи (не только корпоративного
одобрения) — 9 февраля 2026 года, передача 89,01% ООО «812 Капитал» и
11,5% ЦИМТ на АО «Тетра» — подтверждена СОГЛАСОВАННО в трёх независимых
запросах WebSearch по раскрытиям Don Agro/UpHealth на SGX (сама страница
minichart.com.sg заблокирована для WebFetch — 403, попытки через
web.archive.org и SGX PDF тоже не дали читаемого текста), при этом
итоговая структура владения (99,99% через доп. опцион на 9,98% у
Сбербанк Инвестиций) согласуется с изначально заявленным в law.struct
планом «99,99% головной компании». Прямую дословную цитату с этой
страницы получить не удалось — статус меняется на основании личной
проверки одного прямого русскоязычного источника (НГ.ru) плюс
независимого совпадения суммы сделки, а не одной лишь сводки поиска.

Запуск: python3 pipeline/fix_tugolukov_evroonko_deal_closed.py
        python3 pipeline/fix_tugolukov_evroonko_deal_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3b9c077a'

OLD_STATUS = 'Подписана'
NEW_STATUS = 'Закрыта'

OLD_CONTEXT = (
    '«Евроонко» — федеральная сеть клиник экспертной онкологии, которая '
    'работает в сфере здравоохранения с 2011 года.'
)
CONTEXT_ADDITION = (
    ' В январе 2026 года покупатель — сингапурская Don Agro International '
    'Limited (контролируется Туголуковым через АО «Тетра»), переименованная '
    'в UpHealth Group Limited, — «провела внеочередное собрание акционеров '
    'и... наконец получила одобрение на приобретение медицинских активов '
    '«Евроонко» и «ЮНИКлиник» полностью» (НГ.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Независимая газета', 'https://www.ng.ru/economics/2026-07-02/100_020726_1455.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== status: {OLD_STATUS!r} -> {NEW_STATUS!r} ===')
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
