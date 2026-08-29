# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g709c335a
(«Ригла» купила аптечные сети «Аптечество» и Farmani, август 2024).
Дельта-поиск нашёл биографию продавца, Юрия Гайсинского, которой в
карточке не было вовсе (только имя текстом), и его дальнейший проект
после продажи. Проверено лично прямым WebFetch
(vademec.ru/news/2025/09/24/yuriy-gaysinskiy-stal-sovladeltsem-kliniki-
fomina-v-nizhnem-novgorode/, 24.09.2025).

«Гайсинский был одним из первых владельцев фармзавода «Нижфарм» после
приватизации» (в 2005 году площадка была выкуплена немецкой Stada). «В
1994 году совместно со своим младшим братом Игорем предприниматель
создал фармдистрибьютора «Фармкомплект»» — этот бизнес Гайсинский не
продавал, он и сейчас в его портфеле («выручка 84,3 млрд рублей» за 2024
год). «В августе 2024 года Гайсинский продал розничный актив «Ригле»» —
только розницу («Нижегородская аптечная сеть» с брендами «Аптечество» и
Farmani), не «Фармкомплект». После сделки: «Юрию Гайсинскому перешло во
владение 24,5% ООО «Клиника Фомина Нижний Новгород»», где он выступает
инвестором (сентябрь 2025).

Независимая оценка суммы, консультанты, ребрендинг/закрытие точек под
«Риглой» — дельта-поиск не нашёл ничего сверх уже стоящей в карточке
информации (тот же диапазон 2,2–3,4 млрд ₽ повторяется во всех
источниках без второй независимой цифры).

Запуск: python3 pipeline/fix_rigla_apteczhestvo_gaisinsky_postdeal.py
        python3 pipeline/fix_rigla_apteczhestvo_gaisinsky_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g709c335a'

OLD_CONTEXT = 'Таким образом, общее число аптечных точек компании возросло до 4700.'
CONTEXT_ADDITION = (
    ' Продавец, Юрий Гайсинский, — один из первых владельцев фармзавода '
    '«Нижфарм» после приватизации (в 2005 году выкуплен немецкой Stada) и '
    'основатель фармдистрибьютора «Фармкомплект» (1994 год, вместе с '
    'братом Игорем) — этот бизнес он не продавал, он остаётся в его '
    'портфеле. После сделки, в сентябре 2025 года, «Юрию Гайсинскому '
    'перешло во владение 24,5% ООО «Клиника Фомина Нижний Новгород»», где '
    'он выступает инвестором (vademec.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Vademecum', 'https://vademec.ru/news/2025/09/24/yuriy-gaysinskiy-stal-sovladeltsem-kliniki-fomina-v-nizhnem-novgorode/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
