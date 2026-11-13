"""Частый забор новостей без агента (28 октября 2026).

Владелец: «почему нельзя по нахождении новости сразу отправить в консоль,
если сомнительная…». Раньше забор, фильтр, ворота и показ сырья жили внутри
часового прогона притока, который шел часами. Здесь — та же цепочка скриптов
и ничего, что требует чтения человеком или моделью:

  fetch.py → triage.py → draft.py → promote.py --write → signals.py --write
  → список несрешенного сырья (raw_screen.py) → [агент отсеивает мусор:
  raw_screen.py --drop] → send_drafts.py --write (сырье ⚠️ с кнопками;
  готовые карточки, если их еще не показал сервер) → напоминание в личку о
  том, что сутки ждет решения (remind_undecided.py) → коммит очереди,
  hold-файлов и памяти о сырье → push.

Две фазы, потому что между ними — единственный шаг по смыслу: отсев
очевидного мусора в сырье (routines/intake.md, шаг 14: свадьбы, курсы,
гайды, криминальная хроника). Первый забор 28 октября 2026 без этого шага
отправил в консоль «МВД пресекло работу криптообменников…» — владелец:
«как это оказалось в сомнительных?». Механические правила classify.py
дополнены, но правило притока «решение по смыслу, не механика» остается:
перед показом сырье читает агент, пусть и на полминуты.

Что остается агенту притока: чтение источников, написание карточки,
приемка, второе чтение, показ готовой карточки (`ship_card.py`), запись в
базу. Память «что уже показано» — на сайте (/api/moderation/shown), поэтому
два контейнера (этот и прогон притока) не показывают одно и то же дважды.

    python3 pipeline/ingest/sweep.py            # все сухо
    python3 pipeline/ingest/sweep.py --write    # фаза 1: забор, ворота, список сырья на отсев
    python3 pipeline/ingest/sweep.py --send     # фаза 2: показ в консоль, коммит, push
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRACKED = ['static/data/pending.json', 'static/data/signals.json', 'data/inbox/hold', 'data/inbox/duplicates',
           'data/inbox/moderation_state.json', 'data/inbox/undecided_reminders.json',
           # память страниц сделок консультантов: без нее запись с сайта фирмы
           # приходила бы каждый час заново (deal_pages.py)
           'pipeline/ingest/deal_pages_seen.json']
REMINDERS = 'data/inbox/undecided_reminders.json'


def run(name, *args, must=True):
    r = subprocess.run([sys.executable, os.path.join(HERE, name), *args], cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout or '').strip().splitlines()[-3:]
    print('%s %s → %s' % (name, ' '.join(args), ' | '.join(tail)[:300]))
    if r.returncode and must:
        print((r.stderr or '').strip()[-600:])
        raise SystemExit('%s упал (код %d)' % (name, r.returncode))
    return r


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)


def commit_and_push(message):
    # Только существующие пути: `git add` с несуществующим путем отказывается
    # добавлять ВСЕ (13 ноября 2026: файла напоминаний еще не было, коммит не
    # создавался, а прогон писал «Запушено» — отсев терялся с 12 ноября).
    paths = [p for p in TRACKED if os.path.exists(os.path.join(ROOT, p))]
    added = git('add', *paths)
    if added.returncode:
        print('git add не прошел: %s' % added.stderr.strip()[:200])
        return 1
    if not git('diff', '--cached', '--name-only', '--', *paths).stdout.strip():
        print('Нового нет — коммитить нечего.')
        return 0
    made = git('commit', '-q', '-m', message)
    if made.returncode:
        print('КОММИТ НЕ СОЗДАН: %s' % (made.stderr or made.stdout).strip()[:200])
        return 1
    for i in range(4):
        if git('pull', '--rebase', '--autostash', 'origin', 'main').returncode and rebasing() \
                and not settle_rebase():
            print('git pull: конфликт не в служебных файлах сырья — ребейз отменен, '
                  'очередь останется локальной до следующего забора.')
            return 1
        if git('push', '-u', 'origin', 'main').returncode == 0:
            print('Запушено.')
            return 0
        time.sleep(2 ** (i + 1))
    print('push не прошел после четырех попыток — очередь останется локальной до следующего забора.')
    return 1


def rebasing():
    """Ребейз еще идет (REBASE_HEAD для этого не годится: он остается и после конца)."""
    return any(os.path.exists(os.path.join(ROOT, git('rev-parse', '--git-path', d).stdout.strip()))
               for d in ('rebase-merge', 'rebase-apply'))


def settle_rebase():
    """Ребейз остановился на конфликте. 9 ноября 2026: приток и забор в одну
    минуту записали `data/inbox/hold/<день>.json`, ребейз встал посреди файла
    с маркерами конфликта, и следующий забор упал на чтении JSON. Файлы
    сырья (`hold/`) каждый прогон собирает заново — берем версию из main и
    продолжаем. Конфликт в чем-то другом — ребейз отменяется, ничего не
    теряется. Возвращает True, если ребейз довели до конца."""
    while True:
        files = [f for f in git('diff', '--name-only', '--diff-filter=U').stdout.split() if f]
        if not files:
            if rebasing():
                git('rebase', '--abort')
                return False
            return True
        if not all(f.startswith('data/inbox/hold/') or f == REMINDERS for f in files):
            git('rebase', '--abort')
            return False
        # Отметки напоминаний — свежее наша версия (в ребейзе это --theirs):
        # иначе через час напомнили бы еще раз о том же.
        if REMINDERS in files:
            git('checkout', '--theirs', '--', REMINDERS)
        hold = [f for f in files if f != REMINDERS]
        if hold:
            git('checkout', '--ours', '--', *hold)
        git('add', '--', *files)
        r = subprocess.run(['git', 'rebase', '--continue'], cwd=ROOT, capture_output=True, text=True,
                           env=dict(os.environ, GIT_EDITOR='true'))
        if r.returncode and not git('diff', '--name-only', '--diff-filter=U').stdout.strip():
            # пустой коммит после разрешения — пропускаем его
            git('rebase', '--skip')
        if not rebasing():
            return True


STALE_DECISION_MIN = 30


def stale_decisions_warning(now=None):
    """Решения людей из консоли ждут публикацию дольше STALE_DECISION_MIN минут —
    сказать вслух: их доведет до поста `ship_decisions.py --write` (28 октября
    2026, «пост больше двух часов назад одобрил»)."""
    try:
        from datetime import datetime, timedelta, timezone
        sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
        import publication_busy
        now = now or datetime.now(timezone.utc)
        old = [d for d in publication_busy.busy()
               if now - datetime.fromisoformat(str(d.get('created_at'))).replace(
                   tzinfo=datetime.fromisoformat(str(d.get('created_at'))).tzinfo or timezone.utc)
               > timedelta(minutes=STALE_DECISION_MIN)]
    except Exception as e:  # noqa: BLE001 — страховка не должна ронять забор
        print('Проверка решений не удалась: %s' % e)
        return []
    if old:
        print('\nРЕШЕНИЯ ЖДУТ ДОЛЬШЕ %d МИНУТ (%s) — публикация их не применила: '
              'python3 pipeline/publish/ship_decisions.py --write' % (STALE_DECISION_MIN, ', '.join(str(d.get('deal_id')) for d in old[:5])))
    return old


def remind_undecided():
    """Напоминание в личку о том, что сутки ждет решения в консоли
    (pipeline/publish/remind_undecided.py, 12 ноября 2026: молчание больше не
    публикует). Отметки «напомнили» коммитятся вместе с очередью. Сбой
    напоминания забор не роняет."""
    try:
        path = os.path.join(ROOT, 'pipeline', 'publish', 'remind_undecided.py')
        r = subprocess.run([sys.executable, path, '--write'], cwd=ROOT, capture_output=True,
                           text=True, timeout=120)
        tail = (r.stdout or '').strip().splitlines()[-2:]
        print('remind_undecided.py --write → %s' % ' | '.join(tail)[:300])
        if r.returncode:
            print('Напоминание не сработало (код %d): %s' % (r.returncode, (r.stderr or '').strip()[-400:]))
    except Exception as e:  # noqa: BLE001 — напоминание не должно ронять забор
        print('Напоминание не сработало: %s' % e)


def main(argv):
    write, send = '--write' in argv, '--send' in argv
    g = git('pull', '--rebase', '--autostash', 'origin', 'main')
    if g.returncode and rebasing() and settle_rebase():
        g = g.__class__(g.args, 0, g.stdout, g.stderr)
    if g.returncode:
        raise SystemExit('git pull: %s' % (g.stderr or g.stdout).strip()[-300:])
    if send:
        # Фаза 2: мусор уже отсеян (raw_screen.py --drop) — показать и записать.
        run('send_drafts.py', '--write', must=False)
        remind_undecided()
        rc = commit_and_push('Забор новостей: сырье показано, очередь (sweep.py --send)')
        stale_decisions_warning()
        return rc
    run('fetch.py')
    run('triage.py')
    run('draft.py')
    run('promote.py', *(['--write'] if write else []))
    if write:
        run('signals.py', '--write', must=False)
    if not write:
        run('send_drafts.py', must=False)
        print('Сухой прогон: ворота и показ не записаны. Запись — с ключом --write.')
        return 0
    rc = commit_and_push('Забор новостей: очередь и сырье (sweep.py)')
    print('\nНЕСРЕШЕННОЕ СЫРЬЕ — отсеять мусор (raw_screen.py --drop <id…> --reason "…" --write), затем sweep.py --send:')
    run('raw_screen.py', must=False)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
