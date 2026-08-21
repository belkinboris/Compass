#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки Займер/«Таксиагрегатор»+IntellectMoney ссылался на профиль
совсем другой компании — «КИВИ».

ЧТО СЛОМАНО. Карточка `g8af20254` («МФК «Займер» приобретает по 50% в
«Таксиагрегаторе» и IntellectMoney у ГК Qiwi») хранит `target: "gd5d02d09"`
(«КИВИ» — платёжный холдинг), хотя сама карточка называет предмет своими же
полями: «по 50% цифрового сервиса «Таксиагрегатор» и платформы... IntellectMoney»
(`law.struct`), «планирует приобрести по 50% в ООО «КИВИ ТЕХНОЛОГИИ» (бренд
«Таксиагрегатор») и ООО «ИНТЕЛЛЕКТМАНИ» (бренд IntellectMoney)» (`extra`).
Похожий класс дефекта, что уже чинился для Альфа-Банк/Flocktory
(`fix_alfabank_flocktory_target_profile.py`), найден при том же чтении —
здесь причина путаницы виднее: юрлицо-мишень называется «ООО «КИВИ
ТЕХНОЛОГИИ»» (совпадение по подстроке «КИВИ» с платёжным холдингом «АО
«КИВИ»», хотя это разные юрлица) — вероятная причина автоматической
подмены при разборе.

ЛОТ ИЗ ДВУХ АКТИВОВ. Сделка покупает доли в ДВУХ разных юрлицах
(«Таксиагрегатор» и IntellectMoney) одним договором — тот же случай, что
уже описан в CLAUDE.md («лот из нескольких юрлиц») и уже чинился этим же
приёмом для ЛСР/Domina Пулково (`fix_pulkovo_target_profile.py`, оттуда
взят и формат нового профиля — `lot: true`, суффикс `-target` в id).

СТАТУС СДЕЛКИ — «ОБСУЖДАЕТСЯ», НЕ ЗАКРЫТА. Это не мешает починке ссылки
(предмет сделки известен независимо от статуса закрытия), но означает, что
новый профиль НЕ получает поле `ownership` этим скриптом — доля ещё не
перешла фактически (см. G8, PRODUCT_ROADMAP.md: `ownership` — только для
уже состоявшихся фактов).

ПОЧЕМУ ПРОФИЛЬ КИВИ НЕ ТРОГАЕТСЯ. `gd5d02d09` верно используется в
нескольких других сделках (g0a6f7569, g5d9d8e6c, g6bccb70f, g0fadc207) —
не удаляется и не переименовывается.

Запуск:
    python3 pipeline/fix_zaimer_taxiaggregator_intellectmoney_target.py            # сухой прогон
    python3 pipeline/fix_zaimer_taxiaggregator_intellectmoney_target.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g8af20254'
BAD_PROFILE_ID = 'gd5d02d09'
BAD_PROFILE_NAME = 'КИВИ'
NEW_PROFILE_ID = 'g8af20254-target'
NEW_PROFILE_NAME = 'ООО «КИВИ Технологии» (бренд «Таксиагрегатор») и ООО «Интеллектмани» (бренд IntellectMoney)'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == BAD_PROFILE_ID, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, BAD_PROFILE_ID, deal.get('target'))
    assert deal.get('status') == 'Обсуждается', \
        '%s: статус изменился (%r) — перепроверить, не пора ли добавлять ownership' % (
            DEAL_ID, deal.get('status'))

    bad = companies.get(BAD_PROFILE_ID)
    assert bad is not None, 'нет профиля %s' % BAD_PROFILE_ID
    assert bad.get('name') == BAD_PROFILE_NAME, \
        '%s: имя профиля не совпадает дословно: %r' % (BAD_PROFILE_ID, bad.get('name'))

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, BAD_PROFILE_ID, BAD_PROFILE_NAME))
    print('Станет: target=%s (%r, lot=true)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Профиль %s (КИВИ) не трогается — верно используется в других сделках' % BAD_PROFILE_ID)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': 'ИТ и интернет',
        'desc': 'Цифровой сервис «Таксиагрегатор» и платформа приёма '
                'онлайн-платежей IntellectMoney; по 50% в каждом «Займер» '
                'договорился купить у ГК Qiwi в 2025 году, сделка не закрыта.',
        'kpi': ['Профиль', 'Автоматический'],
        'lot': True,
    }
    deal['target'] = NEW_PROFILE_ID

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert BAD_PROFILE_ID in companies  # КИВИ остаётся

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
