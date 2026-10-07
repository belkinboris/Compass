# -*- coding: utf-8 -*-
"""Карточка `g5eb6ff22` (Росатом/ГК «Дело») — `eco.fin` дополнен: чем
профинансировал выкуп сам «Росатом» (в поле раньше было только про
отказ Шишкарева от бридж-кредита). Источник — «Интерфакс», цитата
дословная (прямая речь пресс-службы «Росатома»).

Разовый скрип, не таблица FIXES review.py: добавляемое предложение из
ДРУГОГО источника, чем уже стоящий в поле текст, — объединять две
цитаты в одно поле `review.py` не даёт (дословность целого поля), поэтому
правка — прямая, с assert на старое значение, как и другие разовые
правки этой карточки.

Источник: https://www.interfax.ru/russia/1120839

    python3 pipeline/fix_g5eb6ff22_rosatom_financing.py           # показать
    python3 pipeline/fix_g5eb6ff22_rosatom_financing.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g5eb6ff22'

OLD_FIN = ('Для финансирования планировавшегося выкупа Шишкаревым доли '
           '«Росатома» рассматривались бридж-кредит в российском банке и '
           'партнёрство с «Ростехом»; от этого варианта Шишкарев '
           'впоследствии отказался.')

ADDED = ('Сам выкуп «Росатом» профинансировал заёмными средствами: '
         'пресс-служба госкорпорации сообщила «Интерфаксу», что '
         'финансовые условия сделки не раскрываются, а цена соответствует '
         'условиям, установленным при запуске процедуры «русской рулетки», '
         'и в ходе её реализации не менялась.')

QUOTE = ('Финансовые условия сделки мы не обсуждаем. Можем подтвердить, что '
         'цена соответствует условиям, установленным при запуске '
         'предусмотренной соглашением процедуры, и в ходе ее реализации не '
         'менялась, - сообщил "Росатом". - Для реализации выкупа были '
         'использованы заемные средства')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert deal['eco']['fin'] == OLD_FIN, deal['eco']['fin']
    deal['eco']['fin'] = OLD_FIN + ' ' + ADDED
    deal['src'] = list(deal.get('src') or [])
    url = 'https://www.interfax.ru/russia/1120839'
    if not any(len(s) > 1 and s[1] == url for s in deal['src']):
        deal['src'].append(['Интерфакс', url])
    print('eco.fin дополнен источником Интерфакс (заёмное финансирование выкупа)')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
