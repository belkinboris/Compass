# -*- coding: utf-8 -*-
"""Новая карточка: крупная (не названная) инвестиционная компания
обсуждает с топ-менеджментом группы МГКЛ («Мосгорломбард», сеть
ломбардов и золотообменников, профиль `g41f567f1`) вхождение в
капитал и финансирование покупки банка и других проектов — прямые
вложения ~7–10 млрд ₽. Статус «Обсуждается»: сделка не закрыта,
условия обсуждаются, могут закрыть в IV кв. 2026 – I кв. 2027 г.

Ворота отклонили черновик («не установлен предмет сделки» — заголовок
не называет ни инвестора, ни банк по имени), собрано отдельным
скриптом. Инвестор и банк, который МГКЛ планирует купить, — по новому
правилу владельца (14 октября 2026, docs/intake_run.md/routines/
intake.md шаг 8 — «не назван продавец, покупатель или непонятен
предмет — искать обязательно») искал саб-агентом (WebSearch, несколько
формулировок) — ни название инвестора, ни название банка не нашлись ни
в одном источнике деловых СМИ; честная пустота, не выдумка. Отдельно
нашлась вторичная (не деловые СМИ первого эшелона, smart-lab.ru/
marketpower.pro) история про банк «ГолдБанк», который МГКЛ анонсировала
в своей стратегии 2026–2030, — связь с ЭТОЙ сделкой НЕ подтверждена ни
одним первоисточником, в карточку не включена (предположение, не факт).

Источники (прочитаны полностью, кэш data/inbox/raw/2026-10-15-articles.jsonl):
  Ведомости (15.10.2026, автор Наталья Заруцкая) — первоисточник,
    закрыт подпиской на 92% текста, видимые 8% процитированы целиком
    https://www.vedomosti.ru/finance/articles/2026/10/15/1237169-mgkl-nashla-investora
  Frank Media (15.10.2026) — пересказ той же статьи «Ведомостей» с доп.
    деталями (капитализация МГКЛ, оценка аналитика «Гарда капитала»);
    текст не читается автоматически (связь с сервером обрывается),
    добавлен в src по описанию саб-агента, который открыл его сам —
    дословных цитат оттуда в карточке нет
    https://frankmedia.ru/310222

Запуск:
    python3 pipeline/build_mgkl_investor_2026_10_15.py            # сухой прогон
    python3 pipeline/build_mgkl_investor_2026_10_15.py --write    # применить
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_VED = ['Ведомости', 'https://www.vedomosti.ru/finance/articles/2026/10/15/1237169-mgkl-nashla-investora']
SRC_FM = ['Frank Media', 'https://frankmedia.ru/310222']

DRAFT = {
    'date': '2026-10-15',
    'title': 'Крупный инвестор обсуждает вход в капитал МГКЛ для покупки банка',
    'ind': 'Финансовые услуги',
    'type': 'Инвестиция',
    'status': 'Обсуждается',
    'src': [SRC_VED, SRC_FM],
    'buyer_name': 'Крупная инвестиционная компания (название не раскрыто)',
    'sum': '7–10 млрд ₽',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('МГКЛ' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['target'] = 'g41f567f1'
    card['asset'] = 'МГКЛ (Мосгорломбард)'

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
