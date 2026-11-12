# -*- coding: utf-8 -*-
"""Запись одной партии вычитки одной командой, под общим замком.

ЗАЧЕМ. 12 ноября 2026 владелец попросил вычитать все оставшиеся карточки (1243) за
15 часов несколькими помощниками сразу. Шаги 4–5 `routines/reread.md` (review.py
--write, отметки, проверки, коммит, push) писались под одного исполнителя: два
помощника в одной рабочей папке затирали бы друг другу базу, а отклоненная запись
в чужой недописанной партии останавливала бы запись своей. Здесь эти шаги —
одна команда: она берет замок (в один момент базу пишет одна партия), видит только
файлы правок своей партии (`REVIEW_ONLY`), сама откатывает рабочую папку, если
проверки красные, и печатает короткий итог. Команда повторяема: записанные правки
пропускаются, отметки ставятся тем карточкам, что еще без них.

    python3 pipeline/reread_apply.py <план.json>            # репетиция в своей копии, без замка
    python3 pipeline/reread_apply.py <план.json> --write

План (пишет помощник, читавший партию):

    {"tag": "m001",                      # метка партии — стоит в именах ее файлов правок
     "ids": ["g…", …],                   # карточки партии
     "written": [["g…", "evidence.json", "written.json"], …],   # проза: write_card.py --check
     "scripts": ["pipeline/archive/2026-11/…_m001.py", …],      # разовые скрипты (--write)
     "legal_names": ["g…", …],           # кому party_legal_names.py --write
     "answers": "…/answers_m001.json",   # ответы для reread_queue.py --stamp
     "errors": [{"id": "g…", "field": "seller", "class": "wrong_seller",
                 "was": "…", "now": "…"}, …]}                   # что было не так — в журнал

Журнал ошибок `pipeline/reread_errors.jsonl` — сырье для новых механических проверок:
какие классы ошибок встречаются чаще всего, те и закрываются воротами приемки.
"""
import fcntl
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = '/tmp/compass_base_write.lock'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ERRORS = os.path.join(ROOT, 'pipeline', 'reread_errors.jsonl')
CLASSES = ('wrong_buyer', 'wrong_seller', 'wrong_target', 'party_text_no_profile', 'wrong_date',
           'wrong_status', 'wrong_sum', 'sum_meaning', 'wrong_share', 'wrong_type', 'wrong_industry',
           'invented_rationale', 'version_as_fact', 'unsupported_claim', 'foreign_fact',
           'adviser_wrong', 'title_standard', 'aggregator_source', 'dead_source', 'source_not_about',
           'profile_wrong_inn', 'profile_wrong_company', 'profile_text', 'duplicate', 'not_a_deal',
           'language', 'verbatim', 'other')
ATTRIBUTION = ('\n\nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\n'
               'Claude-Session: https://claude.ai/code/session_01XhWnVZv9GScsFsvaXEfC2i')


LOG = '/tmp/reread_apply.log'
_T = {'tag': '?', 'steps': []}


def note(text):
    """Строка в общий журнал записи партий: кто, когда, чем кончилось, сколько шел шаг."""
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write('%s %s %s\n' % (time.strftime('%H:%M:%S'), _T['tag'], text))
    except OSError:
        pass


def run(cmd, env=None, timeout=1500):
    t = time.time()
    r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    name = os.path.basename(cmd[1]) if len(cmd) > 1 and cmd[0] != 'git' else ' '.join(cmd[:2])
    if time.time() - t > 5:
        _T['steps'].append('%s %dс' % (name, time.time() - t))
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def tail(text, n=25):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return '\n'.join('      ' + l[:300] for l in lines[-n:])


def dirty_tracked():
    code, out = run(['git', 'status', '--porcelain', '--untracked-files=no'])
    return [l for l in out.splitlines() if l.strip()]


def revert():
    run(['git', 'checkout', 'HEAD', '--', '.'])


def stamped(ids):
    by = {d['id']: d for d in json.load(open(DATA, encoding='utf-8'))['deals']}
    return [i for i in ids if (by.get(i) or {}).get('reread')]


def fail(step, out, write):
    print('СТОП на шаге «%s»:\n%s' % (step, tail(out)))
    if write and '--local' in sys.argv:
        print('Это репетиция в своей копии — база не тронута. Почините причину и повторите.')
        return 1
    if write:
        last = [l for l in out.strip().splitlines() if l.strip()][-3:]
        note('СТОП «%s» | %s | %s' % (step, ' / '.join(l.strip()[:140] for l in last), '; '.join(_T['steps'])))
    if write:
        revert()
        print('Рабочая папка возвращена к последнему коммиту. Файлы правок партии целы — '
              'почините причину и запустите команду снова.')
    return 1


def rehearse(plan_path, plan):
    """Репетиция записи в своей копии репозитория, без замка (12 ноября 2026).

    Запись под замком — одна полоса на всех; пока партия узнавала о красной проверке
    только в ее конце, каждая неудача съедала у всех по четыре минуты, и очередь стояла.
    Репетиция делает те же шаги до коммита в отдельной рабочей копии свежего main:
    правки, проза, разовые скрипты, отметки, цитаты у фактов, проверки данных. Прошла —
    запись под замком почти наверняка пройдет с первого раза."""
    import shutil
    tag = plan['tag']
    wt = '/tmp/reread_rehearse_%s' % tag
    run(['git', 'worktree', 'remove', '--force', wt])
    shutil.rmtree(wt, ignore_errors=True)
    run(['git', 'fetch', '-q', 'origin', 'main'])
    code, out = run(['git', 'worktree', 'add', '--force', '--detach', wt, 'origin/main'])
    if code:
        print('Репетиция не началась (git worktree):\n' + tail(out, 5))
        return 1
    try:
        inbox = os.path.join(wt, 'data', 'inbox')
        shutil.rmtree(inbox, ignore_errors=True)
        os.makedirs(os.path.dirname(inbox), exist_ok=True)
        os.symlink(os.path.join(ROOT, 'data', 'inbox'), inbox)
        fx = os.path.join('pipeline', 'ingest', 'fixes')
        for fn in os.listdir(os.path.join(ROOT, fx)):
            if tag in fn and fn.endswith('.py'):
                shutil.copy(os.path.join(ROOT, fx, fn), os.path.join(wt, fx, fn))
        for sc in plan.get('scripts') or []:
            os.makedirs(os.path.dirname(os.path.join(wt, sc)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, sc), os.path.join(wt, sc))
        shutil.copy(os.path.join(ROOT, 'pipeline', 'reread_apply.py'), os.path.join(wt, 'pipeline', 'reread_apply.py'))
        r = subprocess.run([sys.executable, os.path.join(wt, 'pipeline', 'reread_apply.py'), plan_path, '--write', '--local'],
                           cwd=wt, capture_output=True, text=True, timeout=1500)
        print((r.stdout or '') + (r.stderr or '')[-1500:])
        return r.returncode
    finally:
        run(['git', 'worktree', 'remove', '--force', wt])
        shutil.rmtree(wt, ignore_errors=True)


def main(argv):
    write = '--write' in argv
    local = '--local' in argv            # репетиция: своя копия, без замка, коммита и push
    plan_path = [a for a in argv if not a.startswith('--')][0]
    plan = json.load(open(plan_path, encoding='utf-8'))
    tag, ids = plan['tag'], plan['ids']
    _T['tag'] = tag
    assert tag and len(tag) >= 3 and ids, 'в плане нужны tag и ids'
    bad_cls = sorted({e.get('class') for e in plan.get('errors') or []} - set(CLASSES))
    assert not bad_cls, 'неизвестные классы ошибок: %s (допустимые: %s)' % (bad_cls, ', '.join(CLASSES))
    env = dict(os.environ, REVIEW_ONLY=tag, FIXES_SESSION=tag, MASS_OK='reread')
    py = sys.executable

    # Сухой прогон базу не пишет — замок ему не нужен (12 ноября 2026: сухие прогоны
    # стояли в очереди за записью чужих партий по двадцать минут).
    if not write:
        return rehearse(plan_path, plan)
    if write and not local:
        lock = open(LOCK, 'w')
        t0 = time.time()
        fcntl.flock(lock, fcntl.LOCK_EX)
        waited = int(time.time() - t0)
        if waited > 5:
            print('Ждали замок %d с.' % waited)
        note('замок взят, ждали %d с' % waited)

    if write and not local:
        left = dirty_tracked()
        if left:
            print('В рабочей папке чужие незаписанные правки отслеживаемых файлов — возвращаю к коммиту:\n'
                  + '\n'.join('      ' + l for l in left[:8]))
            revert()
        code, out = run(['git', 'pull', '-q', '--rebase', 'origin', 'main'])
        if code:
            run(['git', 'rebase', '--abort'])
            return fail('git pull --rebase', out, False)

    steps = [('правки (review.py)', [py, 'pipeline/ingest/review.py'] + (['--write'] if write else []))]
    for cid, ev, wr in plan.get('written') or []:
        steps.append(('проза %s (write_card.py)' % cid,
                      [py, 'pipeline/ingest/write_card.py', '--check', cid, ev, wr] + (['--write'] if write else [])))
    for sc in plan.get('scripts') or []:
        steps.append(('разовый скрипт %s' % os.path.basename(sc), [py, sc] + (['--write'] if write else [])))
    if plan.get('legal_names') and write:
        steps.append(('правовая форма сторон', [py, 'pipeline/party_legal_names.py'] + list(plan['legal_names']) + ['--write']))
    if write:
        # Прежние записи таблицы правок на поля, переписанные этой партией, гасятся отпечатком:
        # иначе review.py отклонит их и остановит запись всем следующим партиям (m006, 12 ноября 2026).
        steps.append(('гашение прежних записей таблицы правок',
                      [py, 'pipeline/reread_absorb.py', '--ids'] + list(ids) + ['--write']))
        steps += [('агрегаторы из видимых источников', [py, 'pipeline/split_discovery_sources.py', '--write']),
                  ('слой фактов', [py, 'pipeline/facts_derive.py', '--write'])]
    for name, cmd in steps:
        code, out = run(cmd, env=env)
        refused = 'ОТКАЗ' in out or 'отклонено' in out and 'отклонено 0' not in out
        if code or refused:
            return fail(name, out, write)

    stamp_cmd = [py, 'pipeline/reread_queue.py', '--stamp', plan['answers']] + (['--write'] if write else [])
    code, out = run(stamp_cmd, env=env)
    refusals = [l for l in out.splitlines() if 'ОТКАЗ' in l or l.strip().startswith('- ')]
    if code:
        return fail('отметки (reread_queue.py --stamp)', out, write)
    code, out = run([py, 'pipeline/fact_edit_guard.py'], env=env)
    if code:
        return fail('цитата у каждой правки факта (fact_edit_guard.py)', out, True)
    old = json.loads(subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'], cwd=ROOT,
                                    capture_output=True, text=True).stdout)
    new = json.load(open(DATA, encoding='utf-8'))
    lost = ({d['id'] for d in old['deals']} - {d['id'] for d in new['deals']}) | (set(old['companies']) - set(new['companies']))
    merged = set((new.get('merged') or {}).keys()) if isinstance(new.get('merged'), dict) else set()
    lost -= merged
    if lost and not plan.get('lost_ok'):
        return fail('семантическая сверка базы', 'пропали сделки или профили: %s (если это слияние дублей, '
                    'назовите их в плане: "lost_ok": [...])' % sorted(lost)[:10], True)
    code, out = run([py, 'pipeline/prepush_check.py'], env=env)
    if code:
        return fail('проверки данных (prepush_check.py)', out, True)

    if local:
        done = stamped(ids)
        print('РЕПЕТИЦИЯ ПРОШЛА: правки, проза и скрипты записываются, проверки данных зеленые; '
              'отметку получат %d из %d карточек.' % (len(done), len(ids)))
        missing = [i for i in ids if i not in done]
        if missing:
            print('Без отметки останутся: %s' % ', '.join(missing))
        if refusals:
            print('Причины отказа в отметке:\n' + '\n'.join('      ' + l.strip()[:260] for l in refusals))
        print('Теперь запись: та же команда с ключом --write.')
        return 0
    if plan.get('errors'):
        with open(ERRORS, 'a', encoding='utf-8') as f:
            for e in plan['errors']:
                f.write(json.dumps(dict(e, tag=tag), ensure_ascii=False) + '\n')
    run(['git', 'add', '-u'])
    for path in [ERRORS] + list(plan.get('scripts') or []):
        run(['git', 'add', path])
    code, out = run(['git', 'ls-files', '--others', '--exclude-standard', 'pipeline/ingest/fixes'])
    for f in out.split():
        if tag in f:
            run(['git', 'add', f])
    done = stamped(ids)
    msg = 'Вычитка, партия %s: отметки %d из %d карточек' % (tag, len(done), len(ids))
    code, out = run(['git', 'commit', '-q', '-m', msg + ATTRIBUTION])
    if code and 'nothing to commit' not in out and 'нечего коммитить' not in out:
        return fail('git commit', out, False)
    run([py, 'pipeline/publication_busy.py', '--wait', '20'])
    for i in range(4):
        code, out = run(['git', 'pull', '-q', '--rebase', 'origin', 'main'])
        if code:
            run(['git', 'rebase', '--abort'])
            print('ВНИМАНИЕ: конфликт при подтягивании main — коммит партии остался локально:\n' + tail(out, 6))
            return 1
        code, out = run(['git', 'push', '-q', 'origin', 'HEAD:main'])
        if not code:
            break
        time.sleep(2 ** (i + 1))
    else:
        print('ВНИМАНИЕ: push не прошел, коммит остался локально:\n' + tail(out, 6))
        return 1
    note('ЗАПИСАНО: %s | %s' % (msg, '; '.join(_T['steps'])))
    fcntl.flock(lock, fcntl.LOCK_UN)          # сверка с реестром ходит в сеть — уже без замка
    code, audit = run([py, 'pipeline/party_registry_audit.py', '--ids'] + list(ids), env=env)
    print('ЗАПИСАНО И ЗАПУШЕНО: %s' % msg)
    missing = [i for i in ids if i not in done]
    if missing:
        print('Без отметки остались: %s' % ', '.join(missing))
    if refusals:
        print('Причины отказа в отметке:\n' + '\n'.join('      ' + l.strip()[:260] for l in refusals))
    hits = [l for l in audit.splitlines() if any(i in l for i in ids)]
    if hits:
        print('Сверка сторон с реестром — разобрать в этой же партии (docs/card_parties.md):\n'
              + '\n'.join('      ' + l.strip()[:260] for l in hits[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
