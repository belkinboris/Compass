# -*- coding: utf-8 -*-
"""Новая карточка: филиппинский финтех-стартап Salmon Group, основанный
выходцами из «Тинькофф» (Павел Фёдоров, Георгий Чесаков, Раффи Монтемайор),
привлёк $140 млн ($90 млн акции от Spice Expeditions, WashU и Moore + $50 млн
облигации). Ворота отклонили черновик («не названа ни одна сторона»);
карточка собрана вручную.

Источники (прочитаны полностью через fetch_article_texts.py --write):
  VC.ru, 20.10.2026
  https://vc.ru/money/3205446-finteh-startap-salmon-na-filippinah-privlek-investitsii-ot-tinkoff
  Телеграм-канал «Русский Венчур»
  https://t.me/rusven/7800

Российский бенефициар — основатели, выходцы из «Тинькофф»; сама компания и
раунд — не в России (нероссийский контур с российским бенефициаром — это НЕ
нероссийский контур, CLAUDE.md, «Как владелец решает»).

Этот скрипт создаёт только карточку-оболочку со структурными полями;
текстовые поля дописывает write_card.py отдельно.

Запуск:
    python3 pipeline/build_salmon_group_round_2026_10_20.py            # сухой прогон
    python3 pipeline/build_salmon_group_round_2026_10_20.py --write    # применить
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

SRC = ['VC.ru', 'https://vc.ru/money/3205446-finteh-startap-salmon-na-filippinah-privlek-investitsii-ot-tinkoff']
SRC2 = ['Телеграм-канал: Русский Венчур', 'https://t.me/rusven/7800']

DRAFT = {
    'date': '2026-10-20',
    'title': 'Филиппинский финтех-стартап Salmon Group выходцев из «Тинькофф» привлёк $140 млн',
    'ind': 'Финансовые технологии',
    'type': 'Инвестиция',
    'status': 'Закрыта',
    'src': [SRC, SRC2],
    'buyer_name': 'Spice Expeditions, WashU и Moore',
    'asset': 'Salmon Group — финтех-стартап на Филиппинах',
    'sum': '$140 млн ($90 млн акции, $50 млн облигации)',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Salmon Group' in (c.get('title') or '') for c in pending['cards'] + promoted['deals']):
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
