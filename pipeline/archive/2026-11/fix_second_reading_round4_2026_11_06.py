# -*- coding: utf-8 -*-
"""Второе чтение, круг 4 (6 ноября 2026): g7994f736 (JTI) и g5b2cf7bd (Umbrella IT).

g7994f736: «Цель сделки» открывалась отпиской — теперь мотив президента с атрибуцией; из «Как устроена
сделка» снята фраза «права собственности формально остаются у прежних владельцев» (в источниках не сказана)
и слова Пескова (комментарий, не механика); «остановила новые вложения» → «приостановила инвестиции».
g5b2cf7bd: «Оценка и цена» только повторяла сумму и earn-out (они в «Обзоре» и «Условиях») — поле снято,
запись снята из fixes/written_2026_11_05_vm.py.

Запуск: python3 pipeline/archive/2026-11/fix_second_reading_round4_2026_11_06.py [--write]
"""
import importlib.util
import json
import os
import pprint
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
WRITTEN = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'written_2026_11_05_vm.py')

RAT = ('Президент 1 октября говорил, что механизм временного управления позволяет заранее подготовить '
       'ответные шаги на случай национализации российских предприятий за рубежом; при благоприятном '
       'развитии событий он допускал вернуть контроль прежним владельцам. Отдельно для JTI причину не называли.')
STRUCT = ('Временным управляющим указ назначил АО «Промышленные активы», управление временное. Указ № 817 '
          'внес доли в четырех обществах в перечень имущества под временным управлением, утвержденный '
          'указом № 302 от 25 апреля 2023 года.')
UKAZ_QUOTE = ('Указ Президента Российской Федерации от 05.11.2026 № 817 О внесении изменений в перечень движимого '
              'и недвижимого имущества, ценных бумаг, долей в уставных (складочных) капиталах российских '
              'юридических лиц и имущественных прав, в отношении которых вводится временное управление, '
              'утвержденный Указом Президента Российской Федерации от 25 апреля 2023 г. № 302.')


def main(write):
    pend = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in pend['cards']}
    j, u = cards['g7994f736'], cards['g5b2cf7bd']
    j['eco']['rationale'], j['law']['struct'] = RAT, STRUCT
    ctx = j['eco']['context']
    j['eco']['context'] = ctx.replace('Еще в 2022 году группа остановила новые вложения в Россию.',
                                      'Еще в 2022 году группа приостановила инвестиции в Россию.')
    u['eco']['val'] = '—'
    spec = importlib.util.spec_from_file_location('w', WRITTEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fixes = []
    for fx in mod.FIXES:
        if (fx['id'], fx['field']) == ('g5b2cf7bd', 'eco.val'):
            continue
        if fx['id'] == 'g7994f736':
            if fx['field'] == 'eco.rationale':
                fx['new'] = RAT
            elif fx['field'] == 'law.struct':
                fx['new'] = STRUCT
                if UKAZ_QUOTE not in fx['quote']:
                    fx['quote'] = fx['quote'] + ' … ' + UKAZ_QUOTE
            elif fx['field'] == 'eco.context':
                fx['new'] = j['eco']['context']
        fixes.append(fx)
    print('JTI: rationale, struct, context; Umbrella: eco.val снят; записей', len(mod.FIXES), '->', len(fixes))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    json.dump(pend, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    head = open(WRITTEN, encoding='utf-8').read().split('FIXES = ')[0]
    open(WRITTEN, 'w', encoding='utf-8').write(head + 'FIXES = ' + pprint.pformat(fixes, width=100, sort_dicts=False) + '\n')
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
