# -*- coding: utf-8 -*-
"""234 карточки несут в `eco.rationale` и/или `extra` протёкшую служебную
пометку роли стороны — хвост вида «(Сбербанк (продавец))» или «(ГК «Эксперт»
(покупатель))», прицепленный к концу предложения. Найдено при разборе
жалобы владельца на карточку «Галс Девелопмент»/Наметкина — читая соседние
карточки на тот же класс дефекта («правило проверяется, где дефект РЕАЛЬНО
встречается», CLAUDE.md), обнаружился общий след ОДНОГО источника: партии
компактного импорта синтезировали `eco.rationale`/`extra` шаблоном со
служебной меткой стороны на конце — метка нужна была для внутренней
сортировки при разборе, но осталась в тексте, который показывается читателю.

Это НЕ новый факт и не выдумка — дословный текст ДО тега не меняется ни на
символ, снимается только сам тег. Поэтому это не через `review.py` (там
для снятия текста нужна цитата источника, а тег — не из источника вовсе,
это наша собственная разметка) — тот же приём, что уже использовали точечные
скрипты `fix_batch_d_n06_wrong_years_and_tags.py`, `fix_batch_d_rev06_leaked_tag.py`,
`fix_batch_d_rev07_leaked_tags.py`, `strip_leaked_role_tags_2022.py` — каждый
чистил свою партию (год/пачку импорта), и в сумме почти 250 карточек этот
дефект уже нашли по кусочку. Это ЗАВЕРШАЮЩИЙ сплошной прогон по ВСЕЙ базе,
не по одной партии: раз все потоки дочитывания сейчас на паузе, конфликтов
с параллельной работой над теми же карточками нет.

Регулярка ловит ТОЛЬКО хвост «(<до 80 знаков>(роль))» в конце строки — она
проверена на выборке: НЕ трогает легитимные вложенные пометки вроде «(по
оценке экспертов)» или «(стартовая цена торгов, финальная цена не
опубликована)», которые не заканчиваются словом роли во ВНУТРЕННИХ скобках.

ЗА ГРАНИЦЕЙ ЭТОГО ПРОГОНА: составные пометки вида «(сделка между X
(покупатель) и Y (продавец))» — 46 карточек, найденных тем же разбором, но
устроенных иначе (одна внешняя скобка на ДВЕ стороны, не в конце строки, а
внутри текста) — они не ловятся этой регуляркой и не входят сюда: другой
паттерн снятия, отдельная задача.

Запуск: python3 pipeline/strip_leaked_role_tags_all.py           # проверка
        python3 pipeline/strip_leaked_role_tags_all.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

TAG_RX = re.compile(
    r'\s*\([^()]{2,80}\((?:продавец|покупатель|цель|таргет|конечный '
    r'бенефициар|сторона продавца|сторона покупателя)\)\)\s*$', re.I)

EXPECTED_CARDS = 234


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    todo = {}
    for d in data['deals']:
        changes = {}
        r = (d.get('eco') or {}).get('rationale')
        if isinstance(r, str) and TAG_RX.search(r):
            changes['rationale'] = TAG_RX.sub('', r).rstrip()
        e = d.get('extra')
        if isinstance(e, str) and TAG_RX.search(e):
            changes['extra'] = TAG_RX.sub('', e).rstrip()
        if changes:
            todo[d['id']] = changes

    assert len(todo) == EXPECTED_CARDS, (
        'ожидалось %d карточек с протёкшей пометкой роли, найдено %d — '
        'состояние базы изменилось, проверьте список заново'
        % (EXPECTED_CARDS, len(todo)))

    cards = {d['id']: d for d in data['deals']}
    for cid, changes in todo.items():
        print('ПРАВИМ  %s: снята протёкшая пометка роли (%s)'
              % (cid, ', '.join(sorted(changes))))
    if not write:
        print('Сухой прогон. Запись — с ключом --write. Карточек: %d' % len(todo))
        return

    for cid, changes in todo.items():
        card = cards[cid]
        if 'rationale' in changes:
            card['eco']['rationale'] = changes['rationale']
        if 'extra' in changes:
            card['extra'] = changes['extra']
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: %d карточек.' % len(todo))


if __name__ == '__main__':
    main(write='--write' in sys.argv)
