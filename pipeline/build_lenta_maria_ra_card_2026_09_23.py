# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026: «Лента» купила сеть «Мария-Ра» (по данным
Банкфакса, сотрудникам объявили о смене собственника 18 сентября;
официально о сделке пока не сообщалось). Черновик (d39787722) был
ошибочно подавлен `promote.py`'s `dup_in_batch` как «второе издание»
девятидневной давности черновика о ПЕРЕГОВОРАХ (d18941081, 14 сентября) —
хотя это материальное обновление статуса (переговоры → объявлено
сотрудникам), а не повтор той же новости. Построена напрямую тем же
способом, что и другие ручные карточки в этой сессии
(`promote.new_id()`/`promote.to_card()`).

Запуск: python3 pipeline/build_lenta_maria_ra_card_2026_09_23.py --write
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

SRC_URL = 'https://retailer.ru/smi-soobshhili-o-prodazhe-magazinov-marija-ra-seti-lenta/'

QUOTE_MAIN = (
    'В магазинах "Мария-Ра" объявили сотрудникам о продаже торговой сети компании '
    '"Лента", сообщил "Банкфакс" со ссылкой на несколько источников. По их данным, '
    '18 сентября коллективам заявили о смене собственника'
)

QUOTE_REBRAND = (
    'Источники утверждают, что магазины продолжат работу под вывеской "Мария-Ра". '
    'В ближайшие два года ребрендинг не планируется: через два года сеть будет '
    'праздновать 35-летие со дня основания. Официально о сделке пока не сообщалось.'
)

QUOTE_VAL = (
    'Ранее "Банкфакс" писал, что стоимость розничного бизнеса "Мария-Ра" может '
    'составлять 40-60 млрд руб. Такое предположение высказывал начальник отдела '
    'публичного анализа акций Совкомбанка Вячеслав Бердников. Интерес "Ленты" к '
    'сети он связывал с планами федерального ритейлера по наращиванию бизнеса.'
)

QUOTE_SCALE = (
    'На 1 июля 2026 года сеть насчитывала 1303 магазина в 280 населенных пунктах '
    'Алтайского края, Республики Алтай, Новосибирской, Кемеровской и Томской '
    'областей, по данным Infoline. Бизнесом владеют основатель сети Александр '
    'Ракшин и члены его семьи.'
)


def main(write):
    pending = promote.load_pending()
    existing = [c['id'] for c in pending['cards']]
    deal_id = promote.new_id(existing)
    draft = {
        'date': '2026-09-23',
        'title': '«Лента» купила сеть «Мария-Ра»',
        'ind': 'Ритейл',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['retailer.ru', SRC_URL]],
        'buyer_name': '«Лента»',
        'asset': 'торговая сеть «Мария-Ра»',
        'seller': 'Александр Ракшин',
    }
    card = promote.to_card(draft, deal_id)
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
        'title': 'Сотрудникам объявили о смене собственника',
        'note': QUOTE_MAIN,
        'source': ['retailer.ru', SRC_URL],
    }]
    card['eco']['context'] = QUOTE_REBRAND
    card['eco']['val'] = QUOTE_VAL
    card['eco']['share'] = QUOTE_SCALE
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
