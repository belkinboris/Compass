# -*- coding: utf-8 -*-
"""Сырье d02193838 (t.me/rusven/7862, выход ЗПИФ «Цифровые горизонты» из
«Юрента») владелец признал сделкой («в работу»), но в памяти консоли оно
стояло как `enrich:ga95746a3` — дополнение к карточке покупки контроля
2024 года (known_issues/intake.md). Карточка собрана отдельно: g2ebcbafc
(`fix_add_mts_yurent_fund_exit_card_2026_11_23.py`). Здесь отметка сырья
приводится к той, что стоит у сырья, взятого в работу и ставшего карточкой
(`take`, как у d86170319): и в `decided_raw`, и в `raw_titles` по заголовку
этого же сырья.

    python3 pipeline/fix_raw_take_d02193838_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_raw_take_d02193838_2026_11_23.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

STATE = os.path.join(ROOT, '..', 'data', 'inbox', 'moderation_state.json')
DRAFT_ID = 'd02193838'
OLD, NEW = 'enrich:ga95746a3', 'take'


def apply(state):
    import promote
    assert state['decided_raw'].get(DRAFT_ID) == OLD, \
        'ожидали %r, стоит %r' % (OLD, state['decided_raw'].get(DRAFT_ID))
    assert state['decided_raw'].get('d86170319') == NEW, 'образец отметки (d86170319) изменился'
    key = promote.raw_key(state['raw_sent_titles'][DRAFT_ID])
    assert state['raw_titles'].get(key) == OLD, 'raw_titles: ожидали %r, стоит %r' % (OLD, state['raw_titles'].get(key))
    state['decided_raw'][DRAFT_ID] = NEW
    state['raw_titles'][key] = NEW
    return key


def main(write):
    state = json.load(open(STATE, encoding='utf-8'))
    key = apply(state)
    print('decided_raw[%s]: %s -> %s' % (DRAFT_ID, OLD, NEW))
    print('raw_titles[%s…]: %s -> %s' % (key[:40], OLD, NEW))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    state = json.load(open(STATE, encoding='utf-8'))  # перечитать прямо перед записью
    apply(state)
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
