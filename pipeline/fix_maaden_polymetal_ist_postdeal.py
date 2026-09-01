# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
geb236ba2 (Госкомпания Омана Maaden International Investment купила
23,9% акций Polymetal у группы ИСТ, закрыта в январе 2024) — Polymetal
довёл до конца более крупный шаг, о котором сама карточка уже
упоминала как о планах: продал весь российский бизнес отдельно от
доли ИСТ, а оманский инвестор нарастил долю и стал стратегическим
партнёром за пределами исходной сделки.

Проверено лично прямым WebFetch (Интерфакс, 19.02.2024,
interfax.ru/business/946692): «Polymetal заключил соглашение о
продаже своего российского бизнеса в лице АО "Полиметалл"» компании
«Мангазея Плюс» (структура группы «Мангазея» Сергея Янчукова) —
активы оценены в $3,69 млрд (включая $2,21 млрд чистого долга),
денежный компонент покупателю — $50 млн. Сделка закрыта к 11 марта
2024 года (по данным саб-агента, dp.ru); компания сменила название на
Solidcore Resources и сосредоточилась на активах в Казахстане.

Рост доли Омана и совместный проект — по данным саб-агента (не
проверено дополнительно прямым WebFetch в этом заходе, кроме
подтверждения самой продажи «Мангазее»): доля Maaden выросла с 23,9%
до 29,7–31,7%; в июле 2026 Solidcore и Minerals Development Oman
подписали соглашение о геолого-разведочном проекте Khabiyat в Омане.

НЕ ВКЛЮЧЕНО в структурные поля: точная текущая доля Maaden (источники
2025-2026 годов расходятся в цифре — 29,7% против 31,7%, решение о
том, какую называть, требует отдельной проверки) — оставлено общей
фразой «выросла»; судьба группы ИСТ/Александра Несиса после выхода —
саб-агент не нашёл ни одного источника 2025-2026 годов о новых
крупных сделках группы, поэтому в карточку не добавляется.

Запуск: python3 pipeline/fix_maaden_polymetal_ist_postdeal.py
        python3 pipeline/fix_maaden_polymetal_ist_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'geb236ba2'

OLD_EXTRA = (
    'Сделка закрыта в январе 2024. Покупатель — Maaden International '
    'Investment LLC, дочерняя компания государственного фонда Омана '
    'Mars Development and Investment LLC. Продавец — ICT Holding '
    'Limited (группа ИСТ, возглавляемая Александром Несисом и '
    'партнерами). Продажа доли 23,9% акций Polymetal.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' 19 февраля 2024 года, отдельно от доли ИСТ, Polymetal объявил о '
    'продаже ВСЕГО российского бизнеса (АО «Полиметалл») группе '
    '«Мангазея» Сергея Янчукова — активы оценены в $3,69 млрд '
    '(включая $2,21 млрд чистого долга), сделка закрыта к марту 2024 '
    'года; компания сменила название на Solidcore Resources и '
    'сосредоточилась на активах в Казахстане. Доля Maaden в Solidcore '
    'с тех пор выросла, а в июле 2026 года стороны подписали '
    'соглашение о совместном геолого-разведочном проекте в Омане.'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/946692'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

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
