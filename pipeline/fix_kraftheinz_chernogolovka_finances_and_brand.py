# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gfca749be («Kraft Heinz продает производство детского питания ГК
«Черноголовка»», закрыта 19 марта 2024) — финансы и мощности предмета
не были заполнены, а судьба лицензионного бренда Heinz после сделки
не прослежена.

Проверено лично прямым WebFetch (Интерфакс, источник самой карточки,
https://www.interfax.ru/business/951165): холдинговая компания
покупателя — «АО "Аквалайф ресурс"»; мощности — «более 20 тысяч тонн
готовой продукции в год» (Иваново), «12 тысяч тонн готовой продукции в
год» (Георгиевск); дата публикации о закрытии — 19 марта 2024.

НЕ ВКЛЮЧЕНО: индивидуальные показатели выручки заводов за 2021 год
(555,9 млн ₽ и 282,3 млн ₽) — источник (interfax.ru/russia/893754)
не проверен лично, взят только по докладу саб-агента; запуск бренда
Gipopo взамен лицензионного Heinz в 2024 году — это ОТДЕЛЬНОЕ,
более позднее событие с собственным источником
(interfax.ru/business/970465), не проверенное лично в этом прогоне —
не вносится без отдельной проверки; причина девятимесячной задержки
закрытия (лето 2023 → март 2024) — ни один источник её не объясняет;
финансовый консультант сделки — не назван ни в одном из шести
прочитанных источников.

Запуск: python3 pipeline/fix_kraftheinz_chernogolovka_finances_and_brand.py
        python3 pipeline/fix_kraftheinz_chernogolovka_finances_and_brand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfca749be'

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Совокупные мощности заводов — более 30 000 тонн сухих, жидких каш и '
    'пюре в год: свыше 20 000 тонн в Иванове и 12 000 тонн в Георгиевске.'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/951165'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
