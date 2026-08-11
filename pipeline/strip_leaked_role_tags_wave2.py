# -*- coding: utf-8 -*-
"""Вторая волна снятия протёкшей пометки роли (см.
`strip_leaked_role_tags_all.py`, 234 карточки, прогон 11 августа) — та же
разметка, но с текстом ПОСЛЕ слова роли внутри внутренних скобок:
«(IHC (покупатель потенциальный))», «(Сбербанк Инвестиции (продавец
доли))», «(ГК «Астра» (покупатель через дочернюю компанию SL Soft))».
Первый прогон ловил только ГОЛОЕ слово роли в скобках и такие пропустил.

Найдено при проверке карточки g75920ee3 (IHC/ЛУКОЙЛ) в рамках партии
глубокого дочитывания — тот же принцип: находка не существует в вакууме,
проверить, где дефект есть ещё (CLAUDE.md).

Регулярка расширена (слово роли + до 40 знаков произвольного текста внутри
внутренних скобок) и проверена на выборке — не трогает предшествующие
легитимные скобки вроде «(экспертная оценка, не подтверждённая
сторонами)», ловит только последний хвост в конце строки.

Запуск: python3 pipeline/strip_leaked_role_tags_wave2.py           # проверка
        python3 pipeline/strip_leaked_role_tags_wave2.py --write   # запись
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TAG_RX = re.compile(
    r'\s*\([^()]{2,80}\((?:продавец|покупатель)[^()]{0,40}\)\)\s*$', re.I)

EXPECTED_CARDS = 32


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    todo = {}
    for d in data['deals']:
        changes = {}
        r = (d.get('eco') or {}).get('rationale')
        if isinstance(r, str) and TAG_RX.search(r):
            changes['rationale'] = TAG_RX.sub('', r).rstrip()
        e = d.get('extra')
        if isinstance(e, str) and TAG_RX.search(e):
            changes['extra'] = TAG_RX.sub('', e).rstrip()
        if changes:
            todo[d['id']] = changes

    assert len(todo) == EXPECTED_CARDS, (
        'ожидалось %d карточек с протёкшей пометкой роли (волна 2), '
        'найдено %d — состояние базы изменилось, проверьте список заново'
        % (EXPECTED_CARDS, len(todo)))

    cards = {d['id']: d for d in data['deals']}
    for cid, changes in todo.items():
        print('ПРАВИМ  %s: снята протёкшая пометка роли (%s)'
              % (cid, ', '.join(sorted(changes))))
    if not write:
        print('Сухой прогон. Запись — с ключом --write. Карточек: %d' % len(todo))
        return

    for cid, changes in todo.items():
        card = cards[cid]
        if 'rationale' in changes:
            card['eco']['rationale'] = changes['rationale']
        if 'extra' in changes:
            card['extra'] = changes['extra']
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: %d карточек.' % len(todo))


if __name__ == '__main__':
    main(write='--write' in sys.argv)
