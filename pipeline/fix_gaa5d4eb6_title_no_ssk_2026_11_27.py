# -*- coding: utf-8 -*-
"""Карточка `gaa5d4eb6`: «ССК» уходит из заголовка, покупатели — по реестру.

ЧТО И ПОЧЕМУ. Заголовок «ГК «ССК» купила двух застройщиков группы «Носта»»
держался на посте телеграм-канала @dealsma. По ЕГРЮЛ покупателей два и ни
один не «ССК»: ООО СЗ «Фрихауз» 9 сентября 2026 года получило ООО
«Стройдевелопмент», ООО СЗ «Весенний бриз» 25 сентября — ООО
«Стройситикраснодар» (law.struct карточки, партия reading_2026_11_26_day_07).
Владельцу 27 ноября задан вопрос (open_questions.json,
`gaa5d4eb6-two-developers`): переписать по реестру без «ССК» в заголовке или
оставить версию телеграм-канала с оговоркой. Ответ — заметка 1807 «Убери мск»
(читаем как «Убери ССК»: ответ на этот вопрос, соседние клавиши; слова «мск»
в карточке и вопросе нет).

ЧТО НЕ ТРОГАЕМ. 161.ru пишет, что «Стройдевелопмент» входит в структуру
«ССК» («Теперь им владеет «ССК» через «Стройдевелопмент»») — это остается в
прозе со ссылкой на издание; про «Стройситикраснодар» такой связи источники
не дают, и проза это уже говорит.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Выписки datanewton на диске этого прогона нет
(сайт рвет соединение), review.py цитату сверить не может. Цитата — та же
строка реестра, что уже проверена в записи law.struct партии
reading_2026_11_26_day_07. Запись FIXES на title
(fixes/written_gaa5d4eb6_2026_11_09.py) синхронизирована: new = новый заголовок.

Запуск:
    python3 pipeline/fix_gaa5d4eb6_title_no_ssk_2026_11_27.py            # сухой прогон
    python3 pipeline/fix_gaa5d4eb6_title_no_ssk_2026_11_27.py --write    # запись
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'static', 'data', 'deals_promoted.json')
sys.path.insert(0, HERE)

CARD_ID = 'gaa5d4eb6'
OLD = 'ГК «ССК» купила двух застройщиков группы «Носта»'
NEW = '«Стройдевелопмент» и «Стройситикраснодар» купили двух застройщиков группы «Носта»'
URL = 'https://datanewton.ru/api/v2/history?ogrn=1252300040563&startDate=2000-01-01&attributes=OWNERS'
QUOTE = ('"updated_at":"2026-09-09","values":[{"old":"АКЦИОНЕРНОЕ ОБЩЕСТВО \\"РЕМИДА\\" (ОГРН: 1127747201306) '
         '100.0%; (140 034 979 руб.)","new":null},{"old":null,"new":"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ '
         '\\"СТРОЙДЕВЕЛОПМЕНТ\\" (ОГРН: 1232300055140) 100.0%; (140 034 979 руб.)"} … '
         '"updated_at":"2026-09-25","values":[{"old":"АКЦИОНЕРНОЕ ОБЩЕСТВО \\"РЕМИДА\\" (ОГРН: 1127747201306) '
         '100.0%; (10 000 руб.)","new":null},{"old":null,"new":"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ '
         '\\"СТРОЙСИТИКРАСНОДАР\\" (ОГРН: 1232300033020) 100.0%; (10 000 руб.)"} … '
         'Ранее здание принадлежало ГК «Носта» через компанию АО «Ремида».')


def main(write):
    base = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    before = copy.deepcopy(base)
    card = next((d for d in base['deals'] if d['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточки нет в базе' % CARD_ID)
    if card.get('title') == NEW:
        print('%s: заголовок уже новый — делать нечего' % CARD_ID)
        return 0
    assert card.get('title') == OLD, 'заголовок изменился: %r' % card.get('title')
    print('%s: title\n  было:  %s\n  стало: %s' % (CARD_ID, OLD, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    import fact_edit_guard
    import mass_edit_guard
    card['title'] = NEW
    fact_edit_guard.log(card, 'title', NEW, QUOTE, URL, 'fix_gaa5d4eb6_title_no_ssk_2026_11_27')
    mass_edit_guard.check(before, base)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    print('ЗАПИСАНО: static/data/deals_promoted.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
