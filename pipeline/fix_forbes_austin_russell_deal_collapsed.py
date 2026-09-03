# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g8b9d2708` («Остин Рассел купил контрольный пакет Forbes», статус
«Закрыта», $800 млн, 2023) — СДЕЛКА НЕ ЗАКРЫЛАСЬ. Карточка утверждала
закрытие как факт, хотя сделка была расторгнута сторонами 21 ноября
2023 года — это не уточнение детали, а неверный факт в структурном
поле `status`.

Проверено лично прямым WebFetch двумя НЕЗАВИСИМЫМИ источниками (сама
Washington Post отдаёт 403 при прямом чтении):

- TechCrunch, 21.11.2023,
  https://techcrunch.com/2023/11/21/tech-ceo-austin-russells-bid-to-buy-forbes-fails/ —
  «Tech CEO Austin Russell's bid to buy Forbes fails»; заявление
  семейного офиса Рассела: «it was determined that it was in the best
  interest of the parties that the contract be terminated»; Рассел
  «failed to secure the ideal group of investors needed to close the
  deal», часть инвесторов (в т.ч. Sun Group) не перечислила
  обязательные средства; Forbes остаётся в собственности гонконгской
  Integrated Whale Media Investments, контролирующей 95% компании с
  2014 года.
- Kyiv Independent, 21.11.2023,
  https://kyivindependent.com/forbes-cancels-sale-to-russian-oligarch-linked-billionaire/ —
  «The parent company of Forbes magazine is no longer going forward
  with a sale to billionaire Austin Russell»; сделка на 82% Forbes
  Global Media Holdings оценивалась в $800 млн; «The sale had already
  been paused for weeks after missing a Nov. 1 deadline».

Причина срыва, по заявлениям сторон, — не переведённые синдикатом
инвесторов (в т.ч. индийская Sun Group) деньги к дедлайну закрытия, а
не прямое признание версии Мусаева; источники это разделяют явно, и
карточка следует за источниками, а не домысливает причинно-следственную
связь с публикацией Washington Post.

Побочно найдено и внесено в `eco.context`: в сентябре 2024 года
появились новые, независимые переговоры о продаже Forbes — фонду Koch
Equity Development в партнёрстве с предпринимателем Дивьянком Туракхиа,
целевая оценка $550-600 млн (Axios, 24.09.2024,
https://www.axios.com/2024/09/24/forbes-koch-marketplace-deal-acquisition-talks —
пересказ саб-агента, прямым WebFetch НЕ перепроверен, вносится с
пометкой источника). Подтверждений закрытия или срыва этих переговоров
на сентябрь 2026 года не нашлось — это отдельный, ещё не завершённый
сюжет, в структурные поля (`buyer`/`status`) не переносится.

НЕ ВКЛЮЧЕНО: судьба самого Остина Рассела и его компании Luminar
Technologies в 2025-2026 (отставка, банкротство, иски) — это личная и
корпоративная история ПОСЛЕ несостоявшейся сделки, не имеющая прямого
отношения к судьбе Forbes; официальное расследование SEC/OFAC/CFIUS
именно по эпизоду Мусаев-Рассел-Forbes не подтверждено (только
сенаторское давление и угроза обзора CFIUS, не факт начатой проверки) —
вносить как «расследование» было бы натяжкой.

Запуск: python3 pipeline/fix_forbes_austin_russell_deal_collapsed.py
        python3 pipeline/fix_forbes_austin_russell_deal_collapsed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8b9d2708'

OLD_STATUS = 'Закрыта'
NEW_STATUS = 'Не состоялась'

OLD_EXTRA = (
    'Согласно Washington Post и Kommersant, американский миллиардер '
    'Остин Рассел выкупил контрольный пакет акций глобальной '
    'медиагруппы Forbes. По утверждению владельца АС Рус Медиа '
    '(издателя Forbes Russia) Магомеда Мусаева, он являлся истинным '
    'покупателем, а Рассел выступал в роли публичного лица сделки. '
    'Обе стороны официально отрицают эту информацию.'
)
NEW_EXTRA = (
    'Американский миллиардер Остин Рассел (основатель Luminar '
    'Technologies) договорился о выкупе 82% Forbes Global Media '
    'Holdings у гонконгской Integrated Whale Media Investments за '
    '$800 млн, но сделка была расторгнута сторонами 21 ноября 2023 '
    'года: часть заявленных соинвесторов (в том числе индийская Sun '
    'Group) не перечислила обещанные средства к дедлайну закрытия '
    '(1 ноября 2023 года). По утверждению владельца АС Рус Медиа '
    '(издателя Forbes Russia) Магомеда Мусаева, прозвучавшему в '
    'аудиозаписи, которую опубликовала Washington Post, он являлся '
    'истинным покупателем, а Рассел выступал в роли публичного лица '
    'сделки; обе стороны официально отрицают эту информацию. Forbes '
    'остался под контролем Integrated Whale Media Investments, '
    'контролирующей ~95% компании с 2014 года.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'В сентябре 2024 года появились новые переговоры о продаже Forbes '
    '— фонду Koch Equity Development (структура семьи Кох) в '
    'партнёрстве с предпринимателем Дивьянком Туракхиа; целевая оценка '
    'называлась на уровне $550-600 млн, ниже суммы несостоявшейся '
    'сделки с Расселом. Подтверждений закрытия или срыва этих '
    'переговоров не нашлось.'
)

NEW_SRC = [
    ['TechCrunch', 'https://techcrunch.com/2023/11/21/tech-ceo-austin-russells-bid-to-buy-forbes-fails/'],
    ['Kyiv Independent', 'https://kyivindependent.com/forbes-cancels-sale-to-russian-oligarch-linked-billionaire/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['extra'] = NEW_EXTRA
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
