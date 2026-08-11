# -*- coding: utf-8 -*-
"""Тридцать седьмая партия: 8 описаний. Кандидаты по числу связанных
сделок среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 8 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch37.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch37.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'gf0296008': 'Предприниматель; в 2023 году купил 95% долей '
                 'кондитерской фабрики «Колос» в Челябинске.',
    'gf2c1da31': 'Российское подразделение Henkel; выкупалось '
                 'консорциумом инвесторов, включая Виктора Харитонина '
                 'и Ивана Таврина (Kismet Capital).',
    'gf286b3ae': 'Коллекторская компания, российское подразделение '
                 'немецкой EOS Group; в 2024 году продана '
                 'Газпромбанку.',
    'gf15f4eca': 'Чайный бренд, ранее входивший в портфель Unilever; в '
                 '2023 году куплен Объединённой чайной компанией у '
                 'Ekaterra.',
    'gf15533aa': 'Химический завод в Липецке; в 2023 году продан '
                 'Lanxess AG владельцу ГК «Нортекс» Владимиру Якушину.',
    'gf143a637': 'Инвестиционная структура Андрея Комарова; в 2023 '
                 'году купила у Amcor три завода по производству '
                 'упаковки в России.',
    'gf093eb5c': 'Молочный комплекс в Воронежской области; в 2024 году '
                 'куплен у концерна «Детскосельский».',
    'gf000224d': 'Страховая компания под брендом Raiffeisen; в 2024 '
                 'году продана группе «Ренессанс страхование».',
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
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
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
