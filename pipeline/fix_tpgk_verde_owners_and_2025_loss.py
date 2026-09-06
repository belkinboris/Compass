# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gff984390` («Банк «Траст» продал Тимано-Печорскую газовую компанию
компании «Верде Дженерейшн Инжиниринг»», июнь 2023, Закрыта) — кто
такие совладельцы покупателя и как идут дела у актива после сделки не
прослеживалось.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- bnkomi.ru/data/news/160140/: совладельцы «Верде Дженерейшн
  Инжиниринг» — «Андрей Зозуля (ранее возглавлял компанию Volga Gas), а
  также Кирилл Ратников и Ирина Сметлева» (почти равные доли); компания
  зарегистрирована 15 мая 2023 года; планы — добыча 500 млн куб. м газа
  к 2025 году, 2 млрд куб. м и газохимический комплекс к 2027-му, завод
  СПГ к 2029-му, более 1000 рабочих мест в Коми;
- list-org.com/company/4423988: текущий учредитель — «ООО "ВЕРДЕ
  ДЖЕНЕРЕЙШН ИНЖИНИРИНГ"» (100%); финансовые показатели 2025 года —
  доходы «34 970 000 ₽», расходы «668 997 000 ₽», чистый убыток «678
  558 тыс. руб.» — расходы почти в 20 раз превышают доходы.

НЕ ВНЕСЕНО: планы по добыче и газохимии — заявленные ориентиры компании
на будущее, не факт уже достигнутого; из карточки видно, что реальные
показатели 2025 года (крупный убыток) пока далеки от этих планов —
обе стороны картины (планы и текущий убыток) внесены рядом, без
сглаживания.

Запуск: python3 pipeline/fix_tpgk_verde_owners_and_2025_loss.py
        python3 pipeline/fix_tpgk_verde_owners_and_2025_loss.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gff984390'

OLD_ECO_CONTEXT = (
    'Из-за отсутствия покупателей цена компании постепенно снижалась: '
    'весной 2021 года начальная стоимость на торгах составляла 3,3 млрд '
    '₽, в октябре 2022-го — 2,1 млрд, весной 2023-го — 1,26 млрд ₽.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Совладельцы покупателя — Андрей Зозуля (ранее '
    'возглавлял Volga Gas), Кирилл Ратников и Ирина Сметлева, доли почти '
    'равные; компания рассчитывает нарастить добычу газа и построить '
    'газохимический комплекс и завод СПГ к 2027–2029 годам. Пока эти '
    'планы далеки от исполнения: по итогам 2025 года актив показал '
    'убыток 678,6 млн ₽ при доходах всего 35 млн ₽.'
)

OLD_SRC = [
    ['АК&М', 'https://www.akm.ru/news/trast_prodal_timano_pechorskuyu_gazovuyu_kompaniyu/'],
]
NEW_SRC = OLD_SRC + [
    ['БНК', 'https://www.bnkomi.ru/data/news/160140/'],
    ['list-org.com', 'https://www.list-org.com/company/4423988'],
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
