# -*- coding: utf-8 -*-
"""У карточки `g420cae8d` («Приобретение 100% «Авито» компанией Kismet
Capital Group у Naspers (Prosus)») в `law.adv` — две строки об ОДНОМ и том
же факте (Denuo сопровождала Kismet Capital Group по регуляторным
разрешениям ФАС и правкомиссии): первая — развёрнутая и правильно
оформленная, вторая — испорченный дубль с перепутанными колонками
(«роль» несёт текст описания вместо роли, оба текстовых поля обрываются на
незакрытой скобке). Дубль ничего не добавляет к уже сказанному в первой
строке — только шум и визуальный дефект (незакрытые скобки на экране).

Почему не через review.py: снимается не новый факт, а уже присутствующий в
базе испорченный повтор — резать безопасно, вторая строка не несёт ничего,
чего нет в первой.

Запуск: python3 pipeline/fix_avito_kismet_duplicate_advisor_row.py
        python3 pipeline/fix_avito_kismet_duplicate_advisor_row.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g420cae8d'
GARBLED_ROW = [
    'Kismet capital group: получение регуляторных одобрений фас и правкомиссии)',
    'Denuo Legal (сторона покупателя',
    'Источник: обогащение/веб-поиск',
]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    adv = card['law']['adv']
    if GARBLED_ROW not in adv:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert len(adv) == 2, '%s: ожидалось 2 строки law.adv, найдено %d' % (CARD_ID, len(adv))
    print('ПРАВИМ  %s law.adv: снят испорченный дубль строки про Denuo' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    adv.remove(GARBLED_ROW)
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
