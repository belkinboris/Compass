# -*- coding: utf-8 -*-
"""18 сентября 2026 — дубль «ЦОД СПб» (ge92b1463) всё же попал в базу.

Владелец сказал прямо: «Про цод спб точно две. Одну одобрил вторую тогда
выкидываю, но говорю тебе» — и переслал текст консольного сообщения по
ge92b1463. Пока это решение прорабатывалось (слияние источника и структуры
собственности «ЦОД СПб» в уже существующую карточку gf080e8f0, живущую в
базе с 11 сентября), параллельная сессия рутины «публикация» независимо
применила решения консоли и в их числе — «✅ Опубликовать» по ge92b1463
(коммит 6f3cb31, «Публикация: 6 карточек из решений консоли»): карточка
уехала из pending.json прямо в deals_promoted.json, минуя дедуп, потому что
никто в тот момент ещё не связал её с gf080e8f0.

Факт не потерян — второй источник (Mergers.ru) и структура собственности
уже перенесены в gf080e8f0 (pipeline/ingest/fixes/batch_codspb_merge_2026_
09_18.py, pipeline/fix_codspb_event_date_and_ownership_followup.py) ДО
этого скрипта. Здесь — только удаление самого дубля из базы, с сохранением
ссылки в `merged` (правило CLAUDE.md: «Слияние карточек не должно обрывать
ссылку»). Постов в канал по ge92b1463 не было (no_post: true, в
telegram_posts записи нет) — отменять в Telegram нечего. Записей в таблице
FIXES с id='ge92b1463' нет ни в одном файле pipeline/ingest/fixes/ (grep
проверен перед записью) — снимать нечего.

Запуск: python3 pipeline/discard_codspb_duplicate_published_by_mistake.py [--write]
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DUP_ID = 'ge92b1463'
SURVIVOR_ID = 'gf080e8f0'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))

    matches = [d for d in data['deals'] if d['id'] == DUP_ID]
    assert len(matches) == 1, 'ожидали ровно одну карточку %r, нашли %d' % (DUP_ID, len(matches))
    dup = matches[0]
    assert dup.get('no_post') is True, 'у дубля есть no_post=False — проверьте, не ушёл ли пост в канал'
    assert DUP_ID not in data.get('merged', {}), 'ссылка на дубль уже стоит в merged'

    survivor_matches = [d for d in data['deals'] if d['id'] == SURVIVOR_ID]
    assert len(survivor_matches) == 1, 'карточки-survivor %r не нашли' % SURVIVOR_ID

    data['deals'] = [d for d in data['deals'] if d['id'] != DUP_ID]
    data.setdefault('merged', {})[DUP_ID] = SURVIVOR_ID

    print('%s удалена из deals (%d -> %d записей)' % (DUP_ID, len(matches) + len(data['deals']), len(data['deals'])))
    print('merged[%r] = %r' % (DUP_ID, SURVIVOR_ID))

    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
