# -*- coding: utf-8 -*-
"""Единый писатель вычитки: несколько готовых партий — одной записью под одним замком.

ЗАЧЕМ. 12 ноября 2026, марафон вычитки. Запись партии под замком (`reread_apply.py --write`)
— три-четыре минуты, из них больше минуты — проверки данных и еще минута — служебные шаги
(слой фактов, push). Помощники сдают работу частями по 4–6 карточек, и полоса записи,
пропускающая одну партию за раз, держит не больше 75 карточек в час при потребности 100+.
Здесь готовые партии записываются группой: шаги каждой партии идут по очереди, а общие
шаги (агрегаторы, слой фактов, цитаты у фактов, проверки данных, коммит, push) — один раз
на группу. Партия, чей шаг упал, выпадает из группы (остальные записываются заново с
чистого листа — шаги повторяемы); красные общие проверки — группа распадается, и партии
пишутся по одной обычной командой.

    python3 pipeline/reread_writer.py <план.json> [<план.json> …]

Итог каждой партии печатается блоком «### <tag>» — писатель-демон раскладывает их по
файлам результатов.
"""
import fcntl
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reread_apply as ra  # noqa: E402

py = sys.executable


def plan_steps(plan, env):
    """Шаги одной партии до отметок. (ok, текст сбоя, отказы в отметке)."""
    ids = plan['ids']
    steps = [('правки (review.py)', [py, 'pipeline/ingest/review.py', '--write'])]
    for cid, ev, wr in plan.get('written') or []:
        steps.append(('проза %s (write_card.py)' % cid,
                      [py, 'pipeline/ingest/write_card.py', '--check', cid, ev, wr, '--write']))
    for sc in plan.get('scripts') or []:
        steps.append(('разовый скрипт %s' % os.path.basename(sc), [py, sc, '--write']))
    if plan.get('legal_names'):
        steps.append(('правовая форма сторон', [py, 'pipeline/party_legal_names.py'] + list(plan['legal_names']) + ['--write']))
    steps.append(('гашение прежних записей таблицы правок',
                  [py, 'pipeline/reread_absorb.py', '--ids'] + list(ids) + ['--write']))
    for name, cmd in steps:
        code, out = ra.run(cmd, env=env)
        if code or 'ОТКАЗ' in out or ('отклонено' in out and 'отклонено 0' not in out):
            return False, 'СТОП на шаге «%s»:\n%s' % (name, ra.tail(out)), []
    code, out = ra.run([py, 'pipeline/reread_queue.py', '--stamp', plan['answers'], '--write'], env=env)
    refusals = [l for l in out.splitlines() if 'ОТКАЗ' in l or l.strip().startswith('- ')]
    if code and 'ответов' not in out:
        return False, 'СТОП на шаге «отметки (reread_queue.py --stamp)»:\n%s' % ra.tail(out), []
    return True, '', refusals


def apply_group(plans, results):
    """Применить шаги всех партий; упавшая выпадает, группа начинается заново без нее."""
    while plans:
        ra.revert()
        bad = None
        refusals = {}
        for path, plan in plans:
            env = dict(os.environ, REVIEW_ONLY=plan['tag'], FIXES_SESSION=plan['tag'], MASS_OK='reread')
            ra._T['tag'] = plan['tag']
            ok, text, ref = plan_steps(plan, env)
            if not ok:
                bad = (path, plan, text)
                break
            refusals[plan['tag']] = ref
        if bad is None:
            return plans, refusals
        results[bad[1]['tag']] = bad[2] + '\nБаза не тронута. Файлы правок партии целы — почините причину, репетиция, снова READY.'
        ra.note('СТОП в группе | %s' % bad[2].splitlines()[0][:160])
        plans = [p for p in plans if p[1]['tag'] != bad[1]['tag']]
    return [], {}


def main(argv):
    paths = [a for a in argv if not a.startswith('--')]
    plans = []
    for p in paths:
        plan = json.load(open(p, encoding='utf-8'))
        bad_cls = sorted({e.get('class') for e in plan.get('errors') or []} - set(ra.CLASSES))
        if bad_cls or not plan.get('tag') or not plan.get('ids'):
            print('### %s\nСТОП: в плане неизвестные классы ошибок %s или нет tag/ids. Допустимые: %s'
                  % (plan.get('tag') or os.path.basename(os.path.dirname(p)), bad_cls, ', '.join(ra.CLASSES)))
            continue
        plans.append((p, plan))
    if not plans:
        return 1
    results = {}
    lock = open(ra.LOCK, 'w')
    t0 = time.time()
    fcntl.flock(lock, fcntl.LOCK_EX)
    ra._T['tag'] = '+'.join(p['tag'] for _x, p in plans)
    ra.note('замок взят группой, ждали %d с' % (time.time() - t0))
    if ra.dirty_tracked():
        ra.revert()
    code, out = ra.run(['git', 'pull', '-q', '--rebase', 'origin', 'main'])
    if code:
        ra.run(['git', 'rebase', '--abort'])
        for _p, plan in plans:
            print('### %s\nСТОП: git pull --rebase не прошел, повторите READY позже.\n%s' % (plan['tag'], ra.tail(out, 5)))
        return 1

    good, refusals = apply_group(plans, results)
    committed = False
    if good:
        env = dict(os.environ, MASS_OK='reread')
        shared = [('агрегаторы из видимых источников', [py, 'pipeline/split_discovery_sources.py', '--write']),
                  ('слой фактов', [py, 'pipeline/facts_derive.py', '--write']),
                  ('цитата у каждой правки факта (fact_edit_guard.py)', [py, 'pipeline/fact_edit_guard.py']),
                  ('проверки данных (prepush_check.py)', [py, 'pipeline/prepush_check.py'])]
        failed = None
        for name, cmd in shared:
            code, out = ra.run(cmd, env=env)
            if code:
                failed = (name, out)
                break
        if failed is None:
            old = json.loads(subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'], cwd=ra.ROOT,
                                            capture_output=True, text=True).stdout)
            new = json.load(open(ra.DATA, encoding='utf-8'))
            lost = ({d['id'] for d in old['deals']} - {d['id'] for d in new['deals']}) | (set(old['companies']) - set(new['companies']))
            ok_lost = set()
            for _p, plan in good:
                ok_lost |= set(plan.get('lost_ok') or [])
            if lost - ok_lost:
                failed = ('семантическая сверка базы', 'пропали сделки или профили: %s' % sorted(lost - ok_lost)[:10])
        if failed is not None:
            ra.revert()
            ra.note('СТОП группы «%s» — партии пойдут по одной | %s' % (failed[0], ' / '.join(l.strip()[:150] for l in str(failed[1]).splitlines() if 'FAILED' in l or 'Error' in l)[:600]))
            fcntl.flock(lock, fcntl.LOCK_UN)
            for path, plan in good:                      # по одной, обычной командой (сама берет замок)
                r = subprocess.run([py, 'pipeline/reread_apply.py', path, '--write'], cwd=ra.ROOT,
                                   capture_output=True, text=True, timeout=1500)
                results[plan['tag']] = (r.stdout or '') + (r.stderr or '')[-800:]
            good = []
        else:
            with open(ra.ERRORS, 'a', encoding='utf-8') as f:
                for _p, plan in good:
                    for e in plan.get('errors') or []:
                        f.write(json.dumps(dict(e, tag=plan['tag']), ensure_ascii=False) + '\n')
            ra.run(['git', 'add', '-u'])
            ra.run(['git', 'add', ra.ERRORS])
            code, out = ra.run(['git', 'ls-files', '--others', '--exclude-standard', 'pipeline/ingest/fixes'])
            untracked = out.split()
            done = {}
            for _p, plan in good:
                for sc in plan.get('scripts') or []:
                    ra.run(['git', 'add', sc])
                for f in untracked:
                    if plan['tag'] in f:
                        ra.run(['git', 'add', f])
                done[plan['tag']] = ra.stamped(plan['ids'])
            msg = 'Вычитка, партии %s: отметки %d из %d карточек' % (
                ', '.join(p['tag'] for _x, p in good), sum(len(v) for v in done.values()),
                sum(len(p['ids']) for _x, p in good))
            code, out = ra.run(['git', 'commit', '-q', '-m', msg + ra.ATTRIBUTION])
            ra.run([py, 'pipeline/publication_busy.py', '--wait', '20'])
            pushed = False
            for i in range(4):
                code, out = ra.run(['git', 'pull', '-q', '--rebase', 'origin', 'main'])
                if code:
                    ra.run(['git', 'rebase', '--abort'])
                    break
                code, out = ra.run(['git', 'push', '-q', 'origin', 'HEAD:main'])
                if not code:
                    pushed = True
                    break
                time.sleep(2 ** (i + 1))
            ra.note('%s: %s | %s' % ('ЗАПИСАНО' if pushed else 'НЕ ЗАПУШЕНО', msg, '; '.join(ra._T['steps'][-14:])))
            fcntl.flock(lock, fcntl.LOCK_UN)
            committed = True
            for _p, plan in good:
                tag, ids = plan['tag'], plan['ids']
                lines = ['ЗАПИСАНО И ЗАПУШЕНО: партия %s, отметки %d из %d карточек' % (tag, len(done[tag]), len(ids))
                         if pushed else 'ВНИМАНИЕ: записано локально, push не прошел — сообщите в отчете']
                missing = [i for i in ids if i not in done[tag]]
                if missing:
                    lines.append('Без отметки остались: %s' % ', '.join(missing))
                if refusals.get(tag):
                    lines.append('Причины отказа в отметке:\n' + '\n'.join('      ' + l.strip()[:260] for l in refusals[tag]))
                results[tag] = '\n'.join(lines)
    if not committed:
        try:
            fcntl.flock(lock, fcntl.LOCK_UN)
        except OSError:
            pass
    for tag, text in results.items():
        print('### %s\n%s' % (tag, text))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
