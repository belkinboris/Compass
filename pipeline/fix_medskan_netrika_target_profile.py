#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки Медскан/«Нетрика Медицина» ссылался на профиль совсем
другой компании.

ЧТО СЛОМАНО. Карточка `g630c3361` («ГК «Медскан» заинтересована в покупке
ООО «Нетрика Медицина»») хранит `target: "g12c86c6a"`, а профиль `g12c86c6a`
называется «Клиника «Медицина»» — многопрофильная частная клиника в Москве.
Текст самой карточки прямо называет предмет другим: «разработчик IT-платформ
для здравоохранения ООО «Нетрика Медицина»» — компания-разработчик софта, а
не клиника. Похоже на автоматическое сопоставление по общему слову
«медицина» в названиях (тот же класс дефекта, что уже описан в CLAUDE.md —
«Стороной сделки может быть записан профиль совсем другой сущности», случай
ЛСР/Domina Пулково).

ПОЧЕМУ ИМЕННО ТАК И НЕ ИНАЧЕ. В отличие от Пулково/Селегеня, «Клиника
«Медицина»» — НЕ бессмысленное или пустое имя: это настоящий, отдельно
существующий профиль (подтверждён в реестре ФНС, ИНН 7729058330, см.
`pipeline/fns_registry.py`), просто ошибочно привязанный к ЭТОЙ сделке.
Профиль не удаляется и не переименовывается — он остаётся в базе как есть
(после правки — без единой сделки, как и ~127 других профилей компаний,
см. журнал CLAUDE.md), а для «Нетрика Медицина» заводится ОТДЕЛЬНЫЙ, новый
профиль с именем и описанием, взятыми дословно из текста самой карточки.

ПРОВЕРЕНО. `g12c86c6a` использован ровно в одной сделке (`g630c3361`) — до
правки; профиля «Нетрика Медицина» в базе ещё нет ни под одним ключом.

Запуск:
    python3 pipeline/fix_medskan_netrika_target_profile.py            # сухой прогон
    python3 pipeline/fix_medskan_netrika_target_profile.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g630c3361'
WRONG_PROFILE_ID = 'g12c86c6a'
WRONG_PROFILE_NAME = 'Клиника «Медицина»'
NEW_PROFILE_ID = 'g630c3361-target'
NEW_PROFILE_NAME = 'ООО «Нетрика Медицина»'
NEW_PROFILE_DESC = 'Разработчик IT-платформ для здравоохранения.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']
    match_keys = data['match_keys']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == WRONG_PROFILE_ID, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, WRONG_PROFILE_ID, deal.get('target'))
    assert 'Нетрика' in (deal.get('extra') or ''), \
        '%s: текст карточки больше не называет «Нетрика Медицина» — проверить вручную' % DEAL_ID

    wrong = companies.get(WRONG_PROFILE_ID)
    assert wrong is not None, 'нет профиля %s' % WRONG_PROFILE_ID
    assert wrong.get('name') == WRONG_PROFILE_NAME, \
        '%s: имя профиля не совпадает дословно: %r' % (WRONG_PROFILE_ID, wrong.get('name'))

    refs = [d['id'] for d in data['deals']
            if WRONG_PROFILE_ID in (d.get('target'), d.get('buyer'), d.get('seller_id'), d.get('asset_id'))]
    assert refs == [DEAL_ID], 'профиль %s используется не только в %s: %r' % (WRONG_PROFILE_ID, DEAL_ID, refs)

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID
    assert not any(c.get('name') == NEW_PROFILE_NAME for c in companies.values()), \
        'профиль %r уже есть под другим id' % NEW_PROFILE_NAME

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, WRONG_PROFILE_ID, WRONG_PROFILE_NAME))
    print('Станет: target=%s (%r)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Профиль %s (%r) остаётся в базе как есть, без сделок.' % (WRONG_PROFILE_ID, WRONG_PROFILE_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'ИТ и интернет',
        'desc': NEW_PROFILE_DESC,
        'kpi': ['Профиль', 'Автоматический'],
    }
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert WRONG_PROFILE_ID in companies, 'старый профиль случайно удалён — не должен был'

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
