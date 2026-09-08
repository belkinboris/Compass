# -*- coding: utf-8 -*-
"""Слияние ТРОЙНОГО дубля: одна и та же сделка (Группа «ОКТО» купила
100% МКАО «Западная Голд Майнинг Лимитед», закрыта 25 апреля 2025 года)
существовала под ТРЕМЯ разными id — `g15f35a5d`, `cc2929a95` и
`g8ed07ff5`. Найдено при месячной очереди 8 сентября 2026 года: у
`cc2929a95` в `law.adv` уже стояла запись, оставленная более ранней
сессией («эта карточка — тот же сюжет, что и g8ed07ff5, под другим
id») — находка была сделана, но не доведена до слияния, и служебная
фраза при этом утекла в пользовательский текст (нарушение «Язык для
людей»).

Оставлена карточка `g15f35a5d` — она самая полная (добавлена раньше
всех, 22 июля 2026, уже прошла все три уровня дочитывания, у неё
подтверждённый через реестр профиль предмета `gd1fce9cc` с ИНН, восемь
источников, подробные финансовые показатели цели за 2023 и 2025 годы).

Личный WebFetch подтвердил корректную дату закрытия — zolteh.ru
(28.04.2025): «Сделка закрыта 25 апреля текущего года» — она уже стояла
у `g15f35a5d` и `cc2929a95`; у `g8ed07ff5` была датирована 15 мая 2025
года (по дате пресс-релиза LEVEL Legal Services, не по дате закрытия) —
это была менее точная из трёх карточек, поэтому и не выбрана канонической.

Перенесено в `g15f35a5d`:
1) Источник «Коммерсантъ — Сделки года» и оценка суммы «$400 млн» (из
   `cc2929a95`, изначально — из рэнкинга «Ъ»).
2) Именной состав команды BIRCH (Ситников, Колосков, Баков, Шпак) и
   источник t.me/LawFirms/8961 (из `g8ed07ff5`) — в `g15f35a5d` BIRCH
   был указан без имён партнёров.

Запуск: python3 pipeline/merge_zapadnaya_gold_mining_triplicate.py
        python3 pipeline/merge_zapadnaya_gold_mining_triplicate.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KEEP_ID = 'g15f35a5d'
DROP_IDS = ['cc2929a95', 'g8ed07ff5']

OLD_SUM = 'Не раскрыта'
NEW_SUM = 'не разглашается (возможная сумма сделки — $400 млн, согласно открытым источникам)'

OLD_BIRCH_ADV = [
    'Юридический консультант продавца (акционеров МКАО «Западная Голд Майнинг»)',
    'BIRCH',
    'Продажа ГК «Западная». Источник: birchlegal.ru',
]
NEW_BIRCH_ADV = [
    'Юридический консультант продавца (акционеров МКАО «Западная Голд Майнинг»)',
    'BIRCH',
    'Корпоративный, финансовый и налоговый блоки сделки. Проектом руководили '
    'старший партнёр Антон Ситников и советник Виталий Колосков (корпоративный '
    'блок), партнёр Антон Баков (финансовый блок) и партнёр Андрей Шпак '
    '(налоговый блок). Источник: https://t.me/LawFirms/8961',
]

NEW_SRC = [
    ['Коммерсантъ — «Сделки года»', 'https://www.kommersant.ru/doc/8077927'],
    ['РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)', 'https://t.me/LawFirms/8961'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deals = data['deals']
    by_id = {d['id']: d for d in deals}
    keep = by_id[KEEP_ID]

    for drop_id in DROP_IDS:
        assert drop_id in by_id, f'{drop_id} должна существовать до слияния'

    assert keep['eco']['sum'] == OLD_SUM
    assert keep['sum'] == OLD_SUM
    assert keep['law']['adv'][1] == OLD_BIRCH_ADV

    print('=== g15f35a5d: sum / eco.sum ===')
    print(NEW_SUM)
    print()
    print('=== g15f35a5d: law.adv[1] ===')
    print(NEW_BIRCH_ADV)
    print()
    print('=== g15f35a5d: +src ===')
    for s in NEW_SRC:
        print(s)
    print()
    print('=== удаляются карточки ===', DROP_IDS)

    if write:
        keep['sum'] = NEW_SUM
        keep['eco']['sum'] = NEW_SUM
        keep['law']['adv'][1] = NEW_BIRCH_ADV
        existing_urls = {s[1] for s in keep['src']}
        for s in NEW_SRC:
            if s[1] not in existing_urls:
                keep['src'].append(s)

        merged = data.setdefault('merged', {})
        for drop_id in DROP_IDS:
            merged[drop_id] = KEEP_ID
        data['deals'] = [d for d in deals if d['id'] not in DROP_IDS]

        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано. Сделок было: %d, стало: %d' % (len(deals), len(data['deals'])))
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
