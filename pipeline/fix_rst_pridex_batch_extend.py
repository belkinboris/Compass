# -*- coding: utf-8 -*-
"""Дневная очередь (первый полный обыск), две карточки от 24 августа
2026:

- gb9a22f5f («Русский Стандарт водка» продаёт офисно-складской
  комплекс): realty.ria.ru (независимый источник вместо dp.ru) дал
  принадлежность к холдингу «Руст» Рустама Тарико — продлевает
  `law.struct`.
- ge283bafc (Pridex/Multispace): CRE.ru (независимый источник вместо
  РИА Недвижимость/@dealsma) дал более конкретную формулировку причины
  продажи от управляющего партнёра Pridex — продлевает `eco.rationale`.

Не через `review.py`: источники новые, не образуют с уже записанным
текстом непрерывный кусок.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://realty.ria.ru/20260824/torgi-2112767244.html
https://cre.ru/news/105717

Запуск: python3 pipeline/fix_rst_pridex_batch_extend.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

RST_ID = 'gb9a22f5f'
RST_OLD_STRUCT = (
    'По данным "ДП", недвижимость принадлежит ООО "Русский Стандарт '
    'Водка" (РСВ) и заложена в ООО "КБ "Ростфинанс" и АО "Датабанк". '
    'Здание частично арендовано "Руст Инкорпорэйтэд".'
)
RST_STRUCT_ADDITION = (
    ' Компания "Русский стандарт водка" входит в холдинг "Руст" '
    'бизнесмена Рустама Тарико, являющийся одним из крупнейших '
    'производителей водки в мире.'
)
RST_NEW_STRUCT = RST_OLD_STRUCT + RST_STRUCT_ADDITION

PRIDEX_ID = 'ge283bafc'
PRIDEX_OLD_RATIONALE = (
    'Pridex закрыл сделку по продаже сети сервисных офисов Multispace. '
    'Транзакция реализована в рамках долгосрочной стратегии развития '
    'компании. Новым владельцем Multispace стала группа '
    'профессиональных частных инвесторов. Сеть продолжит '
    'функционировать в нормальном режиме и выполнять свои обязательства '
    'перед резидентами и партнерами'
)
PRIDEX_RATIONALE_ADDITION = (
    '. По словам управляющего партнера и коммерческого директора '
    'Pridex Александра Алейникова, полученная экспертиза помогла '
    'компании перейти к следующему этапу — масштабированию комплексной '
    'реализации офисных проектов: от разработки концепции и '
    'проектирования до строительства и технологического оснащения.'
)
PRIDEX_NEW_RATIONALE = PRIDEX_OLD_RATIONALE + PRIDEX_RATIONALE_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    rst = by_id[RST_ID]
    pridex = by_id[PRIDEX_ID]

    assert rst['law']['struct'] == RST_OLD_STRUCT, \
        f"{RST_ID} law.struct: неожиданное значение {rst['law']['struct']!r}"
    assert pridex['eco']['rationale'] == PRIDEX_OLD_RATIONALE, \
        f"{PRIDEX_ID} eco.rationale: неожиданное значение {pridex['eco']['rationale']!r}"

    print(f'{RST_ID} law.struct: += принадлежность холдингу «Руст»')
    print(f'{PRIDEX_ID} eco.rationale: += формулировка причины продажи '
          f'(Алейников)')

    if write:
        rst['law']['struct'] = RST_NEW_STRUCT
        rst.setdefault('src', [])
        entry = ['realty.ria.ru', 'https://realty.ria.ru/20260824/torgi-2112767244.html']
        if entry not in rst['src']:
            rst['src'].append(entry)

        pridex['eco']['rationale'] = PRIDEX_NEW_RATIONALE
        pridex.setdefault('src', [])
        entry2 = ['CRE.ru', 'https://cre.ru/news/105717']
        if entry2 not in pridex['src']:
            pridex['src'].append(entry2)

        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
