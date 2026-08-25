# -*- coding: utf-8 -*-
"""`test_no_duplicate_deal_cards` поймал дубль сразу после того, как
pipeline/fix_mcexpert_real_buyer_mat_i_ditya.py исправил заголовок и
buyer карточки gddc29a8d на «Мать и дитя»/МЦ «Эксперт» — до правки её
заголовок называл «Медкапитал», и признак дубля (два общих слова в
кавычках при близкой сумме и дате) её не видел. `g833a29f6` — гораздо
более полная, уже глубоко обысканная карточка ТОЙ ЖЕ сделки (добавлена
2026-07-15, десять источников, консультант продавца Nextons, разбивка
оплаты по срокам). gddc29a8d — более поздний, беднее наполненный дубль
(добавлен из партии @dealsma 2026-07-23).

Оставляем g833a29f6, переносим в неё три факта, которых там не было (все
найдены дельта-поиском этого часа и не дублируют уже написанное):
структуру владения покупателя (ООО «Хавен» 99% / ООО «Клиника Мать и
Дитя» 1%), путаницу с предварительно одобренным ФАС, но не закрывшим
сделку кандидатом «Медкапитал» (структура ГК «Медскан»/«Росатом»), и
личность продавца (Елена Латышева, сестра экс-мэра Липецка Евгении
Уваркиной, а не только должность «Председатель СД ГК «Эксперт»»).
gddc29a8d удаляется, адрес редиректится через `merged`.

Запуск: python3 pipeline/merge_mcexpert_duplicate_into_g833a29f6.py
        python3 pipeline/merge_mcexpert_duplicate_into_g833a29f6.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SURVIVOR_ID = 'g833a29f6'
DUP_ID = 'gddc29a8d'

OLD_STRUCT = '—'
NEW_STRUCT = (
    'ООО «Хавен», принадлежащее МД Медикал Груп, получило 99% в «МЦ '
    'Эксперт», оставшийся 1% — у ООО «Клиника Мать и Дитя» (также входит '
    'в МД Медикал Груп).'
)

OLD_CONTEXT = (
    'Сеть «Мать и дитя», основанная известным гинекологом Марком '
    'Курцером, после сделки будет объединять уже 107 медицинских '
    'учреждений.'
)
CONTEXT_ADDITION = (
    ' До этого объявления ФАС предварительно согласовывала покупку 99% '
    '«МЦ Эксперт» другому кандидату — ООО «Медкапитал», структуре ГК '
    '«Медскан» (частный медицинский холдинг с участием госкорпорации '
    '«Росатом»); эта сделка не состоялась. Продавец Елена Латышева — '
    'сестра экс-мэра Липецка Евгении Уваркиной.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['kommersant.ru', 'https://www.kommersant.ru/doc/7738819'],
    ['rb.ru', 'https://rb.ru/news/mat-i-ditya-kupila/'],
    ['center.business-magazine.online', 'https://center.business-magazine.online/fn_1662721.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    survivor = next(d for d in data['deals'] if d['id'] == SURVIVOR_ID)
    dup = next(d for d in data['deals'] if d['id'] == DUP_ID)

    assert survivor['law']['struct'] == OLD_STRUCT
    assert survivor['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in survivor['src']), f'{url} уже в src'

    print('=== g833a29f6 law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== g833a29f6 eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)
    print(f'=== удаляется карточка-дубль {DUP_ID}, редирект на {SURVIVOR_ID} ===')

    if write:
        survivor['law']['struct'] = NEW_STRUCT
        survivor['eco']['context'] = NEW_CONTEXT
        survivor['src'].extend(NEW_SRC)
        data['deals'] = [d for d in data['deals'] if d['id'] != DUP_ID]
        data.setdefault('merged', {})[DUP_ID] = SURVIVOR_ID
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
