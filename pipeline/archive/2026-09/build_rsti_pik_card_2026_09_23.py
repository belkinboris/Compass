# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026: РСТИ покупает у ПИК участок 5,3 га на берегу
Невы в Петербурге (район Шкиперского протока) за ~8 млрд ₽ — компании
подписали предварительный договор, РСТИ внесла задаток. Оба черновика
дня (d82683402 «планирует купить», d46129087 «приобретает») — об одной и
той же сделке, построена одна карточка.

Запуск: python3 pipeline/build_rsti_pik_card_2026_09_23.py --write
"""
import argparse
import json
import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPELINE_DIR)
sys.path.insert(0, os.path.join(PIPELINE_DIR, 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SRC_URL = 'https://realty.ria.ru/20260923/ploschadka-2119747059.html'

QUOTE_MAIN = (
    'РСТИ приобретает у ПИК участок в районе Шкиперского протока с выходом к '
    'береговой линии Невы в Санкт-Петербурге, сообщил "Деловой Петербург" со ссылкой '
    'на источники на рынке недвижимости.'
)

QUOTE_STAGE = (
    'Компания РСТИ подписала предварительный договор с ПИК и уже внесла задаток. '
    'Стоимость сделки составит около 8 миллиардов рублей, говорится в статье. Как '
    'указывается в ней, речь идет об участке площадью 5,3 гектара.'
)

QUOTE_PLANS = (
    'Проект редевелопмента этой территории предусматривает строительство жилого '
    'комплекса примерно на 89 тысяч квадратных метров, включая 65 тысяч "квадратов" жилья.'
)


def main(write):
    pending = promote.load_pending()
    existing = [c['id'] for c in pending['cards']]
    deal_id = promote.new_id(existing)
    draft = {
        'date': '2026-09-23',
        'title': 'РСТИ покупает у ПИК участок на Неве в Петербурге',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['РИА Недвижимость', SRC_URL]],
        'buyer_name': 'РСТИ',
        'asset': 'участок 5,3 га на Шкиперском протоке',
        'seller': 'ПИК',
    }
    card = promote.to_card(draft, deal_id)
    card['sum'] = '8 млрд ₽'
    card['seller_src'] = 'text'
    card['party_evidence'] = {
        'buyer': [{'value': draft['buyer_name'], 'field': 'buyer_name',
                   'method': 'human_review', 'url': SRC_URL}],
        'target': [{'value': draft['asset'], 'field': 'asset',
                    'method': 'human_review', 'url': SRC_URL}],
        'seller': [{'value': draft['seller'], 'field': 'seller',
                    'method': 'human_review', 'url': SRC_URL}],
    }
    card['events'] = [{
        'kind': 'negotiations',
        'date': '2026-09-23',
        'title': 'Подписан предварительный договор',
        'note': QUOTE_MAIN + ' ' + QUOTE_STAGE,
        'source': ['РИА Недвижимость', SRC_URL],
    }]
    card['law']['struct'] = QUOTE_STAGE
    card['eco']['context'] = QUOTE_PLANS
    from datetime import datetime, timezone
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

    assert not any(c['id'] == deal_id for c in pending['cards'])
    pending['cards'].append(card)
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: карточка %s создана.' % deal_id)
    else:
        print('Сухой прогон: карточка %s была бы создана (--write, чтобы записать).' % deal_id)
    return deal_id


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
