# -*- coding: utf-8 -*-
"""Раунд 9, партия 5 агентов, 15 августа 2026 — три правки, всплывшие после
записи и полного pytest:

1) Капитализация четырёх law.*-полей, где извлечённая цитата начиналась со
   строчной буквы (g5bb3e777 law.struct, g82c59e72 law.terms, ge51361bd
   law.struct, gadbed4b9 law.terms) — правится только формулировка, не факт,
   тот же приём, что в раундах 5-8.

2) g221e4969 (Bonum Capital/«Паскаль медикал»): `buyer_name` добавлен зря —
   `buyer` УЖЕ указывал на профиль «Максим Сарманов» (g46a02673), то же
   лицо, что источник называет текстом. `test_buyer_is_named_once` не
   пропускает две записи одной роли; правильно снять текстовую дублирующую
   запись, раз профиль уже есть, а не наоборот.

3) g3e7bc840 (Russ Outdoor/Gallery): `seller` = «ООО «Медиа-1 Аутдор»»
   отклонён `test_asset_is_not_a_party` — и находка честная: поле `target`
   у этой карточки уже указывает на профиль, ФАКТИЧЕСКИ названный «ООО
   «Медиа-1 Аутдор»» (заголовок карточки сам отождествляет Gallery с этим
   ООО), хотя источник (interfax.ru/amp/909583) прямо говорит, что «Медиа-1
   Аутдор» — холдинг ПРОДАВЦА, а реальный актив — отдельное юрлицо «ООО
   "Гэллэри Сервис"», для которого в базе нет профиля. Это тот же класс, что
   уже описан в CLAUDE.md («Стороной сделки бывает записан её предмет» /
   профиль совсем другой сущности) — чинить подменой одной ссылки без
   создания верного профиля для «Гэллэри Сервис» нельзя, это отдельная
   задача. До неё честнее снять `seller`, чем оставить два поля,
   указывающих на одну и ту же (неверно связанную) сущность.

ЗАПУСК:
    python3 pipeline/fix_r9_capitalize_and_reverts.py            # сухой прогон
    python3 pipeline/fix_r9_capitalize_and_reverts.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CAPITALIZE = [
    ('g5bb3e777', 'law', 'struct'),
    ('g82c59e72', 'law', 'terms'),
    ('ge51361bd', 'law', 'struct'),
    ('gadbed4b9', 'law', 'terms'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, section, field in CAPITALIZE:
        val = by_id[cid][section][field]
        assert val and val[0].islower(), '%s.%s.%s уже с заглавной: %r' % (cid, section, field, val)
        print('ПРАВИМ %s.%s.%s: %r -> %r' % (cid, section, field, val[:40], (val[0].upper() + val[1:])[:40]))

    d1 = by_id['g221e4969']
    assert d1.get('buyer') == 'g46a02673', 'g221e4969: buyer уже другой: %r' % d1.get('buyer')
    assert d1.get('buyer_name') == 'Максим Сарманов', \
        'g221e4969: buyer_name уже другой: %r' % d1.get('buyer_name')
    print('ПРАВИМ g221e4969.buyer_name: убираем (дублирует уже стоящий buyer=g46a02673)')

    d2 = by_id['g3e7bc840']
    assert d2.get('seller') == 'ООО «Медиа-1 Аутдор»', \
        'g3e7bc840: seller уже другой: %r' % d2.get('seller')
    print('ПРАВИМ g3e7bc840.seller: убираем (совпадает с профилем target — '
          'испорченная ссылка, отдельная задача)')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, section, field in CAPITALIZE:
        val = by_id[cid][section][field]
        by_id[cid][section][field] = val[0].upper() + val[1:]

    d1['buyer_name'] = None
    d2['seller'] = None

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
