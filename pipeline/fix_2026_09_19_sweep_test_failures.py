# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — четыре находки полного pytest после партии
fix_known_issues_2026_09_19_sweep.py и fix_dedupe_2026_09_18_ingest_reruns.py.

1. g61b33118 (Руском/Черкизово) — нельзя одновременно buyer-ссылку и
   buyer_name текстом (test_buyer_is_named_once): текст был точным именем
   дочерней компании, а не общим названием бренда, но правило одно на всех
   — снимаем текст, факт не теряется (то же самое уже написано в law.struct).

2. Внутренний id карточки не может стоять в тексте для читателя
   (test_no_internal_card_id_in_reader_text) — перекрёстные ссылки на
   g26608f96/c7403d4db/g97679d43, добавленные той же партией, писали адрес
   с id прямо в eco.context. Проект уже отказался от этого приёма 11 сентября
   (id никуда не ведёт для читателя, поиска по нему на сайте нет) — переписаны
   словами, без адреса.

3. c7403d4db.eco.context — предыдущий пункт заодно чинит и это: добавленное
   предложение ломало точное совпадение с уже применённой записью
   review.FIXES (batch_a_2025.py); без добавления совпадение восстанавливается.

4. g5eb6ff22 vs g6a4b0a2a (test_no_duplicate_deal_cards) — у Шишкарева и
   «Дела» с «Росатомом» в базе оказались ДВЕ карточки одной и той же сделки:
   g5eb6ff22 (заведена 15 июля, 14 источников, уже полностью и точно
   описывает исход к 3 сентября) и g6a4b0a2a (заведена 23 июля, 5 источников,
   правка этой же ночи пыталась догнать её до того же состояния — не заметив,
   что более полная карточка уже есть). Оставляем g5eb6ff22, переносим один
   источник, которого там не было (finance.mail.ru, про одобрение ФАС), и
   сливаем g6a4b0a2a в неё.

Запуск: сухой прогон без аргументов, запись — --write.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    tp = data.get('telegram_posts', {})

    # 1. g61b33118 — снять buyer_name, ссылка на профиль уже есть.
    d = deals['g61b33118']
    assert d.get('buyer') == 'gd3bb09b3' and d.get('buyer_name') == 'АО «Куриное царство»'
    del d['buyer_name']

    # 2-3. Перекрёстные ссылки — без внутреннего id в тексте для читателя.
    d = deals['g26608f96']
    OLD_TAIL = (' Сделку с реальным покупателем описывает отдельная карточка: '
                'https://projectcompass.ru/#/deal/g139db8c2 («S8 Capital и ГК '
                '«МТ-Интеграция» приобрели 79% акций «Аквариуса»»).')
    assert d['eco']['context'].endswith(OLD_TAIL)
    d['eco']['context'] = (d['eco']['context'][:-len(OLD_TAIL)] +
                            ' Реальным покупателем стал альянс S8 Capital и ГК '
                            '«МТ-Интеграция» (79% акций, август 2025 года) — этой '
                            'сделке посвящена отдельная карточка на сайте.')

    a, b = deals['c7403d4db'], deals['g97679d43']
    OLD_A = (' Распродажа активов поштучно, включая «Лабинский», описана отдельной '
             'карточкой: https://projectcompass.ru/#/deal/g97679d43')
    assert a['eco']['context'].endswith(OLD_A)
    a['eco']['context'] = a['eco']['context'][:-len(OLD_A)]

    OLD_B = (' План создать общий агрохолдинг на базе этих же активов описан отдельной '
             'карточкой: https://projectcompass.ru/#/deal/c7403d4db')
    assert b['eco']['context'].endswith(OLD_B)
    b['eco']['context'] = b['eco']['context'][:-len(OLD_B)]

    # 4. g6a4b0a2a слита в g5eb6ff22 (та же сделка, более полная карточка).
    assert tp.get('g6a4b0a2a') is None, 'у g6a4b0a2a есть живой пост — слияние вручную'
    survivor = deals['g5eb6ff22']
    url = ('https://finance.mail.ru/article/fas-soglasovala-hodatajstva-rosatoma-i-'
           'shishkareva-o-priobretenii-dolej-v-uk-delo-69207448/')
    if not any(len(s) > 1 and s[1] == url for s in survivor['src']):
        survivor['src'].append(['finance.mail.ru', url])

    data['deals'] = [dd for dd in deals.values() if dd['id'] != 'g6a4b0a2a']
    data.setdefault('merged', {})['g6a4b0a2a'] = 'g5eb6ff22'

    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print('Записано.')
    else:
        print('Сухой прогон ок. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
