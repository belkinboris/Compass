# -*- coding: utf-8 -*-
"""Двадцать вторая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двадцати одной партии настоящее описание есть у 600
профилей из 1855 (32%). Кандидатов искали по числу связанных сделок
среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

Отдельная находка: у IHC (`gba03a733`, Абу-Даби) стояла отрасль «Нефть
и газ» — унаследована от ЕДИНСТВЕННОЙ сделки в базе (интерес к покупке
зарубежных активов ЛУКОЙЛа), а не от рода занятий самой компании. IHC —
диверсифицированный конгломерат (недвижимость, финансы, здравоохранение,
энергетика и другое), а не нефтегазовая компания — интерес к активам
ЛУКОЙЛа для неё частный случай, а не основной бизнес. Тот же класс
дефекта, что «Сбербанк значился „Медиа"». Исправлено на «Холдинги».

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 5 профилям, исправляет
отрасль у 1.

Запуск:
    python3 pipeline/write_company_descriptions_batch22.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch22.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id профиля -> описание. Только компании, чей род занятий общеизвестен и
# подтверждён текстом собственной сделки в базе.
DESCRIPTIONS = {
    'gb7a1b8d6': 'Российская энергетическая компания, дивизион '
                 'госкорпорации «Росатом»; контролирует ПАО «Квадра».',
    'gb6e333d0': 'Челябинская промышленная группа: производство труб '
                 'и энергетического оборудования.',
    'gd6c3c0ff': 'Российский инвестиционный холдинг; в 2023 году '
                 'контроль перешёл от Романа Авдеева к Сергею '
                 'Сударикову.',
    'gc2c803f9': 'Российский сервис онлайн-психотерапии.',
    'gba03a733': 'Диверсифицированный инвестиционный конгломерат из '
                 'Абу-Даби, возглавляется шейхом Тахнуном бен Заидом.',
}

# Профиль, отрасль которого унаследована от единственной сделки, а не от
# рода занятий самой компании (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {
    'gba03a733': ('Нефть и газ', 'Холдинги'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

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
        print('  %-12s %-30s %s' % (cid, str(c.get('name'))[:30], text[:56]))
        c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %-30s %s -> %s'
              % (cid, str(c.get('name'))[:30], old_ind, new_ind))
        c['ind'] = new_ind
        ind_fixed += 1

    print('\nОписаний записано: %d' % wrote)
    print('Отраслей исправлено: %d' % ind_fixed)
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
