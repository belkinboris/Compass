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


def waiting(decisions, now=None, stale_h=STALE_H):
    """Решения людей, которые публикация еще не применила (не старше `stale_h` часов).

    Отсечка по возрасту нужна тому, кто ЖДЕТ с push: старое решение значит, что
    публикация сломалась, и ждать ее бессмысленно. Тому, кто ПРЕДУПРЕЖДАЕТ о не
    примененном решении (`sweep.stale_decisions_warning`), она вредна: решение,
    нажатое в 21:55, к утреннему забору старше трех часов — и забор о нем молчал.
    `stale_h=None` — без отсечки."""
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
        if stale_h is None or now - at <= timedelta(hours=stale_h):
            out.append(d)
    return out


CARD_VERDICTS = {'approve', 'post_yes', 'post_realty', 'post_main', 'post_both', 'post_no', 'post_hold'}


def holding(rows, base, queued, unproven):
    """Из ждущих решений — те, по которым публикации еще есть что делать.

    13 ноября 2026 приток 40 минут ждал с push: на сайте лежали решения по
    двум карточкам, выкинутым из очереди как дубли (g5540db5e, ga241b1af), и
    по карточке, которая уже была в базе. Публикация отвечала «решений нет»,
    а сайт их не гасил: результата выкинутой карточки в базе не будет никогда.
    Решение о карточке держит остальных, только пока карточка жива (в базе или
    в очереди) и результата решения в origin/main еще нет."""
    deals = {d['id'] for d in base.get('deals') or []}
    out = []
    for d in rows:
        if d.get('verdict') in CARD_VERDICTS and '~' not in str(d.get('deal_id') or ''):
            did = d.get('deal_id')
            if did not in deals and did not in queued:
                continue        # карточки нет нигде — выкинута, применять нечего
            if not unproven([d], base):
                continue        # результат уже в main
        out.append(d)
    return out


def busy(stale_h=STALE_H):
    import json
    import subprocess
    import approve
    decisions, _ = approve.fetch_decisions()
    rows = waiting(decisions, stale_h=stale_h)
    if not rows:
        return rows
    try:
        subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT, timeout=120)
        show = lambda path: json.loads(subprocess.run(['git', 'show', 'origin/main:' + path], cwd=ROOT,
                                                      capture_output=True, text=True, timeout=120).stdout)
        base = show('static/data/deals_promoted.json')
        queued = {c.get('id') for c in show('static/data/pending.json').get('cards') or []}
    except Exception as e:  # main не прочитан — считаем по-старому, строже
        print('origin/main не прочитан (%s) — считаю все свежие решения ждущими.' % e)
        return rows
    return holding(rows, base, queued, approve.unproven)


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
