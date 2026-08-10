# -*- coding: utf-8 -*-
"""Карточка `g15386e04` («Softline потратил 340 миллионов на покупку бывшего
консалтингового подразделения KPMG») пришла из притока в очередь предпросмотра
(`static/data/pending.json`) БЕЗ единого поля стороны: нет `buyer`, нет
`asset`, нет `seller` — при том, что источник (CNews, полный текст уже в
кэше притока) называет покупателя, предмет и продавцов прямо, а профиль
покупателя («Softline», `gda7d982b`) уже есть в базе. Карточку в таком виде
владелец увидел в консоли Telegram ещё до какого-либо чтения — отсюда и
вопрос «113 или 340» (см. правки в `pipeline/ingest/fixes/batch_g15386e04.py`).

Здесь заполняются только СТРУКТУРНЫЕ поля каркаса (`buyer`) и плейсхолдеры
пустых состояний (`law.appr`, `law.adv`), принятые по всей базе для «источник
об этом не говорит» — это не перенос факта из статьи, а типовая заглушка,
дословная цитата ей не нужна (см. `pipeline/fill_frame_vpp_softline.py`,
тот же приём). Содержательные поля (`asset`, `seller`, `sum`, `eco.*`,
`law.struct`) заполняются ОТДЕЛЬНО, через `pipeline/ingest/review.py` — там
нужна дословная цитата, и механизм её уже проверяет.

Карточка лежит в ОЧЕРЕДИ ПРЕДПРОСМОТРА, не в базе — правим `pending.json`.

Запуск: python3 pipeline/fill_frame_softline_beringpro.py
        python3 pipeline/fill_frame_softline_beringpro.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g15386e04'
BUYER_ID = 'gda7d982b'  # Softline
LAW_APPR = 'Публично не сообщалось'
LAW_ADV = [['Стороны сделки', 'Не раскрывались',
            'Юридические консультанты в публичных источниках не раскрывались']]


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        print('%s не найдена в очереди предпросмотра' % CARD_ID)
        return 1
    if card.get('buyer') == BUYER_ID and card['law'].get('appr') == LAW_APPR \
            and card['law'].get('adv') == LAW_ADV:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return 0
    assert 'buyer' not in card, '%s: buyer уже задан' % CARD_ID
    assert card['law'].get('appr') == '—', '%s: law.appr уже не заглушка' % CARD_ID
    assert card['law'].get('adv') == [], '%s: law.adv уже не пуст' % CARD_ID
    print('ПРАВИМ  %s: buyer=%s, law.appr=%r, law.adv=плейсхолдер'
          % (CARD_ID, BUYER_ID, LAW_APPR))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    card['buyer'] = BUYER_ID
    card['law']['appr'] = LAW_APPR
    card['law']['adv'] = LAW_ADV
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
