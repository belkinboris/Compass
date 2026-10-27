"""Прочитанные факты не устаревают от замены «е» на «е» (27 октября 2026).

`pipeline/strip_yo.py` переписал тексты карточек без «е». Отпечаток полей,
по которым факт читали (`facts.card_hash`: заголовок, доля, актив, сумма,
статус…), от этого изменился, и `facts_derive.py` отметил 33 прочитанных
факта как `stale` — «карточка изменилась после чтения». Но карточка не
изменилась: буква — та же, прочитанное — то же.

Скрипт берет карточку из `HEAD` (еще с «е»), складывает в ней «е» → «е» и
сравнивает отпечатки: совпали — значит, с чтения поменялась только буква,
и факт возвращается к прежнему основанию с новым отпечатком. Любое другое
расхождение остается `stale`, как и должно.

    python3 pipeline/fix_2026_10_27_facts_after_yo.py            # сухой прогон
    python3 pipeline/fix_2026_10_27_facts_after_yo.py --write    # затем facts_derive.py --write
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import facts  # noqa: E402
import strip_yo  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
READ = ('read', 'verified', 'disputed')


def plan(old_deals, new_deals):
    old = {d['id']: d for d in old_deals}
    out = []
    for d in new_deals:
        o = old.get(d['id'])
        if not o:
            continue
        folded = strip_yo.strip_values(o)
        for key in ('stake', 'price', 'date', 'nature', 'target'):
            prev = (o.get('facts') or {}).get(key) or {}
            cur = (d.get('facts') or {}).get(key) or {}
            basis = prev.get('control_change_basis') if key == 'nature' else prev.get('basis')
            if basis not in READ:
                continue
            cur_basis = cur.get('control_change_basis') if key == 'nature' else cur.get('basis')
            if cur_basis != 'stale':
                continue
            if facts.card_hash(folded, key) != facts.card_hash(d, key):
                continue                      # изменилось что-то кроме буквы — пусть ждет чтения
            out.append((d, key, prev))
    return out


def apply(items):
    for d, key, prev in items:
        restored = dict(prev, card_hash=facts.card_hash(d, key))
        if key == 'nature':
            cur = d['facts'][key]
            cur.update({k: v for k, v in restored.items() if k not in facts.NATURE_FLAGS and k != 'basis'})
            cur['control_change_basis'] = prev.get('control_change_basis') or prev.get('basis')
        else:
            restored.pop('stale_from', None)
            d['facts'][key] = restored


def main(argv):
    write = '--write' in argv
    old = json.loads(subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'],
                                    capture_output=True, text=True, cwd=ROOT).stdout)
    base = json.load(open(DATA, encoding='utf-8'))
    items = plan(old['deals'], base['deals'])
    print('Фактов, устаревших только из-за «е»: %d (%s).' % (len(items), ', '.join(sorted({d['id'] for d, _, _ in items})[:10])))
    if not write:
        print('Сухой прогон. Запись — с ключом --write, затем facts_derive.py --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))
    items = plan(old['deals'], fresh['deals'])
    apply(items)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано: %d.' % len(items))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
