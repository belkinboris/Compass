# -*- coding: utf-8 -*-
"""Карточка `c43f195a5` («Softline покупает контроль в разработчике ПО «Ваш
платежный проводник»») пришла из компактного импорта («from_compact»:
«channel») почти пустой: `eco` — пустой словарь, `law` отсутствует вовсе,
нет ни `buyer`, ни `asset`. Каркас (тип, дата, отрасль, заголовок) уже
верный, но покупатель и предмет сделки не связаны ни с чем — хотя источник
(ComNews, полный текст уже в кэше притока) называет обе стороны прямо, а
профиль покупателя («Softline», `gda7d982b`) уже есть в базе.

Здесь заполняются только СТРУКТУРНЫЕ поля каркаса (`buyer`, `asset`) и
плейсхолдеры пустых состояний (`sum`/`eco.sum`/`law.*`), принятые по всей
базе для «источник об этом не говорит» — это не перенос факта из статьи, а
типовая заглушка, дословная цитата ей не нужна (см. правило CLAUDE.md
«плейсхолдеры не считаются данными»). Содержательные поля линз (`eco.share`,
`eco.rationale`, `eco.context`, `eco.target_fin`) заполняются ОТДЕЛЬНО, через
`pipeline/ingest/review.py` — там нужна дословная цитата, и механизм её уже
проверяет.

Запуск: python3 pipeline/fill_frame_vpp_softline.py
        python3 pipeline/fill_frame_vpp_softline.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c43f195a5'
BUYER_ID = 'gda7d982b'  # Softline
ASSET_TEXT = 'контрольный пакет акций ООО «Ваш платежный проводник»'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card.get('buyer') == BUYER_ID and card.get('asset') == ASSET_TEXT:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert 'buyer' not in card, '%s: buyer уже задан' % CARD_ID
    assert 'asset' not in card, '%s: asset уже задан' % CARD_ID
    assert card.get('eco') == {}, '%s: eco уже не пуст' % CARD_ID
    assert 'law' not in card, '%s: law уже задан' % CARD_ID
    assert 'sum' not in card, '%s: sum уже задан' % CARD_ID
    print('ПРАВИМ  %s: buyer=%s, asset=%r, плейсхолдеры sum/law' % (CARD_ID, BUYER_ID, ASSET_TEXT))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['buyer'] = BUYER_ID
    card['asset'] = ASSET_TEXT
    card['sum'] = 'Не раскрыта'
    card['eco']['sum'] = 'Не раскрыта'
    card['law'] = {
        'struct': '—',
        'appr': 'Публично не сообщалось',
        'adv': [['Стороны сделки', 'Не раскрывались',
                 'Юридические консультанты в публичных источниках не раскрывались']],
        'terms': '—',
    }
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
