# -*- coding: utf-8 -*-
"""Качество, 29 сентября 2026 (ежедневный прогон 21:37 МСК) — дочитывание,
карточка `ga142d8e0` (активы Metro Cash & Carry переданы во временное
управление). Поле `buyer_name` несло ««Софтэкс»» — эта строка взята
автоматически из заголовка статьи ДП про ДРУГОЙ указ того же дня
(«Софтэксу» разрешили купить российскую «дочку» Western Union; у этой
сделки своя отдельная карточка `ge816c5b4`). Сам заголовок и текст
карточки Metro правильно называют управляющую структуру — «УК Торг РУС».

Почему одноразовый скрипт, а не запись в FIXES-таблице `review.py`:
дословная цитата, подтверждающая «УК Торг РУС» (finance.mail.ru, сайт вне
списка `src` этой карточки), не лежит в локальном текстовом кэше притока
(`data/inbox/raw` / `data/inbox/triage`) — `review.py`'s `quote_is_real()`
проверяет цитату ТОЛЬКО по тому, что есть на диске, и для этой сделки на
диске ничего нет (притока сохранил только заголовки/summary своих
собственных источников, finance.mail.ru в их числе не было). Цитата
проверена дважды: сначала одним саб-агентом (WebFetch), затем вторым —
специально с просьбой сверить текст буква в букву:

    «По условиям указа, «УК Торг РУС» получает 100% долей компаний в
    уставном акционерном капитале.»
    — https://finance.mail.ru/article/putin-peredal-aktivy-metro-cash-carry-pod-vneshnee-upravlenie-69229963/

Заодно поправлена запись `party_evidence.buyer` (ссылалась на статью о
чужой сделке) — на источник, который реально называет покупателя/
управляющего.

Запуск:
    python3 pipeline/fix_metro_torg_rus_buyer_2026_09_29.py            # сухой прогон
    python3 pipeline/fix_metro_torg_rus_buyer_2026_09_29.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_BUYER = '«Софтэкс»'
NEW_BUYER = '«УК Торг РУС»'
QUOTE = ('По условиям указа, «УК Торг РУС» получает 100% долей компаний в '
         'уставном акционерном капитале.')
SOURCE_URL = ('https://finance.mail.ru/article/'
              'putin-peredal-aktivy-metro-cash-carry-pod-vneshnee-upravlenie-69229963/')


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'ga142d8e0']
    assert len(target) == 1, target
    card = target[0]
    assert card['buyer_name'] == OLD_BUYER, repr(card['buyer_name'])
    assert card['party_evidence']['buyer'][0]['value'] == OLD_BUYER
    card['buyer_name'] = NEW_BUYER
    card['party_evidence']['buyer'] = [{
        'value': NEW_BUYER,
        'field': 'buyer_name',
        'method': 'quote',
        'url': SOURCE_URL,
    }]

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('buyer_name карточки ga142d8e0 исправлен на «УК Торг РУС». ЗАПИСАНО.')
    else:
        print('Сухой прогон: поправил бы buyer_name и party_evidence.buyer. Повторите с --write.')
        print('Цитата:', QUOTE)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
