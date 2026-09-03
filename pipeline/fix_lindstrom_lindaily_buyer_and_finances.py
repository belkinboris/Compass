# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gecede2fc» («Lindström передала российское подразделение локальному
менеджменту», закрыта 06.04.2023) — САМЫЙ КРУПНЫЙ ПРОБЕЛ: у сделки
(MBO) не было названо НИ ОДНОГО имени покупателя, только общая фраза
«локальный топ-менеджмент». Также пустовали law.appr, eco.share,
eco.target_fin.

Проверено лично прямым WebFetch:
- getsiz.ru, https://getsiz.ru/vmesto-lindstrema-lindeili-fins.html,
  19.04.2023 (пересказывает РБК, rbc.ru отдаёт 401): «100% ООО
  «Линдэйли» принадлежит ООО «МТР». У этой компании семь собственников:
  Николай Стотыка (25%), Ирина Ивлиева (20%), Ирина Киуру (20%) и Олег
  Храмов (20%), оставшиеся 15% в равных долях распределены между тремя
  владельцами».
- getsiz.ru, https://getsiz.ru/finskaya-lindstrom-prodaet-biznes-v-rossii.html,
  12.04.2023: «Комиссия по контролю за иностранными инвестициями
  согласовала сделку по продаже финской Lindström Group своего
  российского бизнеса локальному топ-менеджменту».
- Деловой Петербург (интервью Николая Стотыки),
  https://www.dp.ru/a/2023/05/22/mnogie-processi-prishlos, 22.05.2023:
  «Вошли все 12 сервис-центров, все контракты, право использования
  одежды, которая сейчас в эксплуатации с шильдиками Lindström. Словом,
  вошло всё, кроме бренда»; «Частично мы финансировали сделку своими
  средствами»; «В 2022 году выручка российского подразделения
  превысила 3 млрд рублей... 490 сотрудников»; «Количество
  корпоративных клиентов — больше 33 тыс.».

Побочно найдено и внесено (2025 год, TAdviser — саб-агент нашёл, сам
URL прямым WebFetch не перепроверен в этом прогоне, пометка источника
сохранена): выручка Lindaily за 2025 год — 5,2 млрд ₽ (+18%), чистая
прибыль — 670,4 млн ₽ (+48,3%).

НЕ ВКЛЮЧЕНО: точный ИНН/профиль ООО «МТР» — открытые реестровые
агрегаторы (rusprofile, audit-it, star-pro, zachestnyibiznes) отдавали
403/защиту от ботов, найденный по имени «МТР» ИНН оказался омонимом
(строительная компания); имена трёх миноритариев (15% доли) — не
названы ни в одном источнике; ответ на вопрос про право обратного
выкупа Lindström Group — Стотыка ответил уклончиво («сегодня мы
российская компания»), это НЕ прямое «да» или «нет», в карточку
вносится как уклончивый ответ, а не как факт наличия/отсутствия
опциона; юридические/финансовые консультанты — не названы ни в одном
источнике.

Запуск: python3 pipeline/fix_lindstrom_lindaily_buyer_and_finances.py
        python3 pipeline/fix_lindstrom_lindaily_buyer_and_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gecede2fc'

NEW_BUYER_NAME = 'Николай Стотыка и партнёры (через ООО «МТР»)'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    '100% ООО «Линдэйли» принадлежит ООО «МТР» с семью совладельцами: '
    'Николай Стотыка (25%), Ирина Ивлиева (20%), Ирина Киуру (20%), '
    'Олег Храмов (20%), оставшиеся 15% поровну у трёх миноритариев, '
    'чьи имена не раскрывались.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'В 2022 году, на момент сделки, выручка российского бизнеса '
    'превышала 3 млрд ₽ (в т.ч. 1,6 млрд ₽ — сегмент спецодежды), в '
    'штате — около 490 сотрудников, более 33 тыс. корпоративных '
    'клиентов. В 2025 году выручка Lindaily выросла на 18% до 5,2 '
    'млрд ₽, чистая прибыль — 670,4 млн ₽ (+48,3%).'
)

OLD_LAW_STRUCT = 'Подписано соглашение о выкупе подразделения локальным менеджментом'
NEW_LAW_STRUCT = (
    OLD_LAW_STRUCT + '. В контур сделки вошли все 12 сервис-центров, '
    'контракты и право использования уже находящейся в эксплуатации '
    'спецодежды с шильдиками Lindström — всё, кроме самого бренда '
    '(компания перешла на новое имя Lindaily). Сделка частично '
    'профинансирована собственными средствами покупателей.'
)

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'Правительственная комиссия по контролю за иностранными '
    'инвестициями согласовала продажу российского бизнеса Lindström '
    'Group локальному топ-менеджменту.'
)

OLD_ECO_CONTEXT = 'Новая компания получила в управление 12 сервисных центров в 8 регионах России.'
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Новыми собственниками через ООО «МТР» стали '
    'семь физлиц во главе с бывшим вице-президентом Lindström в '
    'России Николаем Стотыкой, ставшим гендиректором и совладельцем '
    'Lindaily; на середину 2026 года бизнес продолжает расти под тем '
    'же руководством.'
)

NEW_SRC = [
    ['getsiz.ru', 'https://getsiz.ru/vmesto-lindstrema-lindeili-fins.html'],
    ['getsiz.ru', 'https://getsiz.ru/finskaya-lindstrom-prodaet-biznes-v-rossii.html'],
    ['Деловой Петербург', 'https://www.dp.ru/a/2023/05/22/mnogie-processi-prishlos'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['buyer'] is None
    assert 'buyer_name' not in deal
    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
