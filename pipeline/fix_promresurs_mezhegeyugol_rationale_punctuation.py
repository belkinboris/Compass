# -*- coding: utf-8 -*-
"""«Промресурс»/«УК Межегейуголь» (gd3556cc0): двоеточие сразу после названия
компании читается как подпись-значение, а не как предложение.

ЧТО БЫЛО СЛОМАНО. `eco.rationale` нёс: «"Распадская": подтвердила завершение
сделки, актив больше не входит в состав компании.» — двоеточие стоит сразу
после закрывающей кавычки, а дальше идёт глагол в прошедшем времени
(«подтвердила»), у которого «Распадская» — подлежащее, а не подпись. На
экране раздела «Зачем» в живом посте канала это и заметил владелец 4 сентября
2026: «раздел «зачем» вообще тупой». Ответом в Telegram он поправил ТЕКСТ
ПОСТА (это меняет только конкретное сообщение — `post_override`, поле
`eco.rationale` карточки не трогает), но карточка в тот момент ещё не в базе
(`pending.json`), и то же самое предложение показалось бы на самой карточке
сайта в «Экономисте» после публикации.

ПОЧЕМУ НЕ ЧЕРЕЗ ВЫЧИТКУ. Карточка не в базе — `proofread.py` до неё ещё не
дотянется (см. запись в CLAUDE.md про «Azimut отель Ярославль», тот же класс:
владелец видит карточку в консоли раньше, чем её вычитывают). Замер по всей
базе и очереди (двоеточие сразу после закрывающей кавычки, дальше глагол
прошедшего/настоящего времени) нашёл ещё одно совпадение (`ge4cded31`,
«Алаида»), но там колон вводит перечисление после уже законченной мысли —
не тот же дефект, трогать не нужно.

Факт не меняется: «Распадская» подтвердила закрытие сделки, актив больше не
у неё на балансе. Меняется только пунктуация — куда переезжает двоеточие.

Запуск:
    python3 pipeline/fix_promresurs_mezhegeyugol_rationale_punctuation.py
    python3 pipeline/fix_promresurs_mezhegeyugol_rationale_punctuation.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gd3556cc0'
OLD = '«Распадская»: подтвердила завершение сделки, актив больше не входит в состав компании.'
NEW = '«Распадская» подтвердила завершение сделки: актив больше не входит в состав компании.'


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data.get('cards') or [] if c.get('id') == CARD_ID), None)
    if card is None:
        print('Карточки %s в очереди предпросмотра нет — возможно, она уже '
              'в базе и вычитана обычным путём.' % CARD_ID)
        return 1

    current = (card.get('eco') or {}).get('rationale')
    if current == NEW:
        print('Уже поправлено, ничего не делаю.')
        return 0
    assert current == OLD, 'eco.rationale уже другой: %r' % (current,)

    print('Было: %s' % OLD)
    print('Стало: %s' % NEW)
    if not write:
        print('\nСухой прогон. Записать: --write')
        return 0

    card.setdefault('eco', {})['rationale'] = NEW
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nЗаписано в %s' % os.path.relpath(PENDING, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
