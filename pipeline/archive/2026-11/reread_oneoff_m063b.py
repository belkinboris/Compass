# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m063b: правки, которые review.py не умеет.

Доказательства и поиск — в докстроке pipeline/ingest/fixes/reread_2026_11_12_m063b.py, тексты статей —
data/inbox/triage/sources_2026-11-12_m063.json. Здесь: суммы «Не раскрыта» и «(по оценке)» (review.py их не
принимает), даты годом, доли в «Предмет / доля» с числами из нескольких цитат, описания и имена профилей,
снятые значения (retracted), заметки приемки и отпечатки прежних записей таблицы правок на переписанных полях
(иначе test_no_duplicate_fix_for_one_field и test_review_table_is_applied_and_not_pending).

Каждая правка проверяет старое значение (assert); повторный запуск — «уже применено».
Запуск — внутри pipeline/reread_apply.py (после review.py --write):
    python3 pipeline/archive/2026-11/reread_oneoff_m063b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m063b.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

BY = 'вычитка 12 ноября 2026, партия m063b'

SET = [('gf2080ce8',
  'date',
  '2022-10-01',
  '2022',
  'Компания "Технониколь" закрыла осенью 2022 года ряд сделок по покупке предприятий в области лесо- и '
  'деревопереработки на общую сумму более 1,6 миллиарда рублей, рассказал журналистам управляющий партнер компании '
  'Сергей Колесников. Он уточнил, что около 1 миллиарда рублей было потрачено на покупку красноярских предприятий '
  '"ЛесСервис" и ДК "Премьер – Лес", 120 миллионов рублей - на покупку свердловского "ДОК ТН-Нижний Тагил", а 500 '
  'миллионов рублей - на приобретение нижегородского производителя домокомплектов "Малоэтажные комфортные дома".',
  'https://realty.ria.ru/20230117/tekhnonikol-1845482123.html'),
 ('g62698716',
  'sum',
  'Несколько млрд ₽ (точно не указана)',
  '52 млрд ₽',
  'Первой сделкой «Инсайта» стала покупка в 2022 году за 52 млрд рублей у международной корпорации Siemens крупной '
  'российской лизинговой компании (ЛК) «Сименс Финанс» (позже была переименована в «Дельтализинг»).',
  'https://frankmedia.ru/189091'),
 ('g62698716',
  'eco.sum',
  'Несколько млрд ₽ (точно не указана)',
  '52 млрд ₽',
  'Первой сделкой «Инсайта» стала покупка в 2022 году за 52 млрд рублей у международной корпорации Siemens крупной '
  'российской лизинговой компании (ЛК) «Сименс Финанс» (позже была переименована в «Дельтализинг»).',
  'https://frankmedia.ru/189091')]

RETRACT = [('g62698716', 'sum', 'Несколько млрд ₽ (точно не указана)')]

COMP = [('gc240c35d',
  'desc',
  'Четыре лесопромышленных и деревообрабатывающих предприятия в Красноярске, Свердловской и Нижегородской областях; '
  'в 2022 году их купила «Технониколь», вложив ~600 млн ₽ в модернизацию.',
  'Четыре лесопромышленных и деревообрабатывающих предприятия в Красноярске, Свердловской и Нижегородской областях; '
  'в 2022 году их купила «Технониколь».')]

NOTES = {'gf2080ce8': {'no_profile.seller': 'Продавцов «ЛесСервиса», «Премьер-Леса» и «ДОК ТН-Нижний Тагил» не называют РИА '
                                    'Недвижимость и «Коммерсантъ»; поиск по названиям (WebSearch) реквизитов и '
                                    'участников не дал, datanewton недоступен. У «Малоэтажных комфортных домов» '
                                    'СПАРК называет бенефициаром Андрея Пчелкина, но продавцом его источники не '
                                    'называют.'}}

TOUCHED = {'gf2080ce8': ['title', 'eco.share', 'eco.rationale', 'eco.target_fin', 'eco.context', 'extra', 'date'],
 'g62698716': ['title',
               'date_basis',
               'law.struct',
               'eco.finadv',
               'eco.val',
               'eco.context',
               'extra',
               'sum',
               'eco.sum'],
 'gff6e08fe': ['title', 'date_basis', 'eco.val', 'eco.share', 'eco.rationale', 'law.terms', 'eco.context', 'extra']}



def get(card, field):
    obj = card
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def put(card, field, value):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def main(argv):
    write = '--write' in argv
    import fact_edit_guard
    import mass_edit_guard
    import review
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    old = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, was, new, quote, url in SET:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s.%s' % (cid, field))
            continue
        assert cur == was, '%s.%s: в базе %r, ожидали %r' % (cid, field, cur, was)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('%s.%s: %r → %r' % (cid, field, was, new))
        done += 1
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for cid, notes in NOTES.items():
        acc = by[cid].setdefault('accepted_notes', {})
        for key, text in notes.items():
            if '.' in key:
                a, b = key.split('.')
                if acc.setdefault(a, {}).get(b) != text:
                    acc[a][b] = text
                    done += 1
            elif acc.get(key) != text:
                acc[key] = text
                done += 1
    for comp, field, was, new in COMP:
        cur = data['companies'][comp].get(field)
        if field == 'legal_short' and cur:      # party_legal_names.py уже поставил форму из реестра
            continue
        if cur != new:
            assert cur == was, '%s.%s: %r' % (comp, field, cur)
            data['companies'][comp][field] = new
            print('%s.%s → %r' % (comp, field, new))
            done += 1
    # Отпечатки прежних записей таблицы на переписанных полях.
    for cid, fields in TOUCHED.items():
        card = by[cid]
        absorbed = card.setdefault('proofread_absorbed', {})
        for field in fields:
            recs = [f for f in review.FIXES if (f['id'], f['field']) == (cid, field)
                    and BY.split()[-1] not in str(f.get('why', ''))]
            for f in recs:
                if f['new'] == get(card, field):
                    continue
                fp = review.fix_fingerprint(f['new'])
                marks = absorbed.setdefault(field, [])
                if fp not in marks:
                    marks.append(fp)
                    done += 1
        if not absorbed:
            card.pop('proofread_absorbed', None)
    print('изменений: %d' % done)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        return 0
    mass_edit_guard.check(old, data, key='reread')
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
