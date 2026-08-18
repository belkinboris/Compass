# -*- coding: utf-8 -*-
"""Разовый бэкфилл `weekly_researched` для карточек, чей `deep_researched`
случился уже ПОСЛЕ недельного окна с момента `added` — но сам бэкфилл при
этом почему-то не сработал.

НАЙДЕНО владельцем 18 августа 2026, вопросом «зачем недельный проход 1126
карточкам, если большинство из них обогащены полным обыском уже спустя
недели после появления в базе — то есть недельное окно к моменту обыска УЖЕ
прошло, и партия ничего нового искать не обязана». Измерение подтвердило:
1124 из 1126 карточек недельной очереди несут `deep_researched`, стамп
которого стоит на 7+ дней (медиана — 24 дня) ПОЗЖЕ `added`. Это ровно тот
случай, для которого `stamp_deep_researched()` (`pipeline/ingest/review.py`)
и был написан 16-18 августа: «ЗАОДНО ЗАКРЫВАЕТ СЛЕДУЮЩИЕ УРОВНИ, ЕСЛИ ОНИ УЖЕ
ОРГАНИЧЕСКИ ПОКРЫТЫ» — если разрыв между `added` и `deep_researched` уже
7+ дней, `weekly_researched` ставится ТЕМ ЖЕ днём, без отдельного прохода.

Но это поведение самой функции, а не разовая уборка: оно защищает только
карточки, помеченные `--mark-deep` ПОСЛЕ того, как эта защита появилась в
коде. Все 1124 карточки получили `deep_researched` РАНЬШЕ — тем же путём
(`--mark-deep` в review.py, других мест записи в это поле нет), но до того,
как в `stamp_deep_researched()` появилась проверка разрыва. Тот же класс
дефекта уже чинился разово 16 августа (`pipeline/backfill_followup_
researched.py`, «20 карточек партии 2 и 3 проскочили мимо прогона») — здесь
хвост оказался на два порядка больше, потому что это была основная масса
кампании G9, а не отдельная партия.

Правило: `deep_researched` стоит, `weekly_researched` — нет, и разрыв между
`added` и `deep_researched` уже 7+ дней -> `weekly_researched` = дата
`deep_researched` (не сегодняшняя: честно, что окно было пройдено ДАВНО, а
не сейчас). Если разрыв 30+ дней — тем же приёмом сразу закрывается и
`followup_researched`; на 18 августа таких среди хвоста нет (все разрывы —
7-29 дней), но правило пишется на будущее по этой же логике, а не отдельно.

Запуск:
    python3 pipeline/backfill_weekly_researched_from_deep_gap.py            # сухой прогон
    python3 pipeline/backfill_weekly_researched_from_deep_gap.py --write    # запись
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def _parse_date(s):
    try:
        parts = [int(x) for x in str(s).split('-')]
        y, m, d = (parts + [1, 1])[:3]
        return date(y, m, d)
    except (ValueError, TypeError, IndexError):
        return None


def candidates(deals):
    out = []
    for c in deals:
        if not c.get('deep_researched') or c.get('weekly_researched'):
            continue
        added, dr = _parse_date(c.get('added')), _parse_date(c.get('deep_researched'))
        if not added or not dr:
            continue
        gap = (dr - added).days
        if gap >= 7:
            out.append((c, gap))
    return out


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    cands = candidates(deals)

    print('Карточек к бэкфиллу weekly_researched (и, где применимо, '
          'followup_researched): %d' % len(cands))
    followup_too = sum(1 for _, gap in cands if gap >= 30)
    print('  из них разрыв 30+ дней (получат сразу и followup_researched): %d'
          % followup_too)
    for c, gap in cands[:8]:
        print('  %s: added=%s deep_researched=%s (разрыв %d дн.)'
              % (c['id'], c.get('added'), c['deep_researched'], gap))
    if len(cands) > 8:
        print('  ... и ещё %d' % (len(cands) - 8))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for c, gap in cands:
        stamp = c['deep_researched']
        c['weekly_researched'] = stamp
        if gap >= 30 and not c.get('followup_researched'):
            c['followup_researched'] = stamp

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО: %d карточек.' % len(cands))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
