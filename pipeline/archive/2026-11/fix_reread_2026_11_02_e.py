# -*- coding: utf-8 -*-
"""Вычитка базы, партия «e» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_e.py.

Дата-год: `review.py` принимает в `date` только «ГГГГ-ММ-ДД», а правило
(docs/card_status_dates.md, «Нет дня — только год») требует года, когда день
события источник не называет.

- g072d8c14 (Совкомбанк/«Группа Астра», репо): «2025-11-01» — выдуманный
  день: сообщение в раскрытии вышло около 17–18 ноября 2025 года
  (Коммерсантъ 18.11.2025, TAdviser: «18 ноября 2025 года стало известно»),
  день перехода акций по репо не назван → «2025».
- gd2196acd (Совкомбанк/«Рокет»): «2024-11-15» — день публикации
  Коммерсанта («Как стало известно “Ъ”», 15.11.2024), а не день сделки;
  день закрытия источники не называют → «2024» (находка date_unbased).

Профиль предмета gd2196acd (`gc5c47fde`): имя «финтех-платформа «Рокет»» —
описание с именем внутри (READING_BRIEF.md, «Пересказ заголовка — не имя»),
и пост читался «Предмет: финтех-платформа «Рокет» — финтех-платформа (…)».
Переименование на месте (docs/company_profiles.md: у профиля одна сделка,
близнеца по именам и описаниям нет; мертвый псевдоним «финтех-платформа рокет» → «рокетбанк») — «Рокет»,
как платформу называет Коммерсантъ 15.11.2024; описание — «кто это» первой
фразой: необанк без своей лицензии (Википедия: «финтех-сервис, необанк. Не
имеет собственной лицензии»), работает на лицензии Совкомбанка (E1.RU,
пресс-служба: «"Рокет" работает на его лицензии»).

Синхронизация записи FIXES (docs/card_editing.md, «Правка поля мимо таблицы
синхронизирует запись»): у gd2196acd в архиве правок (fixes_archive/2026-10.json)
есть примененная запись eco.sum «Не раскрыта» → «$1 млн»; партия e ставит
«$1 млн (по оценке)» (как в sum), и отпечаток прежнего new уходит в
`proofread_absorbed['eco.sum']`, иначе архивную запись сочтут непримененной.
Для прозы это делает сам review.py (`prose_gate.absorb_earlier`), для eco.sum — нет.

Этапов `events[]` у обеих карточек нет — менять больше нечего; после записи —
`python3 pipeline/facts_derive.py --write` (факт `date` пересчитается).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_e.py          # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_e.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

CHANGES = [
    ('g072d8c14', 'date', '2025-11-01', '2025'),
    ('gd2196acd', 'date', '2024-11-15', '2024'),
]


PROFILE = ('gc5c47fde',
           'финтех-платформа «Рокет»', 'Рокет',
           'Финтех-платформа (бывший Рокетбанк, ранее принадлежала группе Qiwi); в 2024 году бренд и команду '
           'купил Совкомбанк.',
           'Российский необанк без собственной банковской лицензии, прежнее имя — Рокетбанк. Работает через '
           'приложение и курьеров, без отделений; с 2025 года — на лицензии Совкомбанка.')


def main(argv):
    write = '--write' in argv
    raw = open(BASE, encoding='utf-8').read()                 # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    for cid, field, old, new in CHANGES:
        card = deals[cid]
        assert card.get(field) == old, (cid, field, card.get(field), old)
        assert not card.get('events'), (cid, 'есть этапы — проверьте их даты руками')
        card[field] = new
        print('%s %s: %r -> %r' % (cid, field, old, new))
    c = deals['gd2196acd']
    assert c['eco'].get('sum') in ('$1 млн', '$1 млн (по оценке)'), c['eco'].get('sum')
    marks = c.setdefault('proofread_absorbed', {}).setdefault('eco.sum', [])
    fp = review.fix_fingerprint('$1 млн')
    if fp not in marks:
        marks.append(fp)
    print('gd2196acd proofread_absorbed[eco.sum] += %s' % fp)
    cid, old_name, new_name, old_desc, new_desc = PROFILE
    prof = data['companies'][cid]
    assert prof.get('name') == old_name and prof.get('desc') == old_desc, (cid, prof.get('name'), prof.get('desc'))
    # Псевдоним, равный старому имени, мертв (docs/company_profiles.md, «Псевдоним после
    # переименования») — заменяется брендом «рокетбанк»: в заголовках базы он только у этой
    # карточки (новый заголовок «…команду Рокетбанка»).
    assert data['match_keys'].get(cid) == ['финтех-платформа рокет'], data['match_keys'].get(cid)
    data['match_keys'][cid] = ['рокетбанк']
    prof['name'], prof['desc'] = new_name, new_desc
    print('%s name: %r -> %r; desc переписан' % (cid, old_name, new_name))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    with open(BASE, 'w', encoding='utf-8') as f:
        f.write(out)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
