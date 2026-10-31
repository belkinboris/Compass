# -*- coding: utf-8 -*-
"""Новая карточка: гендиректор ПАО «МГКЛ» Алексей Лазутин увеличил личную
долю в компании с 12,7% до 28% через внебиржевые сделки; в МГКЛ подтвердили,
что это не связано с программой байбэка, которую ведет «дочка» группы.
Ворота отклонили черновик («не установлен предмет сделки»); карточка
собрана вручную.

Источники: Ведомости, https://www.vedomosti.ru/investments/news/2026/10/21/1239013-gendirektor-mgkl
(дословные фрагменты через WebFetch, ≤125 знаков за раз, сохранены в
data/inbox/raw/2026-10-21-articles.jsonl); Smart-Lab (официальный блог МГКЛ),
https://smart-lab.ru/company/mgkl/blog/1365264.php — то же сообщение от
самой компании.

Цена и число акций источником не названы — честно оставлены пустыми.

Этот скрипт создает только карточку-оболочку со структурными полями;
текстовые поля дописывает write_card.py отдельно.

Запуск:
    python3 pipeline/build_mgkl_lazutin_stake_2026_10_21.py            # сухой прогон
    python3 pipeline/build_mgkl_lazutin_stake_2026_10_21.py --write    # применить
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

SRC = ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/10/21/1239013-gendirektor-mgkl']
SRC2 = ['Smart-Lab (МГКЛ)', 'https://smart-lab.ru/company/mgkl/blog/1365264.php']

DRAFT = {
    'date': '2026-10-21',
    'title': 'Гендиректор МГКЛ Алексей Лазутин довел личную долю в компании до 28%',
    'ind': 'Финансовые услуги',
    'type': 'M&A',
    'status': 'Закрыта',
    'src': [SRC, SRC2],
    'buyer_name': 'Алексей Лазутин',
    'asset': 'акции ПАО «МГКЛ»',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Лазутин' in (c.get('title') or '') for c in pending['cards'] + promoted['deals']):
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
