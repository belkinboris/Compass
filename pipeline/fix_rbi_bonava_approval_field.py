# -*- coding: utf-8 -*-
"""Правка того же прогона: `pipeline/fix_rbi_bonava_deal_fell_through.py`
дописал в `eco.context` карточки `ga2332f97` предложение «ФАС одобрила
сделку... но правительственная комиссия... не дала разрешение в срок»
— а `law.appr` при этом остался плейсхолдером «Публично не
сообщалось». `test_approval_is_not_left_in_prose` справедливо поймал
это как ровно тот класс дефекта, что описан в CLAUDE.md («Линза
«Юрист» пишет «согласования не раскрыли», когда согласование уже
названо в другом поле карточки») — я его сам создал этой же правкой,
не заметив.

Чинится переносом факта в его собственное поле: `law.appr` получает
согласование (ФАС одобрила, правкомиссия не успела), а `eco.context`
сохраняет только исход (срыв сделки и реальный покупатель), без
повторения слов «одобрила»/«ФАС».

Запуск: python3 pipeline/fix_rbi_bonava_approval_field.py
        python3 pipeline/fix_rbi_bonava_approval_field.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga2332f97'

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'ФАС одобрила сделку в августе 2023 года, но правительственная '
    'комиссия по контролю за иностранными инвестициями не дала '
    'разрешение в срок.'
)

OLD_ECO_CONTEXT = (
    'Претендентов на активы немного, вероятно, потому, что площадки '
    'застройщика невелики и требуют дополнительных затрат на '
    'подготовку к строительству. ФАС одобрила сделку в августе 2023 '
    'года, но правительственная комиссия по контролю за иностранными '
    'инвестициями не дала разрешение в срок — в октябре 2023 года '
    'Bonava расторгла соглашение с RBI и продала петербургские активы '
    'другому покупателю, армянской Star Development (связана с ГК '
    '«ФСК», основной владелец — Владимир Воронин); сделка закрыта 14 '
    'ноября 2023 года.'
)
NEW_ECO_CONTEXT = (
    'Претендентов на активы немного, вероятно, потому, что площадки '
    'застройщика невелики и требуют дополнительных затрат на '
    'подготовку к строительству. В октябре 2023 года Bonava '
    'расторгла соглашение с RBI и продала петербургские активы '
    'другому покупателю, армянской Star Development (связана с ГК '
    '«ФСК», основной владелец — Владимир Воронин); сделка закрыта 14 '
    'ноября 2023 года.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
