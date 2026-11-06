"""Описание профиля «Циан» (g163cfc8b) без второго тире (6 ноября 2026).

Второе чтение карточки g637fe00a: строка поста «Предмет» читалась как «Циан — интернет-сервис
объявлений о недвижимости — аренда и продажа…» — два тире подряд, описание склеивалось с долей.
Смысл описания не меняется, меняется только построение фразы.
Запуск: python3 pipeline/archive/2026-11/fix_cian_profile_desc_2026_11_06.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = 'Интернет-сервис объявлений о недвижимости — аренда и продажа жилой и коммерческой недвижимости. Юрлицо — МКПАО «Циан».'
NEW = 'Интернет-сервис объявлений о продаже и аренде жилой и коммерческой недвижимости. Юрлицо — МКПАО «Циан».'
d = json.load(open(P, encoding='utf-8'))  # перечитано прямо перед записью
c = d['companies']['g163cfc8b']
if c['desc'] == NEW:
    print('Уже исправлено.'); sys.exit(0)
assert c['desc'] == OLD, c['desc']
c['desc'] = NEW
print('g163cfc8b desc ->', NEW)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(P, 'a').write('\n'); print('Записано.')
