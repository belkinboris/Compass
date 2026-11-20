# -*- coding: utf-8 -*-
"""Разрешение конфликта ребейза 19 ноября 2026 (~09:20 МСК прогон) для трех
файлов: data/inbox/duplicates/2026-11-19.json, data/inbox/hold/2026-11-19.json
(списки объектов с уникальным ключом — 'key' у дублей, 'draft_id' у hold:
трехсторонний merge по ключу, порядок 'ours' сохраняется, новые записи
'theirs' дописываются в конец) и data/inbox/moderation_state.json (словарь
словарей и один список sent_raw — merge по под-ключу/объединение множеств).

Одноразовый скрипт разрешения конфликта — не обычная правка данных,
используется прямо при `git rebase`, без --write/сухого прогона: читает три
стадии (:1/:2/:3 через git show) и пишет результат в рабочее дерево.
"""
import json
import subprocess

ROOT = '/home/user/Compass'


def show(stage, path):
    out = subprocess.run(['git', 'show', '%s:%s' % (stage, path)], cwd=ROOT,
                          capture_output=True, text=True).stdout
    return json.loads(out)


def merge_list(base_items, ours_items, theirs_items, key):
    base = {it[key]: it for it in base_items}
    ours = {it[key]: it for it in ours_items}
    theirs = {it[key]: it for it in theirs_items}
    conflicts = []
    merged = []
    for it in ours_items:
        k = it[key]
        b, o, t = base.get(k), ours.get(k), theirs.get(k)
        if k not in theirs:
            if k in base and b != o:
                pass  # ours изменил, theirs убрал — оставляем ours (новее)
            merged.append(o)
            continue
        if o == t:
            merged.append(o)
        elif b == o:
            merged.append(t)   # ours не менял — берем theirs
        elif b == t:
            merged.append(o)   # theirs не менял — берем ours
        else:
            conflicts.append(k)
            merged.append(o)   # по умолчанию ours, конфликт — в отчет
    for it in theirs_items:
        k = it[key]
        if k in ours:
            continue
        # 20 ноября 2026: id из base, которого ours не несет и theirs не
        # менял, — это НАМЕРЕННОЕ удаление (drop_pending.py), не пропуск.
        # Слепое дописывание сюда возвращало выкинутые карточки обратно
        # (gb82efd9f, g502a9986 и другие — известная ошибка, known_issues/intake.md).
        if k in base and base[k] == it:
            continue
        merged.append(it)
    return merged, conflicts


def merge_dict_of_dicts(base, ours, theirs):
    conflicts = []
    out = {}
    for k in set(base) | set(ours) | set(theirs):
        b, o, t = base.get(k), ours.get(k), theirs.get(k)
        if o == t:
            if o is not None:
                out[k] = o
        elif b == o:
            if t is not None:
                out[k] = t
        elif b == t:
            if o is not None:
                out[k] = o
        else:
            conflicts.append(k)
            if o is not None:
                out[k] = o
    return out, conflicts


def merge_list_of_scalars(base, ours, theirs):
    merged = list(ours)
    for x in theirs:
        if x not in ours:
            merged.append(x)
    return merged


def do_dup_or_hold(path, listkey, idkey):
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    merged_items, conflicts = merge_list(base[listkey], ours[listkey], theirs[listkey], idkey)
    out = dict(ours)
    out[listkey] = merged_items
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: %d записей, конфликтов: %d %s' % (path, len(merged_items), len(conflicts), conflicts))


def do_moderation_state():
    path = 'data/inbox/moderation_state.json'
    base = show(':1', path)
    ours = show(':2', path)
    theirs = show(':3', path)
    out = {}
    all_conflicts = {}
    for k in set(base) | set(ours) | set(theirs):
        b, o, t = base.get(k, {}), ours.get(k, {}), theirs.get(k, {})
        if isinstance(o, list) or isinstance(t, list) or isinstance(b, list):
            out[k] = merge_list_of_scalars(b if isinstance(b, list) else [],
                                            o if isinstance(o, list) else [],
                                            t if isinstance(t, list) else [])
        else:
            merged, conflicts = merge_dict_of_dicts(b, o, t)
            out[k] = merged
            if conflicts:
                all_conflicts[k] = conflicts
    with open('%s/%s' % (ROOT, path), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%s: конфликтов: %s' % (path, all_conflicts or 'нет'))


if __name__ == '__main__':
    do_dup_or_hold('data/inbox/duplicates/2026-11-19.json', 'items', 'key')
    do_dup_or_hold('data/inbox/hold/2026-11-19.json', 'drafts', 'draft_id')
    do_moderation_state()
