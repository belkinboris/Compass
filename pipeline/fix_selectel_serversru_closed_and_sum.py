# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g37737226
(Selectel покупает облачного провайдера servers.ru) — карточка держала
статус «Обсуждается» (только ходатайство в ФАС), хотя сделка закрылась
в тот же день, которым датирована сама карточка.

Проверено лично прямым WebFetch. Официальный пресс-релиз Selectel
(16.12.2024, selectel.ru): «Selectel... сообщает о приобретении 100%
компании ООО "Единая сеть"» — сумму сделки релиз не раскрывает.
Независимая оценка (runet.news, 16.12.2024): «Сумма сделки не превысит
3,1 млрд руб.» — та же цифра, что уже стояла в карточке как «(по
оценке)», подтверждена независимо.

`status`: «Обсуждается» → «Закрыта». `eco.context` (стоял прочерком)
дополнен фактом о сохранении брендов и влиянии сделки на выручку
Selectel: «После сделки компании продолжат поддержку продуктов и
привычных для клиентов сервисов в обычном режиме» (пресс-релиз
Selectel) — ребрендинга не произошло. Дальнейший рост: «Прирост
выручки составил 39% год к году и включает эффект от приобретения
компании Servers.ru, консолидированной в периметр Группы в конце 2024
года» (пресс-релиз Selectel об итогах 2025 года) — без отдельной
цифры вклада именно Servers.ru.

НЕ ВКЛЮЧЕНО: более детальная структура платежа (базовый + earn-out,
1,945 + 1,1 млрд ₽ по данным TAdviser) — страница TAdviser недоступна
напрямую (404 при прямом WebFetch, только через поисковую выдачу),
подтвердить дословной цитатой из первоисточника не удалось; top-level
`sum` остаётся с уже стоявшей и независимо подтверждённой оценкой
«не более 3,1 млрд ₽».

Запуск: python3 pipeline/fix_selectel_serversru_closed_and_sum.py
        python3 pipeline/fix_selectel_serversru_closed_and_sum.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g37737226'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Бренды сохранены: «После сделки компании продолжат поддержку '
    'продуктов и привычных для клиентов сервисов в обычном режиме» '
    '(пресс-релиз Selectel, 16 декабря 2024 года). Год спустя: «Прирост '
    'выручки составил 39% год к году и включает эффект от приобретения '
    'компании Servers.ru, консолидированной в периметр Группы в конце '
    '2024 года» (пресс-релиз Selectel об итогах 2025 года).'
)

NEW_SRC = [
    ['Selectel', 'https://selectel.ru/about/newsroom/news/selectel-soobshchaet-o-priobretenii-oblachnogo-provajdera-servers-ru/'],
    ['runet.news', 'https://runet.news/articles/60778'],
    ['Selectel', 'https://selectel.ru/about/newsroom/news/vyruchka-selectel-sostavila-183-mlrd-rublej-po-itogam-2025-goda/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
