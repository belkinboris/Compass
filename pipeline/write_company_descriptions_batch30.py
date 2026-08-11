# -*- coding: utf-8 -*-
"""Тридцатая партия: 8 описаний + профиль «Pre-seed» держал две разные
компании — не однофамильцы, а вообще НЕ имя: «Pre-seed» — это стадия
раунда финансирования, а не название стороны сделки. Родня уже
записанного класса «Парус»/«Глобус»/«Северный» (общее слово скрывает
две сущности), но здесь общее — не разговорное имя компании, а сам
факт, что разбор принял ярлык стадии инвестиции за имя цели.

ДЕФЕКТ. Профиль `g5dcbd18b` «Pre-seed» использовался как `target` в
ДВУХ разных сделках: `g26b16b4b` (игровая студия KEK Entertainment,
$3 млн от The Games Fund и Play Ventures) и `g84432523` (EdTech-стартап
StudyFree, $600 тыс. во главе с Acrobator VC). Оба заголовка начинаются
со слова «Pre-seed» — стадии раунда, а не имени компании; разбор,
видимо, взял первое слово заголовка. Профилей для этих стартапов в базе
не было — заведены два новых (id и имена проверены на отсутствие
коллизии), `target` обеих сделок перенаправлен.

ЧТО ДЕЛАЕТ. 8 описаний, 2 новых профиля, 2 перенаправления роли.

Запуск:
    python3 pipeline/write_company_descriptions_batch30.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch30.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

NEW_COMPANIES = {
    'g661cd7ce': {
        'name': 'KEK Entertainment',
        'ind': 'ИТ и интернет',
        'desc': 'Игровая студия, основана в сентябре 2021 года бывшими '
                'топ-менеджерами Pixonic (создатели War Robots) — '
                'Георгием Егоровым и Олегом Порошиным.',
        'kpi': ['Профиль', 'Автоматический'],
    },
    'g2d8dbb5d': {
        'name': 'StudyFree',
        'ind': 'Образование',
        'desc': 'EdTech-стартап; pre-seed раунд возглавил нидерландский '
                'фонд Acrobator VC при участии акселераторов Techstars '
                'и Berkeley SkyDeck.',
        'kpi': ['Профиль', 'Автоматический'],
    },
}

DESCRIPTIONS = {
    'gfd9eea5c': 'Разработчик ПО для анализа эмоций по видео (Sense '
                 'Machine); среди инвесторов — фонд «Восход» и '
                 'венчурная структура «Билайна», фонд «Хайв».',
    'ge8c9b2bc': 'Ульяновский девелопер; в 2023 году контроль полностью '
                 'перешёл к Артёму Чайке, выкупившему доли у партнёров.',
    'g7ad3dcb0': 'Оператор сотовой связи в Армении (2 млн абонентов) с '
                 'платёжной системой МобиДрам; в 2023 году МТС продала '
                 '80% акций компании Fedilco Group.',
    'g68204914': 'Крупнейший франчайзи KFC (Rostic\'s) в России; '
                 'выкупил долю в «Юниресте» у структуры Константина '
                 'Котова и Андрея Осколкова.',
    'g527da4e8': 'Скупает в России заводы ушедших автопроизводителей — '
                 'предприятия Schaeffler и Benteler; гендиректор обеих '
                 'компаний Александр Горлов.',
    'g389d0bbb': 'Структура, связанная с мажоритарным акционером '
                 'ВСМПО-Ависма; скупает активы ушедших иностранных '
                 'производителей — завод Arconic, завод Volvo в Калуге.',
    'g3104e805': 'Компания Константина Котова и Андрея Осколкова; '
                 'выкупила у AmRest и Yum! Brands российский бизнес '
                 'KFC — 215 и 70 ресторанов соответственно.',
    'g069c7294': 'Кредитный брокер, специализируется на '
                 'POS-кредитовании; в 2021 году продан холдингом СФИ '
                 'компании «М.Видео-Эльдорадо».',
}

# Перенаправление роли: сделка -> (поле, старый id, новый id).
TARGET_FIXES = {
    'g26b16b4b': ('target', 'g5dcbd18b', 'g661cd7ce'),
    'g84432523': ('target', 'g5dcbd18b', 'g2d8dbb5d'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals_by_id = {d['id']: d for d in data['deals']}

    for new_id, new_c in NEW_COMPANIES.items():
        assert new_id not in comps, 'id %s уже занят' % new_id
        for c in comps.values():
            assert c.get('name') != new_c['name'], 'имя %r уже занято' % new_c['name']
        print('  НОВЫЙ ПРОФИЛЬ %-12s %s' % (new_id, new_c['name']))

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
        real += len(NEW_COMPANIES)
        total = len(comps) + len(NEW_COMPANIES)
    else:
        for new_id, new_c in NEW_COMPANIES.items():
            comps[new_id] = new_c
        real = sum(1 for v in comps.values()
                   if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
        total = len(comps)

    print('\nОписаний записано: %d (+%d новых профиля)' % (wrote, len(NEW_COMPANIES)))
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
