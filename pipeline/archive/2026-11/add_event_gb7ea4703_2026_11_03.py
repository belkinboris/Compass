# -*- coding: utf-8 -*-
"""Карточка gb7ea4703: добавляет событие о первом публичном комментарии
совладельца «Марии-Ра» Александра Ракшина (сделки пока нет, переговоры не
отрицает). Источник — НГС, 02.11.2026 (сохранен fetch_article_texts.py).
Не веха (kind=negotiations, не из POSTWORTHY_MILESTONE_KINDS) — обычное
дополнение ленты сделки, без отдельного поста.

Карточка: gb7ea4703. Запуск: python3 add_event_gb7ea4703_2026_11_03.py --write
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NOTE = ('Совладелец «Марии-Ра» Александр Ракшин впервые прокомментировал СМИ возможную '
        'продажу сети «Ленте»: сказал, что сделки пока нет, но факт переговоров не '
        'отрицает — «Обещать — не значит жениться».')


def main():
    write = '--write' in sys.argv[1:]
    data = json.load(open(DATA, encoding='utf-8'))
    found = False
    for c in data['deals']:
        if c['id'] == 'gb7ea4703':
            found = True
            events = c.setdefault('events', [])
            if any(e.get('note') == NOTE for e in events):
                print('Уже есть.')
                return
            events.append({
                'kind': 'negotiations',
                'date': '2026-11-02',
                'title': 'Владелец впервые прокомментировал переговоры',
                'note': NOTE,
                'source': ['НГС', 'https://ngs.ru/text/business/2026/11/02/76738898/'],
            })
    if not found:
        raise SystemExit('gb7ea4703 не найдена')
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
