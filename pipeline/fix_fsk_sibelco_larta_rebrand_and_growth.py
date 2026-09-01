# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g369b9b26 (ФСК купил российские активы Sibelco, закрыта 10.11.2023) —
активы переименованы в бренд «Ларта», Sibelco подтвердила полный выход
из России, бизнес растёт новыми инвестициями.

Проверено лично прямым WebFetch (сайт Sibelco,
https://www.sibelco.com/en/news/sibelco-completes-the-divestment-of-its-business-in-russia):
«Today, Sibelco is announcing the completion of the sale of our
business in Russia to FSK Group, a leader in the Russian building
construction sector, effective immediately» — полный, а не частичный
выход подтверждён самой компанией-продавцом.

Проверено лично прямым WebFetch (audit-it.ru,
https://www.audit-it.ru/contragent/1025005120470_ao-ramenskiy-gok):
управляющая организация АО «Раменский ГОК» — «ООО "Ларта Минералс"»;
2025 год — «выручку в сумме 3,3 млрд руб.» (+15,9%), прибыль 779 млн
руб. (годом ранее, 2024 — убыток 69,5 млн руб.); с 15 сентября 2025
года комбинат «находится в процессе реорганизации в форме присоединения
к нему других юридических лиц».

По данным саб-агента (не дозаверено отдельным WebFetch, но именной
источник — abireg.ru): бывший «Сибелко Воронеж» переименован в «Ларта
Минералс Воронеж», выручка за 2025 год — 1,4 млрд руб., чистая прибыль
— 298,9 млн руб.; компания планирует вложить 500 млн руб. в 2026–2028
годах в производство огнеупорных глин в Хохольском районе. Сумма самой
сделки 2023 года по-прежнему нигде не раскрыта — включая финансовую
отчётность Sibelco за 2023 год, где фигурирует лишь бухгалтерский убыток
ПРОДАВЦА от выбытия российского бизнеса (26,8 млн евро) — это не цена
сделки, и в карточку как сумма не идёт (правило «Число может быть
верным фактом и совсем не той величиной»).

НЕ ВКЛЮЧЕНО: реальная (не только организационно-брендовая) синергия с
бывшими стекольными активами NSG («Ларта Гласс», ГК STiS) — источники
подтверждают только объединение под общей управляющей структурой EVA,
физических поставок сырья на стекольные заводы не подтверждают; судьба
торгового дома в Санкт-Петербурге отдельно от группы — не упоминается
ни в одном источнике после 2023 года.

Запуск: python3 pipeline/fix_fsk_sibelco_larta_rebrand_and_growth.py
        python3 pipeline/fix_fsk_sibelco_larta_rebrand_and_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g369b9b26'

NEW_EXTRA = (
    'Активы переименованы в бренд «Ларта»: «Сибелко Рус» стало «Ларта '
    'Минералс» (управляет Раменским ГОКом), «Сибелко Воронеж» — «Ларта '
    'Минералс Воронеж», «Сибелко Неболчи» — «Ларта Минералс Неболчи». '
    'Sibelco подтвердила полный выход из России. Бизнес растёт: '
    'выручка Раменского ГОКа за 2025 год — 3,3 млрд ₽ (после убытка в '
    '2024-м комбинат вышел в прибыль, 779 млн ₽), «Ларта Минералс '
    'Воронеж» планирует вложить 500 млн ₽ в 2026–2028 годах в '
    'производство огнеупорных глин.'
)

NEW_SRC = [
    ['Sibelco', 'https://www.sibelco.com/en/news/sibelco-completes-the-divestment-of-its-business-in-russia'],
    ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1025005120470_ao-ramenskiy-gok'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('extra') is None

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
