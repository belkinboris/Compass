# -*- coding: utf-8 -*-
"""Новая карточка: «Дом.РФ» выставил на аукцион право заключить договор о
комплексном развитии территории (КРТ) на участке 52,31 га в посёлке Петра
Дубрава Самарской области. `triage.py` ошибочно пометил статью как
`enrich:g49431b3c` (особняк Штиглица в Петербурге — тот же организатор
торгов «Дом.РФ» и фраза «выставил на торги», не общая сделка): сюжеты не
связаны, карточка нужна своя. У черновика нет `draft_id` (ворота не
создавали запись на «enrich»-вердикт), поэтому карточка собирается
отдельным скриптом, как и прошлые такие случаи в этом окне.

Текст написан пишущим саб-агентом по фактам (WRITING_BRIEF.md,
write_card.py) — первая карточка по новому порядку "Сбор → Текст →
Проверка и запись". Факты и ответ пишущего:
  /tmp/claude-0/-home-user-Compass/b93b17a7-510c-5faf-af4e-13d582b870b2/scratchpad/evidence_samara_krt.json
  /tmp/claude-0/-home-user-Compass/b93b17a7-510c-5faf-af4e-13d582b870b2/scratchpad/written_samara_krt.json

Источник (прочитан полностью):
  РИА Недвижимость (14.10.2026)
  https://realty.ria.ru/20261014/samara-2124434687.html

Этот скрипт создаёт только карточку-оболочку со структурными полями
(продавец, предмет, тип, отрасль, статус, дата, источник) — переносятся
обычным способом, с дословной привязкой к статье. Текстовые поля
(eco.share, eco.val, law.struct, law.terms, extra) дописывает отдельно
`write_card.py --check/--write` из `written.json` — ровно так, как
велит WRITING_BRIEF.md, через цитаты и проверку review.py.

Запуск:
    python3 pipeline/build_samara_krt_2026_10_14.py            # сухой прогон
    python3 pipeline/build_samara_krt_2026_10_14.py --write    # применить
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC = ['РИА Недвижимость', 'https://realty.ria.ru/20261014/samara-2124434687.html']

DRAFT = {
    'date': '2026-10-14',
    'title': '«Дом.РФ» выставил на торги право на КРТ участка в Самарской области',
    'ind': 'Недвижимость',
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'src': [SRC],
    'seller': '«Дом.РФ»',
    'asset': 'право заключить договор о КРТ участка 52,31 га в посёлке Петра Дубрава (Самарская область)',
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']}
    if any('Петра Дубрав' in (c.get('title') or '') or '52,31' in (c.get('asset') or '')
           for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    card_id = promote.new_id(existing_ids)
    card = promote.to_card(DRAFT, card_id)
    card['seller_id'] = 'gb2b066c3'

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
