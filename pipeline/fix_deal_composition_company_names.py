# -*- coding: utf-8 -*-
"""Имя профиля — деловой глагол из заголовка сделки, а не название компании.

ЧТО СЛОМАНО. У 12 профилей в базе имя начинается с «Приобретение»,
«Продажа», «Инвестици[яи]» — это вырезанный без разбора глагольный
заголовок сделки («Приобретение NGINX компанией F5 Networks за ~$670
млн» → профиль назван «Приобретение NGINX» вместо «NGINX»), а не имя
самой компании. Тот же класс дефекта, что «Имя компании — не место для
доли» (CLAUDE.md), только вместо доли в имени осталось действие сделки.
`test_company_name_is_not_a_deal_composition` его не ловит: регулярка
ищет только «%», «долей», «акций», «оставшиеся», а не глаголы сделки.

ЧТО ДЕЛАЕТ ЭТОТ СКРИПТ — только БЕЗОПАСНУЮ часть находки:

* Переименовывает 3 профиля, где по собственной сделке видно: сам
  профиль — и есть предмет или сторона сделки, просто с лишним словом
  в начале. `gb3e93376` «Приобретение NGINX» → «NGINX» (F5 Networks
  приобрела NGINX); `g4caccddc` «Приобретение Veeam Software» →
  «Veeam Software» (продана фонду Insight Partners); `gc216a92e`
  «Приобретение Luxoft Holding» → «Luxoft Holding» (продан DXC
  Technology).

* Сливает ДВУХ близнецов, вскрывшихся при чтении контекста:

  1. `ga2d76207` «Kismet Capital Group Ивана» (без фамилии — обрезано
     от «Kismet Capital Group Ивана Таврина», сделка про покупку доли
     в HeadHunter) и `g0126cbf5` «Приобретение Kismet Capital Group»
     (сделка про покупку ППР у Fleetcor) — оба профиля с ролью
     «Покупатель» в СВОИХ сделках, то есть одна и та же инвесткомпания
     Ивана Таврина записана дважды. Выживает `ga2d76207`, переименован
     в чистое «Kismet Capital Group».

  2. `g5006b71b` «Приобретение Qiwi» — профиль-сирота, ни одной сделки
     в базе. Первая попытка просто переименовать его в «Qiwi» тут же
     уронила `test_no_company_twins`: в базе уже есть полноценный
     профиль «КИВИ» (`gd5d02d09`, 6 сделок, своё описание) — та же
     компания кириллицей. Простое переименование само стало бы
     близнецом. Правка — не переименование, а слияние: `g5006b71b`
     сливается в `gd5d02d09`.

* Заодно у «РТ-Капитала» (`g9fe6ac51`) была неверная отрасль «ГМК и
  добыча» — унаследована от предмета его единственной сделки (продажа
  доли в металлургическом ОАО «ВИЛС»), а не от рода занятий самого
  РТ-Капитала: дочерняя структура Ростеха, реализующая непрофильные
  активы госкорпорации через открытые аукционы. Исправлено на
  «Управление активами».

ЧТО НЕ СДЕЛАНО (найдено, но не входит в этот прогон — см. G-бэклог).
У остальных 6 профилей той же группы дефект глубже переименования:
`target` сделки указывает на профиль ИНВЕСТОРА, а не получателя
инвестиции — «Инвестиции Hyundai» (цель — стартап Arrival, не сам
Hyundai), «Инвестиции Gagarin Capital» (цель — Earth AI), «Инвестиции
Дмитрия Потапова» (цель — CarCraft), «Инвестиция Игоря Рыбакова» (цель —
AMMA Pregnancy Tracker), «Продажа Roust Corporation» (Roust — ПРОДАВЕЦ
польской «дочки» CEDC International, а не сам предмет продажи), и
«Продажа Михаилом Прохоровым» — один профиль ошибочно служит `target`
СРАЗУ у двух несвязанных сделок (продажа доли в Brooklyn Nets и
отдельная продажа ГДР TCS Group трастом Rigi Trust, не имеющим
отношения к Прохорову). Починка требует не переименования, а создания
новых профилей и переноса `target` — решение принимает отдельный прогон.

Запуск:
    python3 pipeline/fix_deal_composition_company_names.py            # сухой прогон
    python3 pipeline/fix_deal_composition_company_names.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)
# Тот же признак, что у test_match_key_alias_is_a_name: алиас дубля,
# доставшийся ему от бракованного «Приобретение X»/«Продажа X» имени, не
# переносится на выжившего — это кусок заголовка сделки, а не имя.
BAD_ALIAS_WORD = re.compile(
    r'\b(выкуп\w*|покупк\w*|продаж\w*|приобрет\w*)\b', re.I)

# Простые переименования: профиль верно определяет сторону/предмет своей
# сделки, лишнее — только глагол в начале имени.
RENAMES = {
    'gb3e93376': ('Приобретение NGINX', 'NGINX'),
    'g4caccddc': ('Приобретение Veeam Software', 'Veeam Software'),
    'gc216a92e': ('Приобретение Luxoft Holding', 'Luxoft Holding'),
}

# (dup_id, survivor_id, [deal_ids дубля], имя дубля, имя выжившего ДО правки,
#  новое имя выжившего или None — оставить как есть)
MERGES = [
    ('g0126cbf5', 'ga2d76207', ['gd133363d'],
     'Приобретение Kismet Capital Group', 'Kismet Capital Group Ивана', 'Kismet Capital Group'),
    ('g5006b71b', 'gd5d02d09', [], 'Приобретение Qiwi', 'КИВИ', None),
]

DESCRIPTIONS = {
    'gb3e93376': 'Американский разработчик открытого веб-сервера '
                 'nginx; в 2019 году куплен компанией F5 Networks.',
    'g4caccddc': 'Разработчик программного обеспечения для резервного '
                 'копирования данных; в 2020 году продан фонду Insight '
                 'Partners.',
    'gc216a92e': 'ИТ-компания российского происхождения, разработка '
                 'программного обеспечения на заказ; в 2019 году '
                 'продана DXC Technology.',
    'ga2d76207': 'Инвестиционная компания Ивана Таврина.',
    'g9fe6ac51': 'Дочерняя структура госкорпорации «Ростех», '
                 'реализует непрофильные активы через открытые '
                 'аукционы.',
}

INDUSTRY_FIXES = {
    'g9fe6ac51': ('ГМК и добыча', 'Управление активами'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    for cid, (old_name, new_name) in RENAMES.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c['name'] == old_name, 'имя %s уже другое: %r' % (cid, c['name'])
        print('ПЕРЕИМЕНОВЫВАЕМ  %s: %r -> %r' % (cid, old_name, new_name))
        if write:
            c['name'] = new_name
            data['match_keys'][cid] = [new_name.lower()]

    for dup_id, survivor_id, deal_ids, dup_name, survivor_old_name, survivor_new_name in MERGES:
        assert companies[dup_id]['name'] == dup_name, 'дубль %s уже не тот' % dup_id
        assert companies[survivor_id]['name'] == survivor_old_name, 'выживший %s уже не тот' % survivor_id
        full_text_refs = sorted(d['id'] for d in deals if dup_id in json.dumps(d, ensure_ascii=False))
        assert full_text_refs == sorted(deal_ids), (
            'дубль %s встречается не только в учтённых сделках: %r' % (dup_id, full_text_refs))

        final_name = survivor_new_name or survivor_old_name
        print('СЛИВАЕМ  %s -> %s (%s)' % (dup_id, survivor_id, final_name))
        if not write:
            continue

        for d in deals:
            if d.get('id') in deal_ids:
                if d.get('buyer') == dup_id:
                    d['buyer'] = survivor_id
                if d.get('target') == dup_id:
                    d['target'] = survivor_id
                if d.get('seller_id') == dup_id:
                    d['seller_id'] = survivor_id
                if d.get('asset_id') == dup_id:
                    d['asset_id'] = survivor_id

        survivor_aliases = set(data['match_keys'].get(survivor_id, []))
        dup_aliases = data['match_keys'].pop(dup_id, [])
        survivor_aliases.update(a for a in dup_aliases if not BAD_ALIAS_WORD.search(a))
        if survivor_new_name:
            survivor_aliases.add(survivor_new_name.lower())
        data['match_keys'][survivor_id] = sorted(survivor_aliases)
        data.setdefault('merged_companies', {})[dup_id] = survivor_id
        del companies[dup_id]
        if survivor_new_name:
            companies[survivor_id]['name'] = survivor_new_name

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ  %-12s %-30s %s' % (cid, str(c.get('name'))[:30], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r' % (cid, c.get('ind')))
        print('  ОТРАСЛЬ  %-12s %s -> %s' % (cid, old_ind, new_ind))
        if write:
            c['ind'] = new_ind
        ind_fixed += 1

    print('\nПереименовано: %d, слито близнецов: %d, описаний: %d, отраслей: %d'
          % (len(RENAMES), len(MERGES), wrote, ind_fixed))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
