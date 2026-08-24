# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gf3a811bd (Умар Кремлев/«АТС-Авто»):
дельта-поиск нашёл, что случилось с предметом сделки ПОСЛЕ покупки —
не рост, а приостановка производства из-за прекращения господдержки,
при «колоссальном» спросе, и разработка собственной программы
финансирования с «Газпромом». Не через `review.py`: источник
(dvizhok.su, от 23 августа 2026) не образует с уже записанным текстом
`eco.context` (из другого материала, версия эксперта о характере
актива) непрерывный кусок.

Источник — читал напрямую (WebFetch, дословная цитата подтверждена):
https://dvizhok.su/business/ryinok-gazomotornogo-topliva-realnost-ne-sovpala-s-otchetami-gazproma

Запуск: python3 pipeline/fix_ats_avto_production_halt_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf3a811bd'

OLD_CONTEXT = (
    '«Актив носит скорее стратегический характер — это выход на '
    'рынок установки метанового ГБО (газобаллонного оборудования.— '
    '«Ъ» ). Либо перевод мощностей «АТС-Авто» на установку ГБО на '
    'пропане, а это заход на потенциально новый рынок за минимальные '
    'вложения»,— полагает он.'
)
CONTEXT_ADDITION = (
    ' Год спустя гендиректор «АТС-Авто» Алексей Сучков сообщил, что '
    'программа производства гибридных битопливных моделей Lada, '
    'работающих на сжатом или компримированном метане (CNG), '
    'приостановлена — из-за изменений в программе государственных '
    'субсидий Минпромторга. При этом, по его словам, спрос на '
    'переоборудованные машины остаётся «колоссальным», и компания '
    'совместно с «Газпромом» разрабатывает собственную программу '
    'финансирования автопроизводителей, не зависящую от поддержки '
    'Минпромторга.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += приостановка производства год '
          f'спустя')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
