# -*- coding: utf-8 -*-
"""Пост «Циана» и задержка двух постов (владелец, 6 ноября 2026).

g9b4c2e71: текст поста — тот, что владелец прислал в консоли (`post_override`),
плюс по его просьбе «добавь ещё в пост цену на акцию и всего количество акций»
(без премии — «не пиши, что выше»): 993,05 ₽ за акцию (пресс-релиз
«Т-Технологий», Интерфакс), около 77,7 млн акций (проспект ценных бумаг
2025 года: «77 млн 670 тыс.»; сходится с расчетом 77,1 млрд ₽ за все акции по
цене предложения). Разметка «<b>Продавц</b>ы<b>:</b>» из правки в Telegram
сведена в «<b>Продавцы:</b>» — текст тот же.

g8eb9ed40, g8317fa58: «посты подтвердил, но давай их не выкладывать сегодня» —
post_not_before = 2026-11-07 (send_telegram.held_until).

    python3 pipeline/archive/2026-11/fix_cian_post_and_holds_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD_SELLER = '<b>Продавц</b>ы<b>:</b> текущие акционеры Циан\n<b>Предмет:</b> Циан\n'
NEW_SELLER = ('<b>Продавцы:</b> текущие акционеры Циан\n<b>Предмет:</b> Циан\n'
              '<b>Цена:</b> 993,05 ₽ за акцию\n<b>Всего акций:</b> около 77,7 млн\n')


def apply(base):
    D = {d['id']: d for d in base['deals']}
    c = D['g9b4c2e71']
    po = c['post_override']
    assert po.count(OLD_SELLER) == 1, po
    c['post_override'] = po.replace(OLD_SELLER, NEW_SELLER)
    for i in ('g8eb9ed40', 'g8317fa58'):
        assert i not in (base.get('telegram_posts') or {}) or base['telegram_posts'][i] is None, i
        D[i]['post_not_before'] = '2026-11-07'


def main(argv):
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base)
    print('g9b4c2e71: + цена и число акций в посте; g8eb9ed40, g8317fa58: пост не раньше 7 ноября')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
