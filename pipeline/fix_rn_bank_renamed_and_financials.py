# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g2a27e6b5` («Автоваз» покупает «РН Банк» у альянса Renault-Nissan и
UniCredit», Закрыта) — переименование банка после сделки и его
дальнейшие финансовые показатели не были отражены.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- vedomosti.ru/business/news/2023/07/21/986441 (21.07.2023, 19:34):
  «"АвтоВАЗ" решил переименовать "РН банк", приобретенный у холдинга
  BARN B.V., в "Авто финанс банк"»; «Сделка была закрыта в конце июня
  этого года»; «"АвтоВАЗ" избрал новый состав совета директоров,
  досрочно прекратив полномочия прежнего».
- kommersant.ru/doc/8462205 (25.02.2026, 11:56): «Чистая прибыль АО
  «Авто Финанс Банк» по российским стандартам бухгалтерского учета
  (РСБУ) за 2025 год составила четыре млрд рублей»; «АвтоВАЗ получит
  дивиденды в размере два млрд рублей от дочернего АО «Авто Финанс
  Банк» за 2025 год» — подтверждает, что АвтоВАЗ по-прежнему
  единственный акционер спустя более двух лет после закрытия сделки.

НЕ ВНЕСЕНО: показатели за 2024 год и первое полугодие 2025 года,
квартальная отчётность по МСФО за 1К 2026 — эти цифры сабагент нашёл
только через сниппеты WebSearch (сам сайт autofinancebank.ru дважды
отдал 401/503 при прямой проверке), дословно не подтверждены.

Запуск: python3 pipeline/fix_rn_bank_renamed_and_financials.py
        python3 pipeline/fix_rn_bank_renamed_and_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2a27e6b5'

OLD_ECO_CONTEXT = (
    'В июне 2023 года «АвтоВАЗ» закрыл сделку по приобретению 100% акций '
    'РН банка у холдинговой компании BARN B.V.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' 21 июля 2023 года банк переименован в «Авто финанс '
    'банк», совет директоров переизбран. За 2025 год банк заработал по '
    'РСБУ 4 млрд ₽ чистой прибыли и выплатил «АвтоВАЗу» как единственному '
    'акционеру 2 млрд ₽ дивидендов.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
