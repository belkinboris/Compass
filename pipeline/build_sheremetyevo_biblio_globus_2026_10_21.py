# -*- coding: utf-8 -*-
"""Новая карточка: аэропорт Шереметьево ведет переговоры о продаже 75% в
туроператоре «Библио-Глобус» (юрлицо — ООО «Туроператор БГ»; Шереметьево
купил эту долю в 2021 году, ФАС одобрила сделку 29 сентября 2021-го).
Сейчас, по данным РБК (через dp.ru), средства от продажи могут пойти на
выкуп государственной доли в самом аэропорте — Шереметьево в начале
августа 2026 исключили из перечня стратегических предприятий, что сделало
возможной его приватизацию. Ворота отклонили черновик («не установлен
предмет сделки»); карточка собрана вручную — покупатель и цена источником
не названы, честно оставлены пустыми.

Источник: Деловой Петербург, https://www.dp.ru/a/2026/10/21/sheremetevo-nachal-peregovori
(со ссылкой на РБК) — текст сайта на Angular, прямой curl не вернул тело
статьи (SPA, контент через API); дословные фрагменты (≤125 знаков за раз)
забраны через WebFetch и сохранены в data/inbox/raw/2026-10-21-articles.jsonl.

Этот скрипт создает только карточку-оболочку со структурными полями;
текстовые поля дописывает write_card.py отдельно.

Запуск:
    python3 pipeline/build_sheremetyevo_biblio_globus_2026_10_21.py            # сухой прогон
    python3 pipeline/build_sheremetyevo_biblio_globus_2026_10_21.py --write    # применить
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

SRC = ['Деловой Петербург', 'https://www.dp.ru/a/2026/10/21/sheremetevo-nachal-peregovori']

DRAFT = {
    'date': '2026-10-21',
    'title': 'Шереметьево начал переговоры о продаже 75% туроператора «Библио-Глобус»',
    'ind': 'Гостиницы и туризм',
    'type': 'M&A',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': 'Международный аэропорт Шереметьево',
    'asset': '75% ООО «Туроператор БГ» (бренд «Библио-Глобус»)',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    # «Библио-Глобус» — книжный магазин («Торговый дом «Библио-Глобус»», c36556448)
    # и туроператор («Туроператор БГ») — РАЗНЫЕ компании с одним брендом; проверяем
    # именно туроператорскую карточку, не книжный магазин.
    if any('Шереметьево' in (c.get('title') or '') and 'Библио-Глобус' in (c.get('title') or '')
           for c in pending['cards'] + promoted['deals']):
        print('ОТКАЗ: похожая карточка уже есть')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')

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
