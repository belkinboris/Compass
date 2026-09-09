# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `gacc757b6`
(«Selectel: проданы 10% акций структурам Геворка Вермишяна и 4,852% —
Андрею Голухову», добавлена в базу 3 августа 2026, полностью обыскана в
тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл продавца — карточка
несла пустое поле `seller`, хотя источник, УЖЕ стоящий в `src`
(interfax.ru/business/1024079), дочитан глубже и прямо называет
продавца. Личный WebFetch подтвердил дословно: «10% были куплены у
материнской компании – Servertech» и «член совета директоров АО
«Селектел» Андрей Голухов приобрел 4,852% компании у Servertech» — в
обоих случаях продавец один и тот же, Servertech Holding Ltd. (сам
мажоритарный акционер Selectel).

Отдельно, саб-агент нашёл крупную, более позднюю и отдельную сделку —
29 декабря 2025 года СП «Т-Технологий»/«Интеррос» («Каталитик Пипл»)
купило 25% Selectel за 16 млрд ₽ у действующих акционеров. Это не
дополнение к данной карточке (другая дата, другие стороны, другой
масштаб), а кандидат на отдельную карточку — вынесено в CLAUDE.md
«Известные проблемы» для приточной рутины.

Запуск:
    python3 pipeline/fix_selectel_vermishyan_seller.py            # сухой прогон
    python3 pipeline/fix_selectel_vermishyan_seller.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_SELLER = None
NEW_SELLER = 'Servertech Holding Ltd.'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gacc757b6']

    assert d.get('seller') == OLD_SELLER, \
        'gacc757b6 seller уже занят: %r' % (d.get('seller'),)

    print('gacc757b6: seller None -> "Servertech Holding Ltd." '
          '(подтверждено interfax.ru/business/1024079)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['seller'] = NEW_SELLER

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
