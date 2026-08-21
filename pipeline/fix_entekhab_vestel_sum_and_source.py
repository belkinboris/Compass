# -*- coding: utf-8 -*-
"""Чинит недостоверную сумму на карточке g8433f5c1 («Entekhab Group
покупает завод Vestel в Александрове»).

Найдено в рамках G5 (PRODUCT_ROADMAP.md): замер на бессодержательные
плейсхолдеры eco.val дал 10 карточек; у трёх сумма не подтверждается их
источниками вообще — это одна из них. `sum`/`eco.sum` несли «3 млрд ₽
(по оценке)», но ни один из двух источников карточки (vedomosti.ru,
cnews.ru) этой цифры не содержит — только $80 млн стоимости
ПЕРЕОБОРУДОВАНИЯ завода (другая величина, из cnews.ru) и прямое
указание cnews.ru, что цену завода собеседник издания не назвал.

Третий, независимый источник (Коммерсантъ, найден WebSearch, ещё не
стоял в `src`, хотя `eco.context` этой же карточки уже пересказывает
Коммерсант текстом без ссылки — тот же класс дефекта, что уже описан в
CLAUDE.md про источник, упомянутый в тексте, но не добавленный в src)
называет цену прямо: «Сделка оценивалась в $45 млн, управляющей
компанией завода должен был стать «Русклимат»» — со ссылкой на
конкретного участника переговоров (Гусейн Иманов, учредитель Jacky's,
экс-менеджер Vestel), а не анонимно.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g8433f5c1'
OLD_SUM = '3 млрд ₽ (по оценке)'
NEW_SUM = '$45 млн (по оценке)'
OLD_VAL = 'Оценка экспертов'
NEW_VAL = ('По словам учредителя производителя бытовой техники Jacky\'s '
           'и экс-менеджера Vestel Гусейна Иманова, стороны договорились '
           'о цене в районе $45 млн (4,1 млрд руб.), управляющей '
           'компанией со стороны иранского инвестора в РФ должен был '
           'стать производитель кондиционеров «Русклимат».')
NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6609342']


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['sum'] == OLD_SUM, f"sum: ожидали {OLD_SUM!r}, нашли {deal['sum']!r}"
    assert deal['eco']['sum'] == OLD_SUM, \
        f"eco.sum: ожидали {OLD_SUM!r}, нашли {deal['eco']['sum']!r}"
    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: ожидали {OLD_VAL!r}, нашли {deal['eco']['val']!r}"
    assert NEW_SRC not in deal['src'], "источник уже стоит в src"

    print(f"{CARD_ID} sum: {OLD_SUM!r} -> {NEW_SUM!r}")
    print(f"{CARD_ID} eco.sum: {OLD_SUM!r} -> {NEW_SUM!r}")
    print(f"{CARD_ID} eco.val: {OLD_VAL!r} -> {NEW_VAL!r}")
    print(f"{CARD_ID} src += {NEW_SRC!r}")

    deal['sum'] = NEW_SUM
    deal['eco']['sum'] = NEW_SUM
    deal['eco']['val'] = NEW_VAL
    deal['src'].append(NEW_SRC)

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
