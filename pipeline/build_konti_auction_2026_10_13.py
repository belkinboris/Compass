# -*- coding: utf-8 -*-
"""Новая карточка: Росимущество выставило на продажу единым лотом активы
национализированной российской «дочки» украинской кондитерской группы
«Конти» — пакет акций АО «Конти-Рус» (Курск) и 100% долей в трёх смежных
компаниях (ООО «Кэндимакс», ООО «Кондитерский центр „Мерлетто“», ООО
«Мерлетто капитал»). Повод для карточки — очередной (как минимум
девятый-десятый) перенос сроков приёма заявок, о котором 13 октября
написало Право.ру; лот висит на торгах с марта 2026 года, предыдущие
попытки не нашли покупателя. Статус — «Обсуждается» (торги не состоялись,
исхода нет).

Источники (прочитаны полностью, кэш data/inbox/raw/2026-10-13-articles.jsonl):
  Право.ру (13.10.2026, повод для карточки)
    https://pravo.ru/news/266283/
  Право.ру (31.08.2026, девятый перенос, стартовая цена)
    https://pravo.ru/news/265602/
  Retail.ru (27.03.2026, повторные торги, полная стартовая цена и отсечение)
    https://www.retail.ru/news/rosimushchestvo-naznachilo-povtornyy-auktsion-po-prodazhe-aktivov-gruppy-konti-r-27-marta-2026-275993/
  Коммерсантъ (03.04.2026, финансы АО «Конти-рус» за 2025 год)
    https://www.kommersant.ru/doc/8568665

Запуск:
    python3 build_konti_auction_2026_10_13.py            # сухой прогон
    python3 build_konti_auction_2026_10_13.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_TODAY = ['Право.ру', 'https://pravo.ru/news/266283/']
SRC_AUG = ['Право.ру (девятый перенос, стартовая цена)', 'https://pravo.ru/news/265602/']
SRC_RETAIL = ['Retail.ru', 'https://www.retail.ru/news/rosimushchestvo-naznachilo-povtornyy-auktsion-po-prodazhe-aktivov-gruppy-konti-r-27-marta-2026-275993/']
SRC_KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8568665']

DRAFT = {
    'date': '2026-10-13',
    'title': 'Росимущество выставило на торги активы кондитерской группы «Конти»',
    'ind': 'Пищепром и напитки',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC_TODAY, SRC_AUG, SRC_RETAIL, SRC_KOMMERSANT],
    'seller': 'Росимущество',
    'asset': 'акции АО «Конти-Рус», 100% ООО «Кэндимакс», ООО «Кондитерский центр „Мерлетто“» и ООО «Мерлетто капитал»',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Конти' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['seller_id'] = 'g9fd82fee'  # Росимущество
    card['sum'] = '4,78 млрд ₽'
    card['sum_basis'] = 'auction_start'
    card['eco']['sum'] = '4,78 млрд ₽'
    card['eco']['share'] = (
        'Лотом целиком — один комплект активов: акции АО «Конти-Рус» (производство в '
        'Курской области) и 100% в трёх смежных компаниях — ООО «Кэндимакс», ООО '
        '«Кондитерский центр „Мерлетто“» и ООО «Мерлетто капитал» (Липецкая область). '
        'На предприятиях занято 3020 человек.'
    )
    card['eco']['val'] = (
        'Торги идут на понижение: стартовая цена лота — 4,78 млрд ₽, цена отсечения '
        '(минимальная цена продажи, ниже которой организатор прекращает приём ставок) — '
        '2,39 млрд ₽.'
    )
    card['eco']['target_fin'] = (
        'АО «Конти-Рус» (по данным бухгалтерской отчётности, «Ъ-Черноземье»): выручка за '
        '2025 год — 17 млрд ₽ (-3% к 18 млрд ₽ годом раньше); убыток до налогообложения '
        'вырос более чем втрое, с 290 млн до 900 млн ₽; чистый убыток — 687 млн ₽ (+87% к '
        '367 млн ₽); активы сократились на 3%, до 11,2 млрд ₽.'
    )
    card['eco']['context'] = (
        'Российские активы украинского кондитерского холдинга «Конти» (основан в 1997 '
        'году) обратили в доход государства по решению Ленинского районного суда Курска '
        'в 2023 году — по иску Генеральной прокуратуры деятельность связанной с бывшими '
        'совладельцами группы была признана экстремистской. Росимущество выставило лот на '
        'торги в марте 2026 года; первая попытка (25 марта) не состоялась из-за отсутствия '
        'заявок, и с тех пор сроки переносились как минимум девять раз — очередной перенос, '
        'давший повод для этой карточки, сдвинул приём заявок на 26 октября, итоги торгов — '
        'на 28 октября.'
    )
    card['law']['struct'] = (
        'Имущество находится на балансе Росимущества после обращения в доход государства '
        'по суду; продаётся единым лотом через электронную торговую площадку ГИС «Торги».'
    )
    card['party_evidence'] = {
        'seller': [{'value': 'Росимущество', 'field': 'seller', 'method': 'explicit_news_title', 'url': SRC_TODAY[1]}],
        'target': [{'value': DRAFT['asset'], 'field': 'asset', 'method': 'explicit_news_title', 'url': SRC_RETAIL[1]}],
    }
    card['themes'] = ['Продажа с торгов']
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    card['events'] = [{
        'id': 'negotiations-2026-10-13', 'kind': 'negotiations', 'date': '2026-10-13',
        'title': 'Переговоры', 'historicalTitle': DRAFT['title'], 'note': '',
        'sources': [SRC_TODAY],
    }]

    print('НОВАЯ КАРТОЧКА %s: %s' % (card_id, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == card_id for c in fresh['cards']):
        print('ОТКАЗ: id уже занят — перечитайте и повторите')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
