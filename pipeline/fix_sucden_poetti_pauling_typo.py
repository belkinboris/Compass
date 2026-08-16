# -*- coding: utf-8 -*-
"""Дочитывание REVISION_BRIEF, партия 6: опечатка «Pauling» вместо «Paulig».

`eco.context` карточки gmru-sucden-poetti называет финского производителя
кофе «Pauling» — опечатка, унаследованная из источника mergers.ru/Коммерсантъ
(тот же дефект есть и в самой статье-источнике). Верное имя компании —
Paulig (OY Gustav Paulig Ab); независимый источник (abn.agency) пишет верно:
«ООО «Милфудс» до мая 2022 года носило название «Паулиг Рус» и находилось
под контролем OY Gustav Paulig Ab».

Найдено саб-агентом партии 6 (16 августа 2026) при перепроверке источника.
Не через review.py: это исправление опечатки в уже написанном тексте, а не
перенос новой цитаты — дословная модель review.py тут не подходит (родня
`fix_leiblpak_extra_quote.py`, партия 5).

Запуск:
    python3 pipeline/fix_sucden_poetti_pauling_typo.py            # сухой прогон
    python3 pipeline/fix_sucden_poetti_pauling_typo.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_CONTEXT = (
    'ООО «Милфудс» существует с 2008 года. В 2022 году компания выкупила '
    'российские активы финского производителя кофе Pauling. На его '
    'мощностях в Твери запустили линейку Poetti. Викас Сои ранее был '
    'главой российской Milagro Beverage Company (бренды кофе Milagro, '
    'D’Arte, Belagio). Активы этой компании, вероятно, вошли в '
    'периметр «Милфудс». Сейчас ей принадлежат права на официальный сайт '
    'и бренд Milagro.')
NEW_CONTEXT = OLD_CONTEXT.replace('Pauling', 'Paulig')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'gmru-sucden-poetti')
    current = card['eco']['context']
    assert current == OLD_CONTEXT, 'eco.context уже другой: %r' % current
    assert NEW_CONTEXT != OLD_CONTEXT
    print('%s  gmru-sucden-poetti.eco.context: «Pauling» -> «Paulig»'
          % ('ПИШЕМ' if write else 'ПРАВИМ (сухой прогон)'))
    if write:
        card['eco']['context'] = NEW_CONTEXT
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1,
                   ensure_ascii=False)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
