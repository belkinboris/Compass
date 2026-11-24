# -*- coding: utf-8 -*-
"""g9b852635: пост одобрен владельцем до правки заголовка (знак валюты ₽
вместо слова «рублей») и до уточнения eco.sum «по данным Telegram-каналов» —
post_preview несет СТАРЫЙ текст («...8,1 млрд рублей», «8,1 млрд ₽ (по
данным Telegram-каналов)» в поле «Сумма», тогда как шапка не совпадает со
знаком заголовка). send_telegram.py отдает post_preview приоритет перед
автоформатом — без снятия устаревший текст ушел бы подписчикам.

Снимаем post_preview/post_approved, чтобы карточка собрала пост заново и
прошла одобрение владельца снова — тот же прием, что
fix_ge1c5f194_resend_2026_11_24.py.

Запуск:
    python3 pipeline/fix_g9b852635_resend_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9b852635_resend_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g9b852635'


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    n = 0
    for k in ('post_preview', 'post_approved'):
        if k in card:
            card.pop(k)
            n += 1
    return n


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    n = apply(data)
    print('снято полей: %d' % n)
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
