# -*- coding: utf-8 -*-
"""Карточка `g9368796b` (Александр Калин утратил контроль над 6,51% капитала
«Яндекса», Ведомости/Frank Media, 25 ноября 2026): `sum`/`eco.sum` и `status`
— не через `review.py`.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py.
- `sum`/`eco.sum`: ни Ведомости, ни Frank Media не называют цену и вообще не
  говорят о деньгах — раскрытие информации сообщает только про утрату права
  распоряжаться голосами/акциями. `sum_is_supported()` ждет число и валюту в
  цитате; у «Не раскрыта» их нет, поэтому поле снимается одноразовым
  скриптом с `assert`, а не правкой из таблицы FIXES (docs/card_money.md,
  «После правки или снятия суммы» и прецедент
  `pipeline/fix_g6184df02_valtri_sum_adv_2026_11_25.py`).
- `status`: событие уже произошло и подтверждено точной датой (11 ноября
  2026) и раскрытием информации — это не «Обсуждается» (там нет никаких
  переговоров, сделка не обсуждается, а состоялась), поэтому правильный
  статус — «Закрыта». Но слова источников («утратил право распоряжаться»,
  «перестал владеть», «перестал участвовать в эмитенте») не входят в
  словарь `STATUS_WORDS['Закрыта']` («закрыл», «купил», «перешл» и т. п.) —
  `review.py` отказал бы в правке механически, хотя смысл однозначен
  (docs/card_status_dates.md, «Когда review.py отказывает»: статус меняется
  одноразовым скриптом с `assert` на исходное значение, как и правка дат в
  другой год).

Запуск:
    python3 pipeline/fix_g9368796b_sum_status_2026_11_25.py            # сухой прогон
    python3 pipeline/fix_g9368796b_sum_status_2026_11_25.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'g9368796b'
SUM_VALUE = 'Не раскрыта'
OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточки нет в pending.json (принята или удалена?)' % CARD_ID)

    already = (card.get('sum') == SUM_VALUE and card.get('eco', {}).get('sum') == SUM_VALUE
               and card.get('status') == NEW_STATUS)
    if already:
        print('%s: уже применено (sum=%r, status=%r)' % (CARD_ID, SUM_VALUE, NEW_STATUS))
        return 0

    assert card.get('sum') is None, 'состояние sum изменилось: %r' % card.get('sum')
    assert card.get('eco', {}).get('sum') == '—', (
        'состояние eco.sum изменилось: %r' % card.get('eco', {}).get('sum'))
    assert card.get('status') == OLD_STATUS, 'состояние status изменилось: %r' % card.get('status')

    print('%s: sum None -> %r' % (CARD_ID, SUM_VALUE))
    print('%s: eco.sum %r -> %r' % (CARD_ID, '—', SUM_VALUE))
    print('%s: status %r -> %r' % (CARD_ID, OLD_STATUS, NEW_STATUS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточка пропала при повторном чтении' % CARD_ID)
    assert card.get('sum') is None, 'sum изменился параллельно — остановитесь'
    assert card.get('eco', {}).get('sum') == '—', 'eco.sum изменился параллельно — остановитесь'
    assert card.get('status') == OLD_STATUS, 'status изменился параллельно — остановитесь'

    card['sum'] = SUM_VALUE
    card['eco']['sum'] = SUM_VALUE
    card['status'] = NEW_STATUS
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: static/data/pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
