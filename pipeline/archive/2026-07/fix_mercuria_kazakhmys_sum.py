# -*- coding: utf-8 -*-
"""Разовая правка g15bee2cf (Mercuria / «Казахмыс»): сумма финансирования.

ЧТО НЕВЕРНО. Карточка (заголовок, `sum`, `eco.sum`) несла «$1,5 млрд» — ни
один из ~10 независимых источников, найденных саб-агентом партии 5
REVISION_BRIEF (Bloomberg через mining.com, все казахстанские СМИ —
kz.kursiv.media, nationalbusiness.kz, forbes.kz — и материалы Mercuria через
MINEX Forum за январь, март, май-июнь 2026), не называет $1,5 млрд. Все
единогласно называют $1,2 млрд:

    «Mercuria Energy Group Ltd. is lending $1.2 billion to help fund the
    buyout of major Kazakh copper producer Kazakhmys, the latest in a
    breakneck series of deals from the trading house that's rapidly
    becoming a major force in metals.»
    https://www.mining.com/web/mercuria-redoubles-metals-push-with-1-2-billion-kazakh-deal/

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Правка меняет ТРИ поля разом (title, sum,
eco.sum), а `title` вообще не входит в модель review.py (таблица FIXES
правит только поля карточки внутри `card`, не заголовок). Кроме того,
основной источник — на английском, а формат суммы в базе — русский
(«$1,2 млрд»), то есть дословного переноса не получится в принципе; это
управляемая, проверенная фактом правка, а не перенос цитаты.

Запуск:
    python3 pipeline/fix_mercuria_kazakhmys_sum.py            # сухой прогон
    python3 pipeline/fix_mercuria_kazakhmys_sum.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g15bee2cf'
OLD_TITLE = 'Предоплатное финансирование Mercuria Energy Group группе «Казахмыс» на $1,5 млрд'
NEW_TITLE = 'Предоплатное финансирование Mercuria Energy Group группе «Казахмыс» на $1,2 млрд'
OLD_SUM = '$1,5 млрд'
NEW_SUM = '$1,2 млрд'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['title'] == OLD_TITLE, 'заголовок карточки уже другой'
    assert deal['sum'] == OLD_SUM, 'sum карточки уже другое'
    assert deal['eco']['sum'] == OLD_SUM, 'eco.sum карточки уже другое'

    print('БЫЛО:', OLD_TITLE, '|', OLD_SUM)
    print('СТАНЕТ:', NEW_TITLE, '|', NEW_SUM)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['title'] = NEW_TITLE
    deal['sum'] = NEW_SUM
    deal['eco']['sum'] = NEW_SUM
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
