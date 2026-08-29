#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`gad6ed1b8` («Продажа 55,44% доли СДЭК фонду под управлением СФН»,
2024-04-01, Ведомости) и `gf577d893` («Леонид Гольдорт продал 55,44% СДЭК
компании Кластер Капитал», 2024-07-04, Interfax/Коммерсантъ) — одна и та же
сделка, увиденная на двух стадиях: `seller` (Леонид Гольдорт) и `target`
(g5df2bdb6, СДЭК) совпадают дословно, доля совпадает (55,44%), диапазон
суммы у более ранней карточки (11–13 млрд ₽) — подмножество диапазона более
поздней (11–25 млрд ₽). В апреле покупатель был известен только как «фонд
под управлением СФН» (профиль g125bb214), к июлю источники назвали точное
юрлицо — АО «Кластер Капитал» (g5e5ec0fe, ИНН подтверждён кампанией
самопроверки ИНН, Этап 14).

Найдено кампанией Этап 14, П3 (партия 4/4): попытка подтвердить g125bb214
дала тот же ИНН, что уже подтверждён для g5e5ec0fe, — коллизия, за которой
стоит не профиль-близнец, а дубль самой карточки сделки (тот же класс, что
уже разбирался для «Вим недвижимость»/ВТБ-Открытие/RWB и др.).

Оставлена `gf577d893` — она полнее (три источника вместо одного, включая
Коммерсантъ «Сделки года»; названы оба консультанта; есть выручка/EBITDA/ЧП
цели; точное юрлицо покупателя, уже подтверждённое по ИНН). Из `gad6ed1b8`
перенесены дословно два факта, которых у `gf577d893` не было (`law.appr` —
одобрение ФАС, `law.terms` — отсутствие кадровых перестановок кроме
гендиректора) и ссылка на Ведомости добавлена в `src`. Профиль-заглушка
`g125bb214` («фонд под управлением СФН») удалён как осиротевший после
слияния — он описывал ту же сделку менее точно, чем g5e5ec0fe.

Правки таблицы FIXES, ссылавшиеся на удаляемую карточку `gad6ed1b8`
(`pipeline/ingest/fixes/batch_agents100_r4.py` — три записи `law.appr`/
`law.terms`/`law.struct`, `pipeline/ingest/fixes/batch_b_2024.py` — одна
запись `seller`), сняты вручную ДО слияния — оба факта, дословность которых
они подтверждали, перенесены в оставшуюся карточку этим же скриптом;
`seller` у `gf577d893` уже был тем же значением («Леонид Гольдорт») и
переноса не требовал.

Запуск:
    python3 pipeline/merge_sdek_kластер_kapital_dup.py            # сухой прогон
    python3 pipeline/merge_sdek_kластер_kapital_dup.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

KEEP = 'gf577d893'
DROP = 'gad6ed1b8'
DROP_PROFILE = 'g125bb214'

DROP_APPR = ('Сделка, ранее получившая, по его словам, одобрение Федеральной '
             'антимонопольной службы России (ФАС), закрыта.')
DROP_TERMS = ('По результатам сделки в компании в настоящий момент не ожидают '
              'кардинальных кадровых перестановок за исключением назначения нового '
              'генерального директора (Гольдорт также занимал пост СЕО).')
DROP_SRC = ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/04/26/1034281-osnovatel-sdek-nashel-pokupatelya-na-svoyu-dolyu']


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    keep = deals[KEEP]
    drop = deals[DROP]

    assert keep['seller'] == drop['seller'] == 'Леонид Гольдорт'
    assert keep['target'] == drop['target']
    assert keep['law']['appr'] == 'Публично не сообщалось'
    assert keep['law']['terms'] == '—'
    assert DROP_SRC not in keep['src']
    assert drop['law']['appr'].rstrip('.') == DROP_APPR.rstrip('.')
    assert drop['law']['terms'].rstrip('.') == DROP_TERMS.rstrip('.')
    assert DROP_PROFILE in companies

    REFS = ('buyer', 'seller_id', 'target', 'asset_id')
    other_refs = [d['id'] for d in data['deals']
                  if d['id'] not in (KEEP, DROP) and DROP_PROFILE in {d.get(f) for f in REFS}]
    assert not other_refs, 'профиль ещё нужен другой сделке: %s' % other_refs

    print('Проверки прошли. План:')
    print('  %s -> merged в %s' % (DROP, KEEP))
    print('  law.appr, law.terms перенесены дословно; src +1 (Ведомости)')
    print('  профиль %s удалён (осиротел)' % DROP_PROFILE)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    keep['law']['appr'] = DROP_APPR
    keep['law']['terms'] = DROP_TERMS
    keep['src'].append(DROP_SRC)

    data['deals'] = [d for d in data['deals'] if d['id'] != DROP]
    data.setdefault('merged', {})[DROP] = KEEP
    del companies[DROP_PROFILE]
    data['match_keys'].pop(DROP_PROFILE, None)

    new_deals = {d['id']: d for d in data['deals']}
    assert DROP not in new_deals
    assert new_deals[KEEP]['law']['appr'] == DROP_APPR
    assert new_deals[KEEP]['law']['terms'] == DROP_TERMS
    assert data['merged'][DROP] == KEEP
    assert DROP_PROFILE not in companies

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
