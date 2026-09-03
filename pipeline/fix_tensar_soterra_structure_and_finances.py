# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g930db872` («Tensar продала завод в Петербурге предпринимателю Олегу
Волоховичу», закрыта 14.01.2023) — не заполнены финансы предмета,
структура сделки и судьба бренда после продажи.

Проверено лично прямым WebFetch:
- Ведомости.Северо-Запад,
  https://spb.vedomosti.ru/business/articles/2023/01/12/958787-amerikanskaya-tensar-lishilas-zavoda,
  12.01.2023: завод производит «геосинтетические материалы для
  дорожного строительства, в частности, георешетки»; выручка 2021 года
  — 709,5 млн ₽, в 2022 году — «превысила 1 млрд руб.»; «здесь
  трудоустроены 65 человек»; «Объем инвестиций в новое предприятие
  оценивался более чем в 1 млрд руб.».
- Soterra.ru (сайт правопреемника),
  https://soterra.ru/news/rossiyskiy-biznesmen-vykupil-dolyu-inostrannykh-partnerov-v-kompanii-tensar/,
  12.01.2023: «Первым этапом сделки стал выкуп Олегом Волоховичем доли
  кипрской компании, владеющей 100% ООО «Тенсар Инновэйтив
  Солюшнз»... В последующем планируется перевод бизнеса в российскую
  юрисдикцию»; «В соглашении присутствует пункт о возможности
  обратного выкупа доли прежними владельцами»; «ООО «Сотерра
  Инжиниринг» полностью сохраняет методы производства, технологии,
  номенклатуры, материалы и проектные решения», а также «возьмет на
  себя все текущие активы, пассивы и коммерческие обязательства».

НЕ ВКЛЮЧЕНО: точное число «75%» в текущем `extra` не опровергнуто (речь
может идти о доле, которую Волохович довыкупил сверх уже имевшегося
блокирующего пакета, до 100%) — не трогаю без дословного подтверждения
из недоступного напрямую источника РБК; согласование ФАС/правкомиссии и
консультанты сделки — ни один источник их не называет; более поздние
финансовые показатели «Сотерра Инжиниринг» (2023-2025) — саб-агент
нашёл их только через реестровые агрегаторы (не дословная цитата
статьи), не вношу без независимой журналистской публикации.

Запуск: python3 pipeline/fix_tensar_soterra_structure_and_finances.py
        python3 pipeline/fix_tensar_soterra_structure_and_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g930db872'

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Завод производит геосинтетические материалы для дорожного '
    'строительства (георешётки). Выручка в 2021 году — 709,5 млн ₽, в '
    '2022 году — более 1 млрд ₽; инвестиции в предприятие превысили 1 '
    'млрд ₽; штат — 65 человек.'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Сделка в два этапа: сначала Волохович выкупил долю в кипрской TR '
    'Holdings Limited (владеет 100% ООО «Тенсар Инновэйтив Солюшнз»), '
    'затем планировался перевод бизнеса в российскую юрисдикцию. В '
    'соглашении есть опцион на обратный выкуп доли прежними '
    'владельцами.'
)

OLD_EXTRA = (
    'Продажа американской компанией Tensar 75% акций TR HOLDINGS '
    'LIMITED (Cyprus), владеющей ООО «Тенсар Инновэйтив Солюшнз». '
    'Покупатель — предприниматель Олег Волохович, ранее блокирующий '
    'акционер.'
)
NEW_EXTRA = (
    OLD_EXTRA + ' Компания продолжила работу под новым брендом '
    '«Сотерра Инжиниринг», сохранив технологии, номенклатуру, '
    'материалы и проектные решения, а также взяв на себя все активы, '
    'пассивы и обязательства прежнего юрлица.'
)

NEW_SRC = [
    ['Ведомости.Северо-Запад', 'https://spb.vedomosti.ru/business/articles/2023/01/12/958787-amerikanskaya-tensar-lishilas-zavoda'],
    ['Soterra.ru', 'https://soterra.ru/news/rossiyskiy-biznesmen-vykupil-dolyu-inostrannykh-partnerov-v-kompanii-tensar/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['extra'] == OLD_EXTRA

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
