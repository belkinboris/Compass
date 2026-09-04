# -*- coding: utf-8 -*-
"""«Промресурс»/«УК Межегейуголь» (gd3556cc0): в поле «Цель сделки» стояло
подтверждение закрытия, а не цель.

ЧТО БЫЛО НЕВЕРНО — И ЭТО СМЫСЛОВАЯ ОШИБКА, НЕ ПУНКТУАЦИЯ. Предыдущий заход
(`fix_promresurs_mezhegeyugol_rationale_punctuation.py`, тот же день) поправил
только знак препинания в `eco.rationale`, оставив сам факт на месте:
«"Распадская" подтвердила завершение сделки: актив больше не входит в состав
компании.» Владелец указал на настоящую проблему: `eco.rationale` подписан на
экране как «Цель сделки» (см. `para("Цель сделки", d.eco.rationale)` в
static/index.html, а в посте канала — как «Зачем»), а это предложение НЕ
отвечает на вопрос «зачем» — оно подтверждает, что сделка закрылась, то есть
дублирует уже показанный статус «Закрыта», просто со стороны продавца.

ПРОВЕРЕНО ПО ИСТОЧНИКУ. Прямое чтение (WebFetch)
https://smart-lab.ru/blog/news/1347964.php целевым вопросом «зачем
«Промресурс» покупает этот актив» — статья НЕ называет ни цель покупателя,
ни план развития месторождения, ни стратегию консолидации. Единственное, что
источник говорит о мотиве, — это про СЕСТРИНСКУЮ сделку (Улугхемуголь/
«Северсталь», другая карточка): «продажа соответствует стратегии снижения
использования твердого топлива в производственной цепочке» — про «Северсталь»,
не про «Распадскую», и не про эту карточку. Для этой сделки настоящей цели в
источнике нет вовсе.

ПОЧЕМУ НЕ ПЕРЕНОС, А ОЧИСТКА. Правило «переносить факт в правильное поле
можно, сочинять нельзя» здесь не даёт переноса: факт «Распадская подтвердила
закрытие» и так уже виден читателю как статус «Закрыта» — переложить его в
`eco.context` значило бы показать то же самое дважды другими словами (уже
записанный класс: «Одно поле — одна линза»). Честная пустота лучше: `—`,
тот же плейсхолдер, что уже стоит у val/target_fin/fin этой карточки.

Запуск:
    python3 pipeline/fix_promresurs_mezhegeyugol_rationale_is_not_a_purpose.py
    python3 pipeline/fix_promresurs_mezhegeyugol_rationale_is_not_a_purpose.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gd3556cc0'
OLD = '«Распадская» подтвердила завершение сделки: актив больше не входит в состав компании.'
NEW = '—'


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data.get('cards') or [] if c.get('id') == CARD_ID), None)
    if card is None:
        print('Карточки %s в очереди предпросмотра нет — возможно, она уже '
              'в базе.' % CARD_ID)
        return 1

    current = (card.get('eco') or {}).get('rationale')
    if current == NEW:
        print('Уже поправлено, ничего не делаю.')
        return 0
    assert current == OLD, 'eco.rationale уже другой: %r' % (current,)

    print('Было: %s' % OLD)
    print('Стало: %s (источник цели сделки не называет)' % NEW)
    if not write:
        print('\nСухой прогон. Записать: --write')
        return 0

    card.setdefault('eco', {})['rationale'] = NEW
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nЗаписано в %s' % os.path.relpath(PENDING, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
