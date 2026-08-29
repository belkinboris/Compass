# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gf424fa11
(Wildberries внесла 15 юрлиц в СП «РВБ» с Russ). Дельта-поиск нашёл
согласование ФАС (карточка несла «Публично не сообщалось») и дальнейшую
судьбу доли «Стинн». Проверено лично прямым WebFetch.

1) `law.appr` — Lenta.ru, дословно (совпадает в двух независимых
проверках): «ФАС одобрила передачу компаний Russ в «РВБ» в рамках
объединения с Wildberries» — это было последним регуляторным
согласованием, требовавшимся для завершения слияния (20 сентября 2024
года, дата — из адреса самой статьи).
Источник: https://lenta.ru/news/2024/09/20/fas-odobrila-sliyanie-wildberries-i-russ/

2) `eco.context` — дополнение к уже описанной структуре «Стинн»:
структура сменилась 5 декабря 2024 года. New-Retail.ru, дословно:
«Теперь Григорию Садояну принадлежит в ООО «Стинн» доля 50%, а
оставшиеся 50% — ЗПИФ «Гало»» (управляющая компания — «Эмрис»,
Ростов-на-Дону).
Источник: https://new-retail.ru/novosti/retail/sovladelets_obedinennoy_kompanii_wildberries_i_russ_smenil_sostav_uchrediteley/

Туда же — попытка Валентина Бакальчука заблокировать слияние в суде не
удалась. Secrets.tbank.ru, дословно: «Суд отказался арестовывать доли
Татьяны Ким в компании ООО «Вайлдберриз» и Роберта Мирзояна в компании
ООО «РВБ» и выполнять другие требования Бакальчука, направленные на
блокировку слияния компаний».
Источник: https://secrets.tbank.ru/novosti/spor-wbruss/

НЕ включены: смена долей в самом ООО «Вайлдберриз» (не РВБ) — другое
юрлицо, место для этого факта — профиль компании «Вайлдберриз», не эта
карточка о передаче 15 юрлиц в СП; отчётность РВБ/RWB за 2025 год,
ребрендинг, вопрос IPO — общие корпоративные новости объединённой
компании, не привязаны к событию 4 июля 2024 года, которое описывает эта
карточка; связь с «Известной проблемой» O'Key/«Земун»/«РБФ ритейл» из
CLAUDE.md — дельта-поиск не нашёл ничего, связывающего эти два сюжета,
это разные структуры.

Запуск: python3 pipeline/fix_wildberries_russ_fas_approval_and_stinn.py
        python3 pipeline/fix_wildberries_russ_fas_approval_and_stinn.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf424fa11'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'ФАС 20 сентября 2024 года «одобрила передачу компаний Russ в «РВБ» '
    'в рамках объединения с Wildberries» — последнее регуляторное '
    'согласование, требовавшееся для завершения слияния.'
)

OLD_CONTEXT = (
    'Новый совладелец контролируется Григорием Садояном, которому '
    'напрямую принадлежит 50% долей в компании, 30% принадлежит ООО '
    '«Резерв-А», и 20% — АО «Олимпия». Все доли в ООО «Стин» заложены в '
    'ВТБ.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' С 5 декабря 2024 года структура сменилась: «Теперь Григорию '
    'Садояну принадлежит в ООО «Стинн» доля 50%, а оставшиеся 50% — ЗПИФ '
    '«Гало»» (New-Retail.ru). Валентин Бакальчук пытался через суд '
    'заблокировать слияние — суд «отказался арестовывать доли Татьяны '
    'Ким в компании ООО «Вайлдберриз» и Роберта Мирзояна в компании ООО '
    '«РВБ» и выполнять другие требования Бакальчука, направленные на '
    'блокировку слияния компаний» (secrets.tbank.ru).'
)

NEW_SRC = [
    ['Lenta.ru', 'https://lenta.ru/news/2024/09/20/fas-odobrila-sliyanie-wildberries-i-russ/'],
    ['New-Retail.ru', 'https://new-retail.ru/novosti/retail/sovladelets_obedinennoy_kompanii_wildberries_i_russ_smenil_sostav_uchrediteley/'],
    ['secrets.tbank.ru', 'https://secrets.tbank.ru/novosti/spor-wbruss/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.appr: было ===')
    print(OLD_APPR)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
