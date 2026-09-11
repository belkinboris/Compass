# -*- coding: utf-8 -*-
"""Заметка владельца 11 сентября 2026 (id решения 603, карточка g7299791f,
«Финансовая группа БКС могла купить банк «Форштадт»»): «оставляем закрыта
[вопрос про статус], но в комментариях надо чтобы было видно, что БКС и
банк опровергли. Почему-то что БКС опроверг написано в разделе "Как
устроена сделка", это почему так, это же бред, ты карту сделки не
вычитывал что ли?»

Дефект: `law.struct` («Как устроена сделка») нёс опровержение БКС — факт
про статус СДЕЛКИ, а не про её юридическую структуру; опровержение уже
подробно изложено в `eco.context`, но на главной вкладке («Обзор»,
`extra`) читатель его не видел вовсе. Правка: `law.struct` очищен (нет
подтверждённой структуры сделки — честная пустота), факт опровержения
перенесён в `extra` с источником, как просил владелец.

Запуск: python3 pipeline/fix_bks_forshtadt_extra_denial.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g7299791f'
OLD_LAW_STRUCT = 'В БКС заявили, что информация о сделке не соответствует действительности.'
OLD_EXTRA = 'Strategy Partners сопровождала сделку; её роль не уточнена.'
NEW_EXTRA = (OLD_EXTRA + ' БКС и «Форштадт» опровергли информацию о сделке '
             '6 октября 2025 года: «В БКС заявили, что информация о сделке '
             'не соответствует действительности» (Ведомости, '
             'vedomosti.ru/finance/news/2025/10/06/1144612-gruppa-bks-oprovergla).')


def main(write=False):
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    card = next((c for c in base['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена' % CARD_ID
    assert card['law']['struct'] == OLD_LAW_STRUCT, 'law.struct уже другой'
    assert card['extra'] == OLD_EXTRA, 'extra уже другой'

    card['law']['struct'] = '—'
    card['extra'] = NEW_EXTRA

    print('Правка %s: law.struct очищен, extra дополнен опровержением.' % CARD_ID)

    if write:
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
