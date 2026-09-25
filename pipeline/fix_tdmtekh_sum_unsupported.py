# -*- coding: utf-8 -*-
"""Качество, 25 сентября 2026 (ежедневный прогон 21:37 МСК) — подтверждение
фактов двумя чтениями, карточка `g7fac547e` (Т2 Мобайл / «ТДМ ТЕХ»). Оба
независимых читателя (A и B) прочитали единственный источник карточки
(АК&М) и не нашли в нём никакой суммы сделки — только факт перехода
85% доли, дату и стороны. Прямая проверка кэша подтвердила: слово «млрд» и
цифра «5,95» в тексте статьи не встречаются вовсе.

Откуда взялась цифра «5,95 млрд ₽» в карточке — не установлено (карточка
помечена `auto`/`promoted_from_bulk`, то есть заведена ранним автоматическим
конвейером без такой же строгой проверки, как у притока сейчас). Раз
источник её не подтверждает, поле снимается — по тому же механизму, что и
у `g5599430f` (`retracted`), чтобы `enrich.py` не восстановил её тихо
повторно, если та же цифра попадётся в ленте ещё раз.

Запуск:
    python3 pipeline/fix_tdmtekh_sum_unsupported.py            # сухой прогон
    python3 pipeline/fix_tdmtekh_sum_unsupported.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

WRONG_SUM = '5,95 млрд ₽'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g7fac547e']
    assert len(target) == 1, target
    card = target[0]
    assert card['sum'] == WRONG_SUM, repr(card['sum'])
    assert card['eco']['sum'] == WRONG_SUM, repr(card['eco']['sum'])
    card['sum'] = None
    card['eco']['sum'] = '—'
    card.setdefault('retracted', {}).setdefault('sum', [])
    if WRONG_SUM not in card['retracted']['sum']:
        card['retracted']['sum'].append(WRONG_SUM)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Сумма g7fac547e снята (источник её не подтверждает) и записана в retracted. ЗАПИСАНО.')
    else:
        print('Сухой прогон: снял бы сумму и записал retracted. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
