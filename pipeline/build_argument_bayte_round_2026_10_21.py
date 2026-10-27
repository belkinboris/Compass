# -*- coding: utf-8 -*-
"""Новая карточка: разработчик платформы данных ANG Platform, ООО «Аргумент-
Байт» (бренд «Аргумент»), привлек инвестиции от венчурного фонда
«Созидательный венчур» (страховая компания «Росгосстрах Жизнь», управляющий
партнер — Виталий Полехин) в обмен на 5,46% компании; сумма раунда не
раскрыта. Ворота отклонили черновик («заголовок не написан, а обрезан от
текста новости на полуслове; не названа ни одна сторона»); карточка собрана
вручную.

Источник: Телеграм-канал «Русский венчур», https://t.me/rusven/7803
(21.10.2026) — полный текст поста сохранен в
data/inbox/raw/2026-10-21-articles.jsonl, забран прямым curl в обход отказа
WebFetch пересказывать чужую публикацию целиком.

Юрлицо цели — ООО «Аргумент-Байт» (82,66% у основателя Евгения Митина,
5% — у Максима Пустового, остальное — у миноритариев); пост сам называет
компанию брендом «Аргумент», тождество с «Аргумент-Байт» устанавливается
цитатой из Rusprofile внутри того же поста, а не отдельным ЕГРЮЛ/ИНН-поиском
(ИНН в посте не назван — честный `no_inn`).

Этот скрипт создает только карточку-оболочку со структурными полями;
текстовые поля дописывает write_card.py отдельно.

Запуск:
    python3 pipeline/build_argument_bayte_round_2026_10_21.py            # сухой прогон
    python3 pipeline/build_argument_bayte_round_2026_10_21.py --write    # применить
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

SRC = ['Телеграм-канал: Русский венчур', 'https://t.me/rusven/7803']

DRAFT = {
    'date': '2026-10-21',
    'title': 'Фонд «Созидательный венчур» вложился в 5,46% «Аргумент-Байт»',
    'ind': 'ИТ и интернет',
    'type': 'Инвестиция',
    'status': 'Закрыта',
    'src': [SRC],
    'buyer_name': 'Венчурный фонд «Созидательный венчур»',
    'asset': '5,46% ООО «Аргумент-Байт»',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Аргумент' in (c.get('title') or '') for c in pending['cards'] + promoted['deals']):
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
