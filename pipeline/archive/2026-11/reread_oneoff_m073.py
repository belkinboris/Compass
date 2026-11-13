# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m073 (часть 1): то, что таблица правок не умеет.

- c71e19cc1 (Gunvor/«Лукойл»): предмет не был назван — привязан профиль LUKOIL International GmbH
  (g6b0b26d9), это и есть дочка, которую Gunvor предлагала купить (релиз ЛУКОЙЛа).
- c25d07929 («Точка»/ФРИИ): имя покупателя «Банк «Точка»», поставленное review.py, привязано к
  профилю того же имени (g09ccbaca).
- c85ba6042, c3c15a888: запуск фонда — профиль предмета не нужен (заметка приемки).

Без ключа — сухой прогон; --write пишет, перечитав базу прямо перед записью. Повторный запуск
ничего не ломает («уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m073, 12.11.2026'
LUK = 'https://lukoil.ru/PressCenter/Pressreleases/Pressrelease/lukoil-poluchil-predlozhenie-ot-gunvor-o'


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    out = []
    c = deals['c71e19cc1']
    if c.get('target') != 'g6b0b26d9':
        assert c.get('target') is None and not c.get('asset'), (c.get('target'), c.get('asset'))
        assert comps['g6b0b26d9']['name'] == 'LUKOIL International GmbH'
        c['target'] = 'g6b0b26d9'
        fact_edit_guard.log(c, 'target', 'g6b0b26d9',
                            'Gunvor Group Ltd. (далее – Покупатель) предложения о приобретении LUKOIL International GmbH '
                            '(100% дочернего общества ПАО «ЛУКОЙЛ», владеющего зарубежными активами Группы «ЛУКОЙЛ»).',
                            LUK, BY)
        out.append('c71e19cc1 target -> g6b0b26d9')
    c = deals['c25d07929']
    if c.get('buyer') != 'g09ccbaca':
        assert c.get('buyer') is None and c.get('buyer_name') in (None, 'Банк «Точка»'), c.get('buyer_name')
        assert comps['g09ccbaca']['name'] == 'Банк «Точка»'
        c['buyer'] = 'g09ccbaca'
        c['buyer_name'] = None
        out.append('c25d07929 buyer -> g09ccbaca')
    for cid, why in (('c85ba6042', 'долговой фонд «Амур капитал» — фонд, не компания: профиль не нужен'),
                     ('c3c15a888', 'фонд «Новые чемпионы» — фонд, не компания: профиль не нужен')):
        notes = deals[cid].setdefault('accepted_notes', {}).setdefault('no_profile', {})
        if notes.get('target') != why:
            notes['target'] = why
            out.append('%s accepted_notes.no_profile.target' % cid)
    return out


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    out = apply(data)
    print('\n'.join(out) or 'уже применено')
    if '--write' in argv and out:
        data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(data)
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
