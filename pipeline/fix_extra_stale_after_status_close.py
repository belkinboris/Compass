# -*- coding: utf-8 -*-
"""После смены статуса на «Закрыта» (pipeline/fix_evroonko_uniklinik_closed.py
и pipeline/fix_boosty_harkaneka_closed.py) поле `extra` осталось нетронутым
у обеих карточек и продолжало говорить «в процессе закрытия»/«планируется
закрытие» — тот самый класс дефекта из REVISION_BRIEF.md («после правки —
перечитайте карточку целиком, не только своё поле»).

Запуск: python3 pipeline/fix_extra_stale_after_status_close.py
        python3 pipeline/fix_extra_stale_after_status_close.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_EXTRA_1 = (
    'Сделка находится в процессе закрытия. Клиника взята в управление. '
    'Покупателем выступает ГК «Евроонко» в интересах Евгения Туголукова '
    '— совладельца клиник «Медскан» и клиники «Хадасса». Продавцы — '
    'физические лица из строительного бизнеса.'
)
NEW_EXTRA_1 = (
    'Сделка закрыта. Покупателем выступает ГК «Евроонко» (через АО '
    '«Тетра») в интересах Евгения Туголукова — совладельца клиник '
    '«Медскан» и клиники «Хадасса». Продавцы — Роман и Шеке Ферояны, '
    'физические лица из строительного бизнеса.'
)

OLD_EXTRA_2 = (
    'Сделка между My.Games и кипрским предпринимателем Павлом '
    'Харанеком, основателем Broadsmart Group, по продаже двух активов: '
    'сервиса монетизации для авторов Boosty и сервиса монетизации '
    'трансляций Donation Alerts. Планируется закрытие в третьем '
    'квартале 2024 года.'
)
NEW_EXTRA_2 = (
    'Сделка между My.Games и кипрским предпринимателем Павлом '
    'Харанеком, основателем Broadsmart Group, по продаже двух активов: '
    'сервиса монетизации для авторов Boosty и сервиса монетизации '
    'трансляций Donation Alerts. Сделка закрыта 11 декабря 2024 года — '
    'с задержкой на квартал против изначально анонсированного срока.'
)

FIXES = [
    ('ga75a4d0a', OLD_EXTRA_1, NEW_EXTRA_1),
    ('g1cc071e4', OLD_EXTRA_2, NEW_EXTRA_2),
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    for deal_id, old, new in FIXES:
        deal = by_id[deal_id]
        assert deal['extra'] == old, f'{deal_id}: extra изменился с момента чтения'
        print(f'=== {deal_id} extra: станет ===')
        print(new)
        print()
        if write:
            deal['extra'] = new

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
