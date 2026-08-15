# -*- coding: utf-8 -*-
"""gfe268487 (ГК «Монополия»/Globaltruck): eco.rationale несёт внутри себя
устаревшую фразу «Статус сделки: переговоры.» — след раннего разбора,
когда сделка ещё обсуждалась. Верхнеуровневый `status` уже «Закрыта»
(источник vedomosti.ru подтверждает закрытие 21 апреля), и фраза внутри
описания сделки ему прямо противоречит. Это не факт из источника, а
внутренняя нестыковка карточки (агент 5, партия 5, раунд 8) — правится
удалением, а не через review.py (нечего цитировать, нечего доказывать).

ЗАПУСК:
    python3 pipeline/fix_r8_monopoliya_stale_status_phrase.py            # сухой прогон
    python3 pipeline/fix_r8_monopoliya_stale_status_phrase.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gfe268487'
STALE = 'Статус сделки: переговоры. '


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id[CARD_ID]

    val = deal['eco']['rationale']
    assert STALE in val, '%s: устаревшей фразы уже нет в eco.rationale: %r' % (CARD_ID, val)
    assert deal.get('status') == 'Закрыта', \
        '%s: status уже другой: %r' % (CARD_ID, deal.get('status'))
    new_val = val.replace(STALE, '')
    print('ПРАВИМ %s.eco.rationale:' % CARD_ID)
    print('  было: %r' % val)
    print('  стало: %r' % new_val)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['eco']['rationale'] = new_val
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
