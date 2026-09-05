# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `ge29c8b25`
(«Фонд НТИ вложил 325 млн рублей в Medical Visual Systems», декабрь
2022) — статус «Обсуждается» держался почти 4 года, хотя сам источник
карточки (Vademecum) уже описывал сделку как свершившийся факт, а не
намерение.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kamaflow.com/ru/post/developer-smart-operating-systems-mvs-attracted-325-million-rubles-kama-flow/:
  «Российский разработчик программно-аппаратных комплексов для
  телемедицины Medical Visual Systems (MVS, ООО "Медицинские системы
  визуализации", резидент Сколково) закрыл инвестиционный раунд на 325
  млн рублей, инвестором выступил Венчурный фонд Национальной
  технологической инициативы под управлением инвестиционной компании
  Kama Flow.» — прямое подтверждение закрытия раунда словом «закрыл»
  (само название статьи инвестора — «...MVS привлек 325 млн рублей от
  KAMA FLOW» — тоже подтверждает завершение сделки словом «привлек»);
- vademec.ru/news/2025/06/19/rfpi-i-uk-pervaya-investiruyut-1-mlrd-rubley-v-medical-visual-systems/:
  «РФПИ и УК «Первая» на ПМЭФ-2025 подписали соглашение о направлении 1
  млрд рублей в развитие компании»; «учредителями ООО «Медицинские
  системы визуализации» являются Андрей Кобец (71,48%), Кирилл
  Запутряев (11%) и Андрей Лукьянов (0,83%)»; «В 2024 году выручка
  компании составила 1,2 млрд рублей, чистая прибыль – 228,3 млн
  рублей»; «Инвестиции позволят MVS запустить производство
  эндоскопической стойки под российским брендом TMG» и «выйти со своими
  продуктами на рынок Индии, Казахстана и других стран БРИКС».

НЕ ВНЕСЕНО: (1) точная доля структуры Kama Flow (КФ Венчурс) в капитале
компании — в проверенных источниках не названа прямо, только выводится
арифметически (сумма именных долей 83,31%); (2) судьба продукта Medikt
(мультимедийная библиотека операций) — в материале 2025 года не
упоминается вовсе, отдельно не проверялось; (3) дата сделки не
уточняется: единственная найденная дата («21 декабря 2022») — это дата
ПУБЛИКАЦИИ статьи на kamaflow.com, а не обязательно дата закрытия
раунда — переносить её в поле `date` не стал (см. правило CLAUDE.md
«Дата публикации статьи — не дата сделки»).

Запуск: python3 pipeline/fix_mvs_kamaflow_closed_and_2025_round.py
        python3 pipeline/fix_mvs_kamaflow_closed_and_2025_round.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge29c8b25'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_ECO_CONTEXT = (
    'Венчурный фонд НТИ запущен РВК в 2018 году при участии Инфрафонда '
    'РВК. Им управляет частная инвестиционная компания Kama Flow, фонд '
    'вкладывается в российские deep tech проекты на ранних стадиях.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В июне 2025 года компания привлекла ещё 1 млрд '
    'рублей от РФПИ и УК «Первая» — на запуск производства '
    'эндоскопической стойки под брендом TMG и выход на рынки Индии, '
    'Казахстана и других стран БРИКС. По итогам 2024 года выручка '
    'компании составила 1,2 млрд рублей, чистая прибыль — 228,3 млн '
    'рублей.'
)

OLD_SRC = [['Vademecum', 'https://vademec.ru/news/2022/12/21/fond-nti-vlozhil-325-mln-rubley-v-razrabotchika-tsifrovykh-operatsionnykh-mvs/']]
NEW_SRC = OLD_SRC + [
    ['Kama Flow', 'http://kamaflow.com/ru/post/developer-smart-operating-systems-mvs-attracted-325-million-rubles-kama-flow/'],
    ['Vademecum', 'https://vademec.ru/news/2025/06/19/rfpi-i-uk-pervaya-investiruyut-1-mlrd-rubley-v-medical-visual-systems/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
