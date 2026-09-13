# -*- coding: utf-8 -*-
"""G3 (PRODUCT_ROADMAP.md) — переизмерение на новой партии притока (154
карточки `from_ingest` вместо 100 на 21 августа). Юрлицо в заголовке вместо
бренда: 1 настоящий кандидат из 3 найденных.

`g76f31c63` несёт «ООО «Птицефабрика «Акашевская»» купило базу отдыха...» —
проверено лично прямым WebFetch (kommersant.ru/doc/6281365): собственный
заголовок источника называет покупателя упрощённо, БЕЗ «ООО»
(«Птицефермой» — сокращение в заголовке, полное юридическое имя — только
в теле статьи). Профиль покупателя в базе тоже без «ООО»
(`gakashevskaya` — «Птицефабрика «Акашевская»»). Правило то же, что уже
применялось к «Кузнецкой ТЭЦ»/«Уралхиммашу» 14 августа: заголовок
карточки называет узнаваемый бренд, а не юридическую форму.

Два других найденных «юрлица в заголовке» — НЕ дефект, тот же вывод, что
уже закрыт 21 августа для «Развития строительных активов» и др.: у
`g0d72e1d5` («ООО «Гранит» (Елена Некрасова)») и `g672c6dfe` («...ООО
«СМ»»)» юрлицо — единственное публичное имя (анонимные/двухбуквенные
названия без узнаваемого бренда), заменять нечем — заголовки не трогаются.

Запуск:
    python3 pipeline/fix_akashevskaya_title_legal_form.py            # сухой прогон
    python3 pipeline/fix_akashevskaya_title_legal_form.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CID = 'g76f31c63'

OLD_TITLE = 'ООО «Птицефабрика «Акашевская»» купило базу отдыха «Ла дача Астрахань» у Наталии Дубовицкой'
NEW_TITLE = '«Птицефабрика «Акашевская»» купила базу отдыха «Ла дача Астрахань» у Наталии Дубовицкой'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    deals = {d['id']: d for d in data['deals']}
    card = deals[CID]

    if card['title'] == NEW_TITLE:
        print('Уже применено — нечего делать (скрипт идемпотентен).')
        return

    assert card['title'] == OLD_TITLE

    print('Правка для %s:' % CID)
    print('  title: %r -> %r' % (OLD_TITLE, NEW_TITLE))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['title'] = NEW_TITLE

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
