"""Решение владельца из консоли — до поста одной командой (28 октября 2026).

Владелец: «я пост больше двух часов назад одобрил» — а цепочка «применить →
полный pytest → push → подтвердить сайту → пост» была двенадцатью шагами
инструкции, которые агент рутины делал по одному; на полном pytest (15
минут) его ход заканчивался, и к push никто не возвращался. Эта команда
делает всю цепочку сама, в одном процессе, и ничего не оставляет памяти
агента. Проверки не сняты: полный pytest перед записью в базу, семантическая
сверка базы, подтверждение сайту только после push (approve.py --consume).

  1. `git pull --rebase origin main`;
  2. `approve.py` сухим прогоном — есть ли решения людей; нет — «Решений нет»;
  3. `approve.py --write` — решения в базу и в очередь;
  4. `facts_derive.py --write` до «Все уже актуально.»;
  5. полный `pytest -q` (ждет сколько нужно); красный — стоп, база не
     коммитится, сайту ничего не подтверждается, в выводе — хвост отчета;
  6. семантическая сверка базы к origin/main: ни одна сделка и ни один
     профиль не пропали;
  7. коммит, `pull --rebase`, push (с повторами); конфликт — стоп с
     подсказкой, что разбирать (routines/publication.md, шаг 10);
  8. `approve.py --consume` — только теперь сайт считает решения примененными;
  9. `send_telegram.py --write --finish --wait-for-site 15` — посты по
     решениям, с ожиданием, пока сайт подтянет базу, и паузой между постами;
 10. коммит отметок об отправке, `pytest test_data.py`, push.

    python3 pipeline/publish/ship_decisions.py            # сухой прогон: что бы сделала
    python3 pipeline/publish/ship_decisions.py --write

Запуск долгий (полный pytest плюс паузы между постами): из сессии агента —
в фоне с большим таймаутом; агент дожидается строки «ГОТОВО» или «СТОП».
Работает в отдельной рабочей копии (`<репозиторий>-ship`, git worktree),
основная копия все это время свободна для забора новостей. Журнал каждого
запуска — data/inbox/ship_decisions.log.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(ROOT, 'data', 'inbox', 'ship_decisions.log')
# ОТДЕЛЬНАЯ РАБОЧАЯ КОПИЯ. Полный pytest идет 20 минут, и все это время
# основная копия была занята незакоммиченной базой — часовой забор новостей
# три раза за день пропускался (28 октября 2026, из-за этого статью
# «Коммерсанта» о Baggins Coffee взяли на час позже конкурента). Команда
# работает в git worktree рядом с репозиторием и пушит оттуда `HEAD:main`;
# основная копия свободна. Кэш текстов источников (raw) живет только в
# основной копии — в worktree он подключается ссылкой; очередь сырья (hold)
# в git и приезжает с origin/main.
WORK = os.environ.get('SHIP_WORKTREE') or (ROOT + '-ship')
LINKED_INBOX = ('raw', 'triage', 'drafts')   # hold — в git, приезжает с origin/main
INGEST = os.path.join(WORK, 'pipeline', 'ingest')
BASE = os.path.join(WORK, 'static', 'data', 'deals_promoted.json')
COMMIT_PATHS = ['static/data/deals_promoted.json', 'static/data/pending.json',
                'data/inbox/moderation_state.json', 'pipeline/ingest/fixes']


def log(msg):
    line = '%s %s' % (datetime.now(timezone.utc).strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def run(args, must=True, timeout=None, cwd=None):
    r = subprocess.run(args, cwd=cwd or WORK, capture_output=True, text=True, timeout=timeout)
    if must and r.returncode:
        raise SystemExit('СТОП: %s не прошел (код %d):\n%s' % (' '.join(args[:3]), r.returncode, (r.stdout + r.stderr)[-1500:]))
    return r


def git(*args, must=True):
    return run(['git', *args], must=must).stdout.strip()


def push_with_retry(tries=4):
    for i in range(tries):
        r = run(['git', 'pull', '--rebase', '--autostash', 'origin', 'main'], must=False)
        if r.returncode:
            run(['git', 'rebase', '--abort'], must=False)
            return 'конфликт при rebase: %s' % (r.stdout + r.stderr)[-600:]
        if run(['git', 'push', 'origin', 'HEAD:main'], must=False).returncode == 0:
            return None
        time.sleep(2 ** (i + 1))
    return 'push не прошел после %d попыток' % tries


def prepare_worktree():
    """Рабочая копия для этой команды: свежий origin/main на ветке ship-wt,
    сырье основной копии — ссылками. Незакоммиченные правки базы в ней
    (прошлый запуск остановился) не трогаем — их подхватит продолжение."""
    run(['git', 'fetch', 'origin', 'main'], cwd=ROOT)
    if not os.path.isdir(os.path.join(WORK, '.git')) and not os.path.isfile(os.path.join(WORK, '.git')):
        run(['git', 'worktree', 'prune'], cwd=ROOT, must=False)
        run(['git', 'worktree', 'add', '-B', 'ship-wt', WORK, 'origin/main'], cwd=ROOT)
        log('Рабочая копия для доводки: %s' % WORK)
    dirty = run(['git', 'status', '--porcelain', '--', *COMMIT_PATHS], must=False).stdout.strip()
    if not dirty:
        run(['git', 'checkout', '-q', '-B', 'ship-wt', 'origin/main'])
    for name in LINKED_INBOX:
        src, dst = os.path.join(ROOT, 'data', 'inbox', name), os.path.join(WORK, 'data', 'inbox', name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(src) and not os.path.lexists(dst):
            os.symlink(src, dst)


def load_json(text):
    return json.loads(text) if text else {}


def base_lost(old, new):
    """Что пропало из базы относительно origin/main: сделки, профили, ключи."""
    lost = []
    for key, name in (('deals', 'сделок'), ('companies', 'профилей компаний')):
        o, n = old.get(key) or {}, new.get(key) or {}
        oid = set(o) if isinstance(o, dict) else {d['id'] for d in o}
        nid = set(n) if isinstance(n, dict) else {d['id'] for d in n}
        if oid - nid:
            lost.append('%s: %s' % (name, ', '.join(sorted(oid - nid)[:5])))
    ok, nk = set((old.get('match_keys') or {})), set((new.get('match_keys') or {}))
    if ok - nk:
        lost.append('match_keys: %d' % len(ok - nk))
    for key in ('telegram_posts', 'telegram_posts_realty'):
        o, n = old.get(key) or {}, new.get(key) or {}
        if isinstance(o, dict) and isinstance(n, dict) and set(o) - set(n):
            lost.append('%s: %d' % (key, len(set(o) - set(n))))
    return lost


def decisions_planned():
    """Сухой approve.py: строки ПУБЛИКУЕМ/ПРИДЕРЖАНА/ВЫКИНУТА/В РАБОТУ/ОТБРОШЕНА."""
    out = run([sys.executable, os.path.join(INGEST, 'approve.py')], must=False).stdout
    rows = [l.strip() for l in out.splitlines()
            if l.strip().startswith(('ПУБЛИКУЕМ', 'ПРИДЕРЖАНА', 'ВЫКИНУТА', 'В РАБОТУ', 'ОТБРОШЕНА'))]
    return rows, out


def main(argv):
    write = '--write' in argv
    log('— ship_decisions %s —' % ('--write' if write else 'сухой прогон'))
    prepare_worktree()
    git('pull', '--rebase', '--autostash', 'origin', 'main')
    # autostash может вернуть правки с конфликтом и кодом 0 — тогда в файлах
    # маркеры <<<<<<<, и полный pytest падает десятком json-ошибок (28 октября
    # 2026). Конфликт — стоп сразу, разбирать по id (docs/publication_pitfalls.md).
    conflicted = [l[3:] for l in git('status', '--porcelain').splitlines() if l[:2] in ('UU', 'AA', 'DU', 'UD')]
    if conflicted:
        log('СТОП: конфликт при подтягивании main в %s — разберите по id (docs/publication_pitfalls.md, шаг 10) и повторите команду.'
            % ', '.join(conflicted))
        return 1
    # Прошлый запуск применил решения, но остановился до push (красный pytest,
    # конфликт): правки уже в рабочей копии — продолжаем с полного pytest, а
    # не применяем решения второй раз.
    resume = bool(git('status', '--porcelain', '--', *COMMIT_PATHS))
    rows, out = decisions_planned()
    if resume:
        log('В рабочей копии уже есть незакоммиченные правки базы и очереди — продолжаю с полного pytest, решения заново не применяю.')
    if not rows and not resume:
        log('Решений нет.')
        return 0
    for r in rows:
        log('  ' + r)
    if 'ТУПИК' in out:
        log('В очереди есть готовые, но не показанные карточки — их покажет send_drafts.py --write (это не мешает решениям).')
    if not write:
        log('Сухой прогон: применила бы решения, прогнала полный pytest, запушила, подтвердила сайту и отправила посты. Запись — с ключом --write.')
        return 0

    old = load_json(git('show', 'origin/main:static/data/deals_promoted.json'))
    if not resume:
        run([sys.executable, os.path.join(INGEST, 'approve.py'), '--write'])
        log('Решения применены локально.')
    for _ in range(4):
        r = run([sys.executable, os.path.join(ROOT, 'pipeline', 'facts_derive.py'), '--write'])
        if 'актуально' in r.stdout:
            break
    log('Слой фактов пересчитан.')

    log('Полный pytest — ждем (обычно 15 минут). Пока он идет, других pytest в этой копии не запускать: тесты делят одну базу.')
    t0 = time.monotonic()
    r = run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'], must=False)
    if r.returncode:
        log('СТОП: полный pytest красный (%d мин). База не закоммичена, сайту ничего не подтверждено. Хвост:\n%s'
            % ((time.monotonic() - t0) / 60, r.stdout[-2000:]))
        return 1
    log('Полный pytest зеленый (%.0f мин).' % ((time.monotonic() - t0) / 60))

    new = json.load(open(BASE, encoding='utf-8'))
    lost = base_lost(old, new)
    if lost:
        log('СТОП: после применения из базы пропало — ' + '; '.join(lost) + '. Разбирать руками, ничего не пушу.')
        return 1
    log('Семантическая сверка базы: ничего не пропало (сделок %d → %d).' % (len(old.get('deals') or []), len(new.get('deals') or [])))

    run(['git', 'add', '--'] + [p for p in COMMIT_PATHS if os.path.exists(os.path.join(ROOT, p))])
    if git('status', '--porcelain', '--', *COMMIT_PATHS):
        titles = [r.split(None, 2)[-1][:60] for r in rows if r.startswith('ПУБЛИКУЕМ')]
        if resume and not titles:
            titles = ['продолжение после остановки']
        git('commit', '-q', '-m', 'Публикация: решения из консоли применены (%s)' % ('; '.join(titles)[:160] or 'очередь'))
        err = push_with_retry()
        if err:
            log('СТОП: %s. Сайту ничего не подтверждено — повторите команду после разбора (routines/publication.md, шаг 10).' % err)
            return 1
        log('База запушена.')
    run([sys.executable, os.path.join(INGEST, 'approve.py'), '--consume'])
    log('Сайту подтверждено: решения применены.')

    log('Посты по решениям — send_telegram --write --finish --wait-for-site 15 (ждет сайт и паузы между постами)…')
    r = run([sys.executable, os.path.join(HERE, 'send_telegram.py'), '--write', '--finish', '--wait-for-site', '15'], must=False)
    tail = [l for l in r.stdout.splitlines() if l.strip()][-6:]
    for l in tail:
        log('  ' + l)
    if r.returncode:
        log('СТОП: отправка постов не прошла (код %d) — см. строки выше; база уже в main.' % r.returncode)
        return 1
    if git('status', '--porcelain', '--', 'static/data/deals_promoted.json'):
        run([sys.executable, '-m', 'pytest', 'test_data.py', '-q', '-p', 'no:cacheprovider'])
        git('add', '--', 'static/data/deals_promoted.json')
        git('commit', '-q', '-m', 'Публикация: посты по решениям отправлены')
        err = push_with_retry()
        if err:
            log('СТОП: отметки об отправке не запушены (%s) — повторите push руками, посты уже ушли.' % err)
            return 1
    run(['git', 'pull', '-q', '--rebase', '--autostash', 'origin', 'main'], cwd=ROOT, must=False)
    log('ГОТОВО: решения применены, база в main, посты отправлены.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
