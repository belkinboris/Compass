# -*- coding: utf-8 -*-
"""Вычитка 20 ноября 2026, партия r1120b: то, чего не умеет review.py (перестановка источника, основание даты).

geb221705 (X5 / MAY24): Oborot.ru пересказывает «Ведомости» («Как сообщают „Ведомости“»: 100% долей,
  продавцы Лисиненко) — статья «Ведомостей» 1 октября 2024 года открыта и ставится первой в src.
gmru-kolomenskoe-peko («Пеко»): дата 23 июля 2026 года — день записи в ЕГРЮЛ (Галина Фрольцова вышла,
  ООО «Хлебинвест» вошло со 100%); основание даты — реестр (date_basis: registry).
gf70a43e6 (Dr. Reddy’s / «Вертекс»): заметка этапа «Сделка завершена» (events[0].note) повторяла фразу
  «Коммерсанта» (verbatim, near_copy) — пересказ теми же фактами; review.py элемент списка не правит.

    python3 pipeline/archive/2026-11/reread_r1120b_oneoff.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_r1120b_oneoff', '2026-11-20'

VED = ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/01/1065880-x5-vikupila-may24']
VED_QUOTE = ('По словам источника, компании перешли 100% долей в ООО «Май24» – юрлице, владеющем торговой площадкой. '
             'Они были приобретены у основателей и владельцев одного из крупнейших в России производителей чая – '
             'компании «Май» (бренды Richard, Curtis, «Майский» и др.) Игоря и Ирины Лисиненко.')

PEKO_QUOTE = ('ЕГРЮЛ, ООО «Хлебокомбинат Пеко» (ИНН 7725702610): 2026-07-23 left Фрольцова Галина Викторовна '
              '(25.0 → None); 2026-07-23 joined ООО «Хлебинвест» (None → 100.0)')

DRR_OLD = ('Российская «дочка» индийской фармкомпании Dr. Reddy’s получила от «Вертекса» права на три '
           'гинекологических препарата.')
DRR_NEW = ('Стороны объявили, что права на три гинекологических препарата «Вертекса» перешли к российскому '
           'подразделению Dr. Reddy’s.')
DRR_QUOTE = ('Российская «дочка» индийской фармкомпании Dr. Reddy’s получила от «Вертекса» права на три гинекологических '
             'препарата. Об этом “Ъ” сообщили стороны сделки.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0

    c = by['geb221705']
    src = c.get('src') or []
    if not (src and src[0][1] == VED[1]):
        assert not any(len(s) > 1 and s[1] == VED[1] for s in src), src
        assert src[0][1].startswith('https://www.comnews.ru/'), src[0]
        src.insert(0, list(VED))
        c['src'] = src
        fact_edit_guard.log(c, 'src', VED, VED_QUOTE, VED[1], BY, DAY)
        n += 1

    c = by['gmru-kolomenskoe-peko']
    if c.get('date_basis') != 'registry':
        assert c['date'] == '2026-07-23' and not c.get('date_basis'), (c['date'], c.get('date_basis'))
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', c['date'], PEKO_QUOTE, '', BY, DAY)
        n += 1
    c = by['gf70a43e6']
    ev = c['events'][0]
    if ev.get('note') != DRR_NEW:
        assert ev.get('note') == DRR_OLD and ev.get('kind') == 'closed', ev
        ev['note'] = DRR_NEW
        fact_edit_guard.log(c, 'events.0.note', DRR_NEW, DRR_QUOTE, 'https://www.kommersant.ru/doc/8861146', BY, DAY)
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
