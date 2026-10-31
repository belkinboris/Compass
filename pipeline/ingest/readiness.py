"""Готовность карточки к консоли и каналу — одно место (H3 аудита кода, 31 октября 2026).

До этого дня «карточка готова» было записано в восьми местах с разными
условиями: send_drafts.build_plan и его «ТУПИК», approve.plan_actions и его
«ТУПИК», accept_card.queue, second_reading.needs_second_reading, своя копия в
ops_status и две в main.py. Они расходились: approve не знал о втором чтении
(принятая после 9 октября без второго чтения печаталась «ТУПИК» и «ждем
решения», хотя ждала приток), три копии needs_second_reading по-разному
читали нестроковую `accepted`, send_drafts не смотрел `held`/`hold_reason`.

    from readiness import state, needs_second_reading, hours_pending, is_shown

`state(card)` отвечает, ЧЕГО карточка ждет, — одно слово по приоритету:

    held            — владелец придержал: ждет его решения
    doubted         — приемка не пропустила (`hold_reason` без `held`): ждет
                      решения человека, по молчанию не выходит никогда
    unreviewed      — не прочитана против источника (review.py)
    accepted_unread — принята, но не прочитана: тупик, а не очередь (OTP Bank,
                      4 октября 2026) — review.py --mark-read
    unaccepted      — прочитана, приемки нет (accept_card.py)
    unread2         — принята с SECOND_READING_SINCE, второго чтения нет и в
                      консоли не показана (second_reading.py)
    ready_unsent    — все есть, в консоли не показана: send_drafts.py --write
    shown           — показана в консоли (draft_sent): ждет решения или молчания

Показанность (`is_shown`) — отдельный признак: карточка, показанная до того,
как гейты стали обязательными, все равно числится `unreviewed`, потому что
ждет именно чтения; молчание ее не публикует (approve), а консоль не шлет
заново только то, что уже отправлено.

Кто зовет: send_drafts.build_plan (не показывает ничего, кроме ready_unsent;
его «ТУПИК» — accepted_unread), approve.plan_actions (молчание публикует только
shown; текст ожидания — по состоянию; его «ТУПИК» — ready_unsent),
accept_card.queue (unaccepted, unreviewed), second_reading.queue (unread2),
ops_status.queue_counts (Counter по состояниям), main._send_queue_batch.
Модуль без зависимостей: его импортирует и main.py.
"""
from datetime import datetime, timezone

SECOND_READING_SINCE = '2026-10-09'      # принятые с этого дня без второго чтения в консоль не идут
ACCEPTED, SECOND_READ = 'accepted', 'second_read'

STATES = ('held', 'doubted', 'unreviewed', 'accepted_unread', 'unaccepted',
          'unread2', 'ready_unsent', 'shown')
# Карточка ждет приток (чтение, приемку, второе чтение), а не человека.
WAITING_INTAKE = frozenset({'unreviewed', 'accepted_unread', 'unaccepted', 'unread2'})
# Что человеку говорит состояние, когда молчание карточку не публикует.
WAIT_TEXT = {
    'unreviewed': 'не прочитана против источника — молчание ее не публикует',
    'accepted_unread': 'принята, но не прочитана против источника (review.py --mark-read) — молчание ее не публикует',
    'unaccepted': 'не прошла приемку (accept_card.py) — молчание ее не публикует',
    'unread2': 'ждет второго чтения (second_reading.py) — молчание ее не публикует',
    'ready_unsent': 'в консоли не показана (send_drafts.py --write) — молчание ее не публикует',
    'doubted': 'приемка не пропустила — ждет вашего решения, по молчанию не выходит',
    'held': 'придержана ранее — ждет ручного решения',
}


def is_shown(card):
    """Показана в консоли: карточка (🗂) или проект поста (📣) ушли владельцу."""
    return bool(card.get('draft_sent') or card.get('post_draft_sent'))


def _accepted_day(card):
    """Дата приемки строкой или None: у старых фикстур `accepted: True`/'d' —
    не дата, они идут по-старому, без второго чтения."""
    acc = card.get(ACCEPTED)
    return acc if isinstance(acc, str) and acc[:4].isdigit() else None


def needs_second_reading(card):
    """Принята с SECOND_READING_SINCE и еще не прочитана второй раз. Одно
    определение на всех (раньше — три с разной трактовкой нестроковой
    `accepted`). Показанность здесь не учитывается — ее решает `state`."""
    acc = _accepted_day(card)
    return bool(acc and acc >= SECOND_READING_SINCE and not card.get(SECOND_READ))


def state(card):
    if card.get('held'):
        return 'held'
    if card.get('hold_reason'):
        return 'doubted'
    if not card.get('reviewed'):
        return 'accepted_unread' if card.get(ACCEPTED) else 'unreviewed'
    if not card.get(ACCEPTED):
        return 'unaccepted'
    if is_shown(card):
        return 'shown'
    if needs_second_reading(card):
        return 'unread2'
    return 'ready_unsent'


def hours_pending(card, now=None):
    """Сколько часов карточка ждет решения. Без `pending_since` отсчет идет от
    приемки или чтения (раньше без отметки часы стояли на нуле навсегда —
    Мадрид, Nestlé, «Ашан», три недели в «выйдут сами»)."""
    now = now or datetime.now(timezone.utc)
    stamp = card.get('pending_since') or card.get(ACCEPTED) or card.get('reviewed')
    try:
        since = datetime.fromisoformat(str(stamp))
    except ValueError:
        return 0.0
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return (now - since).total_seconds() / 3600.0


def _self_check():
    assert state({}) == 'unreviewed'
    assert state({'accepted': '2026-10-01'}) == 'accepted_unread'
    assert state({'reviewed': 'd'}) == 'unaccepted'
    assert state({'reviewed': 'd', 'accepted': 'd'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09'}) == 'unread2'
    assert state({'reviewed': 'd', 'accepted': '2026-10-08'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09', 'second_read': '2026-10-09'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09', 'draft_sent': True}) == 'shown'
    assert state({'reviewed': 'd', 'accepted': 'd', 'hold_reason': 'не сделка'}) == 'doubted'
    assert state({'held': True, 'hold_reason': 'x'}) == 'held'
    assert state({'draft_sent': True}) == 'unreviewed'
    assert set(WAIT_TEXT) == set(STATES) - {'shown'}


_self_check()
