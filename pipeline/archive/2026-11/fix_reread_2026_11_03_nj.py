# -*- coding: utf-8 -*-
"""Вычитка базы, партия nj (3 ноября 2026, ночь): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_03_nj.py (там же список ONE_OFF с причинами).

- g39752167 (Highland Gold/Kinross): в law.adv у Dechert LLP описание с оборванной скобкой
  («Jonathan Angell) — консультант Kinross Gold»); оба консультанта подтверждены MarketScreener.
- ge85383b6 («Анабар»): описание профиля предмета пересказывало сделку — в посте строка «Предмет»
  выходила «Анабар — система…; в 2022 году привлекла 65 млн ₽ от…»; теперь «кто это».
- ge9937266 (Sk Capital/«Софтлайн»): снят источник Ведомости 27.08.2026 — заметка о результатах
  «Софтлайна» за I полугодие 2026 года, о сделке с Sk Capital в ней ни слова (прочитана целиком);
  цифры из нее стояли в extra и сняты записью FIXES.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nj.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    raw = open(BASE, encoding='utf-8').read()                  # перечитываем прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    # g39752167 — law.adv
    c = deals['g39752167']
    old_adv = [['Юридический консультант', 'Dechert LLP', 'Jonathan Angell) — консультант Kinross Gold'],
               ['Юридический консультант', 'Latham & Watkins LLP', 'консультант Highland Gold Mining']]
    assert c['law']['adv'] == old_adv, c['law']['adv']
    c['law']['adv'] = [['Юридический консультант', 'Dechert LLP', 'Джонатан Энджелл — консультант Kinross Gold'],
                       ['Юридический консультант', 'Latham & Watkins LLP', 'консультант Highland Gold Mining']]

    # ge85383b6 — описание профиля предмета
    p = comps['gd492e1fd']
    assert p['name'] == 'Анабар'
    assert p['desc'] == ('Система управления продажами на маркетплейсах; в 2022 году привлекла 65 млн ₽ от '
                         '«Первого Бита», АО «Здоровье» и 13 бизнес-ангелов.'), p['desc']
    p['desc'] = ('Российская система управления продажами на маркетплейсах; запущена в 2020 году бывшими '
                 'топ-менеджерами «Циана».')

    # ge9937266 — источник не о сделке
    c = deals['ge9937266']
    gone = ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/08/27/1224061-gk-softline-vishla']
    assert gone in c['src'], c['src']
    c['src'] = [s for s in c['src'] if s != gone]

    if '--write' in argv:
        out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
        with open(BASE, 'w', encoding='utf-8') as f:
            f.write(out)
        print('записано')
    else:
        print('сухой прогон; запись — с ключом --write')


if __name__ == '__main__':
    main(sys.argv[1:])
