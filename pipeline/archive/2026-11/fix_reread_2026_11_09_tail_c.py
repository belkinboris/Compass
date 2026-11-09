# -*- coding: utf-8 -*-
"""Вычитка 9 ноября 2026, хвост (в): «Команда сделки» g6520943f («Райффайзен Лайф»).

Поиск консультантов по сделке нашел второго консультанта продавца: Schoenherr консультировал
Uniqa по продаже ее 75% (пресс-релиз фирмы на Mondaq: «Schoenherr advises UNIQA on withdrawal
from Russia by selling UNIQA's share in Raiffeisen Life»; адрес запрошен, 200). Строка Melling,
Voitishkin & Partners остается как была: страница фирмы о сделке находится поиском
(mv.legal/en/news/melling-voytishkin-i-partnery-konsultiruet-renessans-strakhovanie-…), но
полный адрес не открылся (404 по обрезанному адресу выдачи) — голый «mv.legal/news» не
заменяется непроверенным адресом.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_09_tail_c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SH = 'https://www.mondaq.com/pressrelease/149062/schoenherr-advises-uniqa-on-withdrawal-from-russia-by-selling-uniqas-share-in-raiffeisen-life'
OLD0 = ['Юридический консультант покупателя («Ренессанс страхование»)', 'Melling, Voitishkin & Partners',
        'Приобретение 100% СК «Райффайзен Лайф» у Uniqa Group и Райффайзенбанка. Источник: mv.legal/news']
NEW2 = ['Юридический консультант продавца (Uniqa)', 'Schoenherr',
        'Продажа 75% «Райффайзен Лайф», принадлежавших Uniqa. Источник: ' + SH]


def _apply(data):
    import review
    card = next(d for d in data['deals'] if d['id'] == 'g6520943f')
    adv = card['law']['adv']
    assert len(adv) == 2 and adv[0] == OLD0 and adv[1][1] == 'АЛРУД', adv
    new = [adv[0], adv[1], NEW2]
    card['law']['adv'] = new
    for f in review.FIXES:
        if (f['id'], f['field']) == ('g6520943f', 'law.adv') and f['new'] is not None and f['new'] != new:
            marks = card.setdefault('proofread_absorbed', {}).setdefault('law.adv', [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
    for label, url in (('Schoenherr — о сделке', SH),):
        if not any(len(s) > 1 and s[1] == url for s in card['src']):
            card['src'].append([label, url])


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data)
    print('g6520943f law.adv: + консультант Uniqa Schoenherr; src +1')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))
    _apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
