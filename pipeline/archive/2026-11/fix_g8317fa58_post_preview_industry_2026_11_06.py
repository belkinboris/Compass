# -*- coding: utf-8 -*-
"""Островная (g8317fa58), 6 ноября 2026: независимое второе чтение поправило
отрасль карточки с «Пищепром и напитки» на «Агро» (review.py, FIXES:
written_g8317fa58_second_reading_2026_11_06.py) — все остальные птицефабрики
базы и собственный словарь притока (`draft.INDUSTRY_RX`) относят предмет
сделки к «Агро».

Карточка уже прошла `send_drafts.py` ДО этой правки, и ее `post_preview`
несет СТАРУЮ отрасль и старый хэштег (`send_telegram.py` при публикации
отдает приоритет сохраненному `post_preview`, см.
`regenerate_custody_post_previews.py`, тот же прием 18 сентября 2026) — не
пересчитать его, значит отправить в канал «Пищепром и напитки» и #пищепром
по карточке, которая уже стоит «Агро».

Запуск: python3 pipeline/archive/2026-11/fix_g8317fa58_post_preview_industry_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
import format_post  # noqa: E402

PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ID = 'g8317fa58'


def main(write):
    pending = json.load(open(PENDING_PATH, encoding='utf-8'))
    base = json.load(open(BASE_PATH, encoding='utf-8'))
    companies = base['companies']
    by_id = {c['id']: c for c in pending['cards']}
    assert ID in by_id, '%s: карточки нет в pending.json' % ID
    card = by_id[ID]
    assert card.get('ind') == 'Агро', '%s: ind не «Агро» — отраслевую правку еще не записали' % ID
    old_preview = card.get('post_preview')
    assert old_preview and 'Пищепром' in old_preview, \
        '%s: в сохраненном post_preview уже нет старой отрасли — нечего чинить' % ID
    new_preview = format_post.render(card, companies)
    assert 'Отрасль:</b> Агро' in new_preview, '%s: пересчитанный пост не несет новую отрасль' % ID
    assert '#агро' in new_preview and '#пищепром' not in new_preview, \
        '%s: хэштег не пересчитался' % ID
    card['post_preview'] = new_preview
    print('%s: post_preview пересчитан' % ID)
    print(new_preview)

    if write:
        json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
