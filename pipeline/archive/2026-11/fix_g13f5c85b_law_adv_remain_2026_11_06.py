# -*- coding: utf-8 -*-
"""Карточка g13f5c85b («Рубеж» купил офис у Upside Development): записать
law.adv — Remain названа консультантом сделки.

ПОЧЕМУ РУКАМИ, А НЕ ЧЕРЕЗ review.py. `law.adv` — список целиком (строки
[роль, фирма, описание]), а не один текст, и review.py сверяет `new` с
цитатой как единую дословную строку — для структуры этого не бывает
(тот же случай уже решался разовым скриптом для Citigroup/«РенКап банк»,
pipeline/ingest/fixes_archive/2026-10.json, «поле law.adv — список целиком,
а не одна строка»).

ФАКТ И ГРАНИЦА (docs/card_parties.md, «Команда сделки»; прецедент — та же
компания «Рубеж», карточка gd6ce73ed, логопарк «Внуково 2»: там Коммерсантъ
так же назвал двух консультантов без подтверждения сторон, и это легло в
law.adv). Коммерсантъ прямо пишет: «В компании Remain, которую на рынке
называют консультантом сделки, отказались от комментариев» — это сообщение
издания о рыночной репутации Remain, а не просьба к сторонам подтвердить
роль; сам отказ от комментария — не консультант (docs/card_parties.md), но
здесь утверждение шире отказа. Источник:
https://www.kommersant.ru/doc/9081283

Запуск:
    python3 pipeline/archive/2026-11/fix_g13f5c85b_law_adv_remain_2026_11_06.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_g13f5c85b_law_adv_remain_2026_11_06.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g13f5c85b'
NEW_ADV = [[
    'Консультант сделки',
    'Remain',
    'Коммерсантъ называет компанию консультантом сделки на рынке; в Remain отказались от '
    'комментариев. Источник: https://www.kommersant.ru/doc/9081283',
]]


def main(argv):
    write = '--write' in argv
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        raise SystemExit('%s: карточки нет в очереди' % CARD_ID)
    old = card.get('law', {}).get('adv')
    assert old == [], 'law.adv уже не пуст: %r' % old
    print('%s: law.adv %r -> %r' % (CARD_ID, old, NEW_ADV))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    card.setdefault('law', {})['adv'] = NEW_ADV
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
