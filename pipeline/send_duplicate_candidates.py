# -*- coding: utf-8 -*-
"""Показать в консоли пары карточек, похожие на одну сделку, и спросить решение.

ЗАЧЕМ. 8 сентября 2026 владелец нашёл дубль про ТРК «Родник» и «Алмаз» сам —
две карточки одной сделки, написанные со стороны продавца и со стороны
покупателя. Починка ворот (`promote.near_duplicate` научился сверять имена из
заголовка новой карточки с именами из ТЕЛА старой) тем же вечером нашла в базе
ещё три пары того же вида, которых не видел никто. Слить их молча нельзя:
сканер дублей — список для чтения, а не приговор (две покупки по 25% одной
компании в одном году — консолидация, а не дубль). Решение принимает человек,
и просьба владельца прямая: «Отправь эти три нам в приватный чат, мы примем
решение».

КАК ВОЗВРАЩАЕТСЯ ОТВЕТ. Каждое сообщение несёт маркер `[карточка <id>]` — тот
же, что у открытых вопросов: ответ владельца или партнёра приходит вебхуком
как ЗАМЕТКА к этой карточке, и её забирает `pipeline/ingest/read_notes.py` в
ближайший прогон притока. Отдельных кнопок у пары нет намеренно: «слить» —
это не одно нажатие, а спецификация с тем, какие поля переносятся
(`pipeline/merge_duplicate_deals_batch.py`), и её всё равно пишет рутина по
ответу человека.

ЧТО ШЛЁТСЯ. Ровно то, что сейчас печатает
`pipeline/find_duplicate_deal_candidates.py`, — прочитанные и признанные
разными пары из его же `NOT_DUPLICATES` не шлются никогда. Отправленное
помнится в `pipeline/duplicate_candidates_sent.json` (в git: контейнер рутины
одноразовый), поэтому шаг можно ставить в рутину, не превращая его в
ежечасное напоминание об одной и той же паре.

Запуск:
    python3 pipeline/send_duplicate_candidates.py            # сухой прогон
    python3 pipeline/send_duplicate_candidates.py --write    # отправить
    python3 pipeline/send_duplicate_candidates.py --again --write   # ещё раз
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'pipeline'))
sys.path.insert(0, str(ROOT / 'pipeline' / 'ingest'))

import console_topics                                    # noqa: E402
from send_drafts import send_one, PAUSE                  # noqa: E402
from find_duplicate_deal_candidates import candidates, NOT_DUPLICATES  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
STATE = ROOT / 'pipeline' / 'duplicate_candidates_sent.json'
SITE = 'https://projectcompass.ru/#/deal/'

HEADER = (
    'Нашлись пары карточек, которые похожи на одну и ту же сделку, описанную '
    'дважды — обычно один раз со стороны продавца, другой со стороны '
    'покупателя.\n\n'
    'По каждой паре нужен ваш ответ: это одна сделка или всё-таки две? '
    'Ответьте на сообщение — «одна» или «две», можно с пояснением. Если одна, '
    'мы объединим карточки в одну с этапами и сохраним все факты из обеих.'
)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    return {'sent': {}, 'header_sent': False}


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True),
                     encoding='utf-8')


def key_of(pair):
    return '~'.join(sorted(pair))


def days_between(a, b):
    from datetime import date
    try:
        pa = date(*[int(x) for x in str(a)[:10].split('-')])
        pb = date(*[int(x) for x in str(b)[:10].split('-')])
    except (ValueError, TypeError):
        return None
    return abs((pa - pb).days)


def plural_days(n):
    """«1 день», «2 дня», «5 дней», «22 дня», «11 дней» — обычное русское
    согласование: решает последняя цифра, кроме чисел, кончающихся на 11-14."""
    if 11 <= n % 100 <= 14:
        return 'дней'
    last = n % 10
    return 'день' if last == 1 else 'дня' if 2 <= last <= 4 else 'дней'


def why_human(pair, by):
    """Почему пара попала в список — словами, а не нашей механикой.

    Правило репозитория «язык для людей»: в консоль нельзя выносить
    нормализованные ключи сопоставления («росспиртпр», «зельгрос росси») —
    человек читает их как опечатку, а не как причину.
    """
    a, b = (by[cid] for cid in sorted(pair))
    parts = ['в обеих карточках названы одни и те же компании']
    gap = days_between(a.get('date'), b.get('date'))
    if gap is not None:
        parts.append('даты расходятся на %d %s' % (gap, plural_days(gap)))
    if a.get('sum') and a.get('sum') == b.get('sum'):
        parts.append('сумма одна и та же')
    return ', '.join(parts)


def render(pair, why, by, num, total):
    a, b = sorted(pair)
    lines = ['[карточка %s] Одна сделка или две? (%d из %d)' % (a, num, total), '']
    for cid in (a, b):
        d = by[cid]
        money = d.get('sum') or 'сумма не раскрыта'
        lines.append('• %s' % (d.get('title') or cid))
        lines.append('  %s · %s · %s' % (d.get('date') or 'дата неизвестна',
                                         money, d.get('status') or 'статус не указан'))
        lines.append('  %s%s' % (SITE, cid))
        lines.append('')
    lines.append('Почему обратили внимание: %s.' % why_human(pair, by))
    return '\n'.join(lines)


def main(argv):
    write = '--write' in argv
    again = '--again' in argv

    data = json.loads(DATA.read_text(encoding='utf-8'))
    by = {d['id']: d for d in data['deals']}
    found = {pair: why for pair, why in candidates(data['deals']).items()
             if pair not in NOT_DUPLICATES and pair <= set(by)}
    state = load_state()
    todo = [(p, w) for p, w in sorted(found.items(), key=lambda kv: sorted(kv[0]))
            if again or key_of(p) not in state['sent']]

    if not found:
        print('Кандидатов нет — сканер чист.')
        return 0
    print('Кандидатов всего: %d, к отправке: %d' % (len(found), len(todo)))
    if not todo:
        print('Все пары уже отправлены. Повторить — с ключом --again.')
        return 0

    texts = [(p, render(p, w, by, i + 1, len(todo))) for i, (p, w) in enumerate(todo)]
    if not write:
        print('\n' + HEADER)
        for _, text in texts:
            print('\n' + '-' * 60 + '\n' + text)
        print('\nСухой прогон. Отправить — с ключом --write.')
        return 0

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = console_topics.console_chats()
    if not token or not chats:
        print('Отправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.')
        return 1

    import httpx
    thread = console_topics.thread_id('decision')
    sent = 0
    with httpx.Client(timeout=20) as client:
        if not state.get('header_sent'):
            if all(send_one(client, token, chat, HEADER, None, thread) for chat in chats):
                state['header_sent'] = True
                save_state(state)
                time.sleep(PAUSE)
        for i, (pair, text) in enumerate(texts):
            ok = all(send_one(client, token, chat, text, None, thread) for chat in chats)
            if ok:
                state['sent'][key_of(pair)] = True
                save_state(state)
                sent += 1
            print('  %s %s' % ('отправлено' if ok else 'НЕ ДОШЛО', key_of(pair)))
            if i < len(texts) - 1:
                time.sleep(PAUSE)
    print('Отправлено пар: %d из %d' % (sent, len(texts)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
