# -*- coding: utf-8 -*-
"""Карточка `g6184df02` («ИТ-компания приобрела четыре этажа под штаб-квартиру
в деловом центре Valtri на Белорусской», CNews, 25 ноября 2026): `sum`/`eco.sum`
и `law.adv` — не через `review.py`.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py.
- `sum`/`eco.sum`: цена сделки ни в одном источнике не названа (ни в CNews,
  ни в найденных при поиске публикациях о других сделках в том же проекте —
  CRE 99480/99513, office-news.ru). `sum_is_supported()` ждет число и валюту
  в цитате; у «Не раскрыта» их нет, поэтому поле снимается одноразовым
  скриптом с `assert`, а не правкой из таблицы FIXES (docs/card_money.md,
  «После правки или снятия суммы»).
- `law.adv`: роль «Консультант сделки» не лежит дословно в цитате (цитата
  называет агентство OF.ru консультантом сделки, но ярлык роли — наша
  классификация, не слово источника) — тот же класс, что у
  `fixes/g0966b2e2_jll_ibc_2026_11_14.py` (ALUMNI Partners/JLL): запись
  напрямую в pending.json, мимо `review.py`.

Запуск:
    python3 pipeline/fix_g6184df02_valtri_sum_adv_2026_11_25.py            # сухой прогон
    python3 pipeline/fix_g6184df02_valtri_sum_adv_2026_11_25.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'g6184df02'
SUM_VALUE = 'Не раскрыта'
LAW_ADV_ROW = ['Консультант сделки', 'OF.ru',
               'Источник называет агентство OF.ru консультантом (брокером) сделки; сторону, '
               'которую оно представляло, источник не уточняет. Источник: '
               'https://www.cnews.ru/news/line/2026-11-25_it-kompaniya_priobrela_chetyre']


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточки нет в pending.json (принята или удалена?)' % CARD_ID)

    already = (card.get('sum') == SUM_VALUE and card.get('eco', {}).get('sum') == SUM_VALUE
               and LAW_ADV_ROW in (card.get('law', {}).get('adv') or []))
    if already:
        print('%s: уже применено (sum=%r, law.adv содержит OF.ru)' % (CARD_ID, SUM_VALUE))
        return 0

    assert card.get('sum') is None, 'состояние sum изменилось: %r' % card.get('sum')
    assert card.get('eco', {}).get('sum') == '—', (
        'состояние eco.sum изменилось: %r' % card.get('eco', {}).get('sum'))
    assert card.get('law', {}).get('adv') == [], (
        'состояние law.adv изменилось: %r' % card.get('law', {}).get('adv'))

    print('%s: sum None -> %r' % (CARD_ID, SUM_VALUE))
    print('%s: eco.sum %r -> %r' % (CARD_ID, '—', SUM_VALUE))
    print('%s: law.adv [] -> [%r]' % (CARD_ID, LAW_ADV_ROW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    card['sum'] = SUM_VALUE
    card['eco']['sum'] = SUM_VALUE
    card['law']['adv'] = [LAW_ADV_ROW]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: static/data/pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
