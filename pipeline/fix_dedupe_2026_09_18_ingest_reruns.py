# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 (ночной разбор «Известные проблемы»).

Приток за ночь 18→19 сентября независимо пересобрал минимум девять сюжетов,
которые уже были в базе отдельными, более полными карточками, — новые
черновики родились из тех же источников, что уже читали раньше, но без
сверки с уже существующей карточкой той же сделки. У всех девяти новых
карточек нет живого поста в канале (проверено: telegram_posts пуст),
поэтому слияние безопасно техническое, а не редакционное решение.

Оставляем более полную/раньше заведённую карточку («survivor»), переносим
из дубля («loser») то немногое, чего в survivor ещё не было (единичный
факт, более точная дата, привязка стороны), и убираем loser с редиректом
через `merged` — тем же приёмом, что уже применялся для gf1608a6f/mts-bik
(см. pipeline/fix_merge_mts_bik_duplicate.py).

Пары (loser → survivor):
1. g726675ea → ge6f1e0ae   Globaltrans/КСП Капитал — перенесена веха
   (смена совета директоров 21.05.2025) и источник на неё.
2. gb64c92ec → g61b33118   Руском/Черкизово (Голышманово) — добавлена
   прямая ссылка на профиль покупателя («Черкизово»).
3. g51965ff0 → g0d72e1d5   Raven Russia/«Константа» — уточнена дата
   (19.09.2024 по ЕГРЮЛ, а не просто «2024») и добавлен источник.
4. gd95bf2d7 → g5745c187   Kellermann Center/Мытищи — перенесена привязка
   предмета к профилю компании (INN 7839506496).
5. g5f1e3e15 → g76f31c63   «Ла дача Астрахань»/«Акашевская» — чистый
   дубль, новых фактов нет.
6. gd7d42e2f → g47cc407c   Tawazun/Aurus 2019 — чистый дубль; у дубля к
   тому же неверно определена природа сделки (control_change вместо
   входа миноритарного инвестора), поэтому не заимствуем у него ничего.
7. ga26b0547 → g04edfc17   «Дедал»/Aurus 2024 — уточнена дата (2024-12-01
   вместо «2024»).
8. g2b02f0f5 → g2d653619   Societe Generale/«АЛД Автомотив» — чистый
   дубль, survivor полнее (веха, больше источников, привязка предмета).
9. g971a5410 → g2b1fe015   VK/«Точка»/«Интеррос» — чистый дубль, survivor
   полнее (привязка покупателя, больше источников).

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

    losers = ['g726675ea', 'gb64c92ec', 'g51965ff0', 'gd95bf2d7', 'g5f1e3e15',
              'gd7d42e2f', 'ga26b0547', 'g2b02f0f5', 'g971a5410']
    for lid in losers:
        assert tp.get(lid) is None, '%s: есть живой пост в канале — слияние вручную' % lid
        assert lid in deals, '%s: карточки уже нет' % lid

    # 1. Globaltrans/КСП Капитал — перенести веху о смене совета директоров.
    loser = deals['g726675ea']
    survivor = deals['ge6f1e0ae']
    assert 'events' not in survivor
    survivor['events'] = loser['events']
    src_url = 'https://www.interfax.ru/world/1026956'
    if not any(len(s) > 1 and s[1] == src_url for s in survivor.get('src', [])):
        survivor['src'].append(['Интерфакс', src_url])

    # 2. Руском/Черкизово (Голышманово) — привязать покупателя к профилю.
    survivor = deals['g61b33118']
    assert survivor.get('buyer') is None
    survivor['buyer'] = 'gd3bb09b3'

    # 3. Raven Russia/«Константа» — точная дата и источник.
    loser = deals['g51965ff0']
    survivor = deals['g0d72e1d5']
    assert survivor['date'] == '2024'
    survivor['date'] = '2024-09-19'
    src_url = 'https://spb.vedomosti.ru/business/news/2024/11/18/1075745-raven-russia-prodala-biznes-tsentr-konstanta-v-peterburge'
    if not any(len(s) > 1 and s[1] == src_url for s in survivor.get('src', [])):
        survivor['src'].append(['Ведомости.Северо-Запад', src_url])

    # 4. Kellermann Center/Мытищи — привязать предмет к профилю компании.
    survivor = deals['g5745c187']
    assert survivor.get('target') is None
    survivor['target'] = 'gpervomaiskayazarya'

    # 5-9. Чистые дубли — новых фактов не переносим.

    for lid in losers:
        pass  # проверки уже сделаны выше

    data['deals'] = [d for d in data['deals'] if d['id'] not in losers]
    merged = data.setdefault('merged', {})
    survivors = {
        'g726675ea': 'ge6f1e0ae', 'gb64c92ec': 'g61b33118',
        'g51965ff0': 'g0d72e1d5', 'gd95bf2d7': 'g5745c187',
        'g5f1e3e15': 'g76f31c63', 'gd7d42e2f': 'g47cc407c',
        'ga26b0547': 'g04edfc17', 'g2b02f0f5': 'g2d653619',
        'g971a5410': 'g2b1fe015',
    }
    for lid, sid in survivors.items():
        merged[lid] = sid

    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print('Слито %d карточек-дублей. ЗАПИСАНО.' % len(losers))
    else:
        print('Сухой прогон: слил бы %d карточек-дублей. Повторите с --write.' % len(losers))
        for lid, sid in survivors.items():
            print('  %s -> %s' % (lid, sid))


if __name__ == '__main__':
    main(write='--write' in sys.argv)
