# -*- coding: utf-8 -*-
"""У карточки `gad807a24` («PVH Corp. продала российскую розницу Calvin
Klein и Tommy Hilfiger Денису Щукину») `date` стоял «2022-06-15» — этой
даты нет ни в одном источнике. Независимая проверка живым поиском (РБК,
«Коммерсантъ», Forbes, Lenta.ru, TAdviser) единогласно подтверждает: PVH
лишь ПРИОСТАНОВИЛА работу в России в марте 2022 года, а саму продажу
розницы Денису Щукину (переименование в ООО «Ритэйл Экселенс») закрыла
только «в середине августа» 2023 года — «Американская PVH в середине
августа вышла из капитала российского подразделения... Новым владельцем и
гендиректором компании стал Денис Щукин», сообщает «Коммерсантъ»
(kommersant.ru/doc/6211345, публикация 13.09.2023). Точного дня источники
не называют («середина августа»), поэтому в дату идёт только год —
тот же принцип, что и у заглушек-плейсхолдеров в `fix_placeholder_dates.py`
(нельзя утверждать точный день, которого источник не называет).

Почему не через review.py: `date_is_supported()` разрешает уточнять день
только ВНУТРИ уже известного года — перенос в другой год сознательно не
поддержан (см. прецедент `fix_osnova_sviblovo_date.py`), да и цитаты в
кэше притока для этой правки нет — источник живого поиска, не кэш.

Запуск: python3 pipeline/fix_pvh_shchukin_date.py
        python3 pipeline/fix_pvh_shchukin_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gad807a24'
OLD_DATE = '2022-06-15'
NEW_DATE = '2023'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == OLD_DATE, '%s: дата уже другая' % CARD_ID
    print('ПРАВИМ  %s date: «%s» -> «%s»' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
