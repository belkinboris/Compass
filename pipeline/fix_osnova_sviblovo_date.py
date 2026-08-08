# -*- coding: utf-8 -*-
"""Карточка g6d73538c («Основа»/промзона «Свиблово») несла дату притока,
а не дату сделки.

ЧТО СЛОМАНО. Поле `date` стояло «2026-08-04» — день, когда карточку забрал
приток (`added` — «2026-08-05», на день позже). Источник (РИА Недвижимость)
прямо называет настоящую дату: «Сделка была закрыта в декабре 2025 года,
уточнил представитель девелопера.» Это молчаливая ошибка ровно того класса,
что уже описан в CLAUDE.md («Дата новости — не дата сделки»): и год, и месяц
были неверны, а не только день.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. Его `date_is_supported()` намеренно запрещает
менять год («переносить год — нет, значит утверждать новое») — механизм
рассчитан на уточнение дня внутри уже известного года, а не на перенос в
другой год. Здесь год меняется по-настоящему (2026 → 2025), и это тот самый
случай, для которого `date_is_supported()` и ставил защиту: перенос года
обязан быть отдельным, явным решением с проверяемым источником, а не
автоматической правкой в общей таблице.

ПОЧЕМУ ГОД, А НЕ ПОЛНАЯ ДАТА. Источник называет месяц и год («декабрь
2025 года»), но не конкретное число. Подставить «2025-12-01» значило бы
выдумать день, которого в источнике нет, — тот же дефект, что уже находили
и чинили у дат-заглушек «1 января» (`fix_placeholder_dates.py`,
`test_year_only_date_is_never_shown_as_the_first_of_january`). Пишем то, что
доказуемо: год. Месяц («декабрь 2025 года») остаётся текстом в `eco.context`
(добавлено через `review.py` этим же прогоном), а не в поле `date`.

Запуск:
    python3 pipeline/fix_osnova_sviblovo_date.py            # сухой прогон
    python3 pipeline/fix_osnova_sviblovo_date.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'g6d73538c'
OLD_DATE = '2026-08-04'
NEW_DATE = '2025'
QUOTE = 'Сделка была закрыта в декабре 2025 года, уточнил представитель девелопера.'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('date') == OLD_DATE, \
        'дата уже другая: %r, ожидали %r' % (deal.get('date'), OLD_DATE)

    print('%s: date %r -> %r' % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('  цитата: %r' % QUOTE)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['date'] = NEW_DATE
    assert deal['date'] == NEW_DATE, 'дата не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
