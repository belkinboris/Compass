# -*- coding: utf-8 -*-
"""Вычитка базы, партия m070 (12 ноября 2026), часть C: то, что не ложится в таблицу FIXES.

domodedovo-aukcion — сумма в «Экономисте» записана до копейки («66 132 908 002,50 ₽»), а в «Обзоре» — «66,13 млрд ₽»:
  одна цена — одно значение (sum_fields_differ). Источник: Интерфакс о планах реорганизации (25 юрлиц).
inkab-ipo — то же для 2,04 млрд ₽.
mts-bik — 21,7 млрд ₽ назвала сама МТС («привлечь денежные средства в размере 21,7 млрд руб.»), это не оценка;
  дата — по ЕГРЮЛ: УК «Доверительная» вошла в участники ООО «БИК» с 49,9% 3 июля 2026 года (25 июня — объявление).
absolut-strah — «≈10 млрд ₽ (по оценке)» — оценка актива 2024 года, когда его выставили на продажу; цену этой сделки
  стороны не раскрыли — сумма снята (retracted.sum), оценка с годом — в eco.val. Дата 26 июня 2026 года — день
  перехода по ЕГРЮЛ (date_basis registry).

    python3 pipeline/archive/2026-11/reread_oneoff_m070c.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m070c.py --write
Повторный запуск ничего не ломает: примененное пропускается.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DB = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m070'

# (id, поле, старое, новое, цитата, адрес) — поля-факты с цитатой для fact_edit_guard
SETS = [
    ('domodedovo-aukcion', 'eco.sum', '66 132 908 002,50 ₽', '66,13 млрд ₽',
     'Дочерняя компания «Международного аэропорта Шереметьево» — ООО «Перспектива» — на торгах 29 января купила аэропорт '
     'Домодедово за 66 132 908 002,5 руб.', 'https://www.kommersant.ru/doc/8380948'),
    ('inkab-ipo', 'eco.sum', '2 038 650 200 ₽', '2,04 млрд ₽', 'Компании удалось привлечь на IPO 2,04 млрд руб.',
     'https://www.kommersant.ru/doc/8763613'),
    ('mts-bik', 'eco.sum', '21,7 млрд ₽ (по оценке)', '21,7 млрд ₽',
     '«Продажа позволит МТС не только значительно укрепить финансовую позицию за счет деконсолидации более чем 80 млрд руб. '
     'долга, но и привлечь денежные средства в размере 21,7 млрд руб.»', 'https://www.kommersant.ru/doc/8765262'),
    ('mts-bik', 'date', '2026-06-25', '2026-07-03',
     'ЕГРЮЛ, история участников ООО «БИК» (ИНН 5027312461): 2026-07-03 — АО УК «Доверительная» вошло в участники с долей '
     '49,9%, доля ПАО «МТС» уменьшилась со 100% до 50,1%', 'https://datanewton.ru/contragents/1227700875181/history/timeline'),
    ('mts-bik', 'date_basis', 'announcement', 'registry', None, None),
    ('absolut-strah', 'sum', '≈10 млрд ₽ (по оценке)', 'Не раскрыта',
     'Тогда среди потенциальных покупателей назывались структуры Совкомбанка, «Югория» и группа МТС, а сам актив оценивался '
     'в 10 млрд рублей.', 'https://bosfera.ru/press-release/investgruppa-absolyut-prodala-100-kompanii-absolyut-strahovanie'),
    ('absolut-strah', 'eco.sum', '≈10 млрд ₽ (по оценке)', 'Не раскрыта',
     'Тогда среди потенциальных покупателей назывались структуры Совкомбанка, «Югория» и группа МТС, а сам актив оценивался '
     'в 10 млрд рублей.', 'https://bosfera.ru/press-release/investgruppa-absolyut-prodala-100-kompanii-absolyut-strahovanie'),
    ('absolut-strah', 'date_basis', None, 'registry', None, None),
    ('absolut-strah', 'retracted.sum', None, ['≈10 млрд ₽ (по оценке)'], None, None),
]
SRC = [
    ('domodedovo-aukcion', ['Интерфакс', 'https://www.interfax.ru/russia/1072098'], False),
]
EVENTS = []
NOTES = {}
PROFILES = [  # имена с правовой формой: реестр сайта во время записи отвечал через раз (party_legal_names.py)
    ('ektos', 'legal_short', None, 'АО «ЭКТОС»'),
    ('inkab', 'legal_short', None, 'ПАО «Инкаб Холдинг»'),
    ('absolutstrah', 'legal_short', None, 'ООО «Абсолют Страхование»'),
    ('g8ca56c95', 'legal_short', None, 'ООО «ИГ «Абсолют»»'),
    ('tokk', 'legal_short', None, 'ООО «ЗУИ ТОКК»'),
    ('metarus', 'legal_short', None, 'ООО «Группа Метарус»'),
    ('bik', 'legal_short', None, 'ООО «БИК»'),
    ('canc', 'legal_short', None, 'ОАО «ЦАНЦ»'),
    ('g69c88bc7', 'legal_short', None, 'ПАО «МТС»'),
]


def get(card, f):
    v = card
    for p in f.split('.'):
        v = (v or {}).get(p)
    return v


def setf(card, f, val):
    parts = f.split('.')
    for p in parts[:-1]:
        card = card.setdefault(p, {})
    card[parts[-1]] = val


def apply(data):
    cards = {c['id']: c for c in data['deals']}
    done = []
    for cid, f, old, new, quote, url in SETS:
        c = cards[cid]
        if get(c, f) == new:
            continue
        assert get(c, f) == old, (cid, f, get(c, f))
        setf(c, f, new)
        if quote:
            fact_edit_guard.log(c, f, new, quote, url, BY)
        done.append('%s %s: %r -> %r' % (cid, f, old, new))
    for cid, src, first in SRC:
        c = cards[cid]
        if any(len(s) > 1 and s[1] == src[1] for s in c.get('src') or []):
            continue
        if first:
            c.setdefault('src', []).insert(0, list(src))
        else:
            c.setdefault('src', []).append(list(src))
        done.append('%s src + %s' % (cid, src[1]))
    for cid, i, f, old, new in EVENTS:
        ev = cards[cid]['events'][i]
        if ev.get(f) == new:
            continue
        assert ev.get(f) == old, (cid, i, f, ev.get(f))
        ev[f] = new
        done.append('%s events[%d].%s' % (cid, i, f))
    for cid, notes in NOTES.items():
        an = cards[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            for role, reason in v.items():
                if (an.get(k) or {}).get(role) != reason:
                    an.setdefault(k, {})[role] = reason
                    done.append('%s accepted_notes.%s.%s' % (cid, k, role))
    for pid, f, old, new in PROFILES:
        p = data['companies'][pid]
        if p.get(f) == new:
            continue
        if f == 'legal_short' and p.get(f):
            continue  # имя с правовой формой уже поставил party_legal_names.py
        assert p.get(f) == old, (pid, f, p.get(f))
        p[f] = new
        done.append('профиль %s %s -> %r' % (pid, f, new))
    return done


def main():
    data = json.load(open(DB, encoding='utf-8'))
    done = apply(data)
    print('\n'.join(done) or 'уже применено')
    if '--write' in sys.argv and done:
        data = json.load(open(DB, encoding='utf-8'))  # перечитать прямо перед записью
        apply(data)
        with open(DB, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('записано')


if __name__ == '__main__':
    main()
