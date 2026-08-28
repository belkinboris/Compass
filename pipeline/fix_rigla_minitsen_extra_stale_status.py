# -*- coding: utf-8 -*-
"""Карточка gfa47c307 («Ригла»/«Аптеки миницен» + «Новая аптека»): следом за
исправлением статуса («Обсуждается» → «Закрыта»,
pipeline/fix_rigla_minitsen_status_closed.py) Playwright-проверка на экране
нашла родственный дефект в другом поле — `extra` («Дополнительный
контекст») по-прежнему начинался с «Сделка находится на согласовании в
ФАС», хотя `status` и `law.appr` уже говорили «Закрыта». Родня уже
записанного в CLAUDE.md класса дефектов: правка одного поля не
гарантирует, что то же утверждение не осталось где-то ещё на карточке.

Первое предложение снято целиком (устарело); два факта, ради которых поле
вообще заведено, — состав сети (282 аптеки в ДФО) и продавцы — оставлены
без изменений, они не зависят от статуса согласования.

Запуск: python3 pipeline/fix_rigla_minitsen_extra_stale_status.py
        python3 pipeline/fix_rigla_minitsen_extra_stale_status.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfa47c307'

OLD_EXTRA = (
    'Сделка находится на согласовании в ФАС. В контур входят 282 аптеки во '
    'всех субъектах ДФО (кроме Чукотского АО). Продавцы: Игорь Жукович '
    '(48%), Артем Жукович (22%), Игорь Бояркин (30%).'
)
NEW_EXTRA = (
    'В контур сделки входят 282 аптеки во всех субъектах ДФО (кроме '
    'Чукотского АО). Продавцы: Игорь Жукович (48%), Артем Жукович (22%), '
    'Игорь Бояркин (30%).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA
    assert deal['status'] == 'Закрыта', 'ожидался уже исправленный статус'

    print('=== extra: станет ===')
    print(NEW_EXTRA)

    if write:
        deal['extra'] = NEW_EXTRA
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
