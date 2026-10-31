# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g8ea21d1b` («СИБУР выкупает 50% долю Solvay в совместном предприятии
«РусВинил»», март 2023, Закрыта) — что случилось с управлением
предприятием сразу после выкупа не было отражено.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/business/892787 (УЖЕ был в `src` карточки, использован
  только для факта об одобрении президента, но не для этого):
  «Генеральным директором ООО "РусВинил" назначен гендиректор
  "СИБУР-Кстово" Сергей Назаров» 24 марта 2023 года — «вместе с
  закрытием сделки по продаже группой Solvay своей доли»; прежний
  гендиректор, Марк Лааль (представитель Solvay), возглавлял компанию
  «с декабря 2021 года по март 2023 года».

НЕ ВНЕСЕНО: сообщение о статусе «В процессе реорганизации» у ООО
«РусВинил» по состоянию на август 2026 года — встретилось только в
агрегированной выдаче поиска (rusprofile.ru/zachestnyibiznes.ru), обе
попытки прямого чтения страниц реестра отдали 403; сумма сделки
уточнена и совпала с уже стоящей в карточке (€430 млн), расхождение с
другим упоминанием (€433 млн) в сторонних источниках не проверялось.

Запуск: python3 pipeline/fix_rusvinil_new_ceo_after_solvay_exit.py
        python3 pipeline/fix_rusvinil_new_ceo_after_solvay_exit.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8ea21d1b'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Вместе с закрытием сделки, 24 марта 2023 года, СИБУР сменил '
    'руководство «РусВинила»: гендиректором назначен Сергей Назаров, '
    'ранее возглавлявший «СИБУР-Кстово», вместо Марка Лааля — '
    'представителя Solvay, руководившего предприятием с декабря 2021 '
    'года.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
