# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g383b170f` («ГК Bergauf купила у финской Kiilto заводы по производству
клея и сухих смесей», октябрь 2022, Закрыта) — `eco.context` был
заглушкой («—»), хотя дальнейшая судьба заводов легко находится.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kesto.ru/news/prodolzhaya-istoriyu/: «Право собственности на АО
  «Киилто-Клей», ООО «Киилто Фэмили» и ООО «Киилто-Клей Раменское»
  перешло к Bergauf Group 26 октября 2022 года»; «Мы взяли одно из
  прежних названий бренда, под которым когда-то компания Kiilto начала
  производство в России. Kesto в переводе с финского языка значит
  «продолжительность»»; «Продукция под брендом Kiilto Pro будет
  доступна на российском рынке в течение переходного периода, а до
  конца 2022 года произойдет смена юридических наименований компаний
  Kiilto Group»;
- stroymat.ru/2022/12/01/bergauf-kiillto-2022/: «продукция производится
  на двух собственных предприятиях: заводе по производству клеев в г.
  Раменское и заводе сухих строительных смесей в г. Малоярославец»; «все
  рабочие места сотрудников сохранены с соблюдением Трудового кодекса
  РФ».

НЕ ВНЕСЕНО: (1) сумма сделки — не нашлась ни в одном источнике,
включая собственные материалы Kiilto (её финская материнская компания
частная и финансовое влияние сделки не публикует); (2) юридические/
финансовые консультанты — ни один из проверенных источников их не
называет; (3) финансовые показатели завода за 2022-2024 годы —
найдена только выручка за 2021 год из вторичного агрегатора без
прямой проверяемой цитаты, не вносится.

Запуск: python3 pipeline/fix_bergauf_kiilto_kesto_rebrand.py
        python3 pipeline/fix_bergauf_kiilto_kesto_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g383b170f'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Право собственности на заводы перешло к Bergauf Group 26 октября '
    '2022 года, а юридические наименования были заменены до конца того '
    'же года. Новый бренд — «Кесто» (по-фински «продолжительность»): так '
    'называлась продукция Kiilto, когда компания только начинала '
    'производство в России. Заводы — клеевой в Раменском и сухих '
    'строительных смесей в Малоярославце — продолжают работать.'
)

OLD_SRC = [['Деловой квартал', 'https://www.dk.ru/news/237176012']]
NEW_SRC = OLD_SRC + [
    ['Kesto', 'https://kesto.ru/news/prodolzhaya-istoriyu/'],
    ['Stroymat.ru', 'https://stroymat.ru/2022/12/01/bergauf-kiillto-2022/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
