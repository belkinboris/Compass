# -*- coding: utf-8 -*-
"""Четырнадцатая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После тринадцати партий настоящее описание есть у 530
профилей из 1872 (28%). Кандидатов этой партии искали по узнаваемости
имени, а не по рангу участия в сделках (см. батчи 8–13) — каждый проверен
по тексту его собственной сделки в базе.

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 12 профилям, исправляет
отрасль у 1.

Отдельная находка при чтении контекста: «Соллерс» стоял в «Банки» —
отрасль унаследована от единственной сделки профиля, которая была о
продаже лизинговой дочки «Соллерс-Финанс», а не о самой компании.
«Соллерс» — российский производитель автомобилей и коммерческой техники,
исправлено на «Автопром».

Запуск:
    python3 pipeline/write_company_descriptions_batch14.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch14.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id профиля -> описание. Только компании, чей род занятий общеизвестен.
DESCRIPTIONS = {
    'g8e1a15a7': 'Российский производитель дженериков и биопрепаратов, '
                 'вышел на биржу в 2024 году.',
    'g522c7ca1': 'Российский банк, вошёл в состав Промсвязьбанка в '
                 '2023 году.',
    'g56f7b58a': 'Российский производитель косметики и бытовой химии.',
    'ga8cb8878': 'Российское подразделение Unilever, продано группе '
                 '«Арнест».',
    'g522a000a': 'Российские пивоваренные активы Heineken, проданы группе '
                 '«Арнест».',
    'g5167afe2': 'Российское подразделение автомобильного банка '
                 'Volkswagen Financial Services.',
    'gce18ed36': 'Российская аптечная сеть.',
    'gd101d0a4': 'Российский оператор мобильной связи (бренд «Билайн»).',
    'g1a00189d': 'Российский производитель грузовых автомобилей и '
                 'коммерческой техники.',
    'gd05f527f': 'Российский банк, вошёл в состав ПСБ в 2020 году.',
    'g4ef21c08': 'Российский производитель автомобилей и коммерческой '
                 'техники.',
    'gf5faae55': 'Российская страховая группа.',
}

# Профили, отрасль которых унаследована от одной сделки и не отражает
# основной бизнес компании (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {
    'g4ef21c08': ('Банки', 'Автопром'),
}

# Профили, которым описание не ставится в этой партии: неизвестно, что
# именно они обозначают, или падежная/предметная форма имени.
UNCLEAR = {}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        assert cid not in UNCLEAR, 'профиль %s помечен неясным — описание ставить нельзя' % cid
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        # Своё описание не перетираем: прошлые партии и ручные правки старше этой.
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
    print('Оставлено без описания намеренно: %d профилей (см. UNCLEAR)' % len(UNCLEAR))

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
