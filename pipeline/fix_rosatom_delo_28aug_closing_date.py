# -*- coding: utf-8 -*-
"""Росатом/«Дело»/Шишкарев (`g5eb6ff22`): новый источник (РИА Новости,
25 августа 2026) назвал точную дату юридического завершения выкупа —
28 августа 2026 года, нотариально удостоверяемую. Прежний текст `eco.context`
заканчивался на «завершение ожидается до конца июля 2026 года» — прогноз,
который к 25 августа не подтвердился и не был обновлён. Цитата нового
источника не лежит в тексте старых источников — обычная таблица FIXES
такое не пропускает (review.py проверяет цитату ПРОТИВ ОДНОЙ статьи), тот же
приём, что уже применялся для Pridex/Multispace и IBS/Rubbles: старое
значение сохраняется, к нему дописывается предложение со ссылкой на новый
источник.

Статус карточки НЕ меняется на «Закрыта»: источник говорит будущим временем
(«в эту пятницу... юридически завершается», «завершится»), 28 августа ещё
не наступило на момент правки (25 августа) — «Обсуждается» остаётся честным
статусом до самого закрытия.

Запуск: python3 pipeline/fix_rosatom_delo_28aug_closing_date.py           # проверка
        python3 pipeline/fix_rosatom_delo_28aug_closing_date.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5eb6ff22'
OLD_CONTEXT = (
    'Процедура «русской рулетки» запущена 17 февраля 2026 года. Шишкарев '
    'сначала намеревался выкупить долю «Росатома», но 26 июня 2026 года '
    'отказался от этого варианта, сославшись на неблагоприятную '
    'макроэкономическую конъюнктуру, после чего 6 июля 2026 года «Росатом» '
    'объявил о решении самостоятельно выкупить 51% Шишкарева; оформление '
    'сделки запущено с 1 июля, завершение ожидается до конца июля 2026 '
    'года.'
)
ADDITION = (
    '25 августа 2026 года представитель «Росатома» сообщил точную дату '
    'юридического завершения: «В эту пятницу, 28 августа, юридически '
    'завершается предусмотренная корпоративным соглашением участников ГК '
    '"Дело" процедура выкупа принадлежащей С.Н. Шишкареву 51% доли в '
    'пользу госкорпорации "Росатом". Инициированный "Росатомом" механизм '
    '"русской рулетки" юридически завершится и будет нотариально '
    'удостоверен».'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['РИА Новости', 'https://ria.ru/20260825/rosatom-2113114155.html']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    assert card.get('status') == 'Обсуждается', 'статус уже другое'
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДО: %r' % OLD_CONTEXT)
    print('ПОСЛЕ: %r' % NEW_CONTEXT)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
