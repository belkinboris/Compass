# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gmru-svoj-kredit-evropa-strah` (Группа «Свой» купила страховщика
«Кредит Европа лайф» у «Кредит Европа банка», Закрыта, 27 июля 2026) —
проверка, не появилось ли новых фактов о продавце и о судьбе актива
после сделки.

Проверено ЛИЧНО прямым WebFetch (asn-news.ru/news/92310, полный текст):
«Продавец — «Кредит Европа банк», российская «дочка» турецкой
финансовой группы Fiba Group»; «Интеграция пройдет поэтапно: сначала
объединение IT-платформ и тестирование рабочих процессов, затем смена
названия компании.» Группа намерена сохранить существующие страховые
программы и запустить новые цифровые решения. На дату этого прогона
(6 сентября 2026) само переименование ещё не состоялось — источники
говорят только о ПЛАНАХ, а не о свершившемся факте.

Независимо подтверждено 1prime.ru (20260727/strakhovaya-871781018.html)
и finance.mail.ru — все источники сходятся, что точная сумма сделки
по-прежнему не раскрыта нигде (только уже известная оценочная вилка
400–600 млн ₽).

`buyer_name`/`seller`/`status`/`title` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_svoj_kredit_evropa_integration_plans.py
        python3 pipeline/fix_svoj_kredit_evropa_integration_plans.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-svoj-kredit-evropa-strah'

OLD_ECO_CONTEXT = (
    'В начале этого года холдинг IDF Eurasia объединил все активы в '
    'финансовую группу под единым брендом «Свой»: «Свой банк», «Свой '
    'капитал», две IT-компании — IDF Technology и IDF Lab, две '
    'микрофинансовые организации — Moneyman и Platiza, а также два '
    'коллекторских агентства — ID Collect и «Финансовые системы». Ещё '
    'раньше, в конце 2023 года, холдинг завершил переезд из Республики '
    'Кипр в Россию.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Продавец, «Кредит Европа банк», — российская '
    '«дочка» турецкой финансовой группы Fiba Group. Интеграцию '
    'планируют провести поэтапно: сначала объединить IT-платформы и '
    'протестировать рабочие процессы, затем сменить название компании '
    '— на дату этого прогона переименование ещё не состоялось; текущие '
    'страховые программы группа намерена сохранить, добавив новые '
    'цифровые решения.'
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
