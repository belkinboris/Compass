# -*- coding: utf-8 -*-
"""Разовый бэкфилл `followup_researched` — второго уровня дочитывания.

ЗАЧЕМ. Второй уровень (месяц после появления карточки, дельта поверх
`deep_researched` — см. `pipeline/ingest/REVISION_BRIEF.md`) начинает
работать только сегодня. Но у карточек, чей `deep_researched` УЖЕ стоит
позже, чем через 30 дней после `added`, месячное окно фактически уже
пройдено — тот самый глубокий поиск шёл после него и застал всё, что
второй уровень искал бы отдельно. Ставить их в очередь заново значило бы
дважды платить за один и тот же поиск.

Правило: `deep_researched − added ≥ 30 дней` → `followup_researched =
deep_researched` (тот же день, не сегодняшний — отметка честно говорит,
КОГДА фактически проверялось, а не когда был прогнан бэкфилл).

ЭТО НЕ ТО ЖЕ, ЧТО «РЕАЛЬНАЯ МЕСЯЧНАЯ ОЧЕРЕДЬ СЕГОДНЯ». Ожидание при
постановке задачи было «очередь ~0 сейчас, начнёт наполняться с сентября»
— замер 16 августа 2026 его не подтвердил: `added` — не «дата появления
карточки на сайте», а дата, когда запись в таком виде легла в JSON, и у
876 карточек это 23 июля 2026 (разовый технический перенос, не поток новых
сделок) — для них `today - added` уже больше недели, но пока меньше 30
дней, и растёт с каждым днём. 131 карточка (added 15 июля) уже перешагнула
30-дневную отметку и требует настоящего месячного прохода прямо сейчас, а
не с сентября — цифра в докстроке скрипта `--write` и печатается отдельной
строкой «РЕАЛЬНАЯ месячная очередь», не путать со счётчиком самого
бэкфилла.

Карточки без `added` при уже стоящем `deep_researched` в базе на 16 августа
2026 не встречаются (проверено отдельно) — но если такая появится, скрипт
её посчитает и покажет, а не пропустит молча: см. `no_added` в выводе.

Запуск:
    python3 pipeline/backfill_followup_researched.py            # сухой прогон
    python3 pipeline/backfill_followup_researched.py --write    # запись
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

WINDOW_DAYS = 30
TODAY = date(2026, 8, 16)  # подставлять текущую дату прогона


def parse_date(s):
    try:
        y, m, d = map(int, str(s).split('-'))
        return date(y, m, d)
    except (ValueError, TypeError):
        return None


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']

    to_stamp = []
    no_added = []
    already = 0
    real_queue_today = 0  # реальная очередь ПО СЕГОДНЯШНЕЙ ДАТЕ — критерий
                           # REVISION_BRIEF.md: today - added >= 30, а не
                           # критерий бэкфилла (deep_researched - added >= 30)

    for d in deals:
        dr = d.get('deep_researched')
        if not dr:
            continue
        if d.get('followup_researched'):
            already += 1
            continue
        added_date = parse_date(d.get('added'))
        dr_date = parse_date(dr)
        if not added_date or not dr_date:
            no_added.append(d['id'])
            continue
        if (dr_date - added_date).days >= WINDOW_DAYS:
            to_stamp.append((d, dr))
        if (TODAY - added_date).days >= WINDOW_DAYS:
            real_queue_today += 1

    print('Карточек с deep_researched: %d' % sum(1 for d in deals if d.get('deep_researched')))
    print('Уже несут followup_researched: %d' % already)
    print('Без added/deep_researched в разборном формате (не тронуты): %d' % len(no_added))
    if no_added:
        print('  %r' % no_added[:10])
    print('К проставлению бэкфиллом (deep_researched случился >= %d дней после '
          'added — окно уже органически покрыто самим глубоким поиском): %d'
          % (WINDOW_DAYS, len(to_stamp)))
    print('РЕАЛЬНАЯ месячная очередь на сегодня, %s (today - added >= %d дней, '
          'независимо от бэкфилла): %d'
          % (TODAY.isoformat(), WINDOW_DAYS, real_queue_today))
    # Каждая карточка бэкфилла по построению удовлетворяет и реальному
    # критерию (dr_date <= TODAY, значит today-added >= dr_date-added >= 30)
    # — остаток и есть то, что требует настоящего месячного прохода прямо
    # сейчас, а не когда-нибудь.
    print('Останется в реальной очереди ПОСЛЕ этого бэкфилла: %d'
          % (real_queue_today - len(to_stamp)))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for card, dr in to_stamp:
        assert not card.get('followup_researched'), \
            '%s: followup_researched уже стоит' % card['id']
        card['followup_researched'] = dr

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d карточек получили followup_researched.' % len(to_stamp))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
