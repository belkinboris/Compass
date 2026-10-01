# -*- coding: utf-8 -*-
"""Качество, 1 октября 2026 (ежедневный прогон 21:37 МСК) — месячная
очередь дочитывания (третий уровень), карточка `g0ff8c5c4` (Сбербанк
купил два бизнес-центра Summit Towers в Нью-Дели). Карточка несла
`sum: "Не раскрыта"` — но сумма ЕСТЬ, просто не в рублях: индийская
деловая пресса (не входившая в `src` карточки) прямо называет цену в
рупиях, а также механизм покупки (конкурентный аукцион).

Одноразовый скрипт, а не запись в FIXES-таблице `review.py`: источник
(millenniumpost.in) — на английском, а поле на сайте — русское; `new`
обязано быть ДОСЛОВНОЙ цитатой источника (review.py: `flat(new) in
flat(quote)`), перевод этому условию по определению не удовлетворяет —
тот же класс исключения, что у смены года в дате или исправления имени
внутри абзаца.

Цитата (дословно, английский оригинал — для проверки честности перевода):
    "The two towers comprise about 5.17 lakh sq ft of super built-up area
    and have a sale value of more than Rs 2,000 crore. SBER Bank acquired
    them through a competitive e-auction in April 2026, becoming the
    largest single buyer at the project."
    — https://www.millenniumpost.in/business/nbcc-hands-over-two-bharat-business-park-towers-to-sber-677235

Рублёвый эквивалент НЕ досчитывается — курс рупии на апрель 2026 года
источник не называет, а свой курс искать и подставлять значило бы
досочинять то, чего нет в источнике.

Запуск:
    python3 pipeline/fix_summit_towers_sum_and_struct_2026_10_01.py            # сухой прогон
    python3 pipeline/fix_summit_towers_sum_and_struct_2026_10_01.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_SUM = 'Не раскрыта'
NEW_SUM = 'более 2000 крор рупий (крор = 10 млн рупий, то есть свыше ₹20 млрд)'

OLD_STRUCT = '—'
NEW_STRUCT = ('Сбербанк приобрёл обе башни через конкурентный аукцион в апреле '
              '2026 года, став крупнейшим отдельным покупателем в этом '
              'комплексе (Bharat Business Park).')

SRC_ENTRY = ['Millennium Post',
             'https://www.millenniumpost.in/business/nbcc-hands-over-two-bharat-business-park-towers-to-sber-677235']


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g0ff8c5c4']
    assert len(target) == 1, target
    card = target[0]
    assert card['sum'] == OLD_SUM, repr(card['sum'])
    assert card['eco']['sum'] == '—', repr(card['eco']['sum'])
    assert card['law']['struct'] == OLD_STRUCT, repr(card['law']['struct'])
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    card['law']['struct'] = NEW_STRUCT
    if not any(len(s) > 1 and s[1] == SRC_ENTRY[1] for s in card.get('src') or []):
        card['src'].append(SRC_ENTRY)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g0ff8c5c4: sum/eco.sum/law.struct обновлены, источник добавлен. ЗАПИСАНО.')
    else:
        print('Сухой прогон: поправил бы sum/eco.sum/law.struct карточки g0ff8c5c4. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
