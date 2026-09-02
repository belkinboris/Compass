# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g3e7bc840
(«Russ Outdoor приобрела Gallery (ООО «Медиа-1 Аутдор»)», закрыта
1 июня 2023) — продавец не был назван, оценка сделки отсутствовала, а
`extra` дословно дублировал `law.appr` (плюс нёс служебную скобку
разбора «(ФАС согласовала сделку (антимонопольный надзор))» — тот же
класс дефекта, что уже описан в CLAUDE.md: «Один и тот же текст лежит
в двух полях» и утечка служебного тега в текст для читателя).

Проверено лично прямым WebFetch (Ведомости,
https://www.vedomosti.ru/media/articles/2023/06/23/982081-russ-outdoor-gallery):
«Единственным владельцем головной структуры Gallery – ООО «Гэллари
сервис»... является ООО «Медиа-1 Аутдор»»; «Его конечным бенефициаром
является инвесткомпания Kismet Capital Group, принадлежащая Ивану
Таврину».

Проверено лично прямым WebFetch (ADPASS,
https://adpass.ru/naruzhnyj-reklamnyj-alyans-chto-izmenitsya-posle-obedineniya-russ-outdoor-i-gallery/):
«Справедливая стоимость Gallery находится в диапазоне 1,5-2 годовых
выручек или примерно 7-10 млрд рублей» (Сергей Либин, Газпромбанк);
«консервативной оценкой будут $100 млн или 8 млрд рублей» (Илья
Хоффман, VDI Group). Сумма самой сделки нигде не раскрыта — обе
цифры это независимые оценки, не факт сделки, `sum`/`eco.sum`
остаются «Не раскрыта».

НЕ ВКЛЮЧЕНО: консультанты сделки — ни в одном из девяти прочитанных
источников (Интерфакс, Ведомости, Sostav, AdIndex, ADPASS, vc.ru) не
названы; названные там люди (Либин, Хоффман) — независимые аналитики-
оценщики, а не консультанты сделки. Предыдущая продажа Gallery Ивану
Таврину (2018 год, у Baring Vostok) — это ИСТОРИЯ владения предметом
ДО этой сделки, не относится к её собственным полям.

Запуск: python3 pipeline/fix_russ_outdoor_gallery_seller_and_value.py
        python3 pipeline/fix_russ_outdoor_gallery_seller_and_value.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3e7bc840'

OLD_EXTRA = (
    'ФАС России провела антимонопольный анализ и разрешила приобретение. '
    'Покупатель ООО «Стинн» (91,9% владелец Russ Outdoor) принял '
    'добровольные обязательства: не повышать цены на рекламные услуги до '
    'конца 2023 года, разработать информацию о подходах к ценообразованию '
    'в течение квартала, установить цифровые билборды в городах с '
    'населением менее 500 тыс. человек. ФАС установила, что сделка не '
    'повлияет на конкуренцию, так как наружная реклама составляет ~8% '
    'единого рынка рекламы. (ФАС согласовала сделку (антимонопольный '
    'надзор))'
)
NEW_EXTRA = (
    'До сделки Gallery принадлежала холдингу «Медиа 1»: единственным '
    'владельцем головной структуры, ООО «Гэллари сервис», было ООО '
    '«Медиа-1 Аутдор», конечный бенефициар — инвесткомпания Kismet '
    'Capital Group Ивана Таврина. Сумму сделки стороны не раскрыли; '
    'независимые аналитики оценивали Gallery в 7–10 млрд ₽ (Сергей '
    'Либин, Газпромбанк) и около 8 млрд ₽ (Илья Хоффман, VDI Group). '
    'ФАС России провела антимонопольный анализ и разрешила приобретение. '
    'Покупатель ООО «Стинн» (91,9% владелец Russ Outdoor) принял '
    'добровольные обязательства: не повышать цены на рекламные услуги до '
    'конца 2023 года, разработать информацию о подходах к ценообразованию '
    'в течение квартала, установить цифровые билборды в городах с '
    'населением менее 500 тыс. человек. ФАС установила, что сделка не '
    'повлияет на конкуренцию, так как наружная реклама составляет ~8% '
    'единого рынка рекламы.'
)

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Независимые оценки (сама сумма сделки не раскрыта): 7–10 млрд ₽ '
    '(Сергей Либин, Газпромбанк) и около 8 млрд ₽ / $100 млн (Илья '
    'Хоффман, VDI Group).'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/media/articles/2023/06/23/982081-russ-outdoor-gallery'],
    ['ADPASS', 'https://adpass.ru/naruzhnyj-reklamnyj-alyans-chto-izmenitsya-posle-obedineniya-russ-outdoor-i-gallery/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal.get('seller') is None

    new_src = deal['src'] + NEW_SRC

    print('=== seller: станет ===')
    print('ООО «Медиа-1 Аутдор» (Kismet Capital Group / Иван Таврин)')
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = 'ООО «Медиа-1 Аутдор» (Kismet Capital Group / Иван Таврин)'
        deal['seller_src'] = 'text'
        deal['eco']['val'] = NEW_ECO_VAL
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
