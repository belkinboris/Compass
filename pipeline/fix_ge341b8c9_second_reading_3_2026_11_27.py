# -*- coding: utf-8 -*-
"""Второе чтение карточки ge341b8c9 («Эдисонэнерго», очередь pending.json),
27 ноября 2026, data/inbox/second_reading/2026-11-27-intake-edison-3.json.

ЧТО ЧИНИТ. В eco.context доли одних людей были записаны по-разному: во втором
абзаце «Печерский (28%), Тобак (8%)», в третьем — «с 28,05% до 43,05%». Теперь
точные доли, как в «Коммерсанте» от 02.11.2023 («Григорий Печерский (28,05%),
ООО «СКБ МБ» (15%) и бизнесмен Александр Тобак (7,95%)») и в ЕГРЮЛ. В первом
абзаце «Компания заплатила Москве…» читалось и про ADG — названо «Эдисонэнерго».
Через proofread.py не проходит: 7,95 — число, которого в старом тексте нет.

Запуск: python3 pipeline/fix_ge341b8c9_second_reading_3_2026_11_27.py [--write]
"""
import json
import os
import sys

PENDING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'static', 'data', 'pending.json')
ID = 'ge341b8c9'
REPL = [
    ('Григорий Печерский (28%), Александр Тобак (8%)',
     'Григорий Печерский (28,05%), Александр Тобак (7,95%)'),
    ('Печерских. Компания заплатила Москве', 'Печерских. «Эдисонэнерго» заплатило Москве'),
]


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))   # перечитываем прямо перед записью
    card = next(c for c in data['cards'] if c['id'] == ID)
    text = card['eco']['context']
    if all(new in text for _, new in REPL):
        print('Уже записано.')
        return
    for old, new in REPL:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    card['eco']['context'] = text
    print(text)
    if write:
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
