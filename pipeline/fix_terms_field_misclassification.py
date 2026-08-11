# -*- coding: utf-8 -*-
"""Владелец нашёл на карточке «Галс Девелопмент»/Наметкина, что в линзе
«Юрист» под «Условиями» стоит: «"Концепция развития площадки в настоящее
время готовится", - уточнил представитель девелопера.» — это не условие
сделки (не заверение, не индемнити, не опцион, не согласование), а просто
пока-ещё-не-план покупателя насчёт актива. Проверка соседних карточек на
тот же класс дефекта (правило CLAUDE.md — находка не существует в вакууме,
проверять там, где дефект РЕАЛЬНО встречается) нашла вторую: у Норникеля/РНК
в `law.terms` лежало «Строящийся РНК комплекс позволит создать до 2,5 тыс.
рабочих мест.» — это тоже не юридическое условие, а экономический эффект
проекта.

Оба случая — правильный факт в неправильном поле, не выдумка и не новый
источник: текст переносится дословно, символ в символ, меняется только то,
под какой подписью он показывается.

- gdfa13cf0: `law.terms` -> `eco.rationale` (это ближе всего к «зачем купили
  / что планируют» — честный ответ «пока не решили», а не условие сделки).
  `law.terms` возвращается в прочерк — юридических условий сделки источник
  (короткая заметка РИА Недвижимость) не называет вовсе.
- g97e55758: `law.terms` -> `eco.target_fin` (масштаб/мощность строящегося
  предприятия — то же семейство, что уже там: производственная мощность
  500 000 т/год). `law.terms` — тоже в прочерк.

Запуск: python3 pipeline/fix_terms_field_misclassification.py
        python3 pipeline/fix_terms_field_misclassification.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = [
    dict(id='gdfa13cf0',
         old_field='terms', old_value=(
             '"Концепция развития площадки в настоящее время готовится", '
             '- уточнил представитель девелопера.'),
         new_field='rationale', new_value=(
             '"Концепция развития площадки в настоящее время готовится", '
             '- уточнил представитель девелопера.')),
    dict(id='g97e55758',
         old_field='terms', old_value=(
             'Строящийся РНК комплекс позволит создать до 2,5 тыс. рабочих мест.'),
         new_field='target_fin', new_value=(
             'Строящийся РНК комплекс позволит создать до 2,5 тыс. рабочих мест.')),
]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for fix in FIXES:
        card = by_id[fix['id']]
        assert card['law'][fix['old_field']] == fix['old_value'], \
            '%s: law.%s уже другое' % (fix['id'], fix['old_field'])
        assert card['eco'][fix['new_field']] == '—', \
            '%s: eco.%s уже не прочерк' % (fix['id'], fix['new_field'])
        print('ПЕРЕНОШУ  %s: law.%s -> eco.%s' % (fix['id'], fix['old_field'], fix['new_field']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for fix in FIXES:
        card = by_id[fix['id']]
        card['law'][fix['old_field']] = '—'
        card['eco'][fix['new_field']] = fix['new_value']
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: %d карточек.' % len(FIXES))


if __name__ == '__main__':
    main(write='--write' in sys.argv)
