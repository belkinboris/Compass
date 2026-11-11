# -*- coding: utf-8 -*-
"""Замок публикации: два прогона не выпускают посты одновременно.

ЗАЧЕМ. С 11 ноября 2026 публикация запускается каждый раз в НОВОЙ сессии
(раньше — одна долгая сессия с 7 ноября: память 310 тыс. слов перечитывалась
каждый час, а одна остановка «жду человека» блокировала все следующие запуски —
в тот день посты стояли полдня). Долгая сессия давала одно полезное свойство:
запуски шли строго по очереди. Новые сессии могут пересечься (прогон ждет паузы
20 минут между постами дольше часа), и тогда один пост ушел бы дважды. Замок
возвращает очередь.

КАК. Файл `data/inbox/publication_lock.json` в main: кто и когда начал. Свежий
чужой замок (моложе STALE_MIN) — уходим, ничего не делая: тот прогон сам все
выпустит. Старый — прогон умер, замок забираем. Гонка двух одновременных
`--acquire` решается push: второй получит отказ, подтянет main и увидит чужой замок.

    python3 pipeline/publication_lock.py --acquire   # 0 — замок наш, 1 — работает другой прогон
    python3 pipeline/publication_lock.py --release   # снять свой замок (чужой не трогает)
    python3 pipeline/publication_lock.py             # показать состояние

Замок ставится перед первой ЗАПИСЬЮ прогона (ship_decisions --write ставит и
снимает сам; отдельный send_telegram --write — по routines/publication.md), а
не в пустом прогоне: лишних коммитов в main нет.
"""
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = 'data/inbox/publication_lock.json'
MINE = os.path.join(ROOT, 'data', 'inbox', '.publication_lock_mine')   # не в git: id своего замка
STALE_MIN = 100


def _git(*args, cwd=None, must=False):
    r = subprocess.run(['git', *args], cwd=cwd or ROOT, capture_output=True, text=True)
    if must and r.returncode:
        raise SystemExit('git %s: %s' % (' '.join(args), (r.stderr or r.stdout).strip()[-300:]))
    return r


def remote_lock(cwd=None):
    """Замок в origin/main или None."""
    _git('fetch', '-q', 'origin', 'main', cwd=cwd)
    r = _git('show', 'origin/main:' + REL, cwd=cwd)
    if r.returncode or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def age_min(lock, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        return (now - datetime.fromisoformat(lock['started'])).total_seconds() / 60
    except Exception:
        return 10 ** 6


def busy(lock, mine=None, now=None):
    """Чужой живой замок."""
    return bool(lock) and lock.get('run') != mine and age_min(lock, now) < STALE_MIN


def _my_id():
    return open(MINE).read().strip() if os.path.exists(MINE) else None


def _push(cwd, message, tries=3):
    for _ in range(tries):
        _git('commit', '-q', '-m', message, '--', REL, cwd=cwd)
        if not _git('push', '-q', 'origin', 'HEAD:main', cwd=cwd).returncode:
            return True
        _git('pull', '--rebase', '--autostash', '-q', 'origin', 'main', cwd=cwd)
    return False


def acquire(cwd=None):
    cwd = cwd or ROOT
    lock = remote_lock(cwd)
    if busy(lock, _my_id()):
        print('Публикация уже идет в другом прогоне (начат %s, %.0f мин назад) — этот прогон ничего не делает.'
              % (lock.get('started'), age_min(lock)))
        return 1
    run = uuid.uuid4().hex[:12]
    _git('pull', '--rebase', '--autostash', '-q', 'origin', 'main', cwd=cwd)
    path = os.path.join(cwd, REL)
    json.dump({'run': run, 'started': datetime.now(timezone.utc).isoformat(timespec='seconds')},
              open(path, 'w', encoding='utf-8'))
    _git('add', '-f', '--', REL, cwd=cwd)
    os.makedirs(os.path.dirname(MINE), exist_ok=True)
    open(MINE, 'w').write(run)
    if not _push(cwd, 'Публикация: замок прогона поставлен'):
        print('Замок не запушен — считаю, что работает другой прогон.')
        return 1
    after = remote_lock(cwd)
    if not after or after.get('run') != run:
        print('Замок перехватил другой прогон — этот ничего не делает.')
        return 1
    print('Замок публикации наш (%s).' % run)
    return 0


def release(cwd=None):
    cwd = cwd or ROOT
    mine = _my_id()
    lock = remote_lock(cwd)
    if not lock or not mine or lock.get('run') != mine:
        print('Своего замка нет — снимать нечего.')
        return 0
    _git('pull', '--rebase', '--autostash', '-q', 'origin', 'main', cwd=cwd)
    _git('rm', '-q', '-f', '--', REL, cwd=cwd)
    ok = _push(cwd, 'Публикация: замок прогона снят')
    if os.path.exists(MINE):
        os.remove(MINE)
    print('Замок снят.' if ok else 'Замок не снят (push не прошел) — он сам устареет через %d минут.' % STALE_MIN)
    return 0


def _self_check():
    now = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
    fresh = {'run': 'a', 'started': '2026-11-11T11:30:00+00:00'}
    old = {'run': 'a', 'started': '2026-11-11T09:00:00+00:00'}
    assert busy(fresh, None, now) and busy(fresh, 'b', now)
    assert not busy(fresh, 'a', now) and not busy(old, 'b', now) and not busy(None, 'b', now)


def main(argv):
    _self_check()
    if '--acquire' in argv:
        return acquire()
    if '--release' in argv:
        return release()
    lock = remote_lock()
    print('Замка нет.' if not lock else 'Замок: прогон %s, начат %s (%.0f мин назад)%s'
          % (lock.get('run'), lock.get('started'), age_min(lock), '' if busy(lock, _my_id()) else ' — не держит'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
