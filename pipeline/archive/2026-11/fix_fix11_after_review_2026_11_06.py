# -*- coding: utf-8 -*-
"""ТЦ «Июнь» (gde4f9941): дата карточки — день закрытия, а не день выставления на торги.

ЧТО СЛОМАНО. `date` стояло «2023-02-14» — день, когда РАД выставил центр на
аукцион (РИА Недвижимость, 14 февраля 2023). Статус карточки — «Закрыта», а
закрыта сделка 2 сентября 2026 года: «ООО «Литекс» стало владельцем
торгово-развлекательного центра «Июнь» … Сделка, по данным сервиса Asseto,
была закрыта 2 сентября» (Ведомости, 1 октября 2026; текст сохранен
save_source.py в data/inbox/triage/sources_2026-11-06.json). Год сентября —
2026: статья от 1 октября 2026 года, а в соседней фразе Коммерсанта «к августу
2026 года после нескольких неудачных торгов цену снизили до 1 млрд руб.».

Событие «Сделка завершена» несло 2026-10-01 — день статьи, а не закрытия;
ставится тот же день, 2 сентября 2026 (docs/card_status_dates.md, «Дата —
день события, о котором статус»).

ПОЧЕМУ НЕ ЧЕРЕЗ review.py: `date_is_supported` не переносит дату в другой год
(docs/card_status_dates.md, «review.py год не переносит — и не должен»).

ВТОРОЕ ДЕЛО — отпечатки поглощенных правок заголовка. У g718e3d0e и g7cb5d8f8
партия fix11 (pipeline/ingest/fixes/written_fix11_2026_11_06.py) — вторая
запись поля title; прежняя (written_titles_std_a / pilot_reread) применена, и
ее отпечаток должен лечь в `proofread_absorbed.title`, иначе
test_no_duplicate_fix_for_one_field видит две правки на одно поле (тот же путь,
что pipeline/archive/2026-11/fix_absorbed_titles_base_2026_11_06.py). Делается
только когда review.py --write уже поставил новый заголовок.

Запуск:
    python3 pipeline/fix_fix11_after_review_2026_11_06.py            # сухой прогон
    python3 pipeline/fix_fix11_after_review_2026_11_06.py --write    # записать
Порядок: MASS_OK=titles python3 pipeline/ingest/review.py --write, затем этот
скрипт с --write. После записи — python3 pipeline/facts_derive.py --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gde4f9941'
OLD_DATE, NEW_DATE = '2023-02-14', '2026-09-02'
EVENT_ID, OLD_EVENT_DATE = 'gde4f9941-closed', '2026-10-01'
QUOTE = 'Сделка, по данным сервиса Asseto, была закрыта 2 сентября.'
ABSORB_TITLES = ('g718e3d0e', 'g7cb5d8f8')
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))


def apply(data):
    deal = {d['id']: d for d in data['deals']}.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    changed = []
    if deal.get('date') != NEW_DATE:
        assert deal.get('date') == OLD_DATE, 'дата уже другая: %r' % deal.get('date')
        deal['date'] = NEW_DATE
        changed.append('%s: date %s -> %s' % (DEAL_ID, OLD_DATE, NEW_DATE))
    for e in deal.get('events') or []:
        if isinstance(e, dict) and e.get('id') == EVENT_ID and e.get('date') != NEW_DATE:
            assert e.get('date') == OLD_EVENT_DATE, 'дата события уже другая: %r' % e.get('date')
            e['date'] = NEW_DATE
            changed.append(DEAL_ID + ': events[%s].date %s -> %s' % (EVENT_ID, OLD_EVENT_DATE, NEW_DATE))
    import review
    cards = {d['id']: d for d in data['deals']}
    for cid in ABSORB_TITLES:
        recs = [f for f in review.FIXES if f['id'] == cid and f['field'] == 'title']
        if len(recs) < 2 or cards[cid].get('title') != recs[-1]['new']:
            print('%s: новый заголовок еще не записан — сначала review.py --write' % cid)
            continue
        marks = cards[cid].setdefault('proofread_absorbed', {}).setdefault('title', [])
        for f in recs[:-1]:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                changed.append('%s: proofread_absorbed.title += %s' % (cid, fp))
    return changed


def main(write):
    changed = apply(json.load(open(DATA, encoding='utf-8')))
    for c in changed:
        print(c)
    print('  цитата: %r' % QUOTE)
    if not changed:
        print('Уже записано.')
        return 0
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    if apply(data):
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
