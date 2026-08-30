# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g26b319ff (банк «Траст» вышел из Объединенной вагонной компании с
убытком) — покупатель («профильный инвестор») не был назван вовсе
(поле `buyer` пустое). Проверено лично прямым WebFetch двух
источников.

`buyer_name` (новое поле). Сам «Траст» покупателя официально не
называл — дословно (Ведомости): «Детали сделки и покупателя активов
ОВК глава "Траста" раскрывать отказался, сославшись на важность этой
сделки для государства». Но 25 апреля 2024 года один из покупателей
раскрыл себя сам. Дословно (Frank Media): «Акционеры "Уральской
горно-металлургической компании" (УГМК) выкупили 96% акций,
принадлежащие банку непрофильных активов (БНА) "Траст"»; цитата
Андрея Бокарева: «купили акционеры УГМК, но не на УГМК, а это частные
пакеты» — четыре акционера УГМК получили равные доли как личные
инвестиции, а не корпоративная сделка самой УГМК. Полный список из
четырёх имён нигде не опубликован — записано то, что раскрыто:
Бокарев и другие акционеры УГМК, частные пакеты.

`eco.context` (заполнено, было «—»). Независимая оценка результатов
ОВК после сделки: дословно (smart-lab.ru, со ссылкой на отчётность):
«Прибыль мсфо 32,046 млрд руб» за 2024 год против «21,7 млрд рублей»
за 2025-й — то есть чистая прибыль по МСФО снизилась на 30,9% (цифра
из независимой сводки WebSearch подтверждена direct-цитатой той же
статьи по 2024 году).

НЕ ВКЛЮЧЕНО: выручка и объём выпуска вагонов за 2025 год — прямой
источник (rollingstockworld.ru) отдал 503 при трёх попытках, а
показатели по РСБУ головной компании (выручка 3,71 млрд ₽, прибыль
148,8 млн ₽) относятся к юрлицу-холдингу отдельно от консолидированной
группы (МСФО) — смешивать эти две величины было бы ошибкой того же
класса, что уже описана в CLAUDE.md («соседние числа считаются от
разных знаменателей»), поэтому из РСБУ ничего не перенесено. Сумма
сделки и консультанты — не раскрыты ни в одном источнике.

Запуск: python3 pipeline/fix_trast_ovk_buyer_bokarev.py
        python3 pipeline/fix_trast_ovk_buyer_bokarev.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g26b319ff'

NEW_BUYER_NAME = 'Андрей Бокарев и другие акционеры УГМК (частные пакеты)'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'По данным независимой отчётности, чистая прибыль ОВК по МСФО '
    'снизилась с 32,05 млрд ₽ (2024) до 21,7 млрд ₽ (2025) — на 30,9%.'
)

NEW_SRC = [
    ['Frank Media', 'https://frankmedia.ru/162877'],
    ['Ведомости', 'https://www.vedomosti.ru/finance/articles/2024/02/14/1020217-bank-neprofilnih-aktivov-zavershil'],
    ['smart-lab.ru', 'https://smart-lab.ru/blog/1288467.php'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('buyer') is None, deal.get('buyer')
    assert 'buyer_name' not in deal, deal.get('buyer_name')
    assert deal['eco']['context'] == OLD_CONTEXT, deal['eco']['context']
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== buyer_name (новое поле) ===')
    print(NEW_BUYER_NAME)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
