# -*- coding: utf-8 -*-
"""ge1c5f194: пост одобрен владельцем (post_approved=true) со снимком ДО
правки 24 ноября 2026 (оговорка «по неофициальным данным» для
подконтрольности покупателя структурам Лисина) — post_preview несет СТАРЫЙ
текст без этой оговорки и со старым форматом даты («Закрыта · ноябрь 2026»
вместо текущего года-только «2026»). send_telegram.py отдает post_preview
приоритет перед свежим автоформатом (находка второго чтения, 24 ноября
2026) — без снятия пост с устаревшим неофициальным-как-фактом текстом ушел
бы подписчикам.

Снимаем post_preview/post_approved, чтобы карточка собрала пост заново из
текущих полей и прошла одобрение владельца снова — тот же прием, что
fix_g772c17d9_resend_2026_11_18.py (docs/intake_run.md, «Шаг 15: правка
задела то, что владелец видел»), только для deals_promoted.json.

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'ge1c5f194'


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    n = 0
    for k in ('post_preview', 'post_approved'):
        if k in card:
            card.pop(k)
            n += 1
    return n


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    n = apply(data)
    print('снято полей: %d' % n)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
