"""Частый забор новостей без агента (28 октября 2026).

Владелец: «почему нельзя по нахождении новости сразу отправить в консоль,
если сомнительная…». Раньше забор, фильтр, ворота и показ сырья жили внутри
часового прогона притока, который шел часами. Здесь — та же цепочка скриптов
и ничего, что требует чтения человеком или моделью:

  fetch.py → triage.py → draft.py → promote.py --write → signals.py --write
  → список несрешенного сырья (raw_screen.py) → [агент отсеивает мусор:
  raw_screen.py --drop] → send_drafts.py --write (сырье ⚠️ с кнопками;
  готовые карточки, если их еще не показал сервер) → коммит очереди,
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
TRACKED = ['static/data/pending.json', 'static/data/signals.json', 'data/inbox/hold', 'data/inbox/duplicates', 'data/inbox/moderation_state.json']


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
    git('add', *TRACKED)
    if not git('status', '--porcelain', '--', *TRACKED).stdout.strip():
        print('Нового нет — коммитить нечего.')
        return 0
    git('commit', '-q', '-m', message)
    for i in range(4):
        git('pull', '--rebase', '--autostash', 'origin', 'main')
        if git('push', '-u', 'origin', 'main').returncode == 0:
            print('Запушено.')
            return 0
        time.sleep(2 ** (i + 1))
    print('push не прошел после четырех попыток — очередь останется локальной до следующего забора.')
    return 1


def main(argv):
    write, send = '--write' in argv, '--send' in argv
    g = git('pull', '--rebase', '--autostash', 'origin', 'main')
    if g.returncode:
        raise SystemExit('git pull: %s' % (g.stderr or g.stdout).strip()[-300:])
    if send:
        # Фаза 2: мусор уже отсеян (raw_screen.py --drop) — показать и записать.
        run('send_drafts.py', '--write', must=False)
        return commit_and_push('Забор новостей: сырье показано, очередь (sweep.py --send)')
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
