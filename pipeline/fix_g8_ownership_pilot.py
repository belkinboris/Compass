# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md): первый пилот блока «Собственники» на странице
компании — по просьбе владельца (9 августа): «Собственники: Яндекс,
Сбербанк, NexTouch» у TAdviser, у нас поле `ownership` было пустым у ВСЕХ
1872 профилей. Инфраструктура (схема поля, рендер в `renderCompany()`)
сделана вместе с этим скриптом; сам скрипт наполняет ДВУХ пилотных
кандидатов — не массовую кампанию, чтобы сначала проверить, что схема и
рендер работают на настоящих данных, прежде чем разворачивать шире.

Схема: `company.ownership` — список объектов `{name, id, share, as_of,
source}`. `id` — ссылка на профиль владельца в COMPANIES, если у него
есть свой профиль (иначе null — просто имя текстом, как у физлица).
`as_of` — дата источника с точностью до месяца («YYYY-MM»), а не вечная
истина: владение меняется, и это явно написано на экране рядом с блоком
(тот же принцип, что уже применён к `holding`/«Контроль у»).

Оба кандидата — компании, чью структуру собственности этот же прогон уже
прочитал и процитировал дословно на карточках СДЕЛОК (см. журнал G5),
источники уже в кэше:

  gfd143c7d («ООО «Наш Союз»», элеватор) — 100% выкуплены «Деметра-
  Холдингом» в октябре 2024 (poleinvest.ru, уже в src карточки gc10da566).

  g6f7fd542 («Компании, владеющие отелем Baikal View») — 86,38% у группы
  «Русские фонды», 13,62% остались у прежнего совладельца Марины
  Улахановой (Коммерсантъ, 25.09.2023, уже в src карточки g778efcb9).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KOMMERSANT_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6236835']
POLEINVEST_SRC = ['Поле.рф', 'https://xn--e1alid.xn--p1ai/journal/publication/'
                  'demetra-treiyding-priobrel-elevator-nash-souz-v-orlovskoiy-oblasti']

OWNERSHIP = {
    'gfd143c7d': [
        dict(name='Деметра-Холдинг', id='g519f8484', share='100%',
             as_of='2024-10', source=POLEINVEST_SRC),
    ],
    'g6f7fd542': [
        dict(name='Группа «Русские фонды»', id='gc4c70e0f', share='86,38%',
             as_of='2023-08', source=KOMMERSANT_SRC),
        dict(name='Марина Улаханова', id=None, share='13,62%',
             as_of='2023-08', source=KOMMERSANT_SRC),
    ],
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for cid, ownership in OWNERSHIP.items():
        assert cid in companies, f"нет профиля {cid}"
        assert 'ownership' not in companies[cid], f"{cid} уже несёт ownership"
        print(f"{cid} ({companies[cid]['name']}): += ownership")
        for o in ownership:
            print(f"    {o['name']} — {o['share']} (на {o['as_of']})")
        companies[cid]['ownership'] = ownership

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
