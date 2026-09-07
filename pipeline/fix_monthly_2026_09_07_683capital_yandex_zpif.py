# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), две карточки.
Проверено ЛИЧНО прямым WebFetch.

1) c6b5fb9f3 (Разрешение Президента РФ хедж-фонду 683 Capital Partners
   на выкуп российских акций, март 2025, «Согласование получено»):
   само разрешение не отозвано, но связанная с ним схема обмена
   заблокированных бумаг для розничных инвесторов буксует. Личный
   WebFetch (smart-lab.ru/blog/1331358.php, 22 июля 2026) подтвердил:
   «первая волна», объявленная 1 декабря 2025 года, к июлю 2026-го так
   и не исполнена — заявки инвесторов месяцами висят со статусом
   «принято». Прямых данных о том, что 683 Capital Partners реально
   выкупил акции у западных фондов, не нашлось. `status` НЕ меняется
   (само разрешение остаётся в силе) — добавлен `law.terms` с честной
   оговоркой о буксующем исполнении.

2) c7240231e (Участники ЗПИФ «Консорциум. Первый» перевели доли в
   прямое владение акциями «Яндекса», июль 2025): закрытие подтверждено
   независимо личным WebFetch (interfax.ru/business/1034928, 7 июля
   2025 года) — «Участники... завершили процесс по переводу своих
   долей в прямое владение акциями «Яндекса»». `status` → «Закрыта».

Запуск: python3 pipeline/fix_monthly_2026_09_07_683capital_yandex_zpif.py
        python3 pipeline/fix_monthly_2026_09_07_683capital_yandex_zpif.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CP_ID = 'c6b5fb9f3'
CP_OLD_TERMS = None
CP_NEW_TERMS = (
    'Само разрешение не отозвано, но связанная с ним схема обмена '
    'заблокированных бумаг для розничных инвесторов буксует: «первая '
    'волна», объявленная 1 декабря 2025 года, к июлю 2026-го так и не '
    'исполнена — заявки инвесторов месяцами висят со статусом '
    '«принято». Прямых подтверждений, что фонд реально выкупил акции '
    'у западных инвесторов, не нашлось.'
)

YA_ID = 'c7240231e'
YA_OLD_STATUS = None
YA_NEW_STATUS = 'Закрыта'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    cp = by_id[CP_ID]
    ya = by_id[YA_ID]

    assert cp['law'].get('terms') == CP_OLD_TERMS
    assert ya.get('status') == YA_OLD_STATUS

    print('=== c6b5fb9f3: law.terms ===')
    print(CP_NEW_TERMS)
    print()
    print('=== c7240231e: status ===', YA_NEW_STATUS)

    if write:
        cp['law']['terms'] = CP_NEW_TERMS
        ya['status'] = YA_NEW_STATUS
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
