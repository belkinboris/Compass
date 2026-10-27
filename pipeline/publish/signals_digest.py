# -*- coding: utf-8 -*-
"""Еженедельная подборка «Кто готовится к сделкам: N компаний и почему».

ЗАЧЕМ. Партнер владельца (19 октября 2026): читателю полезно знать, у кого
вероятна сделка, — но доводами, а не процентом. Подборка берет признаки из
`static/data/signals.json` (`pipeline/ingest/signals.py`): заявления компаний
о продаже, покупке, поиске инвестора, размещении акций и обсуждаемые сделки.

КТО ПОПАДАЕТ. Компания с двумя и больше признаками за последние 30 дней или
с одним сильным (сама заявила о продаже, выходе, размещении акций; актив
выставлен на торги — `signals.STRONG_KINDS`). Не больше `MAX_COMPANIES`,
свежие и с большим числом признаков — первыми. Каждая строка — факт с датой и
ссылкой на источник; имя компании — ссылкой на ее страницу на сайте.

ЧЕГО НЕ ДЕЛАЕТ. В канал не публикует и расписания не имеет: это решит
владелец. `--send-draft` кладет ЧЕРНОВИК в консоль, в тему «Подтверждение
постов», с обычными кнопками решения (`mod:digest~signals-<неделя>:post_ok`
/ `post_no` — та же форма, что у месячной сводки, поэтому сайт не примет
решение за пост об этапе сделки). Решение пока ничего не публикует.

Запуск:
    python3 pipeline/publish/signals_digest.py                 # текст подборки (сухой прогон)
    python3 pipeline/publish/signals_digest.py --send-draft    # черновик в консоль
    python3 pipeline/publish/signals_digest.py --date 2026-10-19
"""
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import format_post                                   # noqa: E402  (esc, SITE, buttons_preview)
import monthly_digest                                # noqa: E402  (plural)
import signals as signals_mod                        # noqa: E402  (STRONG_KINDS)

SITE = format_post.SITE
SIGNALS = os.path.join(ROOT, 'static', 'data', 'signals.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'signals_digest.json')

FRESH_DAYS = 30
MIN_SIGNALS = 2
MAX_COMPANIES = 8
MAX_LINES = 3
MONTHS_GEN = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа',
              'сентября', 'октября', 'ноября', 'декабря')
DISCLAIMER = ('Это заявления компаний и сделки, которые пока обсуждаются, а не прогноз: '
              'не каждая из них закончится сделкой.')


def _day(value):
    """Дата признака: «2026-10-12» или «2026-10» (первое число). Год — нет."""
    s = str(value or '')
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
            return date.fromisoformat(s)
        if re.fullmatch(r'\d{4}-\d{2}', s):
            return date.fromisoformat(s + '-01')
    except ValueError:
        return None
    return None


def _when(value, today):
    d = _day(value)
    if not d:
        return str(value or '')
    text = '%d %s' % (d.day, MONTHS_GEN[d.month - 1]) if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)) \
        else MONTHS_GEN[d.month - 1]
    return text if d.year == today.year else '%s %d' % (text, d.year)


def pick(rows, companies, today):
    """[(id компании, [признаки свежие первыми])] — кто попадает в подборку."""
    since = today - timedelta(days=FRESH_DAYS)
    by_company = {}
    for r in rows:
        d = _day(r.get('date'))
        if not d or d < since or d > today + timedelta(days=1):
            continue
        cid = r.get('company_id')
        if cid not in companies:
            continue
        by_company.setdefault(cid, []).append(r)
    out = []
    for cid, items in by_company.items():
        items.sort(key=lambda r: str(r.get('date') or ''), reverse=True)
        strong = any(r.get('kind') in signals_mod.STRONG_KINDS for r in items)
        if len(items) >= MIN_SIGNALS or strong:
            out.append((cid, items))
    out.sort(key=lambda x: (len(x[1]), str(x[1][0].get('date') or '')), reverse=True)
    return out[:MAX_COMPANIES]


def _line(sig, cid, today):
    esc = format_post.esc
    text = str(sig.get('summary') or '')
    if sig.get('company_id') == cid:
        text = re.sub(r'^.*?\s—\s', '', text, count=1)
    parts = ['• %s — %s' % (_when(sig.get('date'), today), esc(text))]
    src = sig.get('source') or []
    if len(src) >= 2 and str(src[1]).startswith('http'):
        parts.append('(<a href="%s">%s</a>)' % (esc(src[1]), esc(src[0] or 'источник')))
    return ' '.join(parts)


def render(rows, companies, today):
    """Текст поста; пусто, если подбирать некого."""
    chosen = pick(rows, companies, today)
    if not chosen:
        return ''
    esc = format_post.esc
    n = len(chosen)
    lines = ['🧭 <b>Кто готовится к сделкам: %d %s и почему</b>'
             % (n, monthly_digest.plural(n, 'компания', 'компании', 'компаний')), '']
    for cid, items in chosen:
        name = (companies.get(cid) or {}).get('name') or cid
        lines.append('<b><a href="%s/#/companies/%s">%s</a></b>' % (SITE, cid, esc(name)))
        for sig in items[:MAX_LINES]:
            lines.append(_line(sig, cid, today))
        lines.append('')
    lines.append(DISCLAIMER)
    lines.append('')
    lines.append('#MA #планы')
    return '\n'.join(lines)


def render_buttons():
    return {'inline_keyboard': [[{'text': 'Компании на «Компасе»', 'url': '%s/#/companies' % SITE}]]}


# Служебные слова и гадание — в подборку не выходят.
_FORBIDDEN = re.compile(r'\bundefined\b|\bnull\b|\bNaN\b|сигнал|линз|знаменател|вероятн|шанс\w*|\d\s*%|прогнозир', re.I)


def check(text):
    """Вычитка подборки: [] — можно показывать."""
    problems = []
    if not text.strip():
        return ['подборка пуста']
    m = _FORBIDDEN.search(text)
    if m:
        problems.append('в тексте лишнее: «%s»' % m.group(0))
    if '/#/companies/' not in text:
        problems.append('нет ни одной ссылки на страницу компании')
    if 'не прогноз' not in text:
        problems.append('потеряна оговорка «не прогноз»')
    for line in text.split('\n'):
        if line.startswith('•') and '<a href=' not in line:
            problems.append('строка без источника: %s' % line[:80])
    return problems


def week_key(today):
    y, w, _ = today.isocalendar()
    return 'signals-%d-W%02d' % (y, w)


def draft_message(text, key):
    """Черновик в консоль: шапка, что это и что будет по кнопке, затем текст."""
    return ('🧭 [подборка %s] — пробный черновик\n'
            'Еженедельная подборка «Кто готовится к сделкам». Сама в канал она не уйдет: '
            'кнопка — ваше решение, нужна ли такая подборка в канале.\n'
            '━━━━━━━━━━━━\n%s\n\n%s'
            % (format_post.esc(key), text, format_post.esc(format_post.buttons_preview(render_buttons()))))


def keyboard(key):
    combo = 'digest~%s' % key
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:%s:post_ok' % combo},
        {'text': '🔕 Без поста', 'callback_data': 'mod:%s:post_no' % combo},
    ]]}


def _load(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def send_draft(text, key, force=False):
    """Черновик в консоль. True — отправлен хотя бы в один чат."""
    import console_topics                               # noqa: E402
    import send_drafts                                  # noqa: E402  (send_targets/send_one)
    state = _load(STATE, {})
    if key in state and not force:
        print('Черновик за %s уже отправлялся (%s). Повтор — с ключом --force.' % (key, state[key]))
        return False
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chats = send_drafts.send_targets()
    if not token or not chats:
        print('TELEGRAM_BOT_TOKEN или адрес консоли не заданы — показываю текст, не отправляю.')
        return False
    import httpx
    thread = console_topics.thread_id('decision')
    ok = False
    with httpx.Client(timeout=20) as client:
        for i, chat in enumerate(chats):
            if i:
                time.sleep(send_drafts.PAUSE)
            if send_drafts.send_one(client, token, chat, draft_message(text, key), keyboard(key), thread, html=True):
                ok = True
    if ok:
        state[key] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Черновик подборки %s отправлен в консоль.' % key)
    return ok


def main(argv):
    today = date.today()
    for i, a in enumerate(argv):
        if a == '--date' and i + 1 < len(argv):
            today = date.fromisoformat(argv[i + 1])
    rows = _load(SIGNALS, {}).get('signals') or []
    companies = _load(DATA, {}).get('companies') or {}
    text = render(rows, companies, today)
    key = week_key(today)
    if not text:
        print('Подборка за %s не собирается: свежих признаков мало.' % key)
        return 0
    problems = check(text)
    print('-' * 60)
    print(text)
    print('-' * 60)
    print(format_post.buttons_preview(render_buttons()))
    if problems:
        print('Вычитка не пропускает подборку: ' + '; '.join(problems))
        return 1
    if '--send-draft' in argv:
        send_draft(text, key, force='--force' in argv)
    else:
        print('Сухой прогон. Черновик в консоль — с ключом --send-draft.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
