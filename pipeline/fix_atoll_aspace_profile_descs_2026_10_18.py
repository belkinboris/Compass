# -*- coding: utf-8 -*-
"""Описания новых профилей «Атолл Капитал» (g0de8db14) и Aspace (g6f14b502).

ПОЧЕМУ. `accept_card.py --apply` дописал к описанию отдельное предложение
«Юрлицо — ООО «Атолл Капитал».». Пост берёт в строку стороны ОДНО
предложение описания и предпочитает предложение с «ёлочками»
(`format_post._pick_novel_sentences`), а имя стороны в начале детали
считает повтором (`names_party_upfront`) — так строка поста стала
«Инвестор: Юрлицо — ООО «Атолл Капитал».», без того, кто это. Юрлицо
переносится в то же предложение, что род занятий. Имя владельца из
описания убрано: оно попадало бы в строку поста о стороне (владелец
17 октября 2026 — без имён людей, если сторона компания); владелец
«Атолл Капитала» назван в «Истории и окружении» карточки ga5a7f3c1.

Запуск:
    python3 pipeline/fix_atoll_aspace_profile_descs_2026_10_18.py          # сухой прогон
    python3 pipeline/fix_atoll_aspace_profile_descs_2026_10_18.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = {
    'g0de8db14': (
        'Российская частная консалтинговая и инвестиционная компания; владелец — Сергей Фрейдин. '
        'Юрлицо — ООО «Атолл Капитал».',
        'Российская частная консалтинговая и инвестиционная компания; юрлицо — ООО «Атолл Капитал».'),
    'g6f14b502': (
        'Оператор сервисных офисов и коворкингов в Москве, один из крупнейших на рынке гибких офисов. '
        'Юрлицо — АО «А Спэйс».',
        'Оператор сервисных офисов и коворкингов в Москве, один из крупнейших на рынке гибких офисов; '
        'юрлицо — АО «А Спэйс».'),
}


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
    changed = 0
    for cid, (old, new) in FIXES.items():
        cur = base['companies'][cid].get('desc')
        if cur == new:
            continue
        assert cur == old, (cid, cur)
        base['companies'][cid]['desc'] = new
        changed += 1
        print('%s: %s' % (cid, new))
    if not write or not changed:
        print('Сухой прогон.' if not write else 'Нечего менять.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
