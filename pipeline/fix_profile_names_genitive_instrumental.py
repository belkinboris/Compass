# -*- coding: utf-8 -*-
"""Три профиля компаний испорчены при разборе заголовка — дефект того же
класса, что уже описан в CLAUDE.md для сторон сделки, только здесь испорчено
каноническое ИМЯ ПРОФИЛЯ, а не разовое поле карточки:

- g05adc740 «Башнефти» (родительный) -> «Башнефть». Нашлось при дочитывании
  gf6232eec (Башкирия продала пакет акций «Башнефти» «Роснефти»): в тексте
  самой карточки родительный падеж уместен («акций «Башнефти»»), а вот имя
  профиля обязано быть в именительном.
- g3daf2d35 «Группой УКМ» (творительный) -> «Группа УКМ». Нашлось при
  дочитывании gecce5162 («Приобретение «Группой УКМ» Никиты Мазепина 20%…») —
  разбор заголовка взял падеж из глагольного управления и не привёл к
  начальной форме.
- g83d157e5 «ООО Центр фармацевтической упаковки (объект приобретения)» ->
  «ООО «Центр фармацевтической упаковки»». Нашлось при дочитывании g53bd1536:
  служебная пометка роли в сделке («объект приобретения») просочилась прямо в
  имя профиля — родня уже записанного урока «Имя компании — не место для
  доли», только протёкшее слово не доля, а роль.

У всех трёх профилей ровно по одной ссылающейся сделке (проверено прогоном
без записи), риск задеть чужие карточки — нулевой.

Запуск: python3 pipeline/fix_bashneft_profile_name.py           # проверка
        python3 pipeline/fix_bashneft_profile_name.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

RENAMES = {
    'g05adc740': ('Башнефти', 'Башнефть'),
    'g3daf2d35': ('Группой УКМ', 'Группа УКМ'),
    'g83d157e5': ('ООО Центр фармацевтической упаковки (объект приобретения)',
                  'ООО «Центр фармацевтической упаковки»'),
}


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    for company_id, (old_name, new_name) in RENAMES.items():
        company = data['companies'].get(company_id)
        assert company is not None, 'профиля %s больше нет' % company_id
        assert company['name'] == old_name, 'имя уже другое: %r' % company['name']
        print('ПРАВИМ  %s: %r -> %r' % (company_id, old_name, new_name))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for company_id, (_old_name, new_name) in RENAMES.items():
        data['companies'][company_id]['name'] = new_name
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
