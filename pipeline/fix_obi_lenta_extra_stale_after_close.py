# -*- coding: utf-8 -*-
"""Карточка gcdd2b6de («Севергрупп выкупил сеть магазинов OBI у
Синдики»): после того как pipeline/fix_obi_lenta_severgrupp_closed.py
обновил статус на «Закрыта» и переписал `eco.context`, поле `extra`
осталось нетронутым и продолжало называть сделку «потенциальной», а
покупателя — «(неизвестен)» — тот самый класс дефекта из
REVISION_BRIEF.md («после правки — перечитайте карточку целиком, не
только своё поле»). Правка не добавляет новых фактов — только убирает
устаревшую формулировку, дублируя то, что уже дословно верно в
`eco.context`.

Запуск: python3 pipeline/fix_obi_lenta_extra_stale_after_close.py
        python3 pipeline/fix_obi_lenta_extra_stale_after_close.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcdd2b6de'

OLD_EXTRA = (
    'Потенциальная сделка между холдингом Синдика (продавец 25% в OBI) и '
    'ООО Севергрупп (покупатель). Севергрупп владеет Северсталью, сетью '
    'Лента, Утконосом и другими активами. (неизвестен)'
)
NEW_EXTRA = (
    'Сделка между холдингом «Синдика» (исходный владелец) и структурами '
    '«Севергрупп» Алексея Мордашова (владеет Северсталью, сетью «Лента», '
    '«Утконосом» и другими активами) — закрыта в январе 2026 года, актив '
    'перешёл группе «Лента» через ООО «Гермес». Подробности — во вкладке '
    '«Экономист».'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA, 'extra изменился с момента чтения — проверьте'

    print('=== extra: станет ===')
    print(NEW_EXTRA)

    if write:
        deal['extra'] = NEW_EXTRA
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
