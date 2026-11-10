# -*- coding: utf-8 -*-
"""Вычитка 10 ноября 2026 (партии fv, fw, fx, fy): правки, которые review.py не умеет.

ЧТО ЧИНИТ. Пять помощников вычитали 45 карточек консультантов-партнеров Форума M&A
(экспертные партнеры и ALUMNI Partners; pipeline/ingest/fixes/reread_2026_11_10_f{v..z}.py,
тексты — data/inbox/triage/sources_2026-11-10_f*.json). В файлах fv, fw, fx, fy, кроме
FIXES, лежит список ONE_OFF: консультанты (`law.adv` — список), продавец по реестру с
`party_evidence`, дата годом или по реестру (`date_basis`), этап `events[0]`, заметки
приемки (`accepted_notes.*`), снятые значения (`retracted.*`), «sum и eco.sum» с
`sum_basis`, описание и имя профиля, строки реестра ФНС, порядок `src`. Партия fz
применяет свою разовую часть сама (`reread_2026_11_10_fz.py --write`).

Поле `what` в ONE_OFF — свободный текст; здесь каждая запись разобрана в операцию по
тегу `fX[i]` (партия и номер). Значения `old`/`new` берутся из самих файлов партий — не
переписаны сюда, чтобы не разойтись с ними. Каждая операция проверяет старое значение.

Разбор, где пришлось выбирать:
  * fw[1], fw[3], fw[9], fw[24] — не правки, а команда `party_legal_names.py <id> --write`
    (выполняется отдельным шагом); fw[5] — заметка о сбое разбора истории участников в
    party_legal_names.py, правки нет.
  * fw[13] (gf3c5069f law.adv[0]) — `old` в записи пустой, хотя строка есть; старое
    значение взято из базы на 10 ноября (Forward Legal, ссылка на Ъ 8077927).
  * fw[23] — один текст сразу на `no_profile.seller` (в нем же перечислено, где искали).
  * fv[13] — строка реестра gcd7550bf: чужое ООО «СИТИМОБИЛ» (Кемерово) → `no_match`.
  * fy[12] — строка реестра g5df2bdb6: ООО УК «СДЭК» → ООО «СДЭК-Глобал» (7722327689).
  * fx[15] — новая строка реестра gd2ebf7b6 (ООО «АСТОР ТЕХ», 7730582675).
  * fx[47], fy[19] — `src`: первоисточник первым (перестановка, состав не меняется).

Два прохода: без ключа --post — все, кроме перестановки src (до review.py --write);
с --post — перестановка src (после review.py --write); --absorb — отпечатки старых записей
таблицы на полях, которые переписал первый проход (до review.py --write); --lot — снять признак
лота с gd2ebf7b6 (после первого прохода).

ЗАПУСК (после разовой части fz и ДО `MASS_OK=reread python3 pipeline/ingest/review.py --write`;
поля ONE_OFF с полями таблиц не пересекаются):
    python3 pipeline/archive/2026-11/apply_reread_oneoff_2026_11_10.py            # сухой прогон
    MASS_OK=reread python3 pipeline/archive/2026-11/apply_reread_oneoff_2026_11_10.py --write

База перечитывается прямо перед записью; запись — через `mass_edit_guard.check`.
Повторный запуск после записи отказывает на первом assert — скрипт разовый.
"""
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG_JSON = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
REG_PY = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
FIXDIR = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes')


def _load(part):
    p = os.path.join(FIXDIR, 'reread_2026_11_10_f%s.py' % part)
    spec = importlib.util.spec_from_file_location('reread_f' + part, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.ONE_OFF


ONE_OFF = {p: _load(p) for p in 'vwxy'}

# Тег → поле карточки (простое присваивание с проверкой old).
SET = {
    'fv[0]': 'law.adv.0', 'fv[1]': 'law.adv', 'fv[2]': 'law.adv', 'fv[3]': 'law.adv.0', 'fv[4]': 'law.adv',
    'fv[5]': 'law.adv', 'fv[6]': 'law.adv', 'fv[7]': 'date', 'fv[8]': 'date', 'fv[9]': 'date', 'fv[10]': 'date',
    'fw[0]': 'date', 'fw[7]': 'asset_share', 'fw[8]': 'law.adv.0.0', 'fw[10]': 'buyer', 'fw[12]': 'date', 'fw[13]': 'law.adv.0',
    'fw[15]': 'date_basis', 'fw[17]': 'target', 'fw[19]': 'law.adv.0', 'fw[21]': 'date',
    'fw[22]': 'law.adv.0.0', 'fw[27]': 'law.adv',
    'fx[0]': 'sum', 'fx[1]': 'eco.sum', 'fx[2]': 'sum_basis', 'fx[4]': 'law.adv', 'fx[5]': 'eco.finadv',
    'fx[9]': 'seller', 'fx[10]': 'seller_id', 'fx[13]': 'law.adv', 'fx[16]': 'seller', 'fx[17]': 'seller_id',
    'fx[20]': 'law.adv', 'fx[23]': 'law.adv', 'fx[24]': 'eco.finadv', 'fx[26]': 'sum', 'fx[27]': 'eco.sum',
    'fx[28]': 'sum_basis', 'fx[29]': 'law.adv', 'fx[30]': 'law.adv', 'fx[31]': 'law.adv', 'fx[35]': 'date',
    'fx[36]': 'date_basis', 'fx[38]': 'buyer', 'fx[39]': 'buyer_name', 'fx[40]': 'seller', 'fx[41]': 'seller_id',
    'fx[43]': 'date', 'fx[44]': 'date_basis', 'fx[45]': 'sum', 'fx[46]': 'eco.sum',
    'fy[0]': 'law.adv', 'fy[1]': 'law.adv', 'fy[2]': 'law.adv', 'fy[3]': 'law.adv', 'fy[4]': 'law.adv',
    'fy[5]': 'date', 'fy[6]': 'date', 'fy[7]': 'law.struct', 'fy[9]': 'seller_id', 'fy[15]': 'eco.context',
    'fy[16]': 'eco.val',
}
RETRACT = {   # тег → (поле, значения)
    'fw[14]': ('seller', ['Росимущества']),
    'fw[30]': None,   # два поля — ниже
    'fx[3]': ('sum', None), 'fx[11]': ('seller', None), 'fx[18]': ('seller', None),
    'fy[10]': ('sum', None), 'fy[11]': ('sum', None),
}
EVIDENCE = {'fx[12]': 'seller', 'fx[19]': 'seller', 'fx[37]': 'seller', 'fx[42]': 'seller'}
NOTE = {'fw[18]': 'no_profile.buyer', 'fw[23]': 'no_profile.seller', 'fy[14]': 'no_profile.seller',
        'fy[17]': 'searched', 'fy[18]': 'searched'}
SKIP = {'fw[1]': 'команда party_legal_names.py', 'fw[3]': 'команда party_legal_names.py',
        'fw[9]': 'команда party_legal_names.py', 'fw[24]': 'команда party_legal_names.py',
        'fw[5]': 'заметка, не правка', 'fw[20]': 'пометка: правка в FIXES партии fw'}
FW13_OLD = ['Юридический консультант покупателя', 'Forward Legal',
            'Коммерсантъ («Сделки года») в описании сделки Росимущества по продаже 40 компаний '
            '(актуализировано под нашу карточку — покупатель Александр Клячин/KR Properties) называет Forward '
            'Legal консультантом покупателя. Источник: https://www.kommersant.ru/doc/8077927']
# Поля, которые разовая часть партии fz обнулила («—») поверх старых записей таблицы из
# архива (fixes_archive/2026-10.json): review.py видит такие записи непримененными и
# отказывает. Отпечатки ВСЕХ записей поля — в proofread_absorbed (поле переписано поверх).
ABSORB_ALL = [('g24b33459', 'law.terms'), ('g74fd5cdb', 'eco.rationale')]
# Заголовки, которые вычитка переписала поверх записей written_titles_* (файлы партий идут по
# имени раньше written_*, поэтому прежняя запись оказывается последней в цепочке): ее отпечаток —
# в proofread_absorbed, иначе следующий review.py откажет «поле уже другое».
ABSORB_TITLES = [('g74fd5cdb', 'title'), ('ge3bc7c98', 'title'), ('gdb4b1cbf', 'title'),
                 ('gf3c5069f', 'title'), ('cd9abfbfd', 'title')]
# fw[16], fw[29]: `old` в записи — пересказ («нынешнее описание с …»), а не текст; дословно — из базы на 10 ноября.
OLD_OVERRIDE = {'fw[16]': 'Платформа лид-менеджмента с маркетинговой аналитикой и автоматизацией работы с лидами; '
                          'в 2023 году 51% ее купил «Вымпелком».',
                'fw[29]': 'Производитель пластиковой упаковки (в т.ч. для молочной продукции), юрлицо ООО «Полекс '
                          'Урал» (после сделки переименовано в ООО «Пегас»); выручка 2025 года — 2,44 млрд ₽.'}
# Записи, где `old` описан словами, а не текстом: дословные старые значения (база на 10 ноября,
# сверены глазами с описанием в записи).
DESCRIBED = {
    'fw[27]': [['Юридический консультант покупателя', 'Лемчик, Крупский и Партнеры (ЛКП)',
                'Комплексное сопровождение покупателя — due diligence, структурирование, подготовка документации, '
                'переговоры и закрытие сделки. Источник: lkpconsult.ru'],
               ['Консультант продавца', 'ALUMNI Partners',
                '«ALUMNI Partners консультировала продавца в связи с продажей группы компаний «Полекс Урал»». '
                'Источник: t.me/alumnimna/287']],
}
COMPANY_RE = re.compile(r"compan(?:y|ies)\W*(g[0-9a-f]+)\W*\.(desc|name)")


def _get(obj, field):
    for p in field.split('.'):
        if isinstance(obj, list):
            obj = obj[int(p)] if p.isdigit() and int(p) < len(obj) else None
        else:
            obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj.setdefault(p, {})
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value


def _retract(card, field, values):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    for v in values:
        if v not in lst:
            lst.append(v)


def _note(card, path, value, tag):
    notes = card.setdefault('accepted_notes', {})
    assert _get(notes, path) is None, (tag, card['id'], path, _get(notes, path))
    _set(notes, path, value)


# Перестановка src — ПОСЛЕ review.py --write: первоисточник добавляет запись таблицы.
POST = {'fx[47]', 'fy[19]'}
PHASE = {'post': '--post' in sys.argv}


def _apply(data, log):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    reg_edit, reg_add = [], []
    import review
    for cid, field in ([] if PHASE['post'] else ABSORB_ALL):
        card = deals[cid]
        assert _get(card, field) == '—', (cid, field, _get(card, field))
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in review.FIXES:
            if (f['id'], f['field']) == (cid, field):
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
        log.append('absorb  %s proofread_absorbed.%s' % (cid, field))
    for part, items in ONE_OFF.items():
        for i, o in enumerate(items):
            tag = 'f%s[%d]' % (part, i)
            card = deals[o['id']]
            what = o['what']
            if (tag in POST) != PHASE['post']:
                continue
            if tag in SKIP:
                log.append('%-7s пропуск: %s' % (tag, SKIP[tag]))
                continue
            if tag in SET:
                f = SET[tag]
                old = FW13_OLD if tag == 'fw[13]' else o['old']
                cur = _get(card, f)
                if isinstance(old, str) and old.startswith('(') and old.endswith(')') and cur != old:
                    # `old` описан словами («(2 строки: …)») — сверено глазами 10 ноября, см. DESCRIBED.
                    assert DESCRIBED.get(tag) == cur, (tag, o['id'], f, 'описанное old', cur)
                else:
                    assert cur == old, (tag, o['id'], f, cur)
                _set(card, f, o['new'])
                if tag == 'fw[0]':
                    assert card.get('date_basis') in (None, 'registry'), (tag, card.get('date_basis'))
                    card['date_basis'] = 'registry'
                log.append('%-7s %s %s' % (tag, o['id'], f))
            elif tag == 'fy[8]':
                assert card['sum'] == o['old'] and card['eco']['sum'] == o['old'], (tag, card['sum'])
                card['sum'] = card['eco']['sum'] = o['new']
                log.append('%-7s %s sum, eco.sum' % (tag, o['id']))
            elif tag == 'fw[25]':
                ev = card['events'][0]
                assert card['date'] == o['old'] and ev.get('date') == o['old'], (tag, card['date'], ev.get('date'))
                card['date'] = ev['date'] = o['new']
                log.append('%-7s %s date, events[0].date' % (tag, o['id']))
            elif tag == 'fw[26]':
                ev = card['events'][0]
                assert ev.get('note') == o['old'], (tag, ev.get('note'))
                ev['note'] = o['new']
                log.append('%-7s %s events[0].note' % (tag, o['id']))
            elif tag == 'fw[6]':
                assert not card.get('seller') and card.get('target_was_seller') is True, (tag, card.get('seller'))
                card['seller'] = o['new']
                card.pop('target_was_seller')
                card.setdefault('party_evidence', {})['seller'] = [{
                    'value': o['new'], 'field': 'seller', 'method': 'registry_owner_history',
                    'url': 'https://datanewton.ru/api/v2/history?ogrn=1217700216700&startDate=2000-01-01&attributes=OWNERS'}]
                _note(card, 'no_profile.seller',
                      'физлица, профилей нет; по истории участников ЕГРЮЛ (datanewton), запись 01.12.2025', tag)
                log.append('%-7s %s seller, party_evidence.seller, no_profile.seller, −target_was_seller' % (tag, o['id']))
            elif tag == 'fw[11]':
                assert card.get('target') == o['old'] and not card.get('asset'), (tag, card.get('target'))
                card['target'] = None
                card['asset'] = o['new']
                log.append('%-7s %s target → None, asset' % (tag, o['id']))
            elif tag in RETRACT:
                if tag == 'fw[30]':
                    _retract(card, 'seller', ['Сергей Черников'])
                    _retract(card, 'asset', ['Полекс'])
                    log.append('%-7s %s retracted.seller, retracted.asset' % (tag, o['id']))
                else:
                    f, vals = RETRACT[tag]
                    _retract(card, f, vals or o['new'])
                    log.append('%-7s %s retracted.%s' % (tag, o['id'], f))
            elif tag in EVIDENCE:
                card.setdefault('party_evidence', {})[EVIDENCE[tag]] = o['new']
                log.append('%-7s %s party_evidence.%s' % (tag, o['id'], EVIDENCE[tag]))
            elif tag in NOTE:
                _note(card, NOTE[tag], o['new'], tag)
                log.append('%-7s %s accepted_notes.%s' % (tag, o['id'], NOTE[tag]))
            elif tag == 'fw[28]':
                url = what.split()[-1]
                hit = [s for s in card['src'] if len(s) > 1 and s[1] == url]
                assert len(hit) == 1, (tag, url)
                card['src'].remove(hit[0])
                assert any(len(s) > 1 and str(s[1]).startswith('http') for s in card['src'])
                log.append('%-7s %s src − %s' % (tag, o['id'], url))
            elif tag == 'fx[47]':
                hit = [s for s in card['src'] if s == o['new']]
                assert len(hit) == 1, (tag, card['src'][:2])
                card['src'].remove(hit[0])
                card['src'].insert(0, hit[0])
                log.append('%-7s %s src: первым %s' % (tag, o['id'], o['new'][1]))
            elif tag == 'fy[19]':
                hit = [s for s in card['src'] if len(s) > 1 and 'interfax.ru' in s[1] and '987128' in s[1]]
                assert len(hit) == 1, (tag, card['src'])
                card['src'].remove(hit[0])
                card['src'].insert(0, hit[0])
                log.append('%-7s %s src: первым %s' % (tag, o['id'], hit[0][1]))
            elif COMPANY_RE.search(what):
                pid, f = COMPANY_RE.search(what).groups()
                if o['old'] is None and tag.startswith('fx'):
                    # Партия fx не записала прежнее описание; правится то, что в базе на 10 ноября
                    # (в нем стоят снятые этой вычиткой «21–23 млрд ₽», «структура «Роснано»» и т. п.).
                    assert comps[pid].get(f), (tag, pid, f)
                else:
                    assert comps[pid].get(f) == OLD_OVERRIDE.get(tag, o['old']), (tag, pid, f, comps[pid].get(f))
                comps[pid][f] = o['new']
                log.append('%-7s профиль %s %s' % (tag, pid, f))
            elif tag == 'fv[13]':
                reg_edit.append((tag, 'gcd7550bf', o['old'], {
                    'decision': 'no_match', 'inn': None,
                    'reason': 'До 10 ноября 2026 стояло ООО «СИТИМОБИЛ» 4205430080 (Кемерово, единственный участник '
                              '— частное лицо с 21.08.2025) — совпадение только имени, к RWB и People&People отношения '
                              'не имеет. Сервисом, по данным SelSup со ссылкой на РБК, управляет петербургская '
                              '«Транс-Миссия»; второго независимого источника нет — ИНН не ставится (вычитка 10 '
                              'ноября 2026, партия fv, карточка g76983314).',
                    'date': '2026-11-10'}))
            elif tag == 'fy[12]':
                reg_edit.append((tag, 'g5df2bdb6', o['old'], {
                    'decision': 'confirmed', 'inn': o['new'],
                    'reason': 'ООО «СДЭК-Глобал», ИНН 7722327689, ОГРН 1157746448463 — «основное юрлицо компании» '
                              '(Ведомости, vc.ru, Интерфакс); ИНН совпал в двух источниках: декларация МЧС '
                              'digital.mchs.gov.ru/fgpn/declaration/78-08-2026-008245 и datanewton. До 10 ноября 2026 '
                              'стояло ООО УК «СДЭК» 8602169471 — управляющая компания, не предмет сделки (вычитка 10 '
                              'ноября 2026, партия fy, карточка gf577d893).',
                    'date': '2026-11-10'}))
            elif tag == 'fx[15]':
                row = dict(o['new'])
                row['company_id'] = 'gd2ebf7b6'
                reg_add.append((tag, row))
            else:
                raise AssertionError('не разобрано: %s %s' % (tag, what))
    return reg_edit, reg_add


def _registry(reg_edit, reg_add, write, log):
    import fns_registry
    rows = json.load(open(REG_JSON, encoding='utf-8'))
    keys = ('company_id', 'decision', 'inn', 'reason', 'date')
    for tag, cid, old_inn, row in reg_edit:
        hits = [i for i, r in enumerate(rows) if r.get('company_id') == cid]
        assert len(hits) == 1, (tag, cid, hits)
        r = rows[hits[0]]
        assert r.get('inn') == old_inn, (tag, r)
        assert row['inn'] is None or fns_registry.inn_is_valid(row['inn']), (tag, row['inn'])
        rows[hits[0]] = dict({'company_id': cid}, **row)
        log.append('%-7s реестр %s: %s %s → %s %s' % (tag, cid, r['decision'], r.get('inn'),
                                                     row['decision'], row['inn']))
    known = {r['company_id'] for r in fns_registry.REGISTRY}
    inns = {r.get('inn') for r in fns_registry.REGISTRY if r.get('inn')}
    for tag, row in reg_add:
        assert row['company_id'] not in known, (tag, 'строка уже есть')
        assert row['inn'] not in inns, (tag, 'ИНН уже у другого профиля')
        assert fns_registry.inn_is_valid(row['inn']), (tag, row['inn'])
        log.append('%-7s реестр %s: новая строка %s %s' % (tag, row['company_id'], row['decision'], row['inn']))
    if not write:
        return
    with open(REG_JSON, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    src = open(REG_PY, encoding='utf-8').read()
    anchor = '\ndef by_company_id('
    assert src.count(anchor) == 1
    block = ('# Вычитка 10 ноября 2026 (партия fx) — pipeline/archive/2026-11/apply_reread_oneoff_2026_11_10.py.\n'
             'REGISTRY += [\n')
    for _tag, r in reg_add:
        block += ('    {"company_id": %r, "decision": %r, "inn": %r,\n     "reason": %r,\n     "date": %r},\n'
                  % (r['company_id'], r['decision'], r['inn'], r['reason'], r['date']))
    block += ']\n\n'
    i = src.index(anchor) + 1
    open(REG_PY, 'w', encoding='utf-8').write(src[:i] + block + src[i:])


def absorb(write):
    """Поля, переписанные разовой частью поверх старых записей таблицы (в том числе из
    fixes_archive): review.py видит такие записи непримененными и отказывает. Отпечатки записей,
    чье значение не совпадает с нынешним, — в proofread_absorbed (поле переписано поверх)."""
    import review
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    targets = set(ABSORB_ALL) | set(ABSORB_TITLES)
    for part, items in ONE_OFF.items():
        for i, o in enumerate(items):
            tag = 'f%s[%d]' % (part, i)
            if tag in SET:
                targets.add((o['id'], SET[tag].split('.0')[0]))
            elif tag == 'fy[8]':
                targets |= {(o['id'], 'sum'), (o['id'], 'eco.sum')}
            elif tag == 'fw[25]':
                targets.add((o['id'], 'date'))
    n = 0
    for cid, field in sorted(targets):
        card = deals[cid]
        cur = _get(card, field)
        stale = [review.fix_fingerprint(f['new']) for f in review.FIXES
                 if (f['id'], f['field']) == (cid, field) and f['new'] != cur]
        have = (card.get('proofread_absorbed') or {}).get(field) or []
        stale = [fp for fp in dict.fromkeys(stale) if fp not in have]
        if stale:
            card.setdefault('proofread_absorbed', {}).setdefault(field, []).extend(stale)
            n += len(stale)
            print('absorb %s.%s %s' % (cid, field, ', '.join(stale)))
    print('отпечатков: %d' % n)
    if write and n:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('записано')


def fix_lot(write):
    """fx[14] переименовал профиль-лот gd2ebf7b6 («ООО «АСТОР ТЕХ» и ГК «АСТОР»») в одно общество
    «АСТОР ТЕХ», а fx[15] сопоставил его с одним ИНН: признак `lot` больше не верен."""
    data = json.load(open(DATA, encoding='utf-8'))
    prof = data['companies']['gd2ebf7b6']
    assert prof.get('name') == 'АСТОР ТЕХ' and prof.get('lot') is True, prof.get('name')
    prof.pop('lot')
    print('gd2ebf7b6: снят признак lot')
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('записано')


def main(write=False):
    from pipeline import mass_edit_guard
    log = []
    data = json.load(open(DATA, encoding='utf-8'))
    reg_edit, reg_add = _apply(data, log)
    _registry(reg_edit, reg_add, False, log)
    print('\n'.join(log))
    print('Записей ONE_OFF: %d; строк реестра: правка %d, новых %d.'
          % (sum(len(v) for v in ONE_OFF.values()), len(reg_edit), len(reg_add)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write (и MASS_OK=reread).')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))     # перечитать прямо перед записью
    _apply(fresh, [])
    mass_edit_guard.check(json.load(open(DATA, encoding='utf-8')), fresh, os.environ.get('MASS_OK'))
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    _registry(reg_edit, reg_add, True, [])
    print('Записано. Дальше: absorb_fix_chain.py, party_legal_names.py --write, facts_derive.py --write.')


if __name__ == '__main__':
    if '--lot' in sys.argv:
        fix_lot('--write' in sys.argv)
    elif '--absorb' in sys.argv:
        absorb('--write' in sys.argv)
    else:
        main('--write' in sys.argv)
