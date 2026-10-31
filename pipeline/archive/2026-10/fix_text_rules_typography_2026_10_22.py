# -*- coding: utf-8 -*-
"""Качество 22 октября 2026, шаг 6 (новый): `pipeline/text_rules.py` нашел
8 старых опечаток чистой типографики — дефис вместо тире, несбалансированные
кавычки (лишнее «« без парной »» у вложенных названий; «„ “»-пара, набранная
как «“ ”»). Факты не меняются, цитата не нужна — правится прямым скриптом
(как `fix_straight_quotes.py` и другие такие же разовые чистки), с `assert`
на старое значение, файл перечитан прямо перед записью.

    python3 pipeline/fix_text_rules_typography_2026_10_22.py          # сухой прогон
    python3 pipeline/fix_text_rules_typography_2026_10_22.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')

FIXES = [
    ('g88304d3a', 'eco.rationale',
     '«Инвестиции в медтех - одни из самых важных',
     '«Инвестиции в медтех — одни из самых важных'),
    ('g995f83cf', 'eco.share',
     '«Ренессанс Капитал - ФК»',
     '«Ренессанс Капитал — ФК»'),
    ('g076a2f4e', 'law.struct',
     'ООО «Специализированный Застройщик «Буран»',
     'ООО Специализированный Застройщик «Буран»'),
    ('g076a2f4e', 'law.struct', '«СЗ «Катерная»', 'СЗ «Катерная»'),
    ('g076a2f4e', 'law.struct', '«СЗ «Тухачевского,80»', 'СЗ «Тухачевского,80»'),
    ('g076a2f4e', 'law.struct', '«СЗ «Регион»', 'СЗ «Регион»'),
    ('g076a2f4e', 'law.struct', '«СЗ «Дом на Бульваре»', 'СЗ «Дом на Бульваре»'),
    ('g076a2f4e', 'law.struct', 'ООО «СЗ «Фронтон»', 'ООО СЗ «Фронтон»'),
    ('ga9be07b2', 'eco.context', '«Агрополис «Сабурово»', '«Агрополис „Сабурово“»'),
    ('ektos', 'extra', 'ООО «УК «ЭКТОС Менеджмент»', 'ООО УК «ЭКТОС Менеджмент»'),
    ('c51d0bb64', 'events.0.note', '( допэмиссия - ИФ )', '( допэмиссия — ИФ )'),
    ('c51d0bb64', 'events.0.note', 'будет", - сказал', 'будет", — сказал'),
    ('g9edfa8d8', 'events.0.note', '“Ъ”', '„Ъ“'),
    ('g6264541d', 'events.0.note', '“Ъ”', '„Ъ“'),
]


def get_set(card, field):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    return obj, parts[-1]


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    by_id = {d['id']: d for d in data['deals']}
    for did, field, frag_old, frag_new in FIXES:
        obj, key = get_set(by_id[did], field)
        current = obj[key]
        assert frag_old in current, (did, field, frag_old, current)
        obj[key] = current.replace(frag_old, frag_new)
        print('%s %s: %r -> %r' % (did, field, frag_old, frag_new))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
