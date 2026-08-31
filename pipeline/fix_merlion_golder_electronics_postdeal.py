# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g8cbf31b0
(Merlion купил Golder Electronics — Vitek, Rondell, Maxwell, Coolfort) —
`eco.target_fin` стоял прочерком, судьба флагманского бренда VITEK после
сделки не отражена.

Судьба бренда VITEK — проверено лично прямым WebFetch (Sostav.ru): «В
2024 году VITEK вошел в портфель собственных торговых марок группы
компаний Merlion, что стало отправной точкой для глубокого обновления
бренда — от позиционирования до дизайна упаковки», «В 2025 году VITEK
выходит в новые сегменты — крупную бытовую, а также климатическую
технику».

Финансы цели — проверено лично прямым WebFetch (audit-it.ru): в 2024
году (первый год под новым владельцем) — убыток 149 млн руб. при
выручке около 3,8 млрд руб.; в 2025 году — разворот в прибыль (38,9 млн
руб.) при снижении выручки на 31,7% до 2,6 млрд руб.; совокупные активы
на 31.12.2025 выросли в 3,1 раза до 14,4 млрд руб.

НЕ ВКЛЮЧЕНО: дальнейшая судьба продавца Андрея Деревянченко — поисковая
выдача путает его с однофамильцами (боксёр, актёр), ничего достоверного
не нашлось; судьба брендов Rondell/Maxwell/Coolfort по отдельности — на
сайте rondell.ru свежих материалов за 2025-2026 год нет, а найденное
поисковиком упоминание участия в кулинарном чемпионате не подтвердилось
прямой проверкой (сам чемпионат бренд Rondell не упоминает) — не
использовано; выручка Merlion за 2024 год «26 млрд руб. прибыли» из
сниппета поисковика — противоречит порядку величины из прямого чтения
audit-it (2,7 млрд руб. за 2025 год), похоже на ошибку суммаризатора,
не переносится.

Запуск: python3 pipeline/fix_merlion_golder_electronics_postdeal.py
        python3 pipeline/fix_merlion_golder_electronics_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8cbf31b0'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'В 2024 году (первый год под новым владельцем) — убыток 149 млн '
    'руб. при выручке около 3,8 млрд руб.; в 2025 году — разворот в '
    'прибыль (38,9 млн руб.) при снижении выручки на 31,7% до 2,6 млрд '
    'руб.; совокупные активы на 31.12.2025 выросли в 3,1 раза до 14,4 '
    'млрд руб. (audit-it.ru).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В 2024 году VITEK вошёл в портфель собственных торговых марок '
    'Merlion, что стало отправной точкой для глубокого обновления '
    'бренда — от позиционирования до дизайна упаковки. В 2025 году '
    'VITEK вышел в новые сегменты — крупную бытовую и климатическую '
    'технику (Sostav.ru).'
)

NEW_SRC = [
    ['Sostav.ru', 'https://www.sostav.ru/publication/25-let-vitek-kak-perezapuskaetsya-rossijskij-brend-bytovoj-tekhniki-79293.html'],
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1027705002588_ooo-golder-elektroniks'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
