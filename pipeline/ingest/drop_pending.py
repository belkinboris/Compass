"""Выкинуть из очереди карточку, которая не сделка, — без вопроса владельцу.

Владелец 24 октября 2026, про 42 вопроса в консоли («Аукцион вещей Брижит
Бардо», «Единороссы получили 86% кресел», «Райан Рейнольдс купил паб»):
«Что за бред нам в консоль пришел? … раньше же все такое удалялось просто».

Раньше мусор отсеивался на шаге сырья (`raw_screen.py --drop`, рутина решает
сама). Эти 42 в 21 сентября — 14 октября проскочили сырье уже карточками
(`pending.json`), а у приемки (`accept_card.py`) есть только «принять» и
«придержать» — месяц они висели в «придержанных», а вечером 24 октября рутина
публикации, не имея права их выкинуть, отправила владельцу 42 вопроса.

Этот скрипт — то же «выкинуть», что кнопка владельца (`approve.py`, вердикт
`discard`): карточка уходит из очереди насовсем, адреса ее источников
запоминаются в `discarded_urls`, чтобы та же новость не вернулась под новым id.
Отметка `by: routine` отличает решение рутины от решения человека.

КОГДА МОЖНО: не сделка уверенно — знаменитости и личные покупки, сувениры и
аукционы вещей, выборы и политика, макростатистика, операции ЦБ с валютой,
закупки оборудования, иностранная сделка без российской стороны. Сомнение —
не выкидывать: один вопрос владельцу со СПИСКОМ, а не по сообщению на карточку
(`routines/publication.md`, приемка).

    python3 pipeline/ingest/drop_pending.py g1 g2 --reason "не сделка: …"          # сухой прогон
    python3 pipeline/ingest/drop_pending.py g1 g2 --reason "не сделка: …" --write
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def drop(pending, state, ids, reason, now):
    cards = {c['id']: c for c in pending['cards']}
    missing = [i for i in ids if i not in cards]
    assert not missing, 'нет в очереди: %s' % missing
    for i in ids:
        card = cards[i]
        for s in card.get('src') or []:
            if len(s) > 1 and str(s[1]).startswith('http'):
                state.setdefault('discarded_urls', {})[str(s[1])] = {
                    'id': i, 'title': card.get('title'), 'by': 'routine', 'reason': reason,
                    'at': now.isoformat(timespec='seconds')}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in set(ids)]
    return [cards[i] for i in ids]


def drop_fix_files(ids):
    """Файлы правок выкинутых карточек больше никому не нужны (бэклог A25)."""
    import fix_files
    for i in ids:
        for path in fix_files.drop_fixes_for(i):
            print('  снят файл правок %s' % os.path.relpath(path, ROOT))


def merge_target(card_id, reason, dropped=()):
    """С какой карточкой слита выкинутая — или None, если из причины это не
    следует однозначно (6 ноября 2026: одной командой сняли два дубля с общей
    причиной «gf18c700f — та же сделка, что g1eda1117 …; gc3faa809 — та же
    сделка, что g9b4c2e71 …», и обе новости владельцу отослали к первому
    номеру в тексте — к самой выкинутой gf18c700f). Номер самой карточки и
    других выкинутых целью не бывает; если причина называет карточку, цель
    ищется в ее куске — до номера следующей выкинутой."""
    import re
    ids_re = r'\bg[0-9a-f]{8}\b'
    text = reason or ''
    gone = set(dropped) | {card_id}
    at = text.find(card_id)
    if at >= 0:
        rest = text[at + len(card_id):]
        cut = [m.start() for m in re.finditer(ids_re, rest) if m.group(0) in gone]
        text = rest[:cut[0]] if cut else rest
    found = [m for m in re.findall(ids_re, text) if m not in gone]
    return found[0] if len(set(found)) == 1 else None


def closure_text(card, reason, dropped=(), base_ids=None, pending_ids=None):
    """Что сказать владельцу, если выкинутая карточка родилась из его «в работу».
    Слияние — ссылка на ту карточку: в базе — страница сделки, в очереди —
    предпросмотр; цель неоднозначна или ее нет нигде — без ссылки, с причиной."""
    raw = card.get('from_raw') or {}
    if not raw:
        return None
    merged = merge_target(card.get('id', ''), reason, dropped)
    head = 'Ваше решение «это сделка» по новости «%s» применено.' % (raw.get('title') or card.get('title') or '')[:120]
    if merged and (base_ids is None or merged in base_ids):
        return ('%s Это та же сделка, что уже есть в базе: https://projectcompass.ru/#/deal/%s — новое из новости '
                'добавлено в ту карточку, отдельной карточки и поста не будет.' % (head, merged))
    if merged and pending_ids is not None and merged in pending_ids:
        return ('%s Это та же сделка, что карточка на проверке: https://projectcompass.ru/#/preview/%s — новое из '
                'новости добавлено туда, отдельной карточки и поста не будет.' % (head, merged))
    return '%s Но карточку пришлось снять: %s.' % (head, (reason or '').strip().rstrip('.'))


def notify_console(texts):
    """Короткие ответы владельцу в консоль (тема решений). Нет токена — только на экран."""
    if not texts:
        return
    import send_drafts
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    import console_topics
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = send_drafts.send_targets()
    if not token or not chats:
        print('Консоль не настроена — ответ владельцу только на экране:\n  ' + '\n  '.join(texts))
        return
    import httpx
    thread = console_topics.thread_id('decision')
    with httpx.Client(timeout=20) as client:
        for chat in chats:
            for t in texts:
                send_drafts.send_one(client, token, chat, '↩️ ' + t, None, thread)


def main(argv):
    write = '--write' in argv
    reason = argv[argv.index('--reason') + 1] if '--reason' in argv else ''
    assert reason.strip(), 'нужна причина: --reason "не сделка: …"'
    ids = [a for a in argv if a.startswith(('g', 'c')) and a not in (reason,) and not a.startswith('--')]
    pending = json.load(open(PENDING, encoding='utf-8'))
    state = promote.load_state()
    gone = drop(pending, state, ids, reason, datetime.now(timezone.utc))
    for c in gone:
        print('  ВЫКИНУТА  %-11s %s' % (c['id'], str(c.get('title'))[:70]))
    print('Выкинуто из очереди: %d, осталось в очереди: %d.' % (len(gone), len(pending['cards'])))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    pending_fresh = json.load(open(PENDING, encoding='utf-8'))   # перечитать прямо перед записью
    state = promote.load_state()
    gone = drop(pending_fresh, state, ids, reason, datetime.now(timezone.utc))
    drop_fix_files(ids)
    json.dump(pending_fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    promote.save_state(state)
    # Карточка из решения владельца («в работу») выкинута или слита — он должен
    # узнать об этом из консоли, а не из тишины (28 октября 2026, «Аккую»).
    base_ids = {d.get('id') for d in json.load(open(BASE, encoding='utf-8')).get('deals', [])}
    pending_ids = {c.get('id') for c in pending_fresh['cards']}
    notify_console([t for t in (closure_text(c, reason, ids, base_ids, pending_ids) for c in gone) if t])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
