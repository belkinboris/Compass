# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g85dfa88c
(Солид-банк покупает Камчатпрофитбанк) — карточка сама писала в extra
«Сделка находится в процессе закрытия» и держала статус «Обсуждается»
больше двух лет; найдено прямое подтверждение закрытия.

Закрытие сделки — проверено лично прямым WebFetch (bankinform.ru):
«Солид Банк приобрёл Муниципальный Камчатпрофитбанк, в результате чего
была создана банковская группа», «И Солид Банк, и Муниципальный
Камчатпрофитбанк продолжают функционировать в обычном режиме». Дата
закрытия и переименование цели — проверено лично прямым WebFetch
(profbanking.com, 28 июля 2025 года): «в конце 2024 года Солид Банк
выкупил контрольный пакет акций Камчатпрофитбанка и два банка образовали
банковскую группу», «"Муниципальный Камчатпрофитбанк" переименован в
Коммерческий Международный "ПРОФИЛЬНЫЙ БАНК"», новое сокращённое
наименование — «КМ "Профильный Банк" (АО)», лицензия Банка России
№ 2103.

`status`: «Обсуждается» → «Закрыта», дата уточнена — конец 2024 года.

НЕ ВКЛЮЧЕНО: получение Солид Банком специального разрешения на сделку
с «недружественным» банком (эта осложняющая деталь уже стоит в
`law.terms`) — ни один источник не подтверждает прямой цитатой сам факт
получения разрешения, только результат (сделка состоялась); финансовые
показатели Солид Банка (активы 33 млрд руб. и т. д.) — цифры взяты
только из сводки поисковика, при прямом чтении пресс-релиза
рейтингового агентства не подтвердились, не переносятся без дословной
проверки.

Запуск: python3 pipeline/fix_solid_bank_kamchatprofitbank_closed.py
        python3 pipeline/fix_solid_bank_kamchatprofitbank_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g85dfa88c'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_EXTRA = 'Сделка находится в процессе закрытия.'
NEW_EXTRA = (
    'Сделка закрыта в конце 2024 года: «Солид Банк приобрёл '
    'Муниципальный Камчатпрофитбанк, в результате чего была создана '
    'банковская группа», «И Солид Банк, и Муниципальный Камчатпрофитбанк '
    'продолжают функционировать в обычном режиме» (bankinform.ru). В '
    'июле 2025 года цель переименована: «"Муниципальный '
    'Камчатпрофитбанк" переименован в Коммерческий Международный '
    '"ПРОФИЛЬНЫЙ БАНК"», новое сокращённое наименование — КМ '
    '"Профильный Банк" (АО) (profbanking.com).'
)

NEW_SRC = [
    ['bankinform.ru', 'https://bankinform.ru/news/135869'],
    ['profbanking.com', 'https://www.profbanking.com/only-news/5228-commercial-international-profile-bank'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
