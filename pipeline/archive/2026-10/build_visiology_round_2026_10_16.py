# -*- coding: utf-8 -*-
"""Новая карточка: Visiology (АО «Визиолоджи», разработчик BI-платформы)
закрыла краудинвестинговый раунд на 200 млн руб. на платформе «Поток»
(организатор — BITL). Раунд объявлен в июле 2025 года (ComNews, CNews):
инвесторам предложена допэмиссия в 12,5% капитала при постинвестиционной
оценке 1,6 млрд руб., минимальный порог входа — 25 200 руб. (180 акций по
140 руб.). Ведомости 16 октября 2026 сообщили о закрытии раунда (342
инвестора, средний чек 584,8 тыс. руб.) — этот текст сохранить не удалось
(пэйвол/навигационная страница вместо статьи), поэтому в карточку идут
только факты, подтвержденные дословно по кэшированному ComNews; сумму и
статус («Закрыта») берем из заголовка Ведомостей.

Запуск:
    python3 pipeline/build_visiology_round_2026_10_16.py            # сухой прогон
    python3 pipeline/build_visiology_round_2026_10_16.py --write    # применить
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

VEDOMOSTI = ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/10/16/1237666-investitsionnii-raund']
COMNEWS = ['ComNews', 'https://www.comnews.ru/content/240377/2025-07-25/2025-w30/1010/visiology-uskorit-razrabotku-platformy-opirayas-sredstva-vneshnikh-investorov']

DRAFT = {
    'date': '2026-10-16',
    'title': 'Visiology завершил инвестиционный раунд объемом 200 млн рублей',
    'ind': 'ИТ и интернет',
    'type': 'Инвестиция',
    'status': 'Закрыта',
    'src': [VEDOMOSTI, COMNEWS],
    'buyer_name': 'частные инвесторы (платформа «Поток», организатор — BITL)',
    'sum': '200 млн ₽',
    'events': [{
        'kind': 'closed',
        'date': '2026-10-16',
        'title': 'Раунд закрыт',
        'note': 'Раунд объявлен в июле 2025 года на инвестиционной платформе «Поток» '
                '(организатор — компания BITL); закрыт 16 октября 2026 года.',
        'source': VEDOMOSTI,
    }],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Visiology' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

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
