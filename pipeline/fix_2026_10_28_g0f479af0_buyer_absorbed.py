# -*- coding: utf-8 -*-
"""Карточка g0f479af0 (ЛСР, выкуп собственных акций): запись таблицы правок
`buyer_name: «Совет директоров ЛСР» → «ЛСР»` применена, а потом приемка
(accept_card.py --apply) привязала покупателя к профилю «Группа ЛСР»
(gb396abf4) и сняла `buyer_name`. `review.already_applied` сверяет имя профиля
с `new` записи, а «Группа ЛСР» ≠ «ЛСР» — и test_review_table_is_applied_and_
not_pending падает, хотя факт записан сильнее. Тот же случай, что у кампании
профилей сторон 23 октября 2026: отпечаток снятого текста кладется в
`proofread_absorbed.buyer_name`, как делает `fix_amber_talvis_parties_and_
milestones.py` (docs/card_editing.md).

Запуск: python3 pipeline/fix_2026_10_28_g0f479af0_buyer_absorbed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD, TEXT = 'g0f479af0', 'ЛСР'


def main(write):
    with open(PATH, encoding='utf-8') as fh:
        data = json.load(fh)
    card = next(c for c in data['cards'] if c['id'] == CARD)
    assert card.get('buyer') == 'gb396abf4', card.get('buyer')
    assert card.get('buyer_name') is None, card.get('buyer_name')
    absorbed = card.setdefault('proofread_absorbed', {}).setdefault('buyer_name', [])
    fp = review.fix_fingerprint(TEXT)
    if fp in absorbed:
        print('уже записано')
        return
    absorbed.append(fp)
    print('отпечаток %s -> proofread_absorbed.buyer_name' % fp)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    with open(PATH, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
