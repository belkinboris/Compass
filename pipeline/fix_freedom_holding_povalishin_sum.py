# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gb7a4435d` («Freedom Holding продал российский бизнес Максиму
Повалишину», закрыта 15.02.2023) — `sum`/`eco.sum` стояли «Не
раскрыта», хотя сумма сделки названа независимыми источниками.

Проверено лично прямым WebFetch:
- Frank Media, https://frankmedia.ru/114256: «покупатель приобретает
  российский бизнес за $140 млн за вычетом суммы обязательств»;
  «Freedom Holding приобрел долю в АО «Фридом Финанс» в ноябре за $91
  млн» (более ранняя, отдельная сделка, породившая встречное
  обязательство холдинга).

По докладу саб-агента (не перепроверено мной лично прямым WebFetch):
fbroker.kz со ссылкой на Forbes.ru называет структуру суммы точнее —
«за российские активы Повалишин заплатит около $33 млн» плюс
«переуступит обязательства холдинга... по отсроченному платежу в 6,6
млрд рублей (около $107 млн)», что в сумме даёт те же $140 млн; цитата
Тимура Турлова (dp.ru) о продаже «по цене, основанной на текущих
активах», без премии за гудвилл.

НЕ ВНЕСЕНО: оценка аналитика Андрея Бархоты (чистые активы ~13,4 млрд
₽ + капитал банка 1,5 млрд ₽, мультипликатор ≈0,63х) — вторичный
источник (rb.ru пересказывает мнение аналитика, не проверено прямым
чтением его собственных расчётов); подробности ребрендинга в «Цифра
брокер»/«Цифра банк» и последующее развитие (IPO, санкционный эпизод
2024 года) — не структурные факты этой сделки, за рамками правки.

Запуск: python3 pipeline/fix_freedom_holding_povalishin_sum.py
        python3 pipeline/fix_freedom_holding_povalishin_sum.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb7a4435d'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '$140 млн'

OLD_ECO_CONTEXT = (
    'Все расчеты между Freedom Holding и новым владельцем проведены, '
    'уточняется в пресс-релизе компании (есть у «Ъ»).'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По данным Frank Media, покупатель приобрёл'
    ' российский бизнес за $140 млн за вычетом суммы обязательств;'
    ' ранее, в ноябре 2022 года, Freedom Holding отдельно приобрёл'
    ' долю в казахстанском АО «Фридом Финанс» за $91 млн.'
)

NEW_SRC = [
    ['Frank Media', 'https://frankmedia.ru/114256'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
