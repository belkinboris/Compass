# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g4dd7a75c`
(«Schneider Electric продал российское подразделение местному
менеджменту», добавлена в базу 3 августа 2026, полностью обыскана в тот
же день).

Дельта-поиск (саб-агент + личная проверка) нашёл название бренда, под
которым продолжил работу бизнес. Личный WebFetch (kommersant.ru/doc/
5446211, 4 июля 2022) подтвердил дословно название новой компании —
Systeme Electric — и то, что «Конкретные покупатели, а также условия
сделки не раскрываются» (карточка права, оставляя сумму и стороны
управления без имён). Личный WebFetch (systeme.ru — собственный сайт
компании) подтвердил дословно, что генеральным директором Systeme
Electric стал Алексей Кашаев: «рассказывает генеральный директор
Systeme Electric Алексей Кашаев».

Саб-агент также нашёл на реестровых агрегаторах (не проверено мной
лично прямым чтением — сайты блокируют доступ капчей) утверждение, что
Кашаев — мажоритарный совладелец (51%) вместе с пятью бывшими топ-
менеджерами Schneider Electric Russia. Эта детализация НЕ вносится:
недостаточно подтверждена независимым дословным чтением.

Запуск:
    python3 pipeline/fix_schneider_electric_systeme_rebrand.py            # сухой прогон
    python3 pipeline/fix_schneider_electric_systeme_rebrand.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SHARE = (
    'Российское подразделение «Шнейдер Электрик» продано местному '
    'менеджменту.'
)
NEW_ECO_SHARE = OLD_ECO_SHARE + (
    ' Бизнес продолжил работу под новым брендом Systeme Electric; '
    'генеральным директором стал Алексей Кашаев.'
)

NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/5446211']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g4dd7a75c']

    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'g4dd7a75c eco.share уже другой: %r' % (d['eco']['share'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g4dd7a75c: eco.share дополнен (бренд Systeme Electric, '
          'гендиректор Алексей Кашаев); добавлен источник kommersant.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['share'] = NEW_ECO_SHARE
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
