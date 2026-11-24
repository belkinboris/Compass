# -*- coding: utf-8 -*-
"""Профиль gea897ee6 (УК «Либра Капитал», покупатель в ge1c5f194) — второе
чтение нашло, что «Обзор»/law.struct честно помечают подконтрольность
структурам Лисина как «по неофициальным данным» (Коммерсантъ не называет
прямого подтверждения — компания на запрос не ответила), а desc профиля,
который формирует строку поста, несет это фактом без оговорки. Профиль
используется только этой карточкой (проверено — безопасно править без
mass_edit_guard).

Запуск:
    python3 pipeline/fix_gea897ee6_unofficial_hedge_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_gea897ee6_unofficial_hedge_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CID = 'gea897ee6'
OLD_DESC = 'Управляющая компания, подконтрольная структурам Владимира Лисина. Юрлицо — АО «УК «Либра Капитал»».'
NEW_DESC = 'Управляющая компания; по неофициальным данным, подконтрольна структурам Владимира Лисина. Юрлицо — АО «УК «Либра Капитал»».'


def apply(data):
    c = data['companies'][CID]
    assert c['desc'] == OLD_DESC, 'desc уже изменен кем-то другим'
    c['desc'] = NEW_DESC


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('desc обновлен:', data['companies'][CID]['desc'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
