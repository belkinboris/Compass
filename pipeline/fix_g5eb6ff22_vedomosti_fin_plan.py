# -*- coding: utf-8 -*-
"""Карточка `g5eb6ff22` (Росатом/ГК «Дело») — `eco.fin` дополнен: «Ведомости»
назвали планы на замещение заёмных средств партнёрскими деньгами (деталь,
которой не было у «Интерфакса»). Разовый скрипт — другой источник, чем уже
стоящий в поле текст.

Источник: https://www.vedomosti.ru/business/articles/2026/10/07/1235090-rosatom-vikupil

    python3 pipeline/fix_g5eb6ff22_vedomosti_fin_plan.py           # показать
    python3 pipeline/fix_g5eb6ff22_vedomosti_fin_plan.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g5eb6ff22'

OLD_FIN = (
    'Для финансирования планировавшегося выкупа Шишкаревым доли «Росатома» '
    'рассматривались бридж-кредит в российском банке и партнёрство с '
    '«Ростехом»; от этого варианта Шишкарев впоследствии отказался. Сам '
    'выкуп «Росатом» профинансировал заёмными средствами: пресс-служба '
    'госкорпорации сообщила «Интерфаксу», что финансовые условия сделки не '
    'раскрываются, а цена соответствует условиям, установленным при запуске '
    'процедуры «русской рулетки», и в ходе её реализации не менялась.'
)

ADDED = ('«Ведомостям» представитель «Росатома» уточнил, что заёмные '
         'средства выкупа предполагается впоследствии заместить '
         'партнёрскими деньгами.')

QUOTE = ('Для выкупа были использованы заемные средства, которые '
         'предполагается заместить партнерскими деньгами, сказал '
         '"Ведомостям" представитель "Росатома"')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert deal['eco']['fin'] == OLD_FIN, deal['eco']['fin']
    deal['eco']['fin'] = OLD_FIN + ' ' + ADDED
    deal['src'] = list(deal.get('src') or [])
    url = 'https://www.vedomosti.ru/business/articles/2026/10/07/1235090-rosatom-vikupil'
    if not any(len(s) > 1 and s[1] == url for s in deal['src']):
        deal['src'].append(['Ведомости', url])
    print('eco.fin дополнен источником Ведомости (план замещения долга партнёрскими деньгами)')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
