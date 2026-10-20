# -*- coding: utf-8 -*-
"""Новая карточка: сеть «X4 Падел» выкупила конкурента Rocket Padel
(Коммерсантъ, 20 октября 2026, https://www.kommersant.ru/doc/9042452).

ПОЧЕМУ РУКАМИ. Ворота `promote.py` не распознали стороны («не названа ни
одна сторона — ни покупатель, ни продавец») из-за игривого заголовка
Коммерсанта («Инвесторы взялись за ракетки // Сеть «X4 Падел» выкупила
конкурента Rocket Padel») — черновик `d72076963` остался «НА РЕШЕНИЕ».
Источник дочитан полностью (наш `fetch_article_texts.py` получил полный
текст статьи, в отличие от первой попытки саб-агента через WebFetch, у
которой Коммерсантъ дважды отдал РАЗНЫЙ пересказ без дословных цитат —
имена и цифры из того пересказа независимо не подтвердились, их не
используем).

ЧТО ИЗВЕСТНО (дословно по статье, data/inbox/raw/2026-10-20-articles.jsonl):
  * Покупатель — сеть клубов «X4 Падел» (юрлицо ООО «Х4 Падел», создано в
    марте 2026; учредитель — Ростислав Шатенок, сооснователь «Альтхаус»;
    гендиректор — Антон Сухобрусов, по СПАРК ранее совладелец УК «Аксиома
    Капитал»).
  * Предмет — НЕ покупка юрлиц: «структура владения юрлицами не менялась».
    Куплены 3 действующих клуба (Кемерово, Волгоград, Уфа, 18 кортов) и
    права на бренд Rocket Padel; клубы перейдут под бренд «Rocket X4
    Падел». Структуры Rocket Padel контролирует Дмитрий Шицле (100% в
    «Рокет Москва», «Рокет Санкт-Петербург», «Рокет Краснодар»; 80% в
    «Рокет Волгоград», «Рокет Кемерово», «Рокет» — остальные 20% у
    Маргариты Бартеневой). Эти доли НЕ переходят покупателю — проданы
    именно корты и бренд, а не компании.
  * Сумму стороны не раскрыли; два аналитика оценивают её в 120–220 млн ₽
    (BGP Capital — 120–150 млн, Fitness Data — 120–220 млн).
  * После сделки у X4 — 13 клубов, 69 кортов в 10 регионах, 15 тыс.
    зарегистрированных игроков; это даёт X4 звание крупнейшего игрока
    рынка по собственной оценке. План на 2027 год — 100 клубов.
  * Продавец Rocket Padel в статье прямо не называется словом «продавец» —
    записан через контролирующее лицо (Дмитрий Шицле), как и в карточке
    «Стаксель» (Владимир Скороход) — по решению, которое уже применялось
    для похожих случаев (docs/card_parties.md).

Запуск:
    python3 pipeline/build_x4padel_rocket_2026_10_20.py            # сухой прогон
    python3 pipeline/build_x4padel_rocket_2026_10_20.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gx4padel01'
DRAFT_ID = 'd72076963'

KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9042452']

DRAFT = {
    'date': '2026-10-20',
    'title': 'Сеть «X4 Падел» выкупила конкурента Rocket Padel',
    'ind': 'Развлечения',
    'type': 'M&A',
    'status': 'Закрыта',
    'sum': '120–220 млн ₽ (оценка)',
    'src': [KOMMERSANT],
    'asset': 'корты и права на бренд Rocket Padel',
    'buyer_name': 'X4 Падел',
    'seller': 'Дмитрий Шицле',
    'events': [
        {
            'kind': 'closed', 'date': '2026-10-20', 'title': 'Сделка завершена',
            'note': 'Сеть клубов «X4 Падел» приобрела три клуба Rocket Padel в Кемерово, '
                    'Волгограде и Уфе (18 кортов) и права на бренд; клубы перейдут под '
                    'вывеску «Rocket X4 Падел». Структура владения юрлицами Rocket Padel '
                    'не менялась — проданы корты и бренд, а не сами компании. Сумму стороны '
                    'не раскрыли.',
            'source': KOMMERSANT,
        },
    ],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in pending['cards']) or any(d['id'] == CARD_ID for d in promoted['deals']):
        print('УЖЕ ЕСТЬ: %s — повторно не собираю' % CARD_ID)
        return 0
    for c in pending['cards']:
        if 'Rocket Padel' in (c.get('title') or '') or 'X4 Падел' in (c.get('title') or ''):
            print('ОТКАЗ: похожая карточка уже в очереди: %s %s' % (c['id'], c['title']))
            return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('УЖЕ ЕСТЬ в pending.json — не пишу')
        return 0
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
