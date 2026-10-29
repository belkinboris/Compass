"""Публикация выпускает решения владельца — остальные рутины ждут с push.

Владелец 24 октября 2026: «А можно просто приоритетно всегда заканчивать с
выпуском постов, а потом уже прорабатывать все остальные плановые задачи?»
В тот день пост по решению 13:36 вышел в 17:28: прогон публикации применил
решение, а потом четыре раза подряд не смог запушить — приток и качество
успевали запушить свое, и каждый раз нужен был новый полный pytest (15 минут).

Правило: пока на сайте лежат решения людей из консоли, которые публикация
еще не применила (`/api/moderation/decisions` — их снимает `approve.py
--consume` сразу после push публикации), другие рутины свои правки не
пушат, а ждут. Работать они могут — ждут только с push.

    python3 pipeline/publication_busy.py             # 0 — свободно, 1 — публикация занята
    python3 pipeline/publication_busy.py --wait 40   # ждать до 40 минут, пока не освободится

Решение старше STALE_H часов не держит никого: значит, публикация сломалась,
и ждать ее бессмысленно (это ее сбой, о нем она сама шлет PushNotification).
Нет токена или сайт не ответил — тоже «свободно»: рутина не должна вставать
из-за недоступного сайта.
"""
import os
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

STALE_H = 3
POLL_S = 60
# «Заметка» в консоли — не решение по карточке, публикации ее применять нечего.
# «Выкинуть» сырье — тоже: поста из него не выйдет, а держать из-за него все
# пуши до следующего прогона публикации незачем (29 октября 2026: восемь
# «выкинуть» по сомнительным новостям держали push больше получаса).
NOT_A_DECISION = {'note', 'drop'}


def waiting(decisions, now=None):
    """Решения людей, которые публикация еще не применила (не старше STALE_H)."""
    now = now or datetime.now(timezone.utc)
    out = []
    for d in decisions:
        if d.get('verdict') in NOT_A_DECISION:
            continue
        try:
            at = datetime.fromisoformat(str(d.get('created_at')))
        except ValueError:
            continue
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        if now - at <= timedelta(hours=STALE_H):
            out.append(d)
    return out


def busy():
    import approve
    decisions, _ = approve.fetch_decisions()
    return waiting(decisions)


def main(argv):
    limit = 0
    if '--wait' in argv:
        limit = float(argv[argv.index('--wait') + 1]) * 60
    start = time.monotonic()
    while True:
        rows = busy()
        if not rows:
            print('Публикация свободна — можно пушить.')
            return 0
        print('Публикация выпускает решения из консоли (%d: %s) — ждем с push.'
              % (len(rows), ', '.join(str(r.get('deal_id')) for r in rows[:5])), flush=True)
        if time.monotonic() - start + POLL_S > limit:
            return 1
        time.sleep(POLL_S)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
