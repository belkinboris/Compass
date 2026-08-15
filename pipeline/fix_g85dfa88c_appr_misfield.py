# -*- coding: utf-8 -*-
"""Откат ошибочной правки law.appr у g85dfa88c (Солид-банк/Камчатпрофитбанк).

ЧТО СЛОМАНО. Партия 5 агентов (раунд 3, 14 августа 2026) записала в law.appr
цитату «В октябре 2022 года «Солид Банк» попал в список 45 банков
«недружественных» стран, сделки с долями которых запрещены без специального
разрешения». Тест `test_approval_names_a_body` справедливо отклонил её при
следующем прогоне: цитата говорит, что разрешение ТРЕБУЕТСЯ, а не что оно
было получено, и не называет орган. Факт уже перенесён в `law.terms`
(pipeline/ingest/fixes/batch_agents100_r3.py, тем же прогоном) — это поле
пустовало и подходит по смыслу («условие сделки», а не «согласование»).
Этот скрипт только возвращает law.appr к прежней заглушке.

ЗАПУСК:
    python3 pipeline/fix_g85dfa88c_appr_misfield.py            # сухой прогон
    python3 pipeline/fix_g85dfa88c_appr_misfield.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g85dfa88c'
WRONG = ('В октябре 2022 года «Солид Банк» попал в список 45 банков '
         '«недружественных» стран, сделки с долями которых запрещены без '
         'специального разрешения.')
CORRECT = 'Публично не сообщалось'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('law', {}).get('appr') == WRONG, \
        'law.appr уже другой: %r' % deal.get('law', {}).get('appr')

    print('ПРАВИМ %s: law.appr — откат к заглушке (факт уже в law.terms)' % DEAL_ID)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['law']['appr'] = CORRECT
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
