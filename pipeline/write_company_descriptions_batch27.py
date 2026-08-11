# -*- coding: utf-8 -*-
"""Двадцать седьмая партия: 8 описаний + разъединение профиля «Глобус»,
который держал две совершенно разные компании под одним id — тот же
класс дефекта, что «Парус» в прошлом прогоне (см.
`write_company_descriptions_batch26.py`).

ДЕФЕКТ. Профиль `gc0e607dc` «ЗАО «Глобус»» использовался как:
  - `buyer` в сделке `g8348fea5` — новосибирская ЗАО «Глобус» (владелец
    отеля Grand Autograph) выкупила у ВЭБ.РФ ТРК «Сибирский Молл» и
    бизнес-центр «Новая высота»;
  - `target` в сделке `g92f41a2d` — ГК «Рота» купила 45% в головной
    компании СОВЕРШЕННО ДРУГОЙ сети, московской «Глобус Гурмэ» (ООО
    «Сколково Парадайз»), у холдинга «Синдика».
Общее — только слово «Глобус» в разговорном названии; разные города,
разные отрасли (недвижимость/отель vs премиальный ритейл), разные
владельцы. В отличие от случая с «Парусом» (где верный профиль актива
уже существовал), готового профиля для «Глобус Гурмэ» в базе нет —
создан новый `gf51e23a8` (id — sha1 от названия юрлица, проверен на
отсутствие коллизии по id и по имени). `target` сделки `g92f41a2d`
перенаправлен на него; `gc0e607dc` остаётся при новосибирской сделке.

ЧТО ДЕЛАЕТ. 8 описаний (включая новый профиль), 1 перенаправление роли.

Запуск:
    python3 pipeline/write_company_descriptions_batch27.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch27.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

NEW_COMPANY_ID = 'gf51e23a8'
NEW_COMPANY = {
    'name': 'ООО «Сколково Парадайз» (сеть «Глобус Гурмэ»)',
    'ind': 'Ритейл',
    'desc': 'Головная компания сети премиальных супермаркетов «Глобус '
            'Гурмэ» в Москве; в 2022 году холдинг «Синдика» продал 45% '
            'ГК «Рота».',
    'kpi': ['Профиль', 'Автоматический'],
}

DESCRIPTIONS = {
    'g10f70324': 'Российская розничная сеть гипермаркетов и '
                 'супермаркетов, дочерняя компания «Севергрупп» Алексея '
                 'Мордашова.',
    'gc4c70e0f': 'Инвестиционная группа, вкладывается в гостиничные '
                 'активы — отели Baikal View на Байкале и «Азимут '
                 'Олимпик».',
    'ga0a4980a': 'Торговый комплекс в Санкт-Петербурге (91 000 кв. м); '
                 'несколько раз менял владельца — от Stockmann к PPF '
                 'Real Estate, затем к фирме «Аптекарский».',
    'g934fd312': 'Агрохолдинг группы Владимира Лисина (НЛМК), молочное '
                 'животноводство и растениеводство в Тверской области.',
    'g67e6a0e1': 'Головная структура Альфа-банка, инвестирует в '
                 'финтех-сервисы (Mozen, Kassir.ru).',
    'gf72c212b': 'Владелец торгово-развлекательных комплексов в '
                 'Санкт-Петербурге — «Владимирский пассаж», «Авеню», '
                 '«Космос».',
    'gc0e607dc': 'Новосибирская компания, владеет отелем Grand '
                 'Autograph; в 2022 году выкупила у ВЭБ.РФ ТРК '
                 '«Сибирский Молл» и бизнес-центр «Новая высота».',
}

# Перенаправление роли: сделка -> (поле, старый id, новый id).
TARGET_FIXES = {
    'g92f41a2d': ('target', 'gc0e607dc', NEW_COMPANY_ID),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals_by_id = {d['id']: d for d in data['deals']}

    assert NEW_COMPANY_ID not in comps, 'id %s уже занят' % NEW_COMPANY_ID
    for c in comps.values():
        assert c.get('name') != NEW_COMPANY['name'], 'имя нового профиля уже занято'
    print('  НОВЫЙ ПРОФИЛЬ %-12s %s' % (NEW_COMPANY_ID, NEW_COMPANY['name']))

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

    for cid, (field, old_target, new_target) in TARGET_FIXES.items():
        d = deals_by_id.get(cid)
        assert d, 'сделки %s нет в базе' % cid
        assert d.get(field) == old_target, ('%s.%s уже другой: %r (ожидали %r)'
                                             % (cid, field, d.get(field), old_target))
        print('  ПЕРЕНАПРАВЛЕНИЕ %s.%s: %s -> %s' % (cid, field, old_target, new_target))
        d[field] = new_target

    if not write:
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
        real += 1  # новый профиль, ещё не добавленный в comps в сухом прогоне
    else:
        comps[NEW_COMPANY_ID] = NEW_COMPANY
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))

    print('\nОписаний записано: %d (+1 новый профиль)' % wrote)
    print('Ролей перенаправлено: %d' % len(TARGET_FIXES))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    total = len(comps) + (0 if write else 1)
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, total, round(100 * real / total)))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
