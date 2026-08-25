# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ga7298401 («Медскан»
привлечение инвестиций перед IPO): дельта-поиск нашёл, что закрытая
подписка, о которой карточка знала только как о планах осени 2025 года,
реально ЗАВЕРШИЛАСЬ в феврале 2026 года (доля «Росатома» размылась до
45,1%), деньги пошли на выкуп доли Сбербанка в «Медскан Лаб» (KDL), а
годовые итоги 2025 года уже вышли и отличаются от прежнего прогноза. Не
через review.py: комбинация фактов из ТРЁХ новых источников (ng.ru,
kommersant.ru/doc/8463640, akm.ru) в двух разных полях.

ВАЖНО: кто именно купил акции допэмиссии — не называется ни в одном
источнике; слух про Газпромбанк относится к ДРУГОЙ карточке (g2197ed53) и
сюда не переносится.

Запуск: python3 pipeline/fix_medskan_ipo_investor_context_extend.py
        python3 pipeline/fix_medskan_ipo_investor_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga7298401'

OLD_CONTEXT = (
    'Сейчас там 50% — у «Росатома» и столько же — у Евгения Туголукова. '
    'Осенью «Медскан» утвердил размещение 17,27 млн акций по закрытой '
    'подписке по цене 296,87 руб. за бумагу, говорится в документах '
    'компании. Таким образом, «Медскан» намеревается привлечь 5,1 млрд руб.'
)

CONTEXT_ADDITION = (
    ' Сделка завершилась в феврале 2026 года: доля «Росатома» в результате '
    'размылась с 50% до 45,1%. В октябре 2025 года «Медскан» выкупил у '
    '«Сбербанк инвестиции» 39% в капитале ООО «Медскан Лаб» (управляет '
    'сетью лабораторий KDL) за 4,8 млрд руб. IPO компания планирует на '
    'сентябрь 2026 года, оценивая готовность примерно в 80%; free-float '
    'после размещения может достичь 15%.'
)

NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

OLD_TARGET_FIN = (
    'Как ожидается, выручка «Медскана» по итогам 2025 года вырастет на '
    '17%, до 33 млрд руб., EBITDA — на 28%, сообщил в эфире Евгений '
    'Туголуков. Количество новых пациентов, по его словам, увеличится на '
    '11%, до 7,7 млн.'
)

TARGET_FIN_ADDITION = (
    ' По итогам 2025 года фактическая выручка выросла на 16%, до 32,6 '
    'млрд руб. (с 28 млрд руб.), EBITDA — на 28%, до 5 млрд руб. (с 3,9 '
    'млрд руб.), а чистый убыток по МСФО составил 3,3 млрд руб. против '
    '1,3 млрд руб. годом ранее.'
)

NEW_TARGET_FIN = OLD_TARGET_FIN + TARGET_FIN_ADDITION

NEW_SRC = [
    ['ng.ru', 'https://www.ng.ru/economics/2026-04-27/100_212326042026.html'],
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8463640'],
    ['akm.ru', 'https://www.akm.ru/news/chistyy_ubytok_gk_medskan_po_msfo_za_2025_god_sostavil_bolee_3_mlrd_rub/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context изменился с момента чтения — проверьте'
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, 'eco.target_fin изменился с момента чтения — проверьте'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print()
    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print()
    print('=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
