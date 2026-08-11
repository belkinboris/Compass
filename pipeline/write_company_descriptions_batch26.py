# -*- coding: utf-8 -*-
"""Двадцать шестая партия: 5 описаний + два дефекта данных, найденных при
подборе кандидатов (тот же приём, что и раньше — читать сделки КАЖДОГО
кандидата перед описанием, а не сочинять по названию).

ДЕФЕКТ 1. Профиль `g10f70324` носил имя «Лентой» — падежная форма («Лента»
в творительном падеже), протёкшая из заголовка сделки в поле имени.
Проверка: другого профиля «Лента» в базе нет, переименование безопасно.

ДЕФЕКТ 2 (серьёзнее). Профиль `gee31f8cf` «Парус» использовался как `target`
для ДВУХ РАЗНЫХ компаний одновременно:
  - сделка `g179841a1`: ООО «Парус» — Ярцевский металлургический завод,
    купленный ТМК у Romelior в 2020 году. У этого же завода уже ЕСТЬ
    отдельный, верный профиль `ga48620bb` «Ярцевский металлургический
    завод» — он используется как `target` в сделке `g9d09dc7c` (ТМК продала
    завод ООО «Фрунзе» в 2024–2025). То есть один и тот же физический
    актив ошибочно записан под двумя разными карточками компании;
  - сделка `g5013525f`: ООО «Парус электро» — производитель зарядных
    станций для электромобилей, 50% купил Росатом у Хлебникова и Павлюка
    в 2023 году. Другой бизнес, другие владельцы, другая отрасль.
Правило CLAUDE.md «стороной сделки может быть записан профиль совсем
другой сущности» (случай ЛСР/Domina) — здесь тот же класс, но чинится
проще: правильный профиль для завода уже существует, новый создавать не
нужно. Правка: `target` сделки `g179841a1` перенаправлен на `ga48620bb`;
профиль `gee31f8cf` остаётся под сделкой `g5013525f` — переименован в
«ООО «Парус электро»», отрасль исправлена с «ГМК и добыча» (унаследована
от завода) на «Автопром», добавлено описание.

ЧТО ДЕЛАЕТ. 5 описаний, 1 переименование (падеж), 1 разъединение профиля
(перенаправление target одной сделки + переименование/отрасль/описание
второго профиля).

Запуск:
    python3 pipeline/write_company_descriptions_batch26.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch26.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'g81045bed': 'Инвестиционный фонд Вагана Гаспаряна (экс-руководителя '
                 '«Сбербанк Капитала»), скупает сети кофеен и фудсервиса — '
                 '«Даблби», One & Double, «Салатерия».',
    'gfe4e2358': 'Инвестиционная структура дилерского холдинга «Авилон», '
                 'владеет бывшими российскими заводами Volkswagen и Hyundai.',
    'gfaf6ab0f': 'Сельскохозяйственное предприятие в Саратовской области; '
                 'до 2025 года принадлежало Павлу Артемову.',
    'ge8616484': 'Российский производитель автокомпонентов, выкупает '
                 'локализованные площадки ушедших из России иностранных '
                 'поставщиков — Grupo Antolin, Joyson Safety Systems.',
    'gce068d4f': 'Инвестор в складскую и коммерческую недвижимость, '
                 'выкупает объекты у иностранных владельцев, покидающих '
                 'российский рынок.',
    'gee31f8cf': 'Производитель зарядных станций для электромобилей; в '
                 '2023 году 50% выкупило АО «РАСУ» (Росатом).',
}

# id профиля -> (старое имя, новое имя). Только падежные/протёкшие формы,
# подтверждённые текстом собственных сделок.
NAME_FIXES = {
    'g10f70324': ('Лентой', 'Лента'),
    'gee31f8cf': ('Парус', 'ООО «Парус электро»'),
}

INDUSTRY_FIXES = {
    'gee31f8cf': ('ГМК и добыча', 'Автопром'),
}

# Перенаправление роли: сделка -> (поле, старый id, новый id). Тот же
# физический актив (Ярцевский завод) уже записан под правильным профилем.
TARGET_FIXES = {
    'g179841a1': ('target', 'gee31f8cf', 'ga48620bb'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals_by_id = {d['id']: d for d in data['deals']}

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:50]))
        c['desc'] = text
        wrote += 1

    for cid, (old_target, new_target) in {k: v[1:] for k, v in TARGET_FIXES.items()}.items():
        d = deals_by_id.get(cid)
        assert d, 'сделки %s нет в базе' % cid
        field = TARGET_FIXES[cid][0]
        assert d.get(field) == old_target, ('%s.%s уже другой: %r (ожидали %r)'
                                             % (cid, field, d.get(field), old_target))
        assert new_target in comps, 'профиля %s нет в базе' % new_target
        print('  ПЕРЕНАПРАВЛЕНИЕ %s.%s: %s -> %s' % (cid, field, old_target, new_target))
        d[field] = new_target

    name_fixed = 0
    for cid, (old_name, new_name) in NAME_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('name') == old_name, ('имя %s уже другое: %r (ожидали %r)'
                                            % (cid, c.get('name'), old_name))
        print('  ИМЯ      %-12s %r -> %r' % (cid, old_name, new_name))
        c['name'] = new_name
        name_fixed += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %s -> %s' % (cid, old_ind, new_ind))
        c['ind'] = new_ind
        ind_fixed += 1

    print('\nОписаний записано: %d' % wrote)
    print('Имён исправлено: %d' % name_fixed)
    print('Отраслей исправлено: %d' % ind_fixed)
    print('Ролей перенаправлено: %d' % len(TARGET_FIXES))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
