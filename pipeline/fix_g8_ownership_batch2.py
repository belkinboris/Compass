# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — вторая партия «Собственников», 21 августа
2026. Пилот (партия 1, `fix_g8_ownership_pilot.py`) проверил схему и
рендер на двух профилях; эта партия — первое расширение по ДЕШЁВОМУ
источнику: закрытые M&A-сделки, у которых уже есть `buyer`/`target` с
профилями и текст самой карточки называет долю. Новых WebFetch/WebSearch
не потребовалось — все факты уже дословно лежат в `eco.share`/`extra`/
`law.struct` этих же карточек, обогащённых в прошлых прогонах.

ЗАМЕР И ЕГО ГРАНИЦА. Механический поиск «единственный % в тексте
закрытой M&A-карточки с обоими профилями» дал 221 кандидата — но
проверка первых 25 вручную показала: доля кандидатов, где найденный %
был ЛОЖНЫМ (относился не к доле покупателя в предмете, а к чему-то
другому — доле в СП самого покупателя, голосам на собрании акционеров,
приросту цены, доле продавца ДО сделки, доле, доставшейся физлицу-
основателю, а не компании-покупателю), — БОЛЬШЕ ПОЛОВИНЫ (13 из 25).
Правило «один % в тексте = доля покупателя» механически неверно
чаще, чем верно, — это ожидаемо: ровно та же ловушка, что уже описана
в CLAUDE.md («Разбор источника доверяет числу из чужого абзаца» и
родственные уроки), только на уровне процента, а не суммы. Каждая из 12
записей ниже прочитана и проверена вручную — % относится ИМЕННО к
доле покупателя в предмете сделки, дословно.

ПОПУТНО НАЙДЕНЫ ДВА ОТДЕЛЬНЫХ ДЕФЕКТА КАРТОЧЕК (не эта партия чинит —
записаны в PRODUCT_ROADMAP.md как приоритет):
  g113002a7 — `target` указывает на профиль «КИВИ», а текст карточки
    целиком про покупку Альфа-Банком ДРУГОЙ компании — «Флоктори»
    (Flocktory); похоже на спутанную ссылку.
  g2d69802d — `extra` называет предметом «ТД «Алтан»», а `target`
    карточки — профиль «Granmulino»; тоже похоже на несовпадение.
Остаток из 221 (после вычета уже проверенных 25 и найденных дефектов)
не пройден — задача для будущих прогонов, партиями по 20-25 с тем же
ручным чтением, а не автоматической записью.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (target_id, buyer_id, share, as_of, source)
ENTRIES = [
    ('g7bbe19c2-target', 'gb396abf4', '100%', '2026-05',
     ['Деловой Петербург', 'https://www.dp.ru/a/2026/04/29/gruppa-lsr-priobrela-otel']),
    ('g83d157e5', 'g59be6698', '100%', '2026-06',
     ['publish.ru', 'https://www.publish.ru/news/202606_20099303']),
    ('gec42121d', 'gb700e4d9', '100%', '2026-02',
     ['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/02/19/1177723-gruppa-arnest-vikupila']),
    ('gd5d02d09', 'g4a74dc09', '100%', '2024-01',
     ['Интерфакс', 'https://www.interfax.ru/business/941116']),
    ('g42a4ea0b', 'g98105961', '100%', '2023-03',
     ['Nokian Tyres (официальный сайт — inside information)',
      'https://www.nokiantyres.com/company/news-article/inside-information-nokian-tyres-plc-to-sell-its-operations-in-russia/']),
    ('g421d113d', 'g8a40b833', '100%', '2022-06',
     ['Интерфакс', 'https://www.interfax.ru/business/853903']),
    ('g8cff91963', 'gc9913f2a', '96%', '2025-12',
     ['Интерфакс', 'https://www.interfax.ru/business/1063509']),
    ('g849d19d0', 'gb6301f1c', '100%', '2025-06',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7796300']),
    ('g33c71ec5', 'gf9d213b7', '100%', '2022',
     ['RB.ru', 'https://rb.ru/news/megafon-onefactor/']),
    ('g9e385bc6', 'ga2cfae5b', '80%', '2025-09',
     ['АБН', 'https://abn.agency/2025/09/16/alfa-bank-stal-mazhoritarnym-vladelczem-servisa-analitiki-dlya-prodavczov-marketplejsov/']),
    ('gd1907243', 'g34ab1e65', '70%', '2025-07',
     ['@dealsma (Telegram)', 'https://t.me/dealsma/7219']),
    ('g52e854a8', 'g710d8647', '100%', '2025-06',
     ['Nec.pro', 'https://www.nec.pro/press/news/elektroshchit-k-voshel-v-sostav-promyshlennoy-gruppy-nek/']),
    ('g4f542f90', 'gfe425e93', '20%', '2026-04',
     ['Forbes', 'https://www.forbes.ru/svoi-biznes/559540-zavarili-sdelku-fond-vostok-investicii-kupil-20-obzarsika-tasty-coffee']),
]


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for target_id, buyer_id, share, as_of, source in ENTRIES:
        assert target_id in companies, f"нет профиля {target_id}"
        assert buyer_id in companies, f"нет профиля {buyer_id}"
        assert 'ownership' not in companies[target_id], \
            f"{target_id} уже несёт ownership"
        entry = dict(name=companies[buyer_id]['name'], id=buyer_id,
                     share=share, as_of=as_of, source=source)
        print(f"{target_id} ({companies[target_id]['name']}): "
              f"+= {entry['name']} — {share} (на {as_of})")
        companies[target_id]['ownership'] = [entry]

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
