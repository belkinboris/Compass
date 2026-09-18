# -*- coding: utf-8 -*-
"""Приток 18.09.2026, часовой прогон 10:20 МСК — слияние `law.terms` на
карточке «Дом.РФ»/гостиница «Мадрид» (gd85b3ba8) из ДВУХ источников.

Карточка уже несла дословную цитату РИА («Победитель конкурса будет обязан
провести работы по ее реставрации и сохранению.») — эта половина не
трогается. Дополнительный поиск (шаг 9а) нашёл у uralweb.ru более
конкретное условие — срок и состав работ («До июня 2029 года... убрать
старое инженерное оборудование и рекламные конструкции с фасада.»). Обе
половины — правда, из разных статей, и объединить их в одну запись
`review.py`'s FIXES нельзя: его проверка `quote_is_real()` ищет цитату
ЦЕЛИКОМ в ОДНОМ кэшированном тексте, а не в конкатенации двух. Поэтому
слияние сделано точечным скриптом с раздельной проверкой каждой половины
(`review.quote_is_real`, вызвано и подтверждено интерактивно перед записью
этого скрипта — то же самое, что делает `review.check()` для обычной
правки, только руками, потому что механизм не рассчитан на два источника
в одном поле).

Дословность и авторство: первая половина — та же цитата РИА, что уже была
записана в review.py's FIXES для этой карточки ранее (не переписывается,
только проверяется на неизменность через `assert`); вторая — из
uralweb.ru, уже добавленного в `src` карточки тем же прогоном.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'
PENDING_PATH = 'static/data/pending.json'

OLD_TERMS = 'Победитель конкурса будет обязан провести работы по ее реставрации и сохранению.'
NEW_TERMS = (
    'Победитель конкурса будет обязан провести работы по ее реставрации и сохранению. Новому '
    'владельцу нужно будет до июня 2029 года восстановить здание и убрать старое инженерное '
    'оборудование и рекламные конструкции с фасада.'
)


def _apply(cards, label):
    target = [c for c in cards if c.get('id') == 'gd85b3ba8']
    if not target:
        return False
    assert len(target) == 1, target
    card = target[0]
    assert card['law']['terms'] == OLD_TERMS, repr(card['law']['terms'])
    card['law']['terms'] = NEW_TERMS
    print('%s: law.terms обновлено' % label)
    return True


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    pending = json.load(open(PENDING_PATH, encoding='utf-8'))

    changed_base = _apply(deals, 'base')
    changed_pending = _apply(pending['cards'], 'pending')
    assert changed_base or changed_pending, 'карточка gd85b3ba8 не найдена ни в базе, ни в pending'

    if write:
        if changed_base:
            json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if changed_pending:
            json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
