# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g4c98dcba`
(«SPO "Группа Астра": продано 21 млн акций по 555 ₽», добавлена в базу
3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл продавца — карточка не
называла его вовсе. Личный WebFetch (interfax.ru/business/956715,
19 апреля 2024) подтвердил дословно: «Реализованный в ходе SPO пакет
акций был предоставлен основным акционером «Группы Астра» Денисом
Фроловым» — 21 млн акций составили 10% уставного капитала.

Это факт именно об АПРЕЛЬСКОМ SPO 2024 года (публичное размещение
существующего пакета Фролова на бирже) — НЕ путать с отдельным, более
поздним сюжетом о продаже его личного пакета холдингу Т1 в мае 2026 года
(карточка `g9d9e7ab6`, переговоры о стратегическом инвесторе). Оба
события реальны, но это два разных факта об одном и том же человеке.

Саб-агент также нашёл: в августе 2024 года акции ASTR включены в первый
котировальный список и базу расчёта индексов Московской биржи (в том
числе Индекс МосБиржи) — добавлено в `eco.context`. Организатор/
андеррайтер SPO по-прежнему нигде не назван.

Запуск:
    python3 pipeline/fix_astra_spo_seller_and_index.py            # сухой прогон
    python3 pipeline/fix_astra_spo_seller_and_index.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_SELLER = None
NEW_SELLER = 'Денис Фролов'

OLD_ECO_CONTEXT = (
    'Сформирован пул инвесторов из крупнейших российских управляющих '
    'компаний, других институциональных инвесторов и розничных '
    'инвесторов.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' В августе 2024 года акции компании включены в первый '
    'котировальный список и базу расчёта индексов Московской биржи, '
    'включая Индекс МосБиржи.'
)

NEW_SRC = ['Интерфакс', 'https://www.interfax.ru/business/956715']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g4c98dcba']

    assert d.get('seller') == OLD_SELLER, \
        'g4c98dcba seller уже занят: %r' % (d.get('seller'),)
    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'g4c98dcba eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g4c98dcba: seller None -> "Денис Фролов"; eco.context дополнен '
          '(включение в индексы МосБиржи); добавлен источник interfax.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['seller'] = NEW_SELLER
    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
