# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF): изначально работа шла над карточкой
g70ea4673 (Sminex/«Инград»), но пока факты собирались, другая, параллельно
работавшая сессия нашла и слила дубль (`pipeline/merge_smineks_ingrad_dup.py`,
28 августа 2026): g70ea4673 оказалась дублем `gdda3e685` («Продажа
«Инграда» девелоперу Sminex») и была удалена, `merged['g70ea4673'] =
'gdda3e685'`. Резюрестировать удалённую карточку было бы неверно — это
откатило бы уже сделанную и верную работу по дедупликации; вместо этого
собранные факты перенесены на ОСТАВШУЮСЯ карточку, где их ещё не было. Все
цитаты подтверждены лично прямым WebFetch (см. также
pipeline/fix_kievskaya_ploshchad_samolet_postdeal_context.py и
pipeline/fix_mts_fiksiki_riki_postdeal_context.py — остальные две карточки
того же захода очереди, слияние их не затронуло).

1. Продавец — концерн «Россиум» (Роман Авдеев, Сергей Судариков): «Sminex
   закрыла сделку по покупке девелопера «Инград» у концерна «Россиум»»
   (vlasti.io). Структурное поле `seller` было пустым даже на оставшейся,
   более сильной карточке.
2. Гендиректор «Россиума» Вячеслав Шелопутов о причине продажи: компания
   продаёт «на пике инвестиционной стоимости» (monocle.ru) — идёт в
   `eco.context`, а не в `eco.val`: там уже стоят две независимые оценки
   суммы (Трубачев 38–40 млрд, Шелковский 35–40 млрд), третья оценка того
   же порядка добавила бы дубль числа, а не новый факт.
3. Судьба непрофильных активов ПОСЛЕ сделки: `extra` карточки уже несёт
   факт про ПОИСК покупателей на 8 площадок (перенесён при слиянии дубля),
   но не про их РЕЗУЛЬТАТ — премиальный жилой комплекс Foriver Residence на
   Симоновской набережной перепродан структуре, связанной с ГК
   «Сибпромстрой» (Спортивно-строительная компания), сделка закрыта
   24 июня 2025 года (vedomosti.ru).

`followup_researched` карточки уже стоит (2026-08-23, более ранний заход
той же месячной очереди) — не трогается повторно: штамп фиксирует факт
дельта-обыска, а не переписывается при каждой новой находке.

Запуск: python3 pipeline/fix_sminex_ingrad_seller_and_postdeal.py
        python3 pipeline/fix_sminex_ingrad_seller_and_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdda3e685'

OLD_SELLER = None
NEW_SELLER = 'Концерн «Россиум»'

OLD_CONTEXT = (
    'Для Sminex это вторая за два года сделка по приобретению крупного '
    'девелопера. В 2022 году за 38 млрд руб. компания купила «Интеко». '
    'После приобретения Инграда портфель реализованной недвижимости '
    'включает 117 проектов общей площадью 11.7 млн кв. м.'
)
CONTEXT_ADDITION = (
    ' Продавцу, концерну «Россиум», принадлежат бизнесмены Роман Авдеев и '
    'Сергей Судариков; гендиректор концерна Вячеслав Шелопутов заявил, что '
    'компания продаёт «Инград» «на пике инвестиционной стоимости» '
    '(Monocle). Один из проектов, которым Sminex позже искала покупателя, '
    'уже нашёл его: премиальный жилой комплекс Foriver Residence на '
    'Симоновской набережной перешёл структуре, связанной с ГК '
    '«Сибпромстрой» (Спортивно-строительная компания), — «по данным '
    '«СПАРК-Интерфакса», сделка была закрыта 24 июня» 2025 года '
    '(Ведомости).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Vlasti.io', 'https://vlasti.io/amp/news/126004-alekcej_tulupov_izvestnyj_kak_rejder_priobrel_aktivy_u_skandaljno_izvestnyh_romana_avdeeva_i_sergeja_sudarikova'],
    ['Monocle', 'https://monocle.ru/monocle/2024/44/sminex-prodolzhayet-skupat-krupnykh-developerov/'],
    ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/06/27/1120479-sminex-prodala-esche-odin-proekt-developera-ingrad'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') == OLD_SELLER
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
