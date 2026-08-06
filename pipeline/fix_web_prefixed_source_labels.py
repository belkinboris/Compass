# -*- coding: utf-8 -*-
"""Подпись источника «web:kommersant.ru» -> «Коммерсантъ».

ЧТО СЛОМАНО. Приток подписывал источник новой карточки внутренним id ленты
(«web:<домен>» из sources.json), и этот id доезжал до экрана: владелец
открыл карточку «Нейропотока» и увидел «web:kommersant.ru» вместо имени
издания. Правило уже записано в CLAUDE.md («подпись — имя издания по
домену ссылки»), просто путь притока о нём не знал.

ЧТО ДЕЛАЕТ. Во всех карточках базы и очереди предпросмотра заменяет подпись
вида «web:<домен>» на имя издания по домену САМОЙ ССЫЛКИ (не по id: id мог
быть шире, чем конкретная статья). Таблица имён — pipeline/source_names.py.
promote.py той же таблицей подписывает новые карточки, так что дефект не
вернётся со следующим прогоном притока.

Запуск:
    python3 pipeline/fix_web_prefixed_source_labels.py            # сухой прогон
    python3 pipeline/fix_web_prefixed_source_labels.py --write    # записать
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from source_names import edition_label  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
WEB_LABEL = re.compile(r'^web:[\w.\-]+$')


def fix_cards(cards, where):
    changed = 0
    for card in cards:
        pairs = list(card.get('src') or [])
        # Метка живёт не только в src: у этапов сделки (events) свой источник,
        # и «Источники этого этапа» на экране печатают его подпись. Первый
        # прогон это место пропустил — «web:frankmedia.ru» остался на карточке
        # JPMorgan в блоке этапа.
        for ev in card.get('events') or []:
            if isinstance(ev.get('source'), list):
                pairs.append(ev['source'])
        for s in pairs:
            if len(s) > 1 and WEB_LABEL.match(str(s[0])) and str(s[1]).startswith('http'):
                new = edition_label(s[1])
                assert new and not new.startswith('web:'), (card.get('id'), s)
                print('  %-8s %-11s %-22s -> %s' % (where, card.get('id'), s[0], new))
                s[0] = new
                changed += 1
    return changed


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else None
    n = fix_cards(data['deals'], 'база')
    m = fix_cards(pending['cards'], 'pending') if pending else 0
    print('Заменено подписей: %d в базе, %d в предпросмотре.' % (n, m))
    if not (n or m):
        print('Заменять нечего.')
        return 0
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if pending:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
