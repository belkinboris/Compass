# -*- coding: utf-8 -*-
"""Новая карточка: «Красцветмет» купил недвижимость и оборудование ювелирного
завода «ПАРС» в Красном-на-Волге (Костромская область) — по просьбе партнёра
(тема «Клод», сообщение 2380, 23 октября 2026).

ПОЧЕМУ РУКАМИ. Партнёр прислал готовый текст поста; приток этой новости не
нашёл (ни в сырье, ни в очереди её нет). Карточка собирается так же, как
кнопкой «в работу»: черновик → `promote.to_card` → `pending.json` с
`pending_since`; дальше обычный путь (write_card.py, accept_card.py, второе
чтение, send_drafts.py).

ЧТО ИЗВЕСТНО И ЧЕГО НЕТ (сверено с источниками и ЕГРЮЛ):
  * предмет — недвижимость и производственное оборудование завода, а не доли
    ООО ЮЗ «ПАРС»: так в пресс-релизе (перепечатка Ювелир.INFO 22.10.2026) и в
    NGS24 (23.10.2026). Юрлицо «ПАРС» остаётся и до конца 2026 года
    исполняет обязательства перед клиентами — профиль предмета не заводится,
    `asset` — текст.
  * продавец — ООО Ювелирный завод «ПАРС» (ИНН 4415007628, ОГРН
    1144437001851): по ЕГРЮЛ (datanewton) его единственный участник и
    гендиректор — Явуз Атак (100%); имя владельца — в прозе, продавец
    карточки — юрлицо, которому принадлежат активы.
  * покупатель — ОАО «Красцветмет» (ИНН 2451000818, ОГРН 1022402056324),
    полностью принадлежит Красноярскому краю (NGS24).
  * дата — 22.10.2026, день пресс-релиза (дата перехода права не раскрыта);
    статус «Закрыта» — «приобрел» в прошедшем времени.
  * сумма не раскрыта. Финансы «ПАРС» за 2025 год (выручка 149,4 млн ₽,
    чистая прибыль 14,7 млн ₽) — по NGS24 со ссылкой на «Контур.Фокус»;
    остальные цифры из текста партнёра (прибыль от продаж, основные средства,
    чистые активы, 62 сотрудника) в источниках не нашлись и в карточку не
    идут.

id — константой (docs/intake_run.md, «id ручной сборки — константой»).

Запуск:
    python3 pipeline/build_krastsvetmet_pars_2026_10_23.py            # сухой прогон
    python3 pipeline/build_krastsvetmet_pars_2026_10_23.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf31c1d53'

UVELIR = ['Ювелир.INFO', 'https://uvelir.info/news/krastsvetmet-priobrel-aktivyi-yuvelirnogo-zavoda-pars-i-rasshiryaet-proizvodstvo-serebryanyih-tsepej/']
NGS24 = ['NGS24.ru', 'https://ngs24.ru/text/economics/2026/10/23/76719312/']

EGRUL_PARS = 'https://datanewton.ru/contragents/1144437001851'

EGRUL = ['ЕГРЮЛ: ООО Ювелирный завод «ПАРС»', EGRUL_PARS]
FIN = ['Бухотчётность ООО Ювелирный завод «ПАРС»', EGRUL_PARS + '/finance']

SELLER = 'ООО Ювелирный завод «ПАРС»'
ASSET = 'недвижимость и оборудование ювелирного завода «ПАРС» в Красном-на-Волге'

DRAFT = {
    'date': '2026-10-22',
    'title': '«Красцветмет» купил активы ювелирного завода «ПАРС» в Костромской области',
    'ind': 'Потребительские товары',
    'type': 'M&A',
    'status': 'Закрыта',
    'sum': 'Не раскрыта',
    'src': [UVELIR, NGS24, EGRUL, FIN],
    'asset': ASSET,
    'seller': SELLER,
    'buyer_name': '«Красцветмет»',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in pending['cards']) or any(d['id'] == CARD_ID for d in promoted['deals']):
        print('УЖЕ ЕСТЬ: %s — повторно не собираю' % CARD_ID)
        return 0
    for c in pending['cards'] + promoted['deals']:
        blob = json.dumps(c, ensure_ascii=False)
        if 'Красное-на-Волге' in blob or 'Красном-на-Волге' in blob or 'завод «ПАРС»' in blob:
            print('ОТКАЗ: похожая карточка уже есть: %s %s' % (c['id'], c['title']))
            return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['eco']['sum'] = 'Не раскрыта'
    card['src'] = [list(s) for s in DRAFT['src']]
    card['kind'] = 'acquisition'
    # Продавец в заголовке не назван («активы завода»): юрлицо-владелец
    # активов — по прочтению статьи и ЕГРЮЛ, а не по заголовку.
    card['party_evidence']['seller'] = [{'value': SELLER, 'field': 'seller',
                                         'method': 'manual_source_review', 'url': EGRUL_PARS}]
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('УЖЕ ЕСТЬ в pending.json — не пишу')
        return 0
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
