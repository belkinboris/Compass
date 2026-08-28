# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gfa47c307 («Ригла» покупает
аптечную сеть «Аптеки миницен» + «Новая аптека»): статус стоял
«Обсуждается» с единственным источником от 2 октября 2024 года («сделка
находится на согласовании в ФАС») — обязательная проверка статуса для
незакрытых сделок (REVISION_BRIEF) нашла, что сделка ЗАКРЫТА уже почти два
года назад, 6 декабря 2024 года, после одобрения ФАС. Оба источника —
независимые издания, цитаты подтверждены лично прямым WebFetch.

1. Vademecum (06.12.2024): «в пятницу, 6 декабря, была завершена сделка по
   приобретению «Риглой» объединенной сети «Новая аптека» & «Аптека
   Миницен» (Хабаровск) после ее согласования в Федеральной
   антимонопольной службе (ФАС)».
2. Konkurent.ru (12.12.2024), независимое подтверждение: «Сеть аптек
   «Ригла» завершила сделку по приобретению дальневосточной объединенной
   аптечной сети «Аптеки миницен» и «Новая аптека»».
3. Судьба сети после закрытия — Vademecum (08.06.2026): розничный сегмент
   группы «Протек» переименован в «Ригла-Здравсити», при этом «Миницен»
   сохранён как отдельный региональный бренд внутри группы, а не
   переименован в «Риглу».

Родственный дефект в поле `extra` (то же противоречие статусу, только в
другом поле) снят отдельным скриптом:
pipeline/fix_rigla_minitsen_extra_stale_status.py — найден Playwright-
проверкой ПОСЛЕ этой записи, когда стало видно, что «Дополнительный
контекст» карточки по-прежнему начинается с «Сделка находится на
согласовании в ФАС» рядом с уже исправленным статусом «Закрыта».

Не через review.py: смена статуса, `law.appr` и `eco.context` меняются
одновременно по двум новым источникам, а не дословным дополнением одного
поля.

Запуск: python3 pipeline/fix_rigla_minitsen_status_closed.py
        python3 pipeline/fix_rigla_minitsen_status_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfa47c307'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_APPR = 'Сделка находится на согласовании в ФАС.'
NEW_APPR = (
    'Сделка закрыта 6 декабря 2024 года: «6 декабря итоговое соглашение '
    'получило одобрение в Федеральной антимонопольной службе (ФАС)» '
    '(Konkurent.ru), после чего «была завершена сделка по приобретению '
    '«Риглой» объединенной сети «Новая аптека» & «Аптека Миницен»» '
    '(Vademecum).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Купленная сеть сохранена как отдельный региональный бренд: по '
    'состоянию на июнь 2026 года розничный сегмент группы «Протек» '
    'переименован в «Ригла-Здравсити», а «Миницен» продолжает работать под '
    'своим именем внутри этой группы, наряду с ещё одним дальневосточным '
    'брендом «Аптека25.рф» (Vademecum).'
)

NEW_SRC = [
    ['Vademecum', 'https://vademec.ru/news/2024/12/06/rigla-zavershila-sdelku-po-pokupke-dalnevostochnoy-apteki-minitsen/'],
    ['Konkurent.ru', 'https://konkurent.ru/article/73339'],
    ['Vademecum', 'https://vademec.ru/news/2026/06/08/roznichnyy-segment-gk-protek-pereimenovan-v-rigla-zdravsiti/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
