# -*- coding: utf-8 -*-
"""Карточка `ga5198c41` (Сергей Семак / «Юхата»): тип M&A -> Инвестиция.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Тип решают по механике сделки
(`pipeline/ingest/REVISION_BRIEF.md`: «допэмиссия/закрытая подписка при типе
не «Инвестиция»?»), а не по глаголу прессы — а `review.py` сверяет тип
только со словом из TYPE_WORDS в цитате источника. У ТАСС и его перепечатки
(Рамблер/спорт) стоит «приобрел долю» (слово M&A), хотя по механике это
вход нового участника в капитал.

ДОКАЗАТЕЛЬСТВО (история участников ЕГРЮЛ, datanewton.ru, ОГРН
1265000045485, запись от 24.11.2026): до записи — Михайлов Иван
Александрович 100% (номинал 10 000 руб.); после — Михайлов 66,66% (номинал
10 000 руб. БЕЗ ИЗМЕНЕНИЯ), Семак Сергей Богданович 33,34% (номинал
5 001 руб., новый участник). Общий уставный капитал выросл с 10 000 до
15 001 руб. Номинал Михайлова не менялся — значит, Семак не выкупил часть
ЕГО доли (это было бы M&A), а довнес новый капитал в саму компанию
(допэмиссия/вход в капитал) — классическая «Инвестиция». Продавца у такой
сделки нет: деньги получила компания, а не Михайлов, поэтому роль
`seller`/`seller_id` не заводится.

Структурное поле (не прозаическое) — отдельный скрипт, а не FIXES review.py
(docs/card_editing_scripts.md, «Когда review.py не подходит»). Остальные
правки той же карточки — accept_card.py (профиль «Юхаты», заголовок,
предмет, отрасль) и write_card.py (eco.context,
pipeline/ingest/fixes/written_2026_11_25_vm.py).

Запуск:
    python3 pipeline/fix_ga5198c41_investment_type_2026_11_25.py            # сухой прогон
    python3 pipeline/fix_ga5198c41_investment_type_2026_11_25.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'ga5198c41'
OLD_TYPE = 'M&A'
NEW_TYPE = 'Инвестиция'


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        sys.exit('%s: карточки нет в pending.json (принята или удалена?)' % CARD_ID)
    assert card.get('type') == OLD_TYPE, (
        'состояние поля изменилось: %r, ожидали %r' % (card.get('type'), OLD_TYPE))
    print('%s: type %r -> %r' % (CARD_ID, OLD_TYPE, NEW_TYPE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    card['type'] = NEW_TYPE
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: static/data/pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
