"""Профили для сторон сделок, записанных текстом (кампания 23 октября 2026).

Владелец: «Конечно нужно всем профили заводить, нам же нужно показывать их фин
показатели если люди кликнут, а значит нужно им инн присваивать и почему бы не
делать страницы для них?» 934 стороны витрины (продавец, покупатель, предмет)
стояли текстом без профиля. Шесть читателей разобрали их по заданию
`data/inbox/profiles_2026_10_23/BRIEF.md`; их ответы — `batchN.result.json`
рядом с пачками. Этот скрипт ничего не решает сам, только применяет:

  existing         — роль привязывается к существующему профилю;
  ru_company       — новый профиль; ИНН есть — строка `confirmed` в
                     `pipeline/fns_registry.py`, нет — `no_match` с тем, что
                     читатель проверил;
  foreign_company  — новый профиль, строка `foreign`;
  person, not_company, state — ничего (профиль заводится только компании).

Страховки, а не доверие к ответу:
  * новый профиль, чей ключ близнецов (`link_parties.company_key`) уже
    ведет в ОДИН профиль базы, не заводится — роль идет в тот профиль;
  * ИНН, уже записанный в реестре за другим профилем, — роль идет в тот профиль;
  * одна компания в нескольких строках пачек (ключ имени или ИНН) — один профиль;
  * роль заполняется, только если пуста, и не тем профилем, что уже стоит
    другой ролью этой карточки (продавец = предмет — та ошибка, что у
    «Медиа-1 Аутдор»);
  * отрасль — только из списка сайта, ИНН — с контрольной суммой.

Без ключа — сухой прогон; `--write` перечитывает базу прямо перед записью.
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import link_parties  # noqa: E402
from pipeline import fns_registry  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
DIR = os.path.join(ROOT, 'data', 'inbox', 'profiles_2026_10_23')
DAY = '2026-10-23'
ROLE_FIELD = {'target': 'target', 'buyer': 'buyer', 'seller': 'seller_id'}

# Имя нового профиля совпало по ключу близнецов с ДРУГОЙ компанией базы —
# прочитано глазами 23 октября: материнская компания против своей российской
# дочки, предмета той же сделки (Autoliv / ООО «Аутолив», OTP Group / ОТП Банк),
# и петербургский девелопер Element против производителя микроэлектроники
# «Элемент». Имя уточняется, чтобы это были два профиля, а не один.
NAME_OVERRIDE = {
    'Autoliv': 'Autoliv Inc.',
    'OTP Bank': 'OTP Group',
    'Element': 'Element (девелопер)',
}
# Близнец по ключу, который ЕСТЬ та же компания, но привязать нельзя: профиль
# «Nokian Tyres» описан как финская материнская компания и при этом стоит
# предметом сделки о продаже российского бизнеса. Чинится отдельно — сначала
# профиль предмета, потом продавец.
SKIP = {'Nokian Tyres'}
# Роли, где имя покупателя записано таблицей FIXES дословно юрлицом
# («ООО «Кинокомпания «Парадиз продакшнз»»»), а профиль базы называется
# брендом («Парадиз»): снять текст — значит потерять правку таблицы
# (review.already_applied сверяет имя профиля по ключу). Привязать — после
# переименования профиля или правки записи таблицы, отдельным шагом.
SKIP_LINKS = set()  # «Парадиз» привязан после правки review.already_applied — отпечаток снятого имени


def inn_ok(inn):
    s = str(inn or '')
    if not re.fullmatch(r'\d{10}|\d{12}', s):
        return False
    d = [int(c) for c in s]
    if len(s) == 10:
        w = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return sum(a * b for a, b in zip(w, d)) % 11 % 10 == d[9]
    w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    return (sum(a * b for a, b in zip(w1, d)) % 11 % 10 == d[10]
            and sum(a * b for a, b in zip(w2, d)) % 11 % 10 == d[11])


def load_answers(partial=False):
    rows = []
    for path in sorted(glob.glob(os.path.join(DIR, 'batch?.result.json'))):
        res = json.load(open(path, encoding='utf-8'))
        src = json.load(open(path.replace('.result', ''), encoding='utf-8'))
        complete = len(res) == len(src) and all(a['text'] == b['text'] for a, b in zip(res, src))
        if partial and not complete:
            print('пачка не готова, пропущена:', os.path.basename(path)); continue
        assert complete, path
        for a, b in zip(res, src):
            rows.append(dict(a, mentions=b['mentions'], batch=os.path.basename(path)))
    return rows


def new_id(name, taken):
    import hashlib
    n = 0
    while True:
        cid = 'g' + hashlib.sha1(('%s|%d' % (name, n)).encode()).hexdigest()[:8]
        if cid not in taken:
            return cid
        n += 1


def plan(data, answers):
    comps = data['companies']
    industries = {v.get('ind') for v in comps.values() if v.get('ind')}
    key_index = link_parties.build_index(comps)
    inn_owner, dead_owner = {}, {}
    for row in fns_registry.REGISTRY:
        if row.get('decision') == 'confirmed' and row.get('inn'):
            if row['company_id'] in comps:
                inn_owner.setdefault(str(row['inn']), row['company_id'])
            else:
                # Строка реестра пережила свой профиль (профиль удален). Новый
                # профиль той же компании получает тот же id — и строка снова
                # работает, а не становится вторым владельцем ИНН.
                dead_owner.setdefault(str(row['inn']), row['company_id'])
    current = fns_registry.by_company_id()
    new_profiles, registry_rows, links, notes = {}, [], [], defaultdict(list)
    made_by_key, made_by_inn = {}, {}

    for a in answers:
        kind = a.get('kind')
        target_id = None
        if kind == 'existing':
            target_id = a.get('existing_id')
            if target_id not in comps:
                notes['existing_missing'].append(a['text']); continue
            inn = a.get('inn')
            if inn and inn_ok(inn) and target_id not in fns_registry.confirmed_inns() \
                    and inn_owner.get(str(inn), target_id) == target_id:
                registry_rows.append({'company_id': target_id, 'decision': 'confirmed', 'inn': str(inn),
                                      'reason': _reason(a), 'date': DAY})
                inn_owner[str(inn)] = target_id
        elif kind in ('ru_company', 'foreign_company'):
            name = ' '.join(str(a.get('name') or '').split())
            name = NAME_OVERRIDE.get(name, name)
            if name in SKIP:
                notes['skipped_by_hand'].append(name); continue
            if not name:
                notes['no_name'].append(a['text']); continue
            inn = str(a.get('inn') or '') or None
            if inn and not inn_ok(inn):
                notes['bad_inn'].append((a['text'], inn)); inn = None
            key = link_parties.company_key(name)
            if inn and inn in inn_owner:
                target_id = inn_owner[inn]; notes['inn_already_in_base'].append((name, target_id))
            elif inn and inn in made_by_inn:
                target_id = made_by_inn[inn]
            elif key and key_index.get(key):
                notes['twin_unresolved'].append((name, sorted(key_index[key]))); continue
            elif key and key in made_by_key:
                target_id = made_by_key[key]
            else:
                ind = a.get('ind') if a.get('ind') in industries else None
                if not ind:
                    notes['bad_ind'].append((name, a.get('ind'))); continue
                desc = ' '.join(str(a.get('desc') or '').split())
                if len(desc) < 20:
                    notes['no_desc'].append(name); continue
                revived = dead_owner.get(inn) if inn else None
                target_id = revived or new_id(name, set(comps) | set(new_profiles))
                if revived:
                    notes['revived_id'].append((name, revived))
                new_profiles[target_id] = {'name': name, 'ind': ind, 'desc': desc, 'kpi': []}
                if key:
                    made_by_key[key] = target_id
                if inn:
                    made_by_inn[inn] = target_id; inn_owner[inn] = target_id
                if kind == 'foreign_company':
                    registry_rows.append({'company_id': target_id, 'decision': 'foreign',
                                          'reason': 'Иностранная компания (кампания профилей сторон, %s): %s'
                                          % (DAY, (a.get('note') or a.get('inn_note') or name)), 'date': DAY})
                elif inn and target_id == dead_owner.get(inn):
                    pass                                   # строка реестра уже есть
                elif inn:
                    registry_rows.append({'company_id': target_id, 'decision': 'confirmed', 'inn': inn,
                                          'reason': _reason(a), 'date': DAY})
                else:
                    registry_rows.append({'company_id': target_id, 'decision': 'no_match',
                                          'reason': 'Кампания профилей сторон (%s): юрлицо не установлено. %s'
                                          % (DAY, a.get('inn_note') or 'читатель не нашел однозначного юрлица'),
                                          'date': DAY})
        else:
            continue
        for m in a['mentions']:
            links.append((m['deal'], m['role'], target_id, a['text']))
    return new_profiles, registry_rows, links, notes


def _reason(a):
    bits = ['Кампания профилей сторон (%s): %s' % (DAY, a.get('legal_name') or a.get('name') or a['text'])]
    if a.get('ogrn'):
        bits.append('ОГРН %s' % a['ogrn'])
    bits.append('ИНН %s' % a['inn'])
    text = '; '.join(bits) + '.'
    if a.get('inn_note'):
        text += ' ' + str(a['inn_note']).strip()
    if a.get('inn_source'):
        text += ' Источник: %s' % a['inn_source']
    return text


def apply_links(data, links):
    import copy
    import review
    by_id = {d['id']: d for d in data['deals']}
    fixes_of = defaultdict(list)
    for fix in review.FIXES:
        fixes_of[fix['id']].append(fix)
    done, skipped = [], []
    for deal_id, role, cid, text in links:
        d = by_id.get(deal_id)
        field = ROLE_FIELD[role]
        if d is None:
            skipped.append((deal_id, role, 'нет карточки')); continue
        if (deal_id, role) in SKIP_LINKS:
            skipped.append((deal_id, role, 'отложено вручную')); continue
        if d.get(field) or (role == 'target' and d.get('asset_id')):
            skipped.append((deal_id, role, 'роль уже привязана')); continue
        others = {d.get(f) for r, f in ROLE_FIELD.items() if r != role} | {d.get('asset_id')}
        if cid in others:
            skipped.append((deal_id, role, 'тот же профиль уже стоит другой ролью')); continue
        before = copy.deepcopy(d)
        d[field] = cid
        if field == 'buyer':
            # Как в link_parties: у покупателя либо профиль, либо текст
            # (test_buyer_is_named_once); у продавца и предмета текст остается.
            # Имя могло прийти из таблицы FIXES — его отпечаток уходит в
            # proofread_absorbed, иначе review.already_applied сочтет правку
            # потерянной (docs/card_editing.md).
            gone = d.pop('buyer_name', None)
            if gone:
                import review
                fps = d.setdefault('proofread_absorbed', {}).setdefault('buyer_name', [])
                fp = review.fix_fingerprint(gone)
                if fp not in fps:
                    fps.append(fp)
        # Привязка не должна «потерять» правку таблицы FIXES (ее проверяет
        # test_review_table_is_applied_and_not_pending): имя покупателя из
        # таблицы засчитывается, только если профиль называется так же.
        if not all(review.already_applied(f, d, data['companies']) for f in fixes_of.get(deal_id, ())):
            d.clear(); d.update(before)
            skipped.append((deal_id, role, 'имя записано таблицей FIXES иначе, чем профиль')); continue
        done.append((deal_id, role, cid))
    return done, skipped


def write_registry(rows):
    """Новые строки — в конец. У профиля одна текущая запись
    (test_fns_registry_company_id_is_not_duplicated): если у существующего
    профиля уже была строка (обычно `no_match` — «искали, не нашли»), она
    снимается из REGISTRY этим же блоком, а текст старой остается в файле
    как история поиска."""
    known = {r['company_id'] for r in fns_registry.REGISTRY}
    replaced = sorted({r['company_id'] for r in rows} & known)
    src = open(REG, encoding='utf-8').read()
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src
    lines = ['', '', '# Кампания профилей для сторон сделок без профиля — %s' % DAY,
             '# (pipeline/apply_party_profiles_2026_10_23.py, ответы читателей в',
             '# data/inbox/profiles_2026_10_23/).']
    if replaced:
        lines += ['# Эти профили искали раньше и не нашли юрлица; кампания нашла ИНН —',
                  '# прежние записи заменены новыми ниже.',
                  'REGISTRY = [row for row in REGISTRY if row["company_id"] not in %r]' % (set(replaced),)]
    lines.append('REGISTRY += [')
    for r in rows:
        inn = ', "inn": %r' % r['inn'] if r.get('inn') else ''
        lines.append('    {"company_id": %r, "decision": %r%s,' % (r['company_id'], r['decision'], inn))
        lines.append('     "reason": %r,' % r['reason'])
        lines.append('     "date": %r},' % r['date'])
    lines.append(']')
    open(REG, 'w', encoding='utf-8').write(src.replace(marker, '\n'.join(lines) + marker, 1))


def main(write):
    answers = load_answers(partial=not write)
    data = json.load(open(DATA, encoding='utf-8'))
    new_profiles, registry_rows, links, notes = plan(data, answers)
    data['companies'].update(new_profiles)
    done, skipped = apply_links(data, links)
    print('ответов %d; новых профилей %d; строк реестра %d (ИНН %d); привязок %d, пропущено %d'
          % (len(answers), len(new_profiles), len(registry_rows),
             sum(1 for r in registry_rows if r.get('inn')), len(done), len(skipped)))
    for k, v in notes.items():
        print('  %s: %d — %s' % (k, len(v), v[:6]))
    why = defaultdict(int)
    for s in skipped:
        why[s[2]] += 1
    print('  пропуски:', dict(why))
    if not write:
        return
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    assert not set(new_profiles) & set(fresh['companies'])
    fresh['companies'].update(new_profiles)
    done2, _ = apply_links(fresh, links)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, indent=1, ensure_ascii=False)
        f.write('\n')
    write_registry(registry_rows)
    print('записано: профилей %d, привязок %d' % (len(new_profiles), len(done2)))


if __name__ == '__main__':
    main('--write' in sys.argv)
