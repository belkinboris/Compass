#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Разрешение кандидатов на дубль — Компас решает сам, не спрашивает владельца.

ЗАЧЕМ. 13 сентября 2026 владелец возразил на предложение развивать консольную
кнопку «это этап уже описанной сделки»: «мне бы хотелось, чтобы ты сам
понимал, что это дубль, чтобы мне не пришлось нажимать». И указал на нюанс,
которого раньше не было: дубль — не всегда новый этап. Это может быть буквально
то же самое, что уже в карточке, без единого нового факта, — тогда черновик
просто не должен становиться карточкой, и владелец не должен об этом даже
узнавать, кроме как из отчёта «обновили карточку X».

ЧТО ЭТО. `promote.py`, найдя кандидата на дубль (`near_duplicate()`), больше
не спрашивает владельца напрямую — он складывает пару (черновик + карточка-
кандидат) в `data/inbox/duplicates/<дата>.json`. Этот скрипт — вторая
половина: `--queue` показывает пары читающему (саб-агенту рутины, по брифу
`DUPLICATE_RESOLUTION_BRIEF.md`), читающий решает один из пяти исходов
(`same_fact`/`new_stage`/`enrich`/`separate`/`unclear`) и отвечает JSON-ом,
`--check` проверяет ответ механически (та же дословность, что и у обычных
правок — `review.check()` переиспользуется, а не копируется), `--apply
--write` применяет: обновляет существующую карточку (событие или поле),
отпускает черновик как отдельную сделку, выбрасывает его как повтор без
нового факта — или, только если читающий сам не смог решить, кладёт пару в
обычный `hold`, откуда её увидит владелец, но уже с прочитанным
обоснованием, а не рутинным «это дубль?».

ГРАНИЦА. Скрипт не судит о смысле — это делает читающий. Скрипт проверяет,
что ответ не позволяет выдумку: цитата обязана лежать в кэше источника
дословно (`review.quote_is_real`), правка поля проходит ту же проверку, что
и обычная запись в таблицу `FIXES` (`review.check()`), событие того же вида
с тем же текстом не добавляется дважды.

Запуск:
    python3 pipeline/ingest/resolve_duplicates.py --queue
    python3 pipeline/ingest/resolve_duplicates.py --queue <key>
    python3 pipeline/ingest/resolve_duplicates.py --check  answers.json
    python3 pipeline/ingest/resolve_duplicates.py --apply  answers.json [--write]
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import promote          # noqa: E402
import review            # noqa: E402
import link_parties      # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DUP_DIR = os.path.join(ROOT, 'data', 'inbox', 'duplicates')
RESOLVED_PATH = os.path.join(DUP_DIR, 'resolved.json')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')
FIXES_DIR = os.path.join(HERE, 'fixes')

VERDICTS = {'same_fact', 'new_stage', 'enrich', 'separate', 'unclear'}
EVENT_KINDS = {'negotiations', 'approval', 'signed', 'closed', 'cancelled'}


def today():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def load_resolved():
    if os.path.exists(RESOLVED_PATH):
        return json.load(open(RESOLVED_PATH, encoding='utf-8'))
    return {}


def save_resolved(resolved):
    os.makedirs(DUP_DIR, exist_ok=True)
    json.dump(resolved, open(RESOLVED_PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def queue_items():
    """Все элементы `data/inbox/duplicates/*.json`, ещё не разрешённые."""
    resolved = load_resolved()
    items = []
    if not os.path.isdir(DUP_DIR):
        return items
    for name in sorted(os.listdir(DUP_DIR)):
        if not name.endswith('.json') or name == 'resolved.json':
            continue
        try:
            payload = json.load(open(os.path.join(DUP_DIR, name), encoding='utf-8'))
        except ValueError:
            continue
        for item in payload.get('items', []):
            if item.get('key') not in resolved:
                items.append(item)
    return items


def find_candidate(candidate_id):
    """(контейнер, список-поле, сама карточка) — из базы или из предпросмотра."""
    data = json.load(open(DATA, encoding='utf-8'))
    for d in data['deals']:
        if d['id'] == candidate_id:
            return data, 'deals', d
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    for c in pending['cards']:
        if c['id'] == candidate_id:
            return pending, 'cards', c
    return None, None, None


def save_container(container, path):
    json.dump(container, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def cmd_queue(only_key=None):
    items = queue_items()
    if only_key:
        items = [i for i in items if i.get('key') == only_key]
    if not items:
        print('Очередь пуста.')
        return
    print('В очереди: %d\n' % len(items))
    for item in items:
        draft = item['draft']
        _, _, card = find_candidate(item['candidate_id'])
        print('=' * 78)
        print('key: %s' % item['key'])
        print('причина ворот: %s' % item.get('reason'))
        print('\nЧЕРНОВИК:')
        print('  заголовок: %s' % draft.get('title'))
        print('  дата: %s | статус: %s' % (draft.get('date'), draft.get('status')))
        print('  источники: %s' % [s[1] for s in (draft.get('src') or []) if len(s) > 1])
        for f in ('asset', 'buyer_name', 'seller', 'sum'):
            if draft.get(f):
                print('  %s: %s' % (f, draft[f]))
        print('\nКАРТОЧКА-КАНДИДАТ (%s):' % item['candidate_id'])
        if card is None:
            print('  НЕ НАЙДЕНА — id мог устареть (слияние/удаление), решайте вручную.')
        else:
            print('  заголовок: %s' % card.get('title'))
            print('  статус: %s | дата: %s' % (card.get('status'), card.get('date')))
            print('  источники: %s' % [s[1] for s in (card.get('src') or []) if len(s) > 1])
            for f in ('asset', 'buyer_name', 'seller', 'sum'):
                if card.get(f):
                    print('  %s: %s' % (f, card[f]))
            if card.get('events'):
                print('  events: %s' % [(e.get('kind'), e.get('date'), str(e.get('note'))[:60])
                                        for e in card['events']])
            eco, law = card.get('eco') or {}, card.get('law') or {}
            for label, obj in (('eco', eco), ('law', law)):
                for f, v in obj.items():
                    if v and str(v).strip() not in ('', '—'):
                        print('  %s.%s: %s' % (label, f, str(v)[:160]))
        print()
    print('Бриф: pipeline/ingest/DUPLICATE_RESOLUTION_BRIEF.md')


def _field_fix_check(candidate_id, card, f, texts, inds, urls, companies):
    fix = dict(id=candidate_id, field=f.get('field'), old=review.get_field(card, f.get('field')),
              new=f.get('new'), quote=f.get('quote'), why=f.get('why') or '')
    return review.check(fix, card, texts, companies, inds, urls)


def _event_problems(candidate_id, card, ev, texts):
    problems = []
    for key in ('kind', 'date', 'title', 'note', 'source'):
        if not ev.get(key):
            problems.append('event.%s пуст' % key)
    if ev.get('kind') and ev['kind'] not in EVENT_KINDS:
        problems.append('event.kind %r не из известных видов %s' % (ev['kind'], sorted(EVENT_KINDS)))
    if ev.get('note') and not review.quote_is_real(ev['note'], texts):
        problems.append('event.note не лежит дословно ни в одном закэшированном источнике')
    for e in card.get('events') or []:
        if e.get('kind') == ev.get('kind') and review.flat(e.get('note')) == review.flat(ev.get('note')):
            problems.append('у кандидата уже есть событие %r с тем же текстом — это не новый этап'
                            % ev.get('kind'))
    return problems


def validate(answers, items_by_key, texts, inds, companies, urls):
    """Список (item, ответ, причины отказа) — причины пусты, если ответ годится."""
    out = []
    seen = set()
    for ans in answers.get('resolved') or []:
        key = ans.get('key')
        problems = []
        if not key or key not in items_by_key:
            problems.append('key %r не найден в живой очереди (устарел или уже разрешён)' % key)
            out.append((None, ans, problems))
            continue
        if key in seen:
            problems.append('key %r встречается дважды в одном ответе' % key)
        seen.add(key)
        item = items_by_key[key]
        verdict = ans.get('verdict')
        if verdict not in VERDICTS:
            problems.append('verdict %r не из %s' % (verdict, sorted(VERDICTS)))
        reasoning = str(ans.get('reasoning') or '').strip()
        if len(reasoning) < 15:
            problems.append('reasoning пуст или слишком короток — нужно объяснение, не штамп')
        candidate_id = ans.get('candidate_id') or item.get('candidate_id')
        if candidate_id != item.get('candidate_id'):
            problems.append('candidate_id не совпадает с тем, что был в очереди')
        _, _, card = find_candidate(candidate_id) if not problems else (None, None, None)
        if verdict in ('new_stage', 'enrich', 'separate') and card is None:
            problems.append('карточка-кандидат %s не найдена — id мог устареть' % candidate_id)
        elif verdict == 'new_stage':
            ev = ans.get('event') or {}
            problems += _event_problems(candidate_id, card, ev, texts)
        elif verdict == 'enrich':
            fixes = ans.get('field_fixes') or []
            if not fixes:
                problems.append('enrich без field_fixes — нечего применять')
            for f in fixes:
                problems += ['%s: %s' % (f.get('field'), p)
                            for p in _field_fix_check(candidate_id, card, f, texts, inds, urls, companies)]
        out.append((item, ans, problems))
    return out


def cmd_check(path):
    answers = json.load(open(path, encoding='utf-8'))
    items = {i['key']: i for i in queue_items()}
    inds, texts = review.industries(), review.source_texts()
    data = json.load(open(DATA, encoding='utf-8'))
    urls = review.source_urls()
    results = validate(answers, items, texts, inds, data['companies'], urls)
    bad = 0
    for item, ans, problems in results:
        label = ans.get('key')
        if problems:
            bad += 1
            print('  ОТКАЗ  %s (%s): %s' % (label, ans.get('verdict'), '; '.join(problems)))
        else:
            print('  ОК     %s -> %s' % (label, ans.get('verdict')))
    print('\nВсего: %d | ок: %d | отказ: %d' % (len(results), len(results) - bad, bad))
    return 1 if bad else 0


def _append_hold(draft, reasons, day=None):
    day = day or today()
    os.makedirs(HOLD_DIR, exist_ok=True)
    path = os.path.join(HOLD_DIR, day + '.json')
    payload = {'made': day, 'drafts': []}
    if os.path.exists(path):
        payload = json.load(open(path, encoding='utf-8'))
    payload.setdefault('drafts', []).append(dict(draft, hold_reasons=reasons))
    json.dump(payload, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def _mark_enrich(title, candidate_id):
    state = promote.load_state()
    state.setdefault('raw_titles', {})[promote.raw_key(title)] = 'enrich:%s' % candidate_id
    promote.save_state(state)


def _promote_as_separate(draft, data):
    """То же самое, что сделал бы promote.py, если бы near_duplicate() не сработал."""
    pending = promote.load_pending()
    existing = {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(draft, deal_id)
    party_index = link_parties.build_index(data['companies'])
    for line in link_parties.link_card(card, party_index, data['companies']):
        print('    %s | связано -> %s' % (deal_id, line))
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    pending['cards'].append(card)
    promote.save_pending(pending)
    try:
        import fetch_article_texts as articles
        targets = [(deal_id, str(s[1]), str(card.get('title') or ''))
                   for s in (card.get('src') or []) if len(s) > 1 and str(s[1]).startswith('http')]
        articles.fetch_and_store(targets, write=True)
    except Exception as e:                                        # noqa: BLE001
        print('    (полный текст источника не скачан: %s)' % e)
    return deal_id


def cmd_apply(path, write):
    answers = json.load(open(path, encoding='utf-8'))
    items = {i['key']: i for i in queue_items()}
    inds, texts = review.industries(), review.source_texts()
    data = json.load(open(DATA, encoding='utf-8'))
    urls = review.source_urls()
    results = validate(answers, items, texts, inds, data['companies'], urls)
    bad = [r for r in results if r[2]]
    if bad:
        print('Есть отклонённые ответы — не применяем НИЧЕГО: ответ надо починить целиком.')
        for item, ans, problems in bad:
            print('  ОТКАЗ  %s (%s): %s' % (ans.get('key'), ans.get('verdict'), '; '.join(problems)))
        return 1
    if not write:
        print('Сухой прогон, %d ответов прошли проверку. Запись — с ключом --write.' % len(results))
        for item, ans, _ in results:
            print('  %s -> %s (%s)' % (ans['key'], ans['verdict'], item['candidate_id']))
        return 0

    resolved = load_resolved()
    enrich_fixes = []   # копятся для одного файла партии, потом один вызов review.py
    updates = []         # человекочитаемые строки для отчёта прогона (FYI, не вопрос)
    for item, ans, _ in results:
        key, verdict, candidate_id = ans['key'], ans['verdict'], item['candidate_id']
        draft, title = item['draft'], item['draft'].get('title')
        if verdict == 'same_fact':
            _mark_enrich(title, candidate_id)
            updates.append('%s: тот же факт, что уже в карточке — черновик не публикуется' % candidate_id)
        elif verdict == 'enrich':
            _, _, card = find_candidate(candidate_id)
            for f in ans['field_fixes']:
                enrich_fixes.append(dict(id=candidate_id, field=f['field'],
                                         old=review.get_field(card, f['field']),
                                         new=f['new'], quote=f['quote'], why=f['why']))
            _mark_enrich(title, candidate_id)
            updates.append('%s: дополнено полями %s (%s)'
                           % (candidate_id, ', '.join(f['field'] for f in ans['field_fixes']), ans['reasoning'][:120]))
        elif verdict == 'new_stage':
            container, field, card = find_candidate(candidate_id)
            ev = dict(ans['event'], id='%s-%s' % (candidate_id, ans['event']['kind']))
            card.setdefault('events', []).append(ev)
            path_ = DATA if field == 'deals' else PENDING
            save_container(container, path_)
            if ev['kind'] in review.POSTWORTHY_MILESTONE_KINDS and ans.get('milestone_headline'):
                out = subprocess.run(
                    [sys.executable, os.path.join(HERE, 'review.py'), '--milestone',
                     candidate_id, ev['kind'], ans['milestone_headline'], '--write'],
                    cwd=HERE, capture_output=True, text=True)
                print(out.stdout)
                if out.returncode != 0:
                    print(out.stderr)
            _mark_enrich(title, candidate_id)
            updates.append('%s: новый этап «%s» (%s)' % (candidate_id, ev['title'], ans['reasoning'][:120]))
        elif verdict == 'separate':
            container, field, card = find_candidate(candidate_id)
            if not card.get('separate_transaction_reviewed'):
                card['separate_transaction_reviewed'] = True
                path_ = DATA if field == 'deals' else PENDING
                save_container(container, path_)
            new_id = _promote_as_separate(draft, data)
            updates.append('%s: не тот же дубль — своя карточка %s (%s)'
                           % (candidate_id, new_id, ans['reasoning'][:120]))
        elif verdict == 'unclear':
            _append_hold(draft, ['похоже на карточку %s, но читающий не смог решить сам: %s'
                                 % (candidate_id, ans['reasoning'])])
            updates.append('%s: не удалось решить чтением — вопрос в консоли' % candidate_id)
        resolved[key] = {'verdict': verdict, 'candidate_id': candidate_id, 'day': today()}

    if enrich_fixes:
        day = today()
        fixes_path = os.path.join(FIXES_DIR, 'batch_duplicate_resolve_%s.py' % day.replace('-', '_'))
        existing_fixes = []
        if os.path.exists(fixes_path):
            # Повторный прогон в тот же день: FIXES из уже существующего файла
            # читаются, чтобы не потерять записи предыдущего вызова --apply.
            ns = {}
            exec(open(fixes_path, encoding='utf-8').read(), ns)          # noqa: S102
            existing_fixes = ns.get('FIXES') or []
        with open(fixes_path, 'w', encoding='utf-8') as fh:
            fh.write('# -*- coding: utf-8 -*-\n')
            fh.write('"""Правки из resolve_duplicates.py (%s): поля, которые дочитывание\n'
                    'чтением дубликатов дополнило существующим карточкам-кандидатам, а не\n'
                    'новым черновикам — сама сделка не изменилась, изменилось то, что о\n'
                    'ней узнали.\n"""\n\n' % day)
            fh.write('FIXES = %r\n' % (existing_fixes + enrich_fixes))
        out = subprocess.run([sys.executable, os.path.join(HERE, 'review.py'), '--write'],
                             cwd=HERE, capture_output=True, text=True)
        print(out.stdout)
        if out.returncode != 0:
            print(out.stderr)

    save_resolved(resolved)
    print('\nПрименено: %d.' % len(results))
    print('\nОБНОВЛЕНИЯ (для отчёта прогона — FYI, не вопрос владельцу):')
    for line in updates:
        print('  - %s' % line)
    return 0


def main():
    args = sys.argv[1:]
    if '--queue' in args:
        i = args.index('--queue')
        only = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith('--') else None
        cmd_queue(only)
        return 0
    if '--check' in args:
        i = args.index('--check')
        return cmd_check(args[i + 1])
    if '--apply' in args:
        i = args.index('--apply')
        return cmd_apply(args[i + 1], write='--write' in args)
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main())
