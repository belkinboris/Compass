# -*- coding: utf-8 -*-
"""Разовый бэкфилл `weekly_researched` — нового среднего уровня очереди
дочитывания (день → неделя → месяц, `pipeline/ingest/REVISION_BRIEF.md`,
18 августа 2026).

ЗАЧЕМ. `stamp_followup_researched()` теперь требует `weekly_researched`, а
не `deep_researched` напрямую — третий уровень стал дельтой поверх второго,
а не поверх первого (см. review.py). У карточек, которым `followup_researched`
уже проставлен ИЗ ПРОШЛОГО, до появления этого поля — второй уровень
формально отсутствует, хотя по смыслу он давно пройден: раз карточку уже
проверяли на события через месяц после появления, недельное окно внутри
этого месяца тем более пройдено. Без бэкфилла `test_followup_researched_
never_appears_without_weekly_researched` упал бы на всей истории — не
потому, что данные неверны, а потому, что поле появилось позже факта.

Правило: `followup_researched` уже стоит и `weekly_researched` ещё нет →
`weekly_researched = followup_researched` (та же дата, а не сегодняшняя —
честно, что фактически было пройдено ДАВНО, а не пришло только что).

Запуск:
    python3 pipeline/backfill_weekly_researched.py            # сухой прогон
    python3 pipeline/backfill_weekly_researched.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']

    to_stamp = [d for d in deals
                if d.get('followup_researched') and not d.get('weekly_researched')]

    print('Карточек с followup_researched без weekly_researched: %d' % len(to_stamp))
    for d in to_stamp[:10]:
        print('  %s: followup_researched=%s' % (d['id'], d['followup_researched']))
    if len(to_stamp) > 10:
        print('  ... и ещё %d' % (len(to_stamp) - 10))

    if '--write' not in argv:
        print('\nСухой прогон — ничего не записано. Добавьте --write.')
        return 0

    for d in to_stamp:
        d['weekly_researched'] = d['followup_researched']

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО: %d карточек.' % len(to_stamp))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
