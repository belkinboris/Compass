# -*- coding: utf-8 -*-
"""Убрать карточки, которые не про российский рынок.

ЗАЧЕМ. Платформа заявлена как база сделок M&A РОССИЙСКОГО рынка, а приток
приносит и чужие: 3 августа ворота пропустили «Visa купила BioCatch за $2,4
млрд» (США — Израиль) и американский Smallest.ai. Решение владельца 5 августа:
такие фильтруем. Ворота теперь отправляют их человеку (`russian_evidence` в
`promote.py`), но две карточки успели попасть в базу до этого правила.

ПОЧЕМУ УДАЛЕНИЕ, А НЕ ПОМЕТКА. У сделки без российской стороны нет ни одного
поля, ради которого её стоит держать: ни профиля компании, ни отрасли в нашем
разрезе, ни подписчика, которому она нужна. Пометка «вне охвата» означала бы
новое состояние в интерфейсе ради двух записей.

ГРАНИЦА. Скрипт удаляет ТОЛЬКО перечисленные поимённо карточки и только если
на них никто не ссылается: их нет ни в `telegram_posts` (то есть в канал они не
уходили), ни в `merged`, ни в профилях компаний. Массовой чистки здесь нет и
быть не может — список закрытый, каждая строка с причиной.

Запуск:
    python3 pipeline/remove_out_of_scope_deals.py            # сухой прогон
    python3 pipeline/remove_out_of_scope_deals.py --write    # удалить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# id -> (заголовок для сверки, причина)
OUT_OF_SCOPE = {
    'gd057d2c1': ('Visa купила BioCatch',
                  'обе стороны иностранные (США — Израиль), российской связи нет'),
    'g4a10e7a2': ('Инвесторы вложили $13 млн в голосовой ИИ',
                  'американский стартап Smallest.ai, российской связи нет'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    outside = json.dumps({k: v for k, v in data.items() if k != 'deals'}, ensure_ascii=False)

    plan, refused = [], []
    for deal_id, (title_part, why) in OUT_OF_SCOPE.items():
        card = cards.get(deal_id)
        if not card:
            refused.append((deal_id, 'карточки уже нет в базе'))
            continue
        # Сверка заголовка — защита от того, что id указывает не на ту карточку.
        if title_part.lower() not in str(card.get('title') or '').lower():
            refused.append((deal_id, 'заголовок не совпадает: %r' % str(card.get('title'))[:60]))
            continue
        if deal_id in outside:
            refused.append((deal_id, 'на карточку ссылаются: telegram_posts / merged / профили'))
            continue
        plan.append((card, why))

    print('Карточек вне охвата в списке: %d' % len(OUT_OF_SCOPE))
    for card, why in plan:
        print('  УДАЛЯЕМ  %s %s' % (card['id'], str(card.get('title'))[:66]))
        print('           %s' % why)
    for deal_id, why in refused:
        print('  НЕ ТРОГАЕМ %s — %s' % (deal_id, why))

    if not write:
        print('\nСухой прогон. Удаление — с ключом --write.')
        return 0
    if not plan:
        print('\nУдалять нечего.')
        return 0

    keep = {c['id'] for c, _ in plan}
    before = len(data['deals'])
    data['deals'] = [d for d in data['deals'] if d['id'] not in keep]
    assert len(data['deals']) == before - len(plan), 'удалилось не то количество'
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nУДАЛЕНО: %d (в базе было %d, стало %d)' % (len(plan), before, len(data['deals'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
