# -*- coding: utf-8 -*-
"""Приток: какие включенные ленты молчат или отвечают ошибкой.

ЗАЧЕМ. 27 ноября 2026 сверка источников нашла 12 включенных лент, от которых
13 дней не пришло ни одной записи (Forbes.ru, Retail.ru, AKM.RU, Sostav.ru,
New Retail, «Эксперт» и другие — по сотне карточек базы у каждой), и никто
этого не видел: забор печатает «Источников с ошибкой: N» в журнал часового
прогона, который человек не читает, а лента, отдающая вместо записей страницу
«вы не робот», ошибкой и вовсе не считалась. Этот скрипт — отдельный сигнал.

ДВА ИСТОЧНИКА ПРАВДЫ.
  * Живой запрос (по умолчанию): каждая включенная лента забирается и
    разбирается тем же кодом, что и забор (`fetch.fetch_source`). Находка —
    ошибка ответа, ответ без записей или новейшая запись старше порога
    (лента «застыла»: TAdviser отвечал, но последняя запись была месячной
    давности). Работает и там, где сырья на диске нет (новая сессия рутины).
  * Сырье на диске (`--disk`, без сети): лента, от которой в
    `data/inbox/raw/*.jsonl` нет записей за порог дней. Годится только там,
    где сырье копится (сессия забора); если сырье покрывает меньше дней, чем
    порог, о ленте без записей честно сказано «судить рано», а не «молчит».

ПОРОГ. 7 дней; у источника, который пишет редко (сайт юрфирмы, малый
телеграм-канал), свой — поле `quiet_days` в `sources.json`.

УЖЕ ИЗВЕСТНАЯ ПОЛОМКА. У ленты, для которой рабочего адреса нет (капча,
401), в реестре стоит `broken_note` — причина словами. Такая лента печатается
отдельной строкой и код возврата не поднимает: иначе проверка краснела бы
каждый день по одному и тому же поводу, и ее перестали бы читать. Лента
ожила — скрипт скажет, что пометку пора снять.

КОД ВОЗВРАТА. 0 — новых находок нет; 1 — есть молчащие или сломанные ленты;
2 — проверка не состоялась (сеть до источников закрыта: не ответило больше
половины лент) — это не находка о лентах.

Запуск:
    python3 pipeline/ingest/feeds_health.py            # живой запрос
    python3 pipeline/ingest/feeds_health.py --disk     # по сырью на диске, без сети
    python3 pipeline/ingest/feeds_health.py --days 3   # другой порог по умолчанию
    python3 pipeline/ingest/feeds_health.py --only web:retail.ru
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch  # noqa: E402

DEFAULT_DAYS = 7


def threshold(src, default=DEFAULT_DAYS):
    try:
        return int(src.get('quiet_days') or default)
    except (TypeError, ValueError):
        return default


def judge_live(src, items, err, today, default=DEFAULT_DAYS):
    """Вердикт по живому ответу ленты: None (все в порядке) или
    {'kind': 'error'|'silent', 'days': N|None, 'why': строка для человека}."""
    if err:
        return {'kind': 'error', 'days': None, 'err': err, 'why': 'отвечает ошибкой: %s' % err}
    days = [d for d in (fetch.published_day(i.get('published')) for i in items) if d]
    if not days:
        return None            # дат в ленте нет — по живому ответу судить нечем
    age = (today - max(days)).days
    if age > threshold(src, default):
        return {'kind': 'silent', 'days': age, 'why': 'молчит %d дн.: новейшая запись от %s'
                % (age, max(days).isoformat())}
    return None


def raw_index(raw_dir):
    """(последний день с записью по источнику, все дни, за которые есть сырье)."""
    last, span = {}, set()
    if not os.path.isdir(raw_dir):
        return last, span
    for name in sorted(os.listdir(raw_dir)):
        if not name.endswith('.jsonl') or name.endswith('-articles.jsonl'):
            continue
        file_day = fetch.published_day(name[:10])
        if file_day:
            span.add(file_day)
        for line in open(os.path.join(raw_dir, name), encoding='utf-8'):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            day = fetch.published_day(row.get('fetched')) or file_day
            sid = row.get('source_id')
            if sid and day and (sid not in last or day > last[sid]):
                last[sid] = day
    return last, span


def judge_disk(src, last, span, today, default=DEFAULT_DAYS):
    """Вердикт по сырью на диске. Третий исход — {'kind': 'unknown'}: сырье
    покрывает меньше порога, и отсутствие записей ничего не доказывает."""
    limit = threshold(src, default)
    seen = last.get(src['id'])
    if seen:
        age = (today - seen).days
        if age > limit:
            return {'kind': 'silent', 'days': age,
                    'why': 'молчит %d дн.: последняя запись в сырье от %s' % (age, seen.isoformat())}
        return None
    covered = (today - min(span)).days if span else 0
    if covered >= limit:
        return {'kind': 'silent', 'days': covered,
                'why': 'молчит не меньше %d дн.: в сырье с %s нет ни одной записи'
                % (covered, min(span).isoformat())}
    return {'kind': 'unknown', 'days': None,
            'why': 'сырья на диске %d дн., судить рано' % covered}


def plain_reason(err):
    """Ошибка забора словами для человека: без «HTTP», «URLError» и скобок."""
    err = str(err or '')
    if err.startswith('HTTP 404'):
        return 'адрес ленты больше не существует'
    if err.startswith(('HTTP 401', 'HTTP 403')):
        return 'сайт закрыл доступ к ленте'
    if err.startswith('HTTP '):
        return 'сайт отвечает ошибкой %s' % err[5:8]
    if err.startswith('вместо ленты'):
        return 'вместо новостей приходит страница сайта'
    if err.startswith(('пустой ответ', 'в ответе нет')):
        return 'ответ приходит без новостей'
    return 'нет связи с сайтом'


def days_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return 'день'
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return 'дня'
    return 'дней'


def report_lines(findings):
    """Строки для отчета рутины, простым языком: «лента <издание> молчит N дней»."""
    out = []
    for src, verdict in findings:
        # У издания бывает несколько лент под одним именем («Коммерсантъ»:
        # новости, газета, раздел «Бизнес») — тогда называем и ленту.
        name = src['name']
        tail = src['id'].split('/', 1)[1] if '/' in src['id'] else ''
        if tail:
            name = '%s (%s)' % (name, tail)
        if verdict['kind'] == 'silent':
            out.append('лента %s молчит %d %s' % (name, verdict['days'], days_word(verdict['days'])))
        else:
            out.append('лента %s не работает: %s' % (name, plain_reason(verdict.get('err'))))
    return out


def check(sources, mode='live', today=None, default=DEFAULT_DAYS, fetcher=None, raw_dir=None):
    """Разбор всех включенных лент. Возвращает словарь:
    new — находки, о которых еще не знали; known — уже помеченные `broken_note`;
    revived — помеченные, но работающие; unknown — судить рано (только --disk);
    checked, failed — сколько лент проверено и сколько не ответило."""
    today = today or datetime.now(timezone.utc).date()
    fetcher = fetcher or fetch.fetch_source
    last, span = raw_index(raw_dir or fetch.RAW) if mode == 'disk' else ({}, set())
    res = {'new': [], 'known': [], 'revived': [], 'unknown': [], 'checked': 0, 'failed': 0}
    for src in sources:
        if not src.get('enabled') or not src.get('feed'):
            continue
        res['checked'] += 1
        if mode == 'disk':
            verdict = judge_disk(src, last, span, today, default)
        else:
            items, err = fetcher(src)
            if err and not str(err).startswith('HTTP 4'):
                # Обрыв связи бывает разовым («Connection reset» у живой ленты):
                # вторая попытка, прежде чем звать это находкой.
                items, err = fetcher(src)
            res['failed'] += bool(err)
            verdict = judge_live(src, items, err, today, default)
        if verdict and verdict['kind'] == 'unknown':
            res['unknown'].append((src, verdict))
        elif verdict and src.get('broken_note'):
            res['known'].append((src, verdict))
        elif verdict:
            res['new'].append((src, verdict))
        elif src.get('broken_note') and mode != 'disk':
            res['revived'].append((src, None))
    return res


def exit_code(res, mode='live'):
    if mode != 'disk' and res['checked'] >= 4 and res['failed'] * 2 > res['checked']:
        return 2
    return 1 if res['new'] else 0


def main(argv):
    mode = 'disk' if '--disk' in argv else 'live'
    default, only = DEFAULT_DAYS, None
    if '--days' in argv:
        default = int(argv[argv.index('--days') + 1])
    if '--only' in argv:
        only = argv[argv.index('--only') + 1]
    sources = [s for s in fetch.load_sources() if not only or s.get('id') == only]
    res = check(sources, mode=mode, default=default)
    code = exit_code(res, mode)

    print('Включенных лент проверено: %d (%s)' % (
        res['checked'], 'по сырью на диске' if mode == 'disk' else 'живым запросом'))
    if code == 2:
        print('ПРОВЕРКА НЕ СОСТОЯЛАСЬ: не ответило %d из %d лент — похоже, из этой среды '
              'сеть до источников закрыта. О лентах это ничего не говорит.'
              % (res['failed'], res['checked']))
        return code
    if res['new']:
        print('\nМОЛЧАТ ИЛИ СЛОМАНЫ (%d):' % len(res['new']))
        for src, verdict in res['new']:
            print('  %-28s %s' % (src['id'], verdict['why']))
        print('\nСтроки в отчет рутины:')
        for line in report_lines(res['new']):
            print('  ' + line)
    else:
        print('Новых молчащих и сломанных лент нет.')
    if res['known']:
        print('\nИзвестно, рабочего адреса нет (%d) — в отчет не нести:' % len(res['known']))
        for src, verdict in res['known']:
            print('  %-28s %s' % (src['id'], src['broken_note']))
    if res['revived']:
        print('\nОЖИЛИ — снять `broken_note` в sources.json (%d):' % len(res['revived']))
        for src, _ in res['revived']:
            print('  %-28s' % src['id'])
    if res['unknown']:
        print('\nСудить рано, сырья на диске меньше порога (%d): %s' % (
            len(res['unknown']), ', '.join(s['id'] for s, _ in res['unknown'][:12])
            + (' …' if len(res['unknown']) > 12 else '')))
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
