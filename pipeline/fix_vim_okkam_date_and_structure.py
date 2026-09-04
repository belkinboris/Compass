# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF, второй уровень), карточка
`g9108dfd0` («ЗПИФ «Вим Недвижимость» выкупил штаб-квартиру группы
Okkam в башне «Империя»») — дата сделки не совпадала ни с одним
известным событием, `law.struct` пустовал.

Проверено лично прямым WebFetch:
- Мир квартир, https://www.mirkvartir.ru/journal/news/2026/08/11/klyuchevye-sobytiya-rynka-nedvizhimosti/:
  «Сделка была оформлена 7 августа через покупку юридического лица
  ООО «Фипс»» (на балансе которого находится объект).
- Коммерсантъ (уже в `src` карточки), https://www.kommersant.ru/doc/8876953:
  «Deal closure date: "7 августа"» (статья опубликована 11.08.2026).
- Ведомости.Недвижимость (уже в `src` карточки),
  https://www.vedomosti.ru/realty/articles/2026/08/10/1219874-vim-sberezheniya-zakrili-odnu-iz-sdelok-s-ofisami,
  опубликована 10.08.2026 — на день раньше Коммерсанта, тоже об уже
  закрытой сделке.

Три независимых источника согласны: сделка закрыта 7 августа 2026
года. Дата в карточке (2026-08-25) не совпадает ни с датой закрытия,
ни с датой публикации ни одного из трёх источников — похоже на
техническую ошибку разбора, а не на альтернативное событие.

НЕ ВНЕСЕНО: точная сумма сделки (диапазон «6–8 млрд ₽» встретился
только в одном вторичном пересказе, mirkvartir.ru, не подтверждён
дословно в первичном тексте Ведомостей — уже стоящая в карточке
формулировка «по оценке экспертов... 8 млрд ₽» осторожнее и не
меняется); идентификация группы «К1» — уже разрешена в самой карточке
цитатой управляющего директора Антона Халдина, повторно проверять не
требуется.

Запуск: python3 pipeline/fix_vim_okkam_date_and_structure.py
        python3 pipeline/fix_vim_okkam_date_and_structure.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9108dfd0'

OLD_DATE = '2026-08-25'
NEW_DATE = '2026-08-07'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Сделка оформлена 7 августа 2026 года через покупку юридического'
    ' лица ООО «Фипс», на балансе которого находится объект (не'
    ' прямая покупка недвижимости, а покупка держателя актива).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['law']['struct'] == OLD_LAW_STRUCT

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)

    if write:
        deal['date'] = NEW_DATE
        deal['law']['struct'] = NEW_LAW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
