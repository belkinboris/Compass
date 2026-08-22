# -*- coding: utf-8 -*-
"""Приток, предварительный отсев «сомнительного» сырья — шаг D
(MILESTONES_BRIEF.md, между `promote.py` и `send_drafts.py`).

ЗАЧЕМ. Владелец 21 августа: «Может хотя бы какую-то предварительную работу
проделывать прежде чем такое отправлять?» — про сырьё вроде «Выкуп, каравай
и икона в банкетном зале. Какие свадьбы сейчас в моде» в консоли «на
решение». Механический фильтр (`classify.py`) ловит форму («выкуп»,
«приобрёл»), но не смысл — «предварительная работа» здесь означает чтение
моделью, а не новую регулярку: то же разделение, что уже записано в
CLAUDE.md («механика отвечает за форму и запрет, чтение — за смысл»).

ЧТО ДЕЛАЕТ ЭТОТ ФАЙЛ, А ЧТО — РУТИНА. Файл только ПОКАЗЫВАЕТ несрешённое
сырьё с контекстом (причины ворот + лучшее совпадение с уже существующей
карточкой через `matcher.match`) и ПРИМЕНЯЕТ решения, переданные явно
(`--drop`/`--enrich`). Суждение «это мусор» / «это сделка» / «это
дополнение к уже известной карточке» делает рутина (агент), читая вывод, —
как и everywhere в этом проекте, где нужен смысл, а не форма.

ТРИ ИСХОДА, КОТОРЫЕ РУТИНА ВЫБИРАЕТ САМА:
  1. МУСОР УВЕРЕННО (свадьбы, кладбища, макроэкономика, гайды «сколько
     стоит», спорт, политика без сделки) — `--drop <id> [<id> ...]
     --reason "..." --write`. Помечается `decided_raw[id]='auto-drop'` —
     ОТДЕЛЬНОЕ от ручного 'drop' значение: аудит должен различать, кто
     решил, человек или рутина (если понадобится откатить один класс
     автоматических решений, не трогая ручные).
  2. ПОХОЖЕ НА СДЕЛКУ ИЛИ НЕПОНЯТНО — не трогать: `send_drafts.py`
     покажет как обычно. ПРИ СОМНЕНИИ — ПОКАЗЫВАТЬ, а не отбрасывать:
     терять сделку молча дороже, чем показать человеку лишнее.
  3. СОВПАДАЕТ С УЖЕ СУЩЕСТВУЮЩЕЙ КАРТОЧКОЙ (случай Alumni Partners/
     «Полекс»: объявление консультанта об уже известной сделке) —
     `--enrich <draft_id>=<deal_id> --write`. Не идёт в консоль как
     «новая сомнительная»; рутина сама читает статью тем же прогоном и
     переносит факты в `<deal_id>` через `review.py`. Флаг ТОЛЬКО
     помечает черновик решённым (чтобы не спросить снова) — сама работа
     чтения и обогащения этим файлом не делается.

ПЕРЕД ВКЛЮЧЕНИЕМ В РУТИНУ — ЗАМЕР, НЕ МНЕНИЕ (см. MILESTONES_BRIEF.md,
раздел D): прогнать критерий «мусор уверенно» по уже принятым решениям
владельца в `moderation_state.json` (~100 его вчерашних 'drop' + все
'take') и убедиться, что ни один 'take' не попал бы под авто-drop.

Запуск:
    python3 pipeline/ingest/raw_screen.py                 # список на решение
    python3 pipeline/ingest/raw_screen.py --limit 40       # ограничить список
    python3 pipeline/ingest/raw_screen.py --drop d1 d2 --reason "свадьбы, не сделка" --write
    python3 pipeline/ingest/raw_screen.py --enrich d3=g123abc --write
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import match as matcher  # noqa: E402
import promote  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')


def all_raw_drafts():
    """Все черновики сырья по всем hold-файлам, БЕЗ дублей по draft_id —
    один и тот же недорешённый черновик переносится вперёд каждый день,
    пока по нему нет решения (см. урок approve.py от 21 августа, там же
    дедуп на сборке `raw_all`)."""
    seen_ids, out = set(), []
    if not os.path.isdir(HOLD_DIR):
        return out
    for name in sorted(os.listdir(HOLD_DIR)):
        if not name.endswith('.json'):
            continue
        for d in json.load(open(os.path.join(HOLD_DIR, name), encoding='utf-8')).get('drafts', []):
            did = str(d.get('draft_id'))
            if did and did not in seen_ids:
                seen_ids.add(did)
                out.append(d)
    return out


def undecided(state=None):
    """Сырьё, которое `send_drafts.py` показал бы дальше: не решено ни по
    draft_id, ни по заголовку, не дубль внутри партии. Та же фильтрация,
    что в `send_drafts.build_plan()` — держать в одном месте нельзя (файлы
    разных рутин), но логика обязана совпадать дословно."""
    state = state if state is not None else promote.load_state()
    decided_ids = set(state.get('decided_raw', {}))
    decided_titles = set(state.get('raw_titles', {}))
    out = []
    for d in all_raw_drafts():
        if str(d.get('draft_id')) in decided_ids:
            continue
        if promote.raw_key(d.get('title')) in decided_titles:
            continue
        if d.get('dup_in_batch'):
            continue
        out.append(d)
    return out


def best_match(draft, idx):
    """Лучшее совпадение с уже существующей карточкой (база + очередь) —
    подсказка рутине для исхода 3 («это дополнение, а не новая сделка»),
    не решение: `matcher.match` считает дублем не только буквальные
    повторы, порог подобран замером в match.py."""
    src = draft.get('src') or []
    found, why = matcher.match(
        {'title': draft.get('title'), 'date': draft.get('date'),
         'url': src[0][1] if src and len(src[0]) > 1 else None,
         'buyer': draft.get('buyer_name'), 'asset': draft.get('asset'),
         'seller': draft.get('seller'), 'status': draft.get('status')}, idx)
    return found, why


def build_index():
    data = json.load(open(DATA, encoding='utf-8'))
    pending = promote.load_pending()
    idx = matcher.index_base(data['deals'] + pending['cards'],
                             data.get('companies'), data.get('match_keys'))
    return idx


def render_list(limit=None):
    state = promote.load_state()
    idx = build_index()
    items = undecided(state)
    if limit:
        items = items[:limit]
    if not items:
        print('Несрешённого сырья нет.')
        return
    print('Несрешённого сырья: %d%s\n' % (len(undecided(state)),
          ' (показаны первые %d)' % limit if limit and len(undecided(state)) > limit else ''))
    for d in items:
        found, why = best_match(d, idx)
        print('draft_id=%s' % d.get('draft_id'))
        print('  заголовок: %s' % str(d.get('title'))[:200])
        print('  дата: %s | источник: %s' % (
            d.get('date'), (d.get('src') or [[None, None]])[0][1] if d.get('src') else '—'))
        reasons = d.get('hold_reasons') or []
        if reasons:
            print('  причина не пропущена автоматически: %s' % '; '.join(reasons))
        if found:
            print('  ПОХОЖЕ НА ДОПОЛНЕНИЕ к %s (%s) — кандидат на --enrich' % (found, why))
        print()


def apply_drop(ids, reason, write):
    state = promote.load_state()
    drafts_by_id = {str(d.get('draft_id')): d for d in all_raw_drafts()}
    missing = [i for i in ids if i not in drafts_by_id]
    if missing:
        print('ОТКАЗ: черновиков нет в hold-файлах: %s' % ', '.join(missing))
        return 1
    print('ВЫКИДЫВАЮ (авто, причина: %s):' % (reason or '(без причины)'))
    for i in ids:
        print('  %s | %s' % (i, str(drafts_by_id[i].get('title'))[:100]))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    for i in ids:
        state.setdefault('decided_raw', {})[i] = 'auto-drop'
        state.setdefault('raw_titles', {})[promote.raw_key(drafts_by_id[i].get('title'))] = 'auto-drop'
        state.setdefault('auto_drop_reasons', {})[i] = reason or ''
    promote.save_state(state)
    print('Записано: %d.' % len(ids))
    return 0


def apply_enrich(pairs, write):
    state = promote.load_state()
    drafts_by_id = {str(d.get('draft_id')): d for d in all_raw_drafts()}
    missing = [did for did, _ in pairs if did not in drafts_by_id]
    if missing:
        print('ОТКАЗ: черновиков нет в hold-файлах: %s' % ', '.join(missing))
        return 1
    print('ПОМЕЧАЮ КАК ДОПОЛНЕНИЕ (не новая сделка, читать и нести в review.py):')
    for did, deal_id in pairs:
        print('  %s -> %s | %s' % (did, deal_id, str(drafts_by_id[did].get('title'))[:100]))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    for did, deal_id in pairs:
        state.setdefault('decided_raw', {})[did] = 'enrich:%s' % deal_id
        state.setdefault('raw_titles', {})[promote.raw_key(drafts_by_id[did].get('title'))] = 'enrich:%s' % deal_id
    promote.save_state(state)
    print('Записано: %d. Теперь прочитайте эти статьи и внесите факты через review.py.' % len(pairs))
    return 0


def main(argv):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--drop', nargs='+', default=None, metavar='DRAFT_ID')
    p.add_argument('--reason', default='')
    p.add_argument('--enrich', nargs='+', default=None, metavar='DRAFT_ID=DEAL_ID')
    p.add_argument('--write', action='store_true')
    args = p.parse_args(argv)

    if args.drop:
        return apply_drop(args.drop, args.reason, args.write)
    if args.enrich:
        pairs = []
        for item in args.enrich:
            assert '=' in item, '--enrich требует вид draft_id=deal_id, получено %r' % item
            did, deal_id = item.split('=', 1)
            pairs.append((did, deal_id))
        return apply_enrich(pairs, args.write)
    render_list(args.limit)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
