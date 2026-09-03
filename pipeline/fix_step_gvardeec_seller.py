# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `g57ec9504`
(«Агрохолдинг Степь выкупил 26 тыс. га земель в Ставропольском крае»,
закрыта 14.04.2023) — продавец не был назван (поля `seller` не было в
записи), хотя `eco.context` этой же карточки уже год как намекает на
предыдущие обменные сделки со «Степью» тем же контрагентом.

Проверено лично прямым WebFetch, Коммерсантъ,
https://www.kommersant.ru/doc/5939827, 17.04.2023, 19:00: «До этого
предприятием владело местное ООО «АПК "Возрождение"»» — тот же
контрагент, что уже назван в `eco.context` карточки по прошлым сделкам
2020 года.

НЕ ВНЕСЕНО: точный ИНН юрлица продавца — под именем «АПК "Возрождение"»
в реестрах встречается несколько юрлиц (Ставрополь), источник называет
его только «местное», без уточняющих реквизитов; связывать `seller_id`
с конкретным профилем компании без прямой сверки по ЕГРЮЛ не стал.
Согласование ФАС и структура сделки — ни один источник не упоминает.
Более широкая программа консолидации земель «Степью» (сделки
«Сергиевское»/«Хуторок», июль 2023, и полный выкуп «РЗ Агро», март
2025) — упомянута только агрегатором (Wikipedia), не проверена лично
дословной цитатой первоисточника, и это, судя по всему, ОТДЕЛЬНЫЕ
сделки без своих карточек в базе — задача для притока/будущего
дочитывания, не для этой правки.

Запуск: python3 pipeline/fix_step_gvardeec_seller.py
        python3 pipeline/fix_step_gvardeec_seller.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g57ec9504'

NEW_SELLER = 'АПК «Возрождение»'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert 'seller' not in deal or deal.get('seller') is None

    print('=== seller: станет ===')
    print(NEW_SELLER)

    if write:
        deal['seller'] = NEW_SELLER
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
