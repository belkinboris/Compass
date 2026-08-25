# -*- coding: utf-8 -*-
"""После подтверждения, что присоединение Почта Банка к ВТБ РЕАЛИЗОВАНО
(pipeline/fix_vtb_pochtabank_merger_completed_context.py — 1 мая 2026
года Почта Банк юридически прекратил существование), поле `extra`
осталось нетронутым и продолжало говорить «ВТБ планирует присоединить
Почта Банк в 2026 году» — тот самый класс дефекта из REVISION_BRIEF.md
(«после правки — перечитайте карточку целиком, не только своё поле»).

Запуск: python3 pipeline/fix_vtb_pochtabank_extra_stale_after_merger.py
        python3 pipeline/fix_vtb_pochtabank_extra_stale_after_merger.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g06a6081f'

OLD_EXTRA = (
    'ВТБ выкупил 49,99% долю «Почты России» в Почта Банке и стал '
    'единственным владельцем кредитной организации. ВТБ планирует '
    'присоединить Почта Банк в 2026 году.'
)
NEW_EXTRA = (
    'ВТБ выкупил 49,99% долю «Почты России» в Почта Банке и стал '
    'единственным владельцем кредитной организации. Присоединение '
    'завершено: с 1 мая 2026 года Почта Банк прекратил существование как '
    'отдельное юрлицо, сеть работает под брендом ВТБ.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA, 'extra изменился с момента чтения'

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
