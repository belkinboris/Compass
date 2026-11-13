# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m223 (часть 3): чего не умеет review.py.

g4d017d5c («Альфа Строй»/Omni Tower): РИА 23 сентября 2026 года пересказывает сообщение пресс-службы Sense о
  продаже; день самой сделки не назван — дата годом. Где искали второй источник — в заметке приемки.
ga7020b5e («Т-Технологии»/«Точка»): предмет — АО «Точка» (ПРАЙМ: «утвердил оценку 100% АО "Точка" для целей сделки»;
  ComNews: «100% долей в капитале АО "Точка"»), а не ООО «Банк Точка» — профиль предмета заменен на профиль
  АО «Точка», текстовый предмет «Банк «Точка»» снят. eco.sum — то же, что sum: 84,8 млрд ₽ — оценка 100% АО
  «Точка» советом директоров покупателя «для целей сделки», то есть цена этой сделки за 100%. Цена за акцию —
  8,48 млн ₽.

    python3 pipeline/archive/2026-11/reread_oneoff_m223c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m223c', '2026-11-12'
RIA_OMNI = 'https://realty.ria.ru/20260923/stroj-2119806492.html'
PRIME = 'https://1prime.ru/20261001/t-tehnologija-873838697.html'
Q_PRICE = ('"Совет директоров "Т-Технологий" утвердил оценку 100% АО "Точка" для целей сделки в размере 84,8 '
           'миллиарда рублей (исходя из стоимости одной обыкновенной акции АО "Точка" в размере 8,48 миллиона '
           'рублей)"')
SEARCHED = ('РИА Недвижимость (23 сентября 2026, со ссылкой на пресс-службу Sense и брокера сделки); поиск «Альфа '
            'Строй» Omni Tower, «Sense» Omni Tower продажа этажа, сайт проекта Omni Tower, Telegram-каналы о '
            'коммерческой недвижимости Москвы, пресс-релизы брокеров — второго сообщения и ИНН покупателя не нашлось.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    c = by['g4d017d5c']
    if c['date'] != '2026':
        assert c['date'] == '2026-09-23', c['date']
        c['date'] = '2026'
        c.pop('date_basis', None)
        fact_edit_guard.log(c, 'date', '2026', 'МОСКВА, 23 сен - РИА Недвижимость. Строительная компания "Альфа Строй" '
                            'купила этаж … О продаже площадей … сообщила пресс-служба девелопера проекта Sense. — день '
                            'сделки не назван, 23 сентября — день сообщения', RIA_OMNI, BY, DAY)
        n += 1
    notes = c.setdefault('accepted_notes', {})
    if notes.get('searched') != SEARCHED:
        notes['searched'] = SEARCHED
        n += 1
    c = by['ga7020b5e']
    if c.get('target') != 'g599e8557':
        assert c.get('target') == 'g09ccbaca', c.get('target')
        c['target'] = 'g599e8557'
        c.setdefault('retracted', {}).setdefault('target', []).append('g09ccbaca')
        fact_edit_guard.log(c, 'target', 'g599e8557', Q_PRICE, PRIME, BY, DAY)
        n += 1
    if c.get('asset'):
        assert c['asset'] == 'Банк «Точка»', c['asset']
        del c['asset']
        fact_edit_guard.log(c, 'asset', None, Q_PRICE + ' — предмет профилем АО «Точка»', PRIME, BY, DAY)
        n += 1
    if c['eco'].get('sum') != '84,8 млрд ₽':
        assert c['eco']['sum'] == '84,8 млрд ₽ (оценка 100% «Точки»)', c['eco']['sum']
        assert c['sum'] == '84,8 млрд ₽', c['sum']
        c['eco']['sum'] = '84,8 млрд ₽'
        fact_edit_guard.log(c, 'eco.sum', '84,8 млрд ₽', Q_PRICE, PRIME, BY, DAY)
        n += 1
    if c['eco'].get('price_per_share') != '8 480 000 ₽ за акцию':
        c['eco']['price_per_share'] = '8 480 000 ₽ за акцию'
        n += 1
    if c.get('sum_basis') != 'disclosed':
        c['sum_basis'] = 'disclosed'
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
