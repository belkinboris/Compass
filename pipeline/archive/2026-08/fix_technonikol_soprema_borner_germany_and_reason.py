# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g428f6180
(Технониколь продала европейские активы компании Soprema). Список
проданных активов был НЕПОЛНЫМ — не хватало немецкого завода, о котором
прямо пишет собственный пресс-релиз покупателя. Проверено лично прямым
WebFetch.

1) `extra`/предмет сделки — SOPREMA (собственный пресс-релиз о сделке),
дословно: «die europäischen Werke von Technonicol in Litauen, Italien und
in Deutschland übernommen, darunter auch die Georg Börner Chemisches
Werk» («европейские заводы Технониколь в Литве, Италии и в Германии,
включая завод Georg Börner») — та же сделка, что и уже описанные Италия/
Литва/Латвия/Эстония, только с недостающей Германией. Уточнение
подтверждено независимо изданием ddh.de, чей заголовок прямо называет обе
части одной новостью: «Soprema übernimmt Technonicol-Werke und Börner».
Источник: https://www.soprema.de/presse/soprema-uebernimmt-boerner.html

2) `eco.context` (новое поле) — причина продажи, обе стороны сделки,
mergers.ru, дословно: гендиректор «Технониколь» Игорь Рыбаков — «эта
сделка вынужденная», «наш 20-тилетний поход в Европу могу назвать
неудачным»; совладелец Сергей Колесников — «В условиях текущих
ограничений и давления на российский бизнес деятельность в Европе
приобретает высокорискованный характер. Вероятность изъятия активов
очень высока, более того, такой прецедент произошел в Польше», сделка
завершена «в рекордно короткие сроки — 5 недель».
Источник: https://mergers.ru/news/tehnonikol-zavershila-sdelku-po-prodazhe-evropejskih-aktivov-kompanii-soprema-83717

Туда же — судьба немецкого завода под Soprema: производство остановлено
к концу 2025 года (osthessen-news.de, 15.11.2025, дословно): «die
Herstellung von Bitumenbahnen in Bad Hersfeld zum Jahresende einzustellen»
(«прекращение производства битумных кровельных мембран в Бад-Херсфельде
к концу года»), со «значительным сокращением рабочих мест».
Источник: https://osthessen-news.de/n11784392/boerner-stampft-dachbahnen-produktion-am-standort-ein.html

НЕ включены: независимая оценка суммы сделки — не найдена ни в одном
источнике (единственное число, «€8 млн», — это цена ПОКУПКИ Italiana
Membrane в 2013 году, а не цена этой продажи, для `sum` не годится, родня
уроку CLAUDE.md «Число из подзаголовка о выкупе бизнеса может быть суммой
займа... а не ценой актива»); консультанты сделки — не найдены; единого
холдингового названия для всего проданного бизнеса нет — источники
называют только отдельные юрлица, профиль-предмет заводить не на чем.

Запуск: python3 pipeline/fix_technonikol_soprema_borner_germany_and_reason.py
        python3 pipeline/fix_technonikol_soprema_borner_germany_and_reason.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g428f6180'

OLD_EXTRA = (
    'Сделка по продаже активов Технониколь в Европе компании Soprema. В '
    'состав проданных активов вошли три производственные площадки в '
    'Италии (Italiana Membrane, Eurodue, Imper Italia), завод Mida LT в '
    'Литве и представительства в Латвии и Эстонии.'
)
NEW_EXTRA = (
    'Сделка по продаже активов Технониколь в Европе компании Soprema. В '
    'состав проданных активов вошли три производственные площадки в '
    'Италии (Italiana Membrane, Eurodue, Imper Italia), завод Mida LT в '
    'Литве, представительства в Латвии и Эстонии, а также немецкий завод '
    'Georg Börner Chemisches Werk (Бад-Херсфельд, Гессен).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Причина продажи (mergers.ru): гендиректор «Технониколь» Игорь '
    'Рыбаков — «эта сделка вынужденная», «наш 20-тилетний поход в Европу '
    'могу назвать неудачным»; совладелец Сергей Колесников — «В условиях '
    'текущих ограничений и давления на российский бизнес деятельность в '
    'Европе приобретает высокорискованный характер. Вероятность изъятия '
    'активов очень высока, более того, такой прецедент произошел в '
    'Польше», сделка завершена «в рекордно короткие сроки — 5 недель». '
    'Судьба немецкого завода: производство остановлено к концу 2025 '
    'года — «прекращение производства битумных кровельных мембран в '
    'Бад-Херсфельде к концу года», со значительным сокращением рабочих '
    'мест (osthessen-news.de, 15.11.2025).'
)

NEW_SRC = [
    ['soprema.de', 'https://www.soprema.de/presse/soprema-uebernimmt-boerner.html'],
    ['mergers.ru', 'https://mergers.ru/news/tehnonikol-zavershila-sdelku-po-prodazhe-evropejskih-aktivov-kompanii-soprema-83717'],
    ['osthessen-news.de', 'https://osthessen-news.de/n11784392/boerner-stampft-dachbahnen-produktion-am-standort-ein.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
