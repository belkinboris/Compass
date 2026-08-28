# -*- coding: utf-8 -*-
"""ВТБ/WB Банк (`c51d0bb64`): 28 августа 2026 года первый зампред ВТБ
Дмитрий Пьянов сообщил, что сделка по покупке 5% WB-банка у RWB перенесена
на сентябрь, но параметры допэмиссии под неё принципиально не
пересматривались; причина переноса — управленческие и человеческие ресурсы
партнёра сейчас направлены на решение проблем, связанных с чрезвычайными
событиями (Коммерсантъ со ссылкой на цитату по ТАСС).

Цитата не лежит в тексте старого источника (Forbes) — тот же приём, что и в
прежних правках этого поля: старое значение сохраняется, дописывается новое
предложение со ссылкой на источник.

Запуск: python3 pipeline/fix_vtb_wb_bank_september_timing.py           # проверка
        python3 pipeline/fix_vtb_wb_bank_september_timing.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c51d0bb64'
OLD_CONTEXT = (
    'Статья описывает стратегическое партнерство между ВТБ и Wildberries '
    '(группой RWB) по развитию WB Банка. ВТБ предоставляет готовую '
    'инфраструктуру (розничные отделения, сеть банкоматов, кредитные и '
    'инвестиционные продукты). ВТБ объявил о планах допэмиссии акций.'
)
ADDITION = (
    '28 августа 2026 года первый зампред ВТБ Дмитрий Пьянов сообщил, что '
    'сделка по покупке миноритарной доли в WB-банке и финтех-активах '
    'перенесена на сентябрь, но параметры допэмиссии под неё принципиально '
    'не пересматривались: «Мы не форсируем ее, понимая, что '
    'управленческие, человеческие ресурсы нашего партнера сейчас '
    'направлены на решение проблем, связанных с чрезвычайными событиями».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8910238']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
