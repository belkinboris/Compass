# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gmru-psb-tpk-chelyabinsk` («ПСБ выставил на продажу компании, владеющие
двумя ТРК в Челябинске», Обсуждается) — карточка уже отслеживала три
неудачных раунда торгов до 5 августа 2026 года и объявление четвёртого
раунда (7 августа, торги 17 августа), но сам исход четвёртого раунда не
был записан.

Проверено ЛИЧНО прямым WebFetch (дословная цитата):
- 74.ru/text/business/2026/08/17/76584242/: «Победителем стало ООО
  «Центр инжиниринговых услуг при проектировании и строительстве»»
  (Санкт-Петербург); «Цена продажи составила 6 082 198 500 рублей»;
  владелец и гендиректор компании-покупателя — Тимофей Белов; выручка
  за 2025 год — 50 млн ₽, чистая прибыль — 4,6 млн ₽; дата публикации —
  17 августа 2026 года.

Независимо подтверждено WebSearch по трём другим изданиям (совпадают в
цифрах и имени покупателя): mgorsk.ru (тот же материал, зеркало 74.ru),
ura.news/news/1053119054 («Кто купил ТРК «Родник» и «Алмаз» в
Челябинске: ЦИУПС»), fedpress.ru/news/74/economy/3448326 — все называют
ЦИУПС/Тимофея Белова победителем и сумму ~6,08 млрд ₽; ura.news и
fedpress.ru также подтверждают, что тот же покупатель ранее приобрёл
национализированный отель Radisson Blu в Челябинске за 1,342 млрд ₽ —
это его вторая такая покупка.

Единый лот включал ООО «Родник» и УК «Содействие» (сами ТРК «Родник» и
«Алмаз» управляются этими компаниями, а не являются отдельными
юрлицами) — предмет сделки не меняется, меняется только исход торгов.

Профиля компании для ЦИУПС/Белова в базе нет — заводить его ради одной
названной сделки не стали (родня правила «лишний профиль ради одной
стороны не стоит»); имя покупателя записано текстом (`buyer_name`).
Решение, заводить ли профиль (у покупателя уже минимум две сделки —
Radisson Blu и это), оставлено притоку.

Поле `eco.context` уже прошло вычитку (`proofread_absorbed`) — за
основу слияния взят ТЕКУЩИЙ (уже вычитанный) текст поля, а не старый
`new` записи FIXES; сама запись (`batch_deep_2026_r6.py`) обновлена тем
же приёмом.

`seller`/`title`/`target`-структура карточки НЕ тронуты.

Запуск: python3 pipeline/fix_psb_chelyabinsk_trk_auction_closed.py
        python3 pipeline/fix_psb_chelyabinsk_trk_auction_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-psb-tpk-chelyabinsk'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2026-07-30'
NEW_DATE = '2026-08-17'

OLD_SUM = None
NEW_SUM = '6 082 198 500 ₽'

OLD_BUYER_NAME = None
NEW_BUYER_NAME = 'ООО «Центр инжиниринговых услуг при проектировании и строительстве» (Тимофей Белов)'

OLD_ECO_SUM = '—'
NEW_ECO_SUM = NEW_SUM

OLD_ECO_CONTEXT = (
    'Росимущество выставило на торги четыре актива холдинга «Макфа». '
    'Холдинг основал бывший губернатор Челябинской области Михаил '
    'Юревич, в 2024 году «Макфа» национализирована.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Четвёртый раунд аукциона на понижение (после '
    'трёх неудачных) состоялся 17 августа 2026 года и завершился '
    'продажей: победителем стало петербургское ООО «Центр инжиниринговых '
    'услуг при проектировании и строительстве» (владелец — Тимофей '
    'Белов), для которого это уже вторая национализированная '
    'челябинская покупка после отеля Radisson Blu (1,342 млрд ₽ ранее).'
)

OLD_SRC = [
    ['mergers.ru', 'https://mergers.ru/news/PSB-prodast-kompanii-vladeyuschie-dvumya-TRK-v-Chelyabinske-87293'],
    ['74.ru', 'https://74.ru/text/business/2026/08/05/76572013/'],
    ['74.ru', 'https://74.ru/text/business/2026/08/07/76577105/'],
]
NEW_SRC = OLD_SRC + [
    ['74.ru', 'https://74.ru/text/business/2026/08/17/76584242/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal.get('sum') == OLD_SUM
    assert deal.get('buyer_name') == OLD_BUYER_NAME
    assert deal['eco']['sum'] == OLD_ECO_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status ===', NEW_STATUS)
    print('=== date ===', NEW_DATE)
    print('=== sum ===', NEW_SUM)
    print('=== buyer_name ===', NEW_BUYER_NAME)
    print('=== eco.sum ===', NEW_ECO_SUM)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['sum'] = NEW_SUM
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['eco']['sum'] = NEW_ECO_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
