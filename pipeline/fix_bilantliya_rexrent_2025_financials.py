# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g3147f84e` («Инвестиционная группа «Инсайт» купила 100% акций АО
«Билантлия» (оператор аренды автомобилей RexRent/Avis)», 2022,
Закрыта) — финансовая судьба предприятия после сделки не
прослеживалась дальше 2022 года.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- list-org.com/company/4196276: выручка 2024 года «1 098 090 тыс. ₽»,
  чистая прибыль «84 930 тыс. ₽»; выручка 2025 года «1 133 480 тыс. ₽»
  (рост ~3%), чистая прибыль «88 054 тыс. ₽» (рост ~4%); директор —
  Мелехин Евгений Владимирович; учредители на странице агрегатора не
  раскрыты («Не указаны»).

НЕ ВНЕСЕНО: (1) утверждение, что лизинговые активы группы «Инсайт»
(включая «Билантлию»/RexRent) выделены в отдельную структуру «Инсайт
Лизинг»/«ФЛИТ» — встретилось только в агрегированной выдаче поиска
(сниппеты insightgroup.ru, companies.rbc.ru), прямого чтения ни одной
из этих страниц не получилось (rbc.ru отдал 401); (2) сообщение о
продаже Аветом Миракяном своей доли в группе (1prime.ru, 28.12.2024)
— тоже только сниппет, не проверено дословным чтением; ни то ни другое
не переносится без прямой проверки.

Запуск: python3 pipeline/fix_bilantliya_rexrent_2025_financials.py
        python3 pipeline/fix_bilantliya_rexrent_2025_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3147f84e'

OLD_ECO_CONTEXT = (
    'Миракян вместе с партнёрами создал группу «Инсайт» в 2022 году. Ему '
    'принадлежит 80% компании, ещё по 4% — у Артёма Астанина, Антона '
    'Баршта, Михаила Гонопольского, Алексея Комара и Давида Погосяна. '
    'Группа уже купила несколько кэптивных лизинговых операторов у '
    'международных компаний, ушедших из России, — в том числе у Siemens и '
    'Deere & Co.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Бизнес продолжает работать и понемногу расти: '
    'выручка 2025 года — 1,13 млрд ₽ (+3% к 2024-му), чистая прибыль — '
    '88 млн ₽ (+4%).'
)

OLD_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/914356'],
]
NEW_SRC = OLD_SRC + [
    ['list-org.com', 'https://www.list-org.com/company/4196276'],
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
