# -*- coding: utf-8 -*-
"""Новая карточка: «Атолл Капитал» получил до 25% в операторе гибких офисов
Aspace (Коммерсантъ, 16 октября 2026; пересказ — cre.ru).

ПОЧЕМУ РУКАМИ. Фильтр притока не узнал заголовок «получил до 25% долей» /
«стал акционером» — сделка не дошла до ворот (фильтр починен коммитом
ff1c9829). Карточка собирается так же, как кнопкой «в работу»: черновик →
`promote.to_card` → `pending.json` с `pending_since`; дальше обычный путь
(write_card.py, review.py --mark-read, accept_card.py, второе чтение,
send_drafts.py).

ЧТО ИЗВЕСТНО И ЧЕГО НЕТ (по статье):
  * тип — «Инвестиция»: миноритарная доля (docs/card_status_dates.md, «Раунд
    и миноритарная доля»), и статья пишет о привлечении инвестора, чтобы
    финансировать рост сети; продавец не назван — роль пуста, а не «не
    раскрыт». Аналитик «Риком-Траст» лишь предполагает пропорциональное
    размытие прежних акционеров; кто получил деньги, стороны не сказали.
  * сумма официально не раскрыта: 330–515 млн ₽ — оценка Ярослава Кабакова
    (ФГ «Финам»), 1,65 млрд ₽ — со слов неназванного собеседника, близкого
    к Aspace; обе — в eco.val, не в sum.
  * день сделки статья не называет — дата годом, о сделке стало известно
    16 октября 2026 (docs/card_status_dates.md, «Нет дня — только год»).

id — константой (docs/intake_run.md, «id ручной сборки — константой»):
повторный запуск не заводит второй карточки.

Запуск:
    python3 pipeline/build_atoll_aspace_2026_10_18.py            # сухой прогон
    python3 pipeline/build_atoll_aspace_2026_10_18.py --write    # применить
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

CARD_ID = 'ga5a7f3c1'

KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9027406']
CRE = ['CRE', 'https://cre.ru/news/106141']

DRAFT = {
    'date': '2026',
    'title': '«Атолл Капитал» получил до 25% оператора гибких офисов Aspace',
    'ind': 'Недвижимость',
    'type': 'Инвестиция',
    'status': 'Закрыта',
    'src': [KOMMERSANT, CRE],
    'buyer_name': '«Атолл Капитал»',
    'asset': 'до 25% в капитале Aspace',
    'events': [{
        'kind': 'closed',
        'date': '2026',
        'title': '«Атолл Капитал» стал акционером',
        'note': 'О сделке стало известно 16 октября 2026 года со слов её сторон; '
                'день, когда «Атолл Капитал» вошёл в капитал, не назван.',
        'source': KOMMERSANT,
    }],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in pending['cards']) or any(d['id'] == CARD_ID for d in promoted['deals']):
        print('УЖЕ ЕСТЬ: %s — повторно не собираю' % CARD_ID)
        return 0
    for c in pending['cards'] + promoted['deals']:
        if 'Атолл' in (c.get('title') or ''):
            print('ОТКАЗ: похожая карточка уже есть: %s %s' % (c['id'], c['title']))
            return 1

    card = promote.to_card(DRAFT, CARD_ID)
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
