# -*- coding: utf-8 -*-
"""Двадцать третья партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двадцати двух партий настоящее описание есть у 605
профилей из 1855 (33%). Кандидатов искали по числу связанных сделок
среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).
«Группа «ВИС»» уже встречалась в этой роли раньше (партия 4, слияние
падежных близнецов) — описание тогда не проставили, хотя профиль-
выживший уже был выбран; закрыто сейчас.

Отдельная находка: у «Каппа РУС» (`gbf2a776d`) стояла отрасль «Пищепром
и напитки» — и у самого профиля, и у ЕДИНСТВЕННОЙ сделки в базе
(покупка Окуловской бумажной фабрики). Каппа РУС — производитель
гофроупаковки, а не пищевая компания; сама Окуловская бумажная фабрика
уже была исправлена на «Лесопром» в прогоне про падежных близнецов, а
покупатель остался с прежней неверной меткой. Верная категория —
«Производство тары» (CLAUDE.md: граница по продукту — производит саму
упаковку, значит тара, а не сырьё для неё).

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 4 профилям, исправляет
отрасль у 1.

Запуск:
    python3 pipeline/write_company_descriptions_batch23.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch23.py --write    # записать
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
    'g40ce292b': 'Российский инфраструктурный холдинг: концессии в '
                 'дорожном строительстве и портах.',
    'ge2421e48': 'Российский проектный институт: разработка метро и '
                 'транспортной инфраструктуры.',
    'gd5658152': 'Один из крупнейших в России производителей '
                 'свинины.',
    'gbf2a776d': 'Российский производитель гофроупаковки.',
}

# Профиль, отрасль которого унаследована от неверной старой метки
# предмета его сделки (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {
    'gbf2a776d': ('Пищепром и напитки', 'Производство тары'),
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
        print('  %-12s %-24s %s' % (cid, str(c.get('name'))[:24], text[:56]))
        c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %-24s %s -> %s'
              % (cid, str(c.get('name'))[:24], old_ind, new_ind))
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
