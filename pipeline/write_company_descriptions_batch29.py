# -*- coding: utf-8 -*-
"""Двадцать девятая партия: 8 описаний + профиль «ТД «Северный»» держал
угольную шахту в Кузбассе — тот же класс дефекта, что «Парус» и
«Глобус» в прошлых прогонах: общее только слово в разговорном имени.

ДЕФЕКТ. Профиль `ga00a9984` «ТД «Северный»» (дистрибутор продуктов
питания, развивает птицеводство — купил птицефабрику «Кинешемская»,
сделка `g7ce0250d`, роль верна) использовался ЕЩЁ и как `target` в
сделке `g1a58d740` — «Группа «Талтэк» продаёт АО «Угольная компания
«Северный Кузбасс»» предпринимателю Станиславу Лупию». Это угольная
шахта в Кузбассе, никак не связанная с продуктовым дистрибутором;
общее — только слово «Северный». Профиля для угольного актива в базе
не было — создан новый (`gac6217b4`, id и имя проверены на отсутствие
коллизии), `target` сделки `g1a58d740` перенаправлен на него.

ЧТО ДЕЛАЕТ. 8 описаний, 1 новый профиль, 1 перенаправление роли.

Запуск:
    python3 pipeline/write_company_descriptions_batch29.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch29.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

NEW_COMPANY_ID = 'gac6217b4'
NEW_COMPANY = {
    'name': 'АО «Угольная компания «Северный Кузбасс»»',
    'ind': 'Уголь',
    'desc': 'Угольный актив в Кузбассе — две шахты, углеобогатительная '
            'фабрика, погрузочно-транспортное управление; входил в '
            'портфель группы «Талтэк».',
    'kpi': ['Профиль', 'Автоматический'],
}

DESCRIPTIONS = {
    'ge438bc54': 'Компания семьи основателя ритейлера «Мария-Ра» '
                 'Александра Ракшина; скупает бывшие офисные здания '
                 '«Ростелекома» и «Сбербанка» в центре Москвы.',
    'g95fe3191': 'Российская лизинговая компания, последний актив '
                 'Société Générale в стране; в 2023 году продана '
                 'структурам Игоря Кима, владельца Экспобанка.',
    'g8fdefffc': 'Инвестиционное подразделение ГК «Ультиматек», '
                 'вкладывается в разработчиков корпоративного ПО — '
                 'CPM-платформы, системы цифровизации промышленности.',
    'g6c733a7f': 'Производитель спортивного питания и фитнес-продуктов '
                 '(бренд Jump), скупает смежные производства — например, '
                 'этикеточную фабрику «Лейблпак».',
    'g283b8f4b': 'Агрохолдинг, развивает тепличные комплексы — '
                 'приобрёл долю в «Агрокультура Групп», планировал '
                 'выкуп теплиц в Орловской области.',
    'g6f4bb996': 'Владелец логистического склада на Липкинском шоссе в '
                 'Московской области (82 142 кв. м); в 2023 году '
                 'выкуплен «Сбербанк Инвестициями».',
    'g474b6e6c': 'Сервис электронной регистрации сделок с недвижимостью '
                 '(ООО «Практика Успеха»); в 2023 году выкуплен Циан.',
    'g1209e3c2': 'Инвестиционная структура «ВымпелКома»; вложилась в '
                 'разработчика технологий автономной торговли Briskly и '
                 'платформу умного дома T.one.',
}

# Перенаправление роли: сделка -> (поле, старый id, новый id).
TARGET_FIXES = {
    'g1a58d740': ('target', 'ga00a9984', NEW_COMPANY_ID),
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
        real += 1
        total = len(comps) + 1
    else:
        comps[NEW_COMPANY_ID] = NEW_COMPANY
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
        total = len(comps)

    print('\nОписаний записано: %d (+1 новый профиль)' % wrote)
    print('Ролей перенаправлено: %d' % len(TARGET_FIXES))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

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
