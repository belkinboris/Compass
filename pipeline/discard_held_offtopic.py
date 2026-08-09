# -*- coding: utf-8 -*-
"""Разовая правка: выкинуть четыре придержанные карточки не нашей темы.

ЗАЧЕМ. Владелец 9 августа, глядя на список придержанных: «а можно все те
четыре, которые придержаны, удалить просто? это не то что нам нужно, там
нерелевантная недвижка и иностранный контур». Проверено по очереди — все
четыре действительно такие:
  * робототехника основателя Uber ($1,7 млрд) — иностранный контур целиком;
  * RTP Global в швейцарский стартап Ahead Health — иностранный контур;
  * самый большой лот на рынке элитных новостроек Москвы — жилая недвижимость
    без значимой стороны (см. «Как владелец решает» в CLAUDE.md);
  * баня авторитетов-экстремистов в Челябинске — то же самое.

ПОЧЕМУ ОТДЕЛЬНЫМ СКРИПТОМ, А НЕ КНОПКОЙ. Кнопка «🗑 Выкинуть» существует и
работает, но эти четыре карточки уже придержаны — чтобы дотянуться до них
кнопкой, нужно сперва вызвать их заново (это добавлено тем же прогоном).
Разовую уборку делаем скриптом с `assert` на исходное состояние, как все
правки данных в этом репозитории.

Запуск:
    python3 pipeline/discard_held_offtopic.py            # сухой прогон
    python3 pipeline/discard_held_offtopic.py --write    # применить
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

# id -> (начало заголовка для сверки, причина отказа)
DISCARD = {
    'ge2c53041': ('Робототехническая компания основателя Uber',
                  'иностранный контур: американская компания, американский инвестор'),
    'gd24f94d3': ('В Москве продали самый большой лот',
                  'жилая недвижимость без значимой стороны сделки'),
    'g699f00f5': ('В Челябинске продали баню',
                  'жилая/коммерческая мелочь без значимой стороны сделки'),
    'gd36f1178': ('RTP Global вновь инвестировал в швейцарский стартап',
                  'иностранный контур: швейцарский стартап, фонд вне российского периметра'),
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}

    drop, refused = [], []
    for cid, (title_start, why) in DISCARD.items():
        card = cards.get(cid)
        if not card:
            refused.append((cid, 'карточки нет в очереди — уже решена?'))
            continue
        if not str(card.get('title') or '').startswith(title_start):
            refused.append((cid, 'заголовок не тот: %r' % str(card.get('title'))[:60]))
            continue
        if not card.get('held'):
            refused.append((cid, 'карточка НЕ придержана — трогать не будем'))
            continue
        drop.append((cid, card, why))

    for cid, why in refused:
        print('  ОТКАЗ   %s: %s' % (cid, why))
    for cid, card, why in drop:
        print('  ВЫКИНУТЬ %s  %s' % (cid, str(card.get('title'))[:60]))
        print('           причина: %s' % why)

    print('\nвыкинуть %d, отказов %d' % (len(drop), len(refused)))
    if refused:
        print('Есть отказы — не пишем НИЧЕГО.')
        return 1
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    keep = [c for c in data['cards'] if c['id'] not in {cid for cid, _, _ in drop}]
    assert len(keep) == len(data['cards']) - len(drop), 'выкинули не то количество'
    data['cards'] = keep
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: в очереди осталось %d карточек.' % len(keep))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
