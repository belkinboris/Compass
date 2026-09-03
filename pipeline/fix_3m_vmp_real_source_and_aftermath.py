# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g81163284 («3M продала российские заводы по производству респираторов
и антикоррозийных покрытий», закрыта 2 июня 2023) — единственный
источник был голой ссылкой на Telegram-агрегатор (t.me/dealsma/3916),
а не на настоящую публикацию — тот же класс дефекта, что уже описан
в CLAUDE.md («Источник — то, что подтверждает факт, а не то, как о
нём узнали»).

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/6124630): «В июне ООО «3М Волга»
перешло казахстанской Ledvakh Trade, возглавляемой господином
Вахрушевым»; «американская корпорация 3М во втором квартале 2023 года
вышла из российских активов и получила $18 млн прибыли»; оценка
Михаила Бурмистрова (Infoline-Аналитика) — «$20–25 млн без учета
доступа к технологиям и интеллектуальной собственности».

Проверено лично прямым WebFetch (Vademecum,
https://vademec.ru/news/2023/06/07/blizkaya-k-vmp-struktura-kupila-rossiyskiy-zavod-zm/):
«Данные о смене собственника появились в ЕГРЮЛ 2 июня 2023 года»; «В
конце февраля 2023 года АО «ЗМ Россия»... возглавил директор по
правовым вопросам Евгений Богатырев».

Новые, авторитетные источники добавлены К УЖЕ СТОЯЩЕЙ ссылке на
Telegram, а не взамен неё — существующая ссылка не удаляется, только
дополняется более сильными.

НЕ ВКЛЮЧЕНО: переименование ООО «3М Волга» в «ВМП-Алабуга» и планы
инвестиций 250 млн ₽ — эти факты добыты только через реестровые
агрегаторы (checko.ru, saby.ru), которые отдали 403 при прямом
WebFetch, дословная цитата не получена; финансовый и юридический
консультанты сделки — ни в одном из семи прочитанных источников не
названы.

Запуск: python3 pipeline/fix_3m_vmp_real_source_and_aftermath.py
        python3 pipeline/fix_3m_vmp_real_source_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g81163284'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Данные о смене собственника появились в ЕГРЮЛ 2 июня 2023 года. '
    'Во втором квартале 2023 года 3M получила от выхода из российских '
    'активов $18 млн прибыли. Гендиректор «Infoline-аналитики» Михаил '
    'Бурмистров оценивал стоимость предприятий в $20–25 млн без учёта '
    'доступа к технологиям и интеллектуальной собственности.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6124630'],
    ['Vademecum', 'https://vademec.ru/news/2023/06/07/blizkaya-k-vmp-struktura-kupila-rossiyskiy-zavod-zm/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
