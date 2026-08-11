# -*- coding: utf-8 -*-
"""Двадцать пятая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двадцати четырёх партий настоящее описание есть у
616 профилей из 1855 (33%). Кандидатов искали по числу связанных сделок
среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

Отдельная находка: у покупателя в сделке `gd1f94881` («Продажа United
Panel Group экс-депутату Александру Салаеву») стояло имя ООО «Универсам
«Диана»» — покупатель назван верно (сама сделка это подтверждает: «Покупателем
стало ООО «Универсам «Диана»» экс-депутата... Александра Салаева»), но
у профиля этой инвестиционной структуры Салаева стояла отрасль
«Лесопром» — очевидно унаследованная от ЦЕЛИ сделки (фанерный комбинат
United Panel Group), а не от рода занятий самого покупателя. Тот же
класс дефекта, что у «Каппа РУС» и «Готэк» в прошлых прогонах.
Исправлено на «Холдинги».

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 5 профилям, исправляет
отрасль у 1.

Запуск:
    python3 pipeline/write_company_descriptions_batch25.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch25.py --write    # записать
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
    'gd045ee29': 'Российский производитель фанеры, основной актив — '
                 'Жешартский фанерный комбинат в Республике Коми.',
    'g466479df': 'Ковровский механический завод — российское '
                 'промышленное предприятие; в 2025 году доля ОСК '
                 'возвращена семье основателя.',
    'gfaca800a': 'Российская сеть клиник репродуктивного здоровья: 35 '
                 'клиник в 34 городах.',
    'g48568133': 'Материнская компания судостроительного завода '
                 '«Звезда» — крупнейшей верфи России.',
    'gb5b2c75e': 'Инвестиционная структура экс-депутата '
                 'петербургского заксобрания Александра Салаева.',
}

# Профиль, отрасль которого унаследована от цели чужой сделки, а не от
# рода занятий самого покупателя (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {
    'gb5b2c75e': ('Лесопром', 'Холдинги'),
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
        print('  %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:56]))
        c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %-34s %s -> %s'
              % (cid, str(c.get('name'))[:34], old_ind, new_ind))
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
