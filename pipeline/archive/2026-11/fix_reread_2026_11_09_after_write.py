# -*- coding: utf-8 -*-
"""Вычитка 9 ноября 2026: две поправки после записи партий fa–fe.

1. g995f83cf («Ренессанс Капитал»), law.adv. Владелец: Orion консультировал «Ренессанс
   Капитал» — это сказано во всех источниках. `_ADV` в pipeline/ingest/fixes/
   reread_2026_11_09_fb.py исправлен уже после того, как разовая часть fb записала базу,
   поэтому в базе стоит прежний вариант: роль «Юридический консультант покупателей
   (Максим Орловский, Владимир Куров и Игорь Даниленко)» и в заметке «Клиента Orion прямо
   не называет». Строки переносятся из `_ADV` файла fb как есть.

2. legal_short, записанные `party_legal_names.py --write` в этом же прогоне с испорченными
   вложенными кавычками (реестр пишет ООО "СК "РЕНЕССАНС ЖИЗНЬ", а `legal_short()`
   теряет «» внутреннего имени и закрывающую кавычку): форма и имя — из реестра, кавычки
   «елочки» парами, как у ПАО «ГМК «Норильский никель»». Профиль «Райффайзен Лайф» — юрлицо
   сейчас ООО «СК «Р.Лайф»» (по реестру, имя сменилось после сделки).

Запуск: python3 pipeline/archive/2026-11/fix_reread_2026_11_09_after_write.py [--write]
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
FB = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'reread_2026_11_09_fb.py')

OLD_ROLE = 'Юридический консультант покупателей (Максим Орловский, Владимир Куров и Игорь Даниленко)'

LEGAL_SHORT = [  # (профиль, записано скриптом, верно)
    ('gf5faae55', 'ООО «СК "ренессанс Жизнь»', 'ООО «СК «Ренессанс Жизнь»»'),
    ('gf000224d', 'ООО «СК "р.лайф»', 'ООО «СК «Р.Лайф»»'),
    ('g12111389', 'ПАО «ГК «Самолет»', 'ПАО «ГК «Самолет»»'),
    ('g5ff0a3de', 'АО «ГК «Черноголовка»', 'АО «ГК «Черноголовка»»'),
]


def _apply(data):
    spec = importlib.util.spec_from_file_location('fb', FB)
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    new_adv = [list(a) for a in fb._ADV['g995f83cf']]
    assert 'Клиента Orion прямо не называет' not in json.dumps(new_adv, ensure_ascii=False)
    card = next(d for d in data['deals'] if d['id'] == 'g995f83cf')
    adv = card['law']['adv']
    assert [a[1] for a in adv] == ['Orion', 'Никольская Консалтинг'], adv
    assert adv[0][0] == OLD_ROLE and 'Клиента Orion прямо' in adv[0][2], adv[0]
    assert adv[1] == new_adv[1], 'строка «Никольской Консалтинг» не та, что в fb'
    card['law']['adv'] = new_adv
    for pid, old, new in LEGAL_SHORT:
        prof = data['companies'][pid]
        assert prof.get('legal_short') == old, (pid, prof.get('legal_short'))
        prof['legal_short'] = new


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data)
    print('g995f83cf law.adv: роль Orion — консультант «Ренессанс Капитала»; legal_short: %d профилей'
          % len(LEGAL_SHORT))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))     # перечитать прямо перед записью
    _apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
