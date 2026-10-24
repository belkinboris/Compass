# -*- coding: utf-8 -*-
"""Russ/мэрия Москвы, сеть рекламных конструкций (g749426ce): второе чтение
(сессия со свежим контекстом, pipeline/ingest/SECOND_READING_BRIEF.md) нашло,
что заголовок карточки — дословная копия тега <title> источника
(«Russ выиграл аукцион на управление рекламными конструкциями Москвы за
33,31 млрд рублей», data/inbox/raw/2026-10-24-articles.jsonl), а не
собственная фраза сборщика. Приёмка это не ловит: её дословная проверка
(`accept_card.verbatim_runs`) сканирует только прозаические поля
(`proofread.PROOFREAD_FIELDS`), заголовок в их число не входит.

Заголовок — структурное поле (`proofread.STRUCTURAL`), вычитка через
`proofread.py` его не берёт; через таблицу `review.py` его тоже не починить
обычным путём: там заголовок обязан быть дословной подстрокой цитаты
(«перенос, а не переформулировка» — review.check, ветка «Имя, предмет,
сумма»), а цель правки — ровно наоборот, не дословная копия чужого текста.
Поэтому правка — разовым скриптом, как и заголовок X4 Падел/Rocket Padel
19–20 октября 2026 (`docs/card_acceptance.md`): «Новый заголовок собирается
из слов той же карточки» (`docs/card_parties.md`) — здесь это уже принятые
поля `asset` («право управления сетью рекламных конструкций Москвы на 10
лет (более 1,8 тыс. объектов)») и `eco.sum`/`sum` («33,31 млрд ₽»), без
единого нового факта. Глагол и форма имени — по образцу уже принятых в базе
заголовков о Russ («Группа Russ приобрела ООО «Эфир Транзит»…»,
«ГК Russ приобрела оператора наружной рекламы «Медиа Простор»»).

Карточка ещё в очереди предпросмотра (static/data/pending.json), поэтому
чтение и запись — через accept_card.load()/save() (тот же путь, что у
proofread.py и second_reading.py), а не прямо по deals_promoted.json.

Без ключа — сухой прогон, запись по --write.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))
sys.path.insert(0, ROOT)

import accept_card  # noqa: E402

CARD_ID = 'g749426ce'
OLD_TITLE = 'Russ выиграл аукцион на управление рекламными конструкциями Москвы за 33,31 млрд рублей'
NEW_TITLE = 'Группа Russ приобрела право управления сетью рекламных конструкций Москвы на 10 лет за 33,31 млрд рублей'


def main():
    write = '--write' in sys.argv
    base, pending = accept_card.load()
    card, where = accept_card.find_card(CARD_ID, base, pending)
    if card is None:
        print('%s: карточки нет ни в базе, ни в очереди' % CARD_ID)
        return 1
    assert card.get('title') == OLD_TITLE, card.get('title')
    card['title'] = NEW_TITLE
    print('%s (%s): title %r -> %r' % (CARD_ID, where, OLD_TITLE, NEW_TITLE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    accept_card.save(base, pending)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
