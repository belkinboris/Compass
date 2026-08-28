#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дубль карточки о продаже «Инвитро», найденный при разборе профилей-
близнецов волны 2 самопроверки ИНН (28 августа 2026).

ПОЧЕМУ ЭТО ДУБЛЬ. `g4803e120` («Продажа сети лабораторий «Инвитро»») и
`g54d92fdd` («Роман Мирончик и партнёры приобрели контрольную долю в сети
лабораторной диагностики «Инвитро»») описывают ОДНО И ТО ЖЕ событие: обе —
`target: g8c7cfb14` («Инвитро»), обе датированы 2023 годом, обе закрыты, у
обеих одинаковый продавец в поле `seller` («Александр Островский» — факт
внесён в ОБЕ карточки НЕЗАВИСИМО двумя разными записями `FIXES` того же
раунда, дословно совпадающими цитатами из Коммерсанта). Разница только в
том, КАК назван покупатель: `g4803e120` называет точное юрлицо-цепочку
(ООО «МС Групп» → ООО «РМ Инвестментс» → АО «Холдинговая компания Инвитро»
→ Мирончик Роман Борисович), `g54d92fdd` — тот же человек и партнёры без
уточнения юрлица.

ЧТО ОСТАЁТСЯ, ЧТО УХОДИТ (сделка). `g4803e120` сильнее: 3 источника против
1, есть точная цепочка юрлиц покупателя, есть финансы самого ООО «Инвитро»
(не всей группы). `g54d92fdd` несёт ЧЕТЫРЕ факта, которых у `g4803e120`
нет вовсе, — независимая оценка Peregrine Capital (12–15 млрд руб.),
оценка выручки ГРУППЫ по Vademecum (39,2 млрд руб. за 2021 год), структура
владения через кипрскую Invitro Holding ltd. (пусто в `law.struct` у
`g4803e120`), и более ранний эпизод интереса Kismet Capital Group/Ивана
Таврина (2022 год) — переносятся дословно, каждый в СВОЁ поле. Числовая
оценка суммы («не менее 19–30 млрд ₽») заменяет плейсхолдер «Не раскрыта»
в `sum`/`eco.sum` — плейсхолдер не данные, реальная оценка их вытесняет
(а не дописывается рядом с плейсхолдером).

ЧТО ОСТАЁТСЯ, ЧТО УХОДИТ (профиль компании). После слияния сделок у
`g2067ce7f» («Роман Мирончик и партнёры») не остаётся ни одной роли — тот
же человек и группа уже названы текстом в перенесённых полях и в самом
заголовке оставленной карточки. Профиль сливается в `g14fd865a» (ООО «МС
Групп») — юрлицо с точной цепочкой владения, уже стоящее покупателем
оставленной карточки.

ШЕСТЬ ЗАПИСЕЙ `pipeline/ingest/fixes/batch_agents100_r7.py`, ссылавшихся на
`g54d92fdd` (law.struct, eco.val, eco.target_fin×2, eco.context, seller),
сняты вместе с этой правкой (см. комментарий в файле) — их факты уже
перенесены сюда дословно этим скриптом, а не потеряны.

Запуск:
    python3 pipeline/merge_invitro_mironchik_dup.py            # сухой прогон
    python3 pipeline/merge_invitro_mironchik_dup.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
REFS = ('buyer', 'seller_id', 'target', 'asset_id')

KEEP_DEAL, DROP_DEAL = 'g4803e120', 'g54d92fdd'
KEEP_COMPANY, DROP_COMPANY = 'g14fd865a', 'g2067ce7f'

DROP_SRC = ['Eqiva.ru', 'https://eqiva.ru/kolomentseva']

NEW_SUM = 'не менее 19–30 млрд ₽'
OLD_SUM_PLACEHOLDER = 'Не раскрыта'

LAW_STRUCT_ADD = ('Головная структура «Инвитро», по данным «СПАРК-Интерфакс»,— кипрская Invitro '
                   'Holding ltd., совладельцами которой называли господина Островского, Валентина '
                   'Дороничева и Владимира Куликовского. Еще 30% было у фондов Russia Partners, '
                   'писал в 2021 году Forbes.')
ECO_VAL_ADD = ('Управляющий директор Peregrine Capital Дмитрий Габышев оценил стоимость «Инвитро» '
               'в 12–15 млрд руб. или 5–6 EBITDA за 2022 год.')
ECO_TARGET_FIN_ADD = 'Отраслевое издание Vademecum оценивало совокупную выручку группы в 2021 году в 39,2 млрд руб.'
ECO_CONTEXT_ADD = ('В 2022 году среди заинтересованных в покупке «Инвитро» издание Vademecum называло '
                    'Kismet Capital Group (KCG) экс-гендиректора «МегаФона» Ивана Таврина. В KCG '
                    'заявили «Ъ», что не имеют отношения к текущей сделке.')


def norm(s):
    return ' '.join(str(s or '').split())


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals, comps = data['deals'], data['companies']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP_DEAL), by_id.get(DROP_DEAL)
    assert keep and drop, 'карточек пары нет в базе — состояние изменилось, скрипт остановлен'
    assert keep.get('target') == drop.get('target') == 'g8c7cfb14', 'цель у карточек уже не совпадает'
    assert keep.get('seller') == drop.get('seller') == 'Александр Островский', 'продавец разошёлся'

    both = [d['id'] for d in deals if {d.get(f) for f in REFS} >= {KEEP_COMPANY, DROP_COMPANY}]
    assert not both, 'сделка ссылается на оба профиля сразу: %s' % both

    assert norm(drop.get('law', {}).get('struct')) == norm(LAW_STRUCT_ADD)
    assert norm(drop.get('eco', {}).get('val')) == norm(ECO_VAL_ADD)
    assert norm(drop.get('eco', {}).get('target_fin')) == norm(ECO_TARGET_FIN_ADD)
    assert norm(drop.get('eco', {}).get('context')) == norm(ECO_CONTEXT_ADD)
    assert drop.get('sum') == NEW_SUM and drop.get('eco', {}).get('sum') == NEW_SUM
    assert keep.get('sum') == OLD_SUM_PLACEHOLDER and keep.get('eco', {}).get('sum') == OLD_SUM_PLACEHOLDER
    assert norm(keep.get('law', {}).get('struct')) in ('', '—')

    keep_urls = {str(s[1]) for s in (keep.get('src') or []) if len(s) > 1}
    assert DROP_SRC[1] not in keep_urls, 'источник дубля уже есть у оставляемой карточки'

    assert comps.get(KEEP_COMPANY) and comps.get(DROP_COMPANY), 'профиля компании нет'

    print('СЛИЯНИЕ ДУБЛЯ СДЕЛКИ')
    print('  оставляем %s  %s' % (KEEP_DEAL, keep['title']))
    print('  удаляем   %s  %s' % (DROP_DEAL, drop['title']))
    print('  переносим: law.struct, eco.val (+), eco.target_fin (+), eco.context (+), sum/eco.sum (замена плейсхолдера)')
    print('  переносим источник: %s' % DROP_SRC[1])
    print('\nСЛИЯНИЕ ПРОФИЛЯ-БЛИЗНЕЦА')
    print('  оставляем %s  «%s»' % (KEEP_COMPANY, comps[KEEP_COMPANY]['name']))
    print('  удаляем   %s  «%s»' % (DROP_COMPANY, comps[DROP_COMPANY]['name']))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    keep['sum'] = NEW_SUM
    keep['eco']['sum'] = NEW_SUM
    keep['law']['struct'] = LAW_STRUCT_ADD
    keep['eco']['val'] = (norm(keep['eco']['val']) + ' ' + ECO_VAL_ADD).strip()
    keep['eco']['target_fin'] = (norm(keep['eco']['target_fin']) + ' ' + ECO_TARGET_FIN_ADD).strip()
    keep['eco']['context'] = (norm(keep['eco']['context']) + ' ' + ECO_CONTEXT_ADD).strip()
    keep.setdefault('src', []).append(DROP_SRC)

    was_deals = len(deals)
    data['deals'] = [d for d in deals if d['id'] != DROP_DEAL]
    assert len(data['deals']) == was_deals - 1, 'удалилась не одна карточка'
    data.setdefault('merged', {})[DROP_DEAL] = KEEP_DEAL

    was_comps = len(comps)
    for d in data['deals']:
        for f in REFS:
            if d.get(f) == DROP_COMPANY:
                d[f] = KEEP_COMPANY
    keys = data.get('match_keys', {})
    aliases = [a for a in (keys.get(DROP_COMPANY) or []) if a not in (keys.get(KEEP_COMPANY) or [])]
    if aliases:
        keys[KEEP_COMPANY] = (keys.get(KEEP_COMPANY) or []) + aliases
    keys.pop(DROP_COMPANY, None)
    comps.pop(DROP_COMPANY)
    data.setdefault('merged_companies', {})[DROP_COMPANY] = KEEP_COMPANY
    assert len(comps) == was_comps - 1, 'удалился не один профиль'

    for d in data['deals']:
        refs = [d.get(f) for f in REFS if d.get(f)]
        assert len(refs) == len(set(refs)), 'после слияния компания заняла две роли: %s' % d['id']

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Сделок: %d (было %d). Профилей: %d (было %d).'
          % (len(data['deals']), was_deals, len(comps), was_comps))


if __name__ == '__main__':
    main('--write' in sys.argv)
