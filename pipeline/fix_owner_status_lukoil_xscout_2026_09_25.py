# -*- coding: utf-8 -*-
"""Решение владельца 25 сентября 2026: ЛУКОЙЛ/Carlyle и ХСкаут — «обе обсуждаются».

Оба вопроса (№ 9 и № 10 в `send_open_questions.QUESTIONS`) возникли из того,
что две проверки прочитали источники по-разному:
  • g20d4cc38 (ЛУКОЙЛ продаёт LUKOIL International GmbH компании Carlyle) —
    стояло «Подписана»; соглашение не эксклюзивно, зависит от разрешения OFAC,
    дата подписания договора ни в одном источнике не названа;
  • g4feb5ec3 (pre-IPO раунд ХСкаут) — стояло «Закрыта»; закрыта книга
    заявок, а не весь объём привлечения («35% от заявленного объёма уже
    закрыто», ABN).
Статус — «Обсуждается». Снятый статус записывается в `retracted.status`,
чтобы `enrich.py` не вернул его по следующему заголовку (тот же механизм, что
у «Ленты»/«Марии-Ра», 24 сентября 2026). Заголовок ЛУКОЙЛа говорил «продал» —
при статусе «Обсуждается» это противоречие, поэтому «продаёт». Вопросы
помечаются отправленными: владелец ответил на них в чате, консоли они не
нужны.

    python3 pipeline/fix_owner_status_lukoil_xscout_2026_09_25.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
QUESTIONS_STATE = os.path.join(ROOT, 'pipeline', 'open_questions_sent.json')

CHANGES = {
    'g20d4cc38': {
        'was': 'Подписана',
        'title': ('ЛУКОЙЛ продал зарубежные активы (LUKOIL International GmbH) компании Carlyle',
                  'ЛУКОЙЛ продаёт зарубежные активы (LUKOIL International GmbH) компании Carlyle'),
    },
    'g4feb5ec3': {'was': 'Закрыта', 'title': None},
}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for did, change in CHANGES.items():
        deal = by_id[did]
        if deal['status'] == 'Обсуждается':
            print('%s: уже «Обсуждается»' % did)
        else:
            assert deal['status'] == change['was'], (did, deal['status'])
            deal['status'] = 'Обсуждается'
            print('%s: статус «%s» → «Обсуждается»' % (did, change['was']))
        values = deal.setdefault('retracted', {}).setdefault('status', [])
        if change['was'] not in values:
            values.append(change['was'])
        if change['title'] and deal['title'] == change['title'][0]:
            deal['title'] = change['title'][1]
            print('%s: заголовок → %s' % (did, deal['title']))
    state = json.load(open(QUESTIONS_STATE, encoding='utf-8'))
    for did in CHANGES:
        state['sent'][did] = True
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        with open(QUESTIONS_STATE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
