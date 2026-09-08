# -*- coding: utf-8 -*-
"""Продолжение fix_mini_ranking_dates_batch1.py/batch2.py: карточка
`cb30dbbc8` («Яндекс»/SolidSoft, СП по кибербезопасности) оставалась с
датой-заглушкой «2025-09-30» (дата публикации рэнкинга «Ъ — Сделки
года», а не дата самой сделки) — на момент прошлых партий точная дата
не нашлась. Найдено 8 сентября 2026 (месячная очередь): точная дата
объявления сделки — 18 июля 2025 года, подтверждена личным WebFetch
(interfax.ru/business/1036868, «13:49, 18 июля 2025»: «Yandex B2B Tech,
бизнес-группа "Яндекса", создает совместное предприятие (СП) с
компанией SolidSoft»), независимо подтверждена по URL-слагам ещё
нескольких изданий того же дня (rbc.ru/.../18/07/2025/…,
anti-malware.ru/news/2025-07-18-121598/…).

Год не переносится (2025 -> 2025), поэтому это уточнение дня/месяца
внутри уже известного года — тот же класс правки, что и в предыдущих
двух партиях.

Запуск:
    python3 pipeline/fix_mini_ranking_dates_batch3.py            # сухой прогон
    python3 pipeline/fix_mini_ranking_dates_batch3.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

FIXES = [
    dict(id='cb30dbbc8', old='2025-09-30', new='2025-07-18',
         quote='Интерфакс, 13:49, 18 июля 2025: «Yandex B2B Tech, '
               'бизнес-группа "Яндекса", создает совместное предприятие '
               '(СП) с компанией SolidSoft»'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for fx in FIXES:
        deal = by_id.get(fx['id'])
        assert deal is not None, 'нет сделки %s' % fx['id']
        assert deal.get('date') == fx['old'], \
            '%s: дата уже другая: %r, ожидали %r' % (
                fx['id'], deal.get('date'), fx['old'])
        print('%s: date %r -> %r' % (fx['id'], fx['old'], fx['new']))
        print('  цитата: %r' % fx['quote'])

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for fx in FIXES:
        by_id[fx['id']]['date'] = fx['new']
        assert by_id[fx['id']]['date'] == fx['new'], 'дата не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
