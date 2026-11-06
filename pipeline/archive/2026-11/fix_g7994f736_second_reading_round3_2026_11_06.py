# -*- coding: utf-8 -*-
"""g7994f736 (JTI), второе чтение, круг 3 (6 ноября 2026).

eco.share читалось как доли самой «Дж.Т.И. Россия» в ее уставном капитале — переписано: передаются доли
в четырех обществах, принадлежавшие названным владельцам (указ № 817, пп. 93–99).
law.struct: слова Пескова сказаны 29 сентября о механизме в целом (Ведомости), не об этом указе — даны с датой.
eco.target_fin: выручка и прибыль ООО «Дж.Т.И. Россия» за 2022–2023 сняты: цифр нет в источниках, год
устарел, а сама «Дж.Т.И. Россия» — держатель долей, под управление не передается.
Заголовок и «Предмет» правятся ответом приемки (accept_card), записи fixes/written_2026_11_05_vm.py
подогнаны под новый текст, иначе review.py откажет «поле уже другое».

Запуск: python3 pipeline/archive/2026-11/fix_g7994f736_second_reading_round3_2026_11_06.py [--write]
"""
import importlib.util
import json
import os
import pprint
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
WRITTEN = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'written_2026_11_05_vm.py')

SHARE = ('В ООО «Дж.Т.И. Донской табак» переданы 99,9999% долей, принадлежавших ООО «Дж.Т.И. Россия», и '
         '0,0001%, принадлежавшие АО «Переславль-Табак». В ООО «Дж.Т.И. Елец» — 65,64% долей, принадлежавших '
         'JT International Holding B.V., 18,85%, принадлежавших ООО «Дж.Т.И. Россия», и 15,51%, принадлежавших '
         'ООО «Петро». Доли в ООО «Крес Нева» и ООО «Петро» переданы полностью: по 100%, принадлежавших '
         'JTI Investments Sarl.')
STRUCT = ('Временным управляющим указ назначил АО «Промышленные активы». Права собственности на доли '
          'формально остаются у прежних владельцев. О самом механизме Дмитрий Песков говорил еще 29 сентября, '
          'в общем виде, не про этот указ: по его словам, он не направлен на смену собственников и обратим, '
          'но условий для возврата активов иностранным владельцам, по его оценке, пока нет.')
VED_QUOTE = ('Ранее, 29 сентября, представитель Кремля подчеркивал , что этот механизм не направлен на смену '
             'собственников. По словам Пескова, процесс обратим, однако предпосылок для возвращения контроля '
             'иностранным владельцам российские власти пока не видят.')


def main(write):
    pend = json.load(open(PENDING, encoding='utf-8'))
    card = [c for c in pend['cards'] if c['id'] == 'g7994f736'][0]
    card['eco']['share'], card['law']['struct'] = SHARE, STRUCT
    card['eco']['target_fin'] = '—'
    spec = importlib.util.spec_from_file_location('w', WRITTEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for fx in mod.FIXES:
        if fx['id'] != 'g7994f736':
            continue
        if fx['field'] == 'eco.share':
            fx['new'] = SHARE
        elif fx['field'] == 'law.struct':
            fx['new'] = STRUCT
            if VED_QUOTE not in fx['quote']:
                fx['quote'] = fx['quote'] + ' … ' + VED_QUOTE
    print('eco.share, law.struct переписаны, eco.target_fin снят')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    json.dump(pend, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    head = open(WRITTEN, encoding='utf-8').read().split('FIXES = ')[0]
    open(WRITTEN, 'w', encoding='utf-8').write(head + 'FIXES = ' + pprint.pformat(mod.FIXES, width=100, sort_dicts=False) + '\n')
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
